"""Library-based SASRec + NSGA-II experiment; every score is a proxy, not experience."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
from importlib.metadata import distributions
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.core.repair import Repair
from pymoo.indicators.hv import HV
from pymoo.operators.crossover.pntx import TwoPointCrossover
from pymoo.operators.mutation.bitflip import BitflipMutation
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from scipy.stats import rankdata
import torch

ROOT = Path(__file__).resolve().parent
POSITIVE_DEFINITION = "history_mean_centered_gt_0"
COMPARISON_METHODS = ["sasrec", "weighted_distance_selected", "nsga2"]
METRICS = ["recall", "ndcg", "candidate_recall", "relevance", "genre_distance",
           "s_proxy", "heldout_distance", "seconds"]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def chronological_split(ratings):
    """Global cuts: an entire timestamp group stays on the same side."""
    ordered = ratings.sort_values(["timestamp", "user_id", "item_id"], kind="stable")
    cuts = [int(ordered.timestamp.iloc[int(len(ordered) * fraction)]) for fraction in (0.8, 0.9)]
    parts = [ordered[ordered.timestamp < cuts[0]].copy(),
             ordered[(ordered.timestamp >= cuts[0]) & (ordered.timestamp < cuts[1])].copy(),
             ordered[ordered.timestamp >= cuts[1]].copy()]
    if any(part.empty for part in parts):
        raise ValueError("Timestamp groups do not permit three nonempty time splits")
    return parts, cuts


def load_data(directory):
    ratings = pd.read_csv(directory / "u.data", sep="\t", header=None,
                          names=["user_id", "item_id", "rating", "timestamp"])
    items = pd.read_csv(directory / "u.item", sep="|", header=None, encoding="latin-1")
    if ratings.isna().any().any() or ratings.duplicated(["user_id", "item_id"]).any():
        raise ValueError("Expected complete, unique MovieLens user/item ratings")
    if not ratings.rating.between(1, 5).all() or not set(ratings.item_id) <= set(items[0]):
        raise ValueError("Invalid ratings or missing item metadata")
    genres = items.set_index(0).iloc[:, 4:].astype(float)
    if genres.shape[1] != 19 or not genres.isin([0, 1]).all().all():
        raise ValueError("Expected MovieLens 100K's 19 binary genre fields")
    if (genres.sum(axis=1) == 0).any():
        raise ValueError("Every movie needs at least one genre (including unknown)")
    genres = genres.div(genres.sum(axis=1), axis=0)
    return ratings, genres


def prepare_recbole(train, config, output):
    from recbole.config import Config
    from recbole.data import create_dataset
    from recbole.data.dataloader import TrainDataLoader

    atomic = output / "atomic" / "temporal-ml100k"
    atomic.mkdir(parents=True)
    # Only train tokens enter RecBole's vocabulary. Rank preserves time ordering
    # without float32 rounding of Unix timestamps inside RecBole.
    frame = train[["user_id", "item_id", "timestamp"]].copy()
    frame.timestamp = frame.timestamp.rank(method="dense").astype(int)
    frame.columns = ["user_id:token", "item_id:token", "timestamp:float"]
    frame.to_csv(atomic / "temporal-ml100k.inter", sep="\t", index=False)
    cfg = Config(model="SASRec", dataset="temporal-ml100k", config_dict={
        "data_path": str(atomic.parent), "use_gpu": False, "seed": config["seed"],
        "load_col": {"inter": ["user_id", "item_id", "timestamp"]},
        "reproducibility": True, "epochs": config["epochs"],
        "stopping_step": config["patience"], "eval_step": 1,
        "train_batch_size": config["train_batch_size"],
        "train_neg_sample_args": None, "loss_type": "CE",
        "eval_args": {"split": {"RS": [1, 0, 0]}, "order": "TO",
                      "group_by": None, "mode": "full"},
        "checkpoint_dir": str(output / "checkpoints"), "show_progress": False,
        "valid_metric": f"NDCG@{config['model_selection_k']}", "metrics": ["NDCG"],
        "topk": [config["model_selection_k"]],
        "log_wandb": False,
    })
    dataset = create_dataset(cfg)
    train_dataset = dataset.build()[0]
    loader = TrainDataLoader(cfg, train_dataset, sampler=None, shuffle=True)
    (output / "recbole_config.txt").write_text(str(cfg))
    return cfg, train_dataset, loader


def make_cases(history, future, train, genre_frame, dataset, k):
    """One frozen query per user at the start of the evaluation window."""
    token_map = dataset.field2token_id["item_id"]
    trained_users = set(train.user_id)
    catalog = np.array(sorted(int(i) for i in token_map if i != "[PAD]"))
    histories = {u: h for u, h in history.groupby("user_id", sort=True)}
    counts = Counter(eligible_users=0, no_positive_history_users=0, no_eligible_positive_users=0)
    user_diagnostics = []
    cases = []
    for user, target in future.groupby("user_id", sort=True):
        counts["window_users"] += 1
        counts["window_events"] += len(target)
        counts["cold_item_events"] += int((~target.item_id.isin(catalog)).sum())
        h = histories.get(user, history.iloc[:0])
        # Freeze the baseline from all past ratings, before catalog filtering.
        # Validation receives train; test receives train + validation, never target.
        user_mean = float(h.rating.mean())
        positive_history = h[((h.rating - user_mean) > 0) & h.item_id.isin(catalog)]
        positives = set(target.loc[((target.rating - user_mean) > 0)
                                   & target.item_id.isin(catalog), "item_id"])
        positives -= set(h.item_id)
        diagnostic = {"user_id": int(user), "history_rating_mean": user_mean if len(h) else None,
                      "positive_history_count": len(positive_history),
                      "future_positives_count": len(positives), "status": "eligible"}
        user_diagnostics.append(diagnostic)
        if user not in trained_users:
            counts["cold_user_users"] += 1
            counts["cold_user_events"] += len(target)
            diagnostic["status"] = "cold_user"
            continue
        if positive_history.empty:
            counts["no_positive_history_users"] += 1
            diagnostic["status"] = "no_positive_history"
            continue
        if not positives:
            counts["no_eligible_positive_users"] += 1
            diagnostic["status"] = "no_eligible_positive"
            continue
        available = catalog[~np.isin(catalog, h.item_id)]
        if len(available) < k:
            counts["insufficient_candidates_users"] += 1
            diagnostic["status"] = "insufficient_candidates"
            continue
        h = h.sort_values(["timestamp", "item_id"], kind="stable")
        sequence = [token_map[str(i)] for i in h.item_id if str(i) in token_map]
        profile = genre_frame.loc[positive_history.item_id].to_numpy().mean(axis=0)
        counts["eligible_users"] += 1
        counts["eligible_positive_items"] += len(positives)
        cases.append({"user": int(user), "sequence": sequence, "available": available,
                      "profile": profile, "positives": positives})
    if not cases:
        raise ValueError(f"No eligible evaluation users: {dict(counts)}")
    return cases, {**counts, "positive_definition": POSITIVE_DEFINITION, "users": user_diagnostics}


def distance(profile, genre_rows):
    return 0.5 * np.abs(genre_rows - profile).sum(axis=1)


@torch.no_grad()
def score_cases(model, cases, dataset, genre_frame, pool_size):
    from recbole.data.interaction import Interaction

    model.eval()
    token_map = dataset.field2token_id["item_id"]
    maxlen = model.max_seq_length
    result = []
    for case in cases:
        start = time.perf_counter()
        history = case["sequence"][-maxlen:]
        seq = torch.zeros((1, maxlen), dtype=torch.long)
        seq[0, :len(history)] = torch.tensor(history)
        logits = model.full_sort_predict(Interaction({model.ITEM_SEQ: seq,
            model.ITEM_SEQ_LEN: torch.tensor([len(history)])})).numpy()[0]
        ids = case["available"]
        raw = logits[[token_map[str(i)] for i in ids]]
        if not np.isfinite(raw).all():
            raise ValueError("Non-finite model scores")
        # Ties receive the same percentile; original IDs break recommendation ties.
        relevance = (rankdata(raw, method="average") - 1) / max(1, len(raw) - 1)
        order = np.lexsort((ids, -raw))[:pool_size]
        candidate_ids = ids[order]
        d = distance(case["profile"], genre_frame.loc[candidate_ids].to_numpy())
        result.append({**case, "ids": candidate_ids, "raw": raw[order],
                       "r": relevance[order], "d": d, "s": relevance[order] * d,
                       "inference_seconds": time.perf_counter() - start})
    return result


def choose_top(values, ids, k):
    return np.lexsort((ids, -values))[:k]


def baselines(case, k):
    start = time.perf_counter()
    result = {"sasrec": np.arange(k)}
    durations = {"sasrec": time.perf_counter() - start}
    for weight in np.linspace(0, 1, 11):
        start = time.perf_counter()
        key = f"weighted_distance:{weight:.1f}"
        result[key] = choose_top(weight * case["r"] + (1 - weight) * case["d"], case["ids"], k)
        durations[key] = time.perf_counter() - start
    return result, durations


class SubsetProblem(Problem):
    def __init__(self, r, d, k):
        if len(r) != len(d) or not 1 <= k <= len(r):
            raise ValueError("Invalid subset dimensions")
        self.values = np.column_stack([r, d])
        if not np.isfinite(self.values).all() or not ((self.values >= 0) & (self.values <= 1)).all():
            raise ValueError("Objectives must be finite values in [0, 1]")
        self.k = k
        super().__init__(n_var=len(r), n_obj=2, xl=0, xu=1, vtype=bool)

    def _evaluate(self, x, out, *args, **kwargs):
        if not (np.asarray(x, dtype=bool).sum(axis=1) == self.k).all():
            raise ValueError("Every recommendation must contain exactly k distinct items")
        # BLAS and selected-array means can differ by 1e-16. Do not turn an
        # arithmetic artifact into a relevance/distance trade-off.
        out["F"] = -np.round((x @ self.values) / self.k, 12)


class FixedSizeRepair(Repair):
    def _do(self, problem, x, **kwargs):
        x = x.astype(bool, copy=True)
        for row in x:
            excess = int(row.sum()) - problem.k
            if excess:
                eligible = np.flatnonzero(row if excess > 0 else ~row)
                row[np.random.choice(eligible, abs(excess), replace=False)] = excess < 0
        return x


def objectives(case, lists):
    return np.round([[case["r"][idx].mean(), case["d"][idx].mean()] for idx in lists], 12)


def representative(case, lists, floor, k):
    scores = objectives(case, lists)
    valid = np.flatnonzero(scores[:, 0] >= floor * case["r"][:k].mean() - 1e-12)
    if not len(valid):
        raise ValueError("Missing feasible SASRec baseline in solution archive")
    return min(valid, key=lambda j: (-scores[j, 1], -scores[j, 0],
                                     tuple(sorted(case["ids"][lists[j]]))))


def evolve(case, starts, config, seed):
    k = config["top_k"]
    problem = SubsetProblem(case["r"], case["d"], k)
    if problem.n_var == k:
        return [np.arange(k)], 0, [{"generation": 0,
            "hypervolume": float(np.prod(problem.values.mean(axis=0)))}]
    rng = np.random.default_rng(seed)
    initial = []
    for idx in starts.values():
        row = np.zeros(problem.n_var, dtype=bool)
        row[idx] = True
        initial.append(row)
    initial = np.unique(initial, axis=0)
    target_size = min(config["population"], math.comb(problem.n_var, k))
    while len(initial) < target_size:
        row = np.zeros(problem.n_var, dtype=bool)
        row[rng.choice(problem.n_var, k, replace=False)] = True
        initial = np.unique(np.vstack([initial, row]), axis=0)
    archive = []
    trace = []

    def capture(algorithm):
        archive.append(algorithm.pop.get("X").copy())
        trace.append({"generation": int(algorithm.n_gen),
                      "hypervolume": float(HV(ref_point=np.zeros(2))(algorithm.pop.get("F")))})

    # Fixed-size bitsets make duplicate items impossible. Reuse pymoo's operators.
    minimize(problem, NSGA2(pop_size=max(target_size, len(initial)), sampling=initial,
             crossover=TwoPointCrossover(), mutation=BitflipMutation(),
             repair=FixedSizeRepair(), eliminate_duplicates=True),
             ("n_gen", config["generations"]), seed=seed, callback=capture, verbose=False)
    # Preserve seeds/earlier nondominated solutions lost by finite-population crowding.
    x = np.unique(np.vstack([initial, *archive]), axis=0)
    f = problem.evaluate(x)
    front = NonDominatedSorting().do(f, only_non_dominated_front=True)
    lists = [np.flatnonzero(row) for row in x[front]]
    chosen = representative(case, lists, config["relevance_floor"], k)
    return lists, chosen, trace


def evaluate_list(case, indices, k):
    # A subset's display order is always the fixed SASRec order.
    idx = np.sort(indices)
    hits = np.isin(case["ids"][idx], list(case["positives"])).astype(float)
    n_positive = len(case["positives"])
    discounts = 1 / np.log2(np.arange(k) + 2)
    return {"recall": float(hits.sum() / n_positive),
            "ndcg": float((hits * discounts).sum() / discounts[:min(k, n_positive)].sum()),
            "candidate_recall": float(np.isin(case["ids"], list(case["positives"])).sum() / n_positive),
            "relevance": float(case["r"][idx].mean()),
            "genre_distance": float(case["d"][idx].mean()),
            "s_proxy": float(case["s"][idx].mean()),
            "heldout_distance": float((hits * case["d"][idx]).sum() / k)}


def fit_model(cfg, dataset, loader, valid_cases, genre_frame, config, output):
    from recbole.model.sequential_recommender.sasrec import SASRec
    from recbole.trainer import Trainer
    selection_k = config["model_selection_k"]

    class TemporalTrainer(Trainer):
        def _valid_epoch(self, valid_data, show_progress=False):
            scored = score_cases(self.model, valid_data, dataset, genre_frame, config["candidate_pool"])
            ndcg = float(np.mean([evaluate_list(c, np.arange(selection_k), selection_k)["ndcg"]
                                  for c in scored]))
            history.append({"epoch": len(history) + 1, "validation_ndcg": ndcg})
            print(f"epoch {len(history)} validation NDCG@{selection_k}={ndcg:.6f}", flush=True)
            pd.DataFrame(history).to_csv(output / "training.csv", index=False)
            return ndcg, {f"ndcg@{selection_k}": ndcg}

    history = []
    model = SASRec(cfg, dataset)
    trainer = TemporalTrainer(cfg, model)
    trainer.fit(loader, valid_cases, saved=True, show_progress=False)
    checkpoint = torch.load(trainer.saved_model_file, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["state_dict"])
    write_json(output / "checkpoint.json", {"path": trainer.saved_model_file,
               "selected_epoch": int(checkpoint["epoch"]) + 1,
               "selection_metric": f"NDCG@{selection_k}",
               "validation_ndcg": float(trainer.best_valid_score)})
    return model


def reuse_model(source, cfg, dataset, config, output):
    """Reuse our own checkpoint only when training configuration and IDs agree."""
    from recbole.model.sequential_recommender.sasrec import SASRec
    if json.loads((source / "completion.json").read_text())["status"] != "complete":
        raise ValueError("Source run is incomplete")
    prior = json.loads((source / "config.json").read_text())
    keys = ["seed", "epochs", "patience", "train_batch_size", "threads"]
    if any(prior[key] != config[key] for key in keys) or prior["smoke"]:
        raise ValueError("Cannot reuse a smoke checkpoint or different training configuration")
    # Reranking length can change; the metric used to select the model cannot.
    selection_k = prior.get("model_selection_k", prior["top_k"])
    if selection_k != config["model_selection_k"]:
        raise ValueError("Checkpoint model-selection metric does not match")
    if json.loads((source / "split.json").read_text())["validation"].get("positive_definition") != POSITIVE_DEFINITION:
        raise ValueError("Checkpoint positive definition does not match; train a new model")
    before = json.loads((source / "environment.json").read_text())
    after = json.loads((output / "environment.json").read_text())
    for name in ["recbole", "torch", "numpy"]:
        if before["packages"][name] != after["packages"][name]:
            raise ValueError(f"Checkpoint library version differs: {name}")
    if before["input_sha256"] != after["input_sha256"]:
        raise ValueError("Checkpoint input data does not match")
    if not pd.read_csv(source / "split_assignments.csv").equals(pd.read_csv(output / "split_assignments.csv")):
        raise ValueError("Checkpoint time split does not match")
    for field in ["user_id", "item_id"]:
        if json.loads((source / f"{field}_mapping.json").read_text()) != dataset.field2token_id[field]:
            raise ValueError("Checkpoint token mapping does not match")
    metadata = json.loads((source / "checkpoint.json").read_text())
    checkpoint = source / "checkpoints" / Path(metadata["path"]).name
    # Only a checkpoint created by this local experiment is accepted; never load
    # untrusted third-party pickle files with weights_only=False.
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    model = SASRec(cfg, dataset)
    model.load_state_dict(state["state_dict"])
    (output / "checkpoints").mkdir(exist_ok=True)
    torch.save(state, output / "checkpoints" / checkpoint.name)
    write_json(output / "checkpoint.json", {**metadata,
        "selection_metric": f"NDCG@{selection_k}",
        "path": str(output / "checkpoints" / checkpoint.name), "reused_from": str(source)})
    pd.read_csv(source / "training.csv").to_csv(output / "training.csv", index=False)
    return model


def run_rerank(cases, config, directory):
    directory.mkdir()
    rows, recommendations, candidates, fronts, convergence = [], [], [], [], []
    k = config["top_k"]
    for number, case in enumerate(cases, 1):
        for j, item in enumerate(case["ids"]):
            candidates.append({"user_id": case["user"], "item_id": int(item),
                "sasrec_score": float(case["raw"][j]), "relevance_rank": float(case["r"][j]),
                "genre_distance": float(case["d"][j]), "s_proxy": float(case["s"][j])})
        starts, durations = baselines(case, k)
        methods = [(name, -1, idx, durations[name]) for name, idx in starts.items()]
        for seed in config["search_seeds"]:
            start = time.perf_counter()
            lists, selected, trace = evolve(case, starts, config, seed)
            elapsed = time.perf_counter() - start
            methods.append(("nsga2", seed, lists[selected], elapsed))
            for j, (idx, values) in enumerate(zip(lists, objectives(case, lists))):
                fronts.append({"user_id": case["user"], "seed": seed, "solution": j,
                    "relevance": float(values[0]), "genre_distance": float(values[1]),
                    "selected": j == selected, "item_ids": " ".join(map(str, case["ids"][idx]))})
            convergence.extend({"user_id": case["user"], "seed": seed, **record} for record in trace)
        # A fair scalarization comparison applies the same per-user relevance floor.
        lists = [idx for name, idx in starts.items() if name.startswith("weighted_distance:")]
        start = time.perf_counter()
        selected = representative(case, lists, config["relevance_floor"], k)
        elapsed = sum(v for key, v in durations.items() if key.startswith("weighted_distance:"))
        methods.append(("weighted_distance_selected", -1, lists[selected], elapsed + time.perf_counter() - start))
        for method, seed, idx, elapsed in methods:
            row = {"user_id": case["user"], "method": method, "seed": seed,
                   **evaluate_list(case, idx, k), "seconds": elapsed}
            rows.append(row)
            for rank, j in enumerate(np.sort(idx), 1):
                recommendations.append({"user_id": case["user"], "method": method, "seed": seed,
                                        "rank": rank, "item_id": int(case["ids"][j])})
        if number % 10 == 0 or number == len(cases):
            print(f"{directory.name}: reranked {number}/{len(cases)} users", flush=True)
    for name, values in [("candidates", candidates), ("recommendations", recommendations),
                         ("pareto", fronts), ("convergence", convergence), ("per_user", rows)]:
        pd.DataFrame(values).to_csv(directory / f"{name}.csv", index=False)
    metrics = pd.DataFrame(rows)
    # Average stochastic search seeds WITHIN each user before user-level bootstrap.
    by_user = metrics.groupby(["user_id", "method"])[METRICS].mean().reset_index()
    by_user = by_user[by_user.method.isin(COMPARISON_METHODS)]
    summary = by_user.groupby("method")[METRICS].mean().reset_index()
    summary.to_csv(directory / "summary.csv", index=False)
    rng = np.random.default_rng(config["seed"])
    differences = []
    comparisons = [("weighted_distance_selected", "sasrec"), ("nsga2", "sasrec"),
                   ("nsga2", "weighted_distance_selected")]
    for method, reference in comparisons:
        baseline = by_user[by_user.method == reference].set_index("user_id")
        paired = by_user[by_user.method == method].set_index("user_id").loc[baseline.index]
        for metric in ["recall", "ndcg", "relevance", "genre_distance", "heldout_distance", "seconds"]:
            delta = (paired[metric] - baseline[metric]).to_numpy()
            sampled = rng.choice(delta, (config["bootstrap_samples"], len(delta)), replace=True).mean(axis=1)
            lo, hi = np.quantile(sampled, [0.025, 0.975])
            differences.append({"method": method, "reference": reference, "metric": metric,
                "mean_delta": float(delta.mean()), "ci_low": float(lo), "ci_high": float(hi),
                "users": len(delta)})
    pd.DataFrame(differences).to_csv(directory / "paired_bootstrap.csv", index=False)
    write_json(directory / "inference.json", {"users": len(cases),
        "mean_seconds": float(np.mean([c["inference_seconds"] for c in cases]))})
    return summary


def save_plots(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    front = pd.read_csv(output / "test" / "pareto.csv")
    user = front.user_id.min()
    baseline = pd.read_csv(output / "test" / "per_user.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    for seed, group in front[front.user_id == user].groupby("seed"):
        axes[0].scatter(group.relevance, group.genre_distance, s=12, label=f"NSGA-II seed {seed}")
    scalar = baseline[(baseline.user_id == user) & baseline.method.str.startswith("weighted_distance:")]
    axes[0].scatter(scalar.relevance, scalar.genre_distance, marker="x", c="black", label="Weighted sum (r,d)")
    for method, marker in [("sasrec", "*"), ("weighted_distance_selected", "s")]:
        row = baseline[(baseline.user_id == user) & (baseline.method == method)]
        axes[0].scatter(row.relevance, row.genre_distance, marker=marker, label=method)
    axes[0].set(xlabel="Mean relevance percentile", ylabel="Mean genre distance", title=f"User {user}: solution sets")
    axes[0].legend(fontsize=8)
    curve = pd.read_csv(output / "test" / "convergence.csv")
    for seed, group in curve.groupby("seed"):
        mean = group.groupby("generation").hypervolume.mean()
        axes[1].plot(mean.index, mean.values, label=f"seed {seed}")
    axes[1].set(xlabel="Generation", ylabel="Mean population hypervolume", title="Search convergence")
    axes[1].legend()
    fig.savefig(output / "comparison.png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--top-k", type=int, help="Recommendation length; does not change model-selection k")
    parser.add_argument("--reuse-model-from", type=Path, help="Reuse a completed local run's model; verify data, split and token mappings")
    parser.add_argument("--smoke", action="store_true", help="Two epochs, 3 generations, 4 users/split; not research results")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    config.setdefault("model_selection_k", config["top_k"])
    if args.top_k is not None:
        config["top_k"] = args.top_k
    if args.smoke:
        config.update(epochs=2, generations=3, search_seeds=[42], bootstrap_samples=100)
    if args.output:
        config["output_dir"] = str(args.output)
    output = Path(config["output_dir"])
    output = output if output.is_absolute() else ROOT / output
    data = Path(config["data_dir"]).expanduser()
    if not data.is_absolute():
        data = args.config.resolve().parent / data
    if not 1 <= config["top_k"] <= config["candidate_pool"] or not 0 <= config["relevance_floor"] <= 1:
        raise ValueError("Require 1 <= top_k <= candidate_pool and 0 <= relevance_floor <= 1")
    if not 1 <= config["model_selection_k"] <= config["candidate_pool"]:
        raise ValueError("Require 1 <= model_selection_k <= candidate_pool")
    if any(config[key] < 1 for key in ["epochs", "patience", "generations", "threads", "bootstrap_samples"]):
        raise ValueError("Iteration counts must be positive")
    if config["population"] < 12 or not config["search_seeds"]:
        raise ValueError("Population must accommodate 12 baseline seeds; search_seeds cannot be empty")
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}; choose a fresh --output")
    output.mkdir(parents=True)
    write_json(output / "config.json", {**config, "smoke": args.smoke})
    write_json(output / "environment.json", {"python": sys.version, "platform": platform.platform(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "packages": dict(sorted((d.metadata["Name"], d.version) for d in distributions())),
        "input_sha256": {name: hashlib.sha256((data / name).read_bytes()).hexdigest() for name in ["u.data", "u.item"]}})
    torch.set_num_threads(config["threads"])
    from recbole.utils import init_seed
    init_seed(config["seed"], True)
    start = time.perf_counter()
    ratings, genres = load_data(data)
    (train, valid, test), cuts = chronological_split(ratings)
    cfg, dataset, loader = prepare_recbole(train, config, output)
    valid_cases, valid_counts = make_cases(train, valid, train, genres, dataset,
                                         max(config["top_k"], config["model_selection_k"]))
    test_cases, test_counts = make_cases(pd.concat([train, valid]), test, train, genres, dataset, config["top_k"])
    split_report = {"cut_timestamps": cuts, "rows": {"train": len(train), "validation": len(valid), "test": len(test)},
        "validation": valid_counts, "test": test_counts,
        "cold_counts_overlap": True, "train_users": int(train.user_id.nunique()),
        "train_items": int(train.item_id.nunique())}
    write_json(output / "split.json", split_report)
    split_ids = pd.concat([frame.assign(split=name) for name, frame in [("train", train), ("validation", valid), ("test", test)]])
    split_ids.to_csv(output / "split_assignments.csv", index=False)
    for field in ["user_id", "item_id"]:
        write_json(output / f"{field}_mapping.json", {str(k): int(v) for k, v in dataset.field2token_id[field].items()})
    if args.smoke:
        valid_cases, test_cases = valid_cases[:4], test_cases[:4]
    print(json.dumps({**split_report, **{stage: {key: value for key, value in split_report[stage].items()
        if key != "users"} for stage in ("validation", "test")}}, indent=2), flush=True)
    if args.reuse_model_from:
        model = reuse_model(args.reuse_model_from.resolve(), cfg, dataset, config, output)
    else:
        model = fit_model(cfg, dataset, loader, valid_cases, genres, config, output)
    training_seconds = time.perf_counter() - start
    for name, cases in [("validation", valid_cases), ("test", test_cases)]:
        scored = score_cases(model, cases, dataset, genres, config["candidate_pool"])
        summary = run_rerank(scored, config, output / name)
        print(summary.to_string(index=False), flush=True)
    save_plots(output)
    write_json(output / "completion.json", {"model_preparation_seconds": training_seconds,
        "model_reused": args.reuse_model_from is not None,
        "total_seconds": time.perf_counter() - start, "status": "complete", "smoke": args.smoke})
    print(f"Completed: {output}", flush=True)


if __name__ == "__main__":
    main()
