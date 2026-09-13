"""One approved RecBole run; all writes stay below this experiment directory."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import resource
import sys
import time

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
import numpy as np
import torch
from recbole.config import Config
from recbole.data import create_dataset
from recbole.data.dataloader import TrainDataLoader
from recbole.model.sequential_recommender.sasrec import SASRec
from recbole.utils import init_seed


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_sequences(path):
    sequences = defaultdict(list)
    for line in path.read_text().splitlines():
        user, item = map(int, line.split())
        if user <= 0 or item <= 0:
            raise ValueError("IDs must be positive")
        sequences[user].append(item)
    if any(len(s) < 3 or len(s) != len(set(s)) for s in sequences.values()):
        raise ValueError("Short sequence or duplicate user-item pair")
    return dict(sorted(sequences.items()))


def candidates(sequences, catalog, seed):
    rng = np.random.default_rng(seed)
    result = {name: [] for name in ("validation", "test")}
    # Separate reproducible streams, independent of model/dropout/shuffle RNGs.
    for name, child_seed, offset in [("validation", seed, -2), ("test", seed + 1, -1)]:
        rng = np.random.default_rng(child_seed)
        for seq in sequences.values():
            available = np.setdiff1d(catalog, seq)
            if len(available) < 100:
                raise ValueError("Fewer than 100 unobserved items")
            result[name].append(np.r_[seq[offset], rng.choice(available, 100, replace=False)])
    return {name: np.asarray(rows) for name, rows in result.items()}


def metrics(scores, ids):
    if scores.shape != ids.shape or not np.isfinite(scores).all():
        raise ValueError("Invalid candidate scores")
    tied = scores == scores[:, :1]
    ranks = 1 + ((scores > scores[:, :1]) | (tied & (ids < ids[:, :1]))).sum(axis=1)
    hit = ranks <= 10
    return {"hit@10": float(hit.mean()),
            "ndcg@10": float(np.where(hit, 1 / np.log2(ranks + 1), 0).mean()),
            "target_tie_user_fraction": float((tied.sum(axis=1) > 1).mean())}, ranks


@torch.no_grad()
def evaluate(model, data, ids, token_ids):
    model.eval()
    result = []
    for start in range(0, len(data), 128):
        batch = data[start:start + 128]
        # Algebraically identical to predict, with one encoder pass per user.
        all_scores = model.full_sort_predict(batch)
        result.append(all_scores.gather(1, token_ids[start:start + 128]).numpy())
    scores = np.concatenate(result)
    summary, ranks = metrics(scores, ids)
    return summary, ranks, scores


def prepare(config_path, output):
    sequences = read_sequences(ROOT / "data/ml-1m.txt")
    counts = Counter(i for seq in sequences.values() for i in seq)
    source = json.loads((ROOT / "data/source.json").read_text())
    assert sha(ROOT / "data/ml-1m.txt") == source["sha256"]
    assert (len(sequences), len(counts), sum(counts.values())) == (6040, 3416, 999611)
    assert min(counts.values()) >= 5
    atomic = output / "atomic/paper-ml1m"
    atomic.mkdir(parents=True, exist_ok=True)
    with (atomic / "paper-ml1m.inter").open("w") as f:
        f.write("user_id:token\titem_id:token\ttimestamp:float\n")
        for user, seq in sequences.items():
            for position, item in enumerate(seq, 1):
                f.write(f"{user}\t{item}\t{position}\n")
    cfg = Config(model="SASRec", dataset="paper-ml1m", config_file_list=[str(config_path)],
                 config_dict={"data_path": str(atomic.parent),
                              "checkpoint_dir": str(output / "checkpoints")})
    init_seed(cfg["seed"], True)
    dataset = create_dataset(cfg)
    train, valid, test = dataset.build()
    assert dataset.user_num == 6041 and dataset.item_num == 3417
    assert len(train) == 999611 - 3 * 6040
    imap = dataset.field2token_id["item_id"]
    umap = dataset.field2token_id["user_id"]
    users = np.array(list(sequences))
    by_token = {int(umap[str(u)]): u for u in users}
    mapped = {u: [int(imap[str(i)]) for i in s] for u, s in sequences.items()}
    splits = {"train": train, "validation": valid, "test": test}
    # Verify every generated prefix, not only aggregate counts.
    for name, split in splits.items():
        positions = split.inter_feat["timestamp"].numpy().astype(int)
        user_tokens = split.inter_feat["user_id"].numpy()
        targets = split.inter_feat["item_id"].numpy()
        seqs = split.inter_feat["item_id_list"].numpy()
        lengths = split.inter_feat["item_length"].numpy()
        for j, (ut, p, target, length) in enumerate(zip(user_tokens, positions, targets, lengths)):
            seq = mapped[by_token[int(ut)]]
            expected_p = len(seq) - (1 if name == "validation" else 0)
            assert (2 <= p <= len(seq) - 2) if name == "train" else p == expected_p
            expected = seq[max(0, p - 1 - 200):p - 1]
            assert target == seq[p - 1] and length == len(expected)
            assert np.array_equal(seqs[j, :length], expected)
            assert not seqs[j, length:].any()
        if name != "train":
            assert len(split) == 6040 and len(set(user_tokens)) == 6040
            order = np.argsort([by_token[int(u)] for u in user_tokens])
            split.inter_feat = split.inter_feat[order]
    pools = candidates(sequences, np.array(sorted(counts)), 1042)
    token_pools = {}
    for name, ids in pools.items():
        for seq, row in zip(sequences.values(), ids):
            assert len(set(row)) == 101 and not set(row[1:]) & set(seq)
        token_pools[name] = torch.tensor([[imap[str(i)] for i in row] for row in ids])
        np.savez_compressed(output / f"{name}_candidates.npz", users=users, ids=ids)
    save_json(output / "sequences.json", sequences)
    save_json(output / "mapping.json", {"item": imap, "user": umap})
    train_counts = Counter(i for seq in sequences.values() for i in seq[:-2])
    stats = {**source, "training_prefixes": len(train), "validation_users": len(valid),
             "test_users": len(test), "excluded_users": 0,
             "heldout_only_items": len(set(counts) - set(train_counts)),
             "all_prefixes_verified": True, "all_candidates_verified": True,
             "negative_seeds": {"validation": 1042, "test": 1043}}
    save_json(output / "data_checks.json", stats)
    (output / "recbole_config.txt").write_text(str(cfg))
    save_json(output / "environment.json", {"python": sys.version, "platform": platform.platform(),
              "packages": {n: importlib.metadata.version(n) for n in ["torch", "recbole", "numpy", "pandas"]},
              "threads": torch.get_num_threads(), "device": "cpu", "source": source,
              "adam_betas": [0.9, 0.999], "adam_eps": 1e-8,
              "evaluation": "fixed unique unobserved negatives; full_sort scores gathered to 101 candidates"})
    return cfg, dataset, train, valid, test, pools, token_pools, train_counts, users


def checkpoint(path, model, optimizer, loader, state):
    temporary = path.with_suffix(".tmp")
    torch.save({**state, "model": model.state_dict(), "optimizer": optimizer.state_dict(),
                "torch_rng": torch.get_rng_state(), "numpy_rng": np.random.get_state(),
                "python_rng": random.getstate(), "loader_rng": loader.generator.get_state()}, temporary)
    temporary.replace(path)


def restore(saved, model, optimizer, loader):
    model.load_state_dict(saved["model"])
    optimizer.load_state_dict(saved["optimizer"])
    torch.set_rng_state(saved["torch_rng"])
    np.random.set_state(saved["numpy_rng"])
    random.setstate(saved["python_rng"])
    loader.generator.set_state(saved["loader_rng"])
    return {k: saved[k] for k in ["epoch", "best_epoch", "best_ndcg", "stale", "updates", "elapsed_seconds"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT not in output.parents:
        raise ValueError("Output must be inside the new experiment folder")
    if args.resume:
        prior = json.loads((output / "source_hashes.json").read_text())
        if prior[args.config.name] != sha(args.config):
            raise ValueError("Resume config differs from original run")
        prior_status = json.loads((output / "status.json").read_text())
        if not prior_status["status"].startswith("paused"):
            raise ValueError("Only a paused run can resume")
        saved = torch.load(output / "latest.pt", map_location="cpu", weights_only=False)
        if saved["epoch"] != prior_status["epoch"]:
            raise ValueError("Checkpoint/status epoch mismatch")
        save_json(output / "status.json", {**prior_status, "status": "resuming"})
    else:
        output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    cfg, dataset, train, valid, test, pools, token_pools, pop, users = prepare(args.config, output)
    save_json(output / ("resume_source_hashes.json" if args.resume else "source_hashes.json"),
              {p.name: sha(p) for p in [ROOT / "run.py", ROOT / "check.py", args.config]})
    loader = TrainDataLoader(cfg, train, None, shuffle=True)
    model = SASRec(cfg, dataset)
    optimizer = torch.optim.Adam(model.parameters(), lr=cfg["learning_rate"], weight_decay=0)
    state = {"epoch": 0, "best_epoch": 0, "best_ndcg": -1.0, "stale": 0,
             "updates": 0, "elapsed_seconds": 0.0}
    if args.resume:
        state = restore(saved, model, optimizer, loader)
    start = time.monotonic() - state["elapsed_seconds"]
    stop_reason = "epoch_limit"
    print(json.dumps({"status": "training", "prefixes": len(train), "batches_per_epoch": len(loader)}), flush=True)
    save_json(output / "status.json", {"status": "training", **state})
    for epoch in range(state["epoch"] + 1, cfg["epochs"] + 1):
        if state["epoch"]:
            last = json.loads((output / "training.jsonl").read_text().splitlines()[-1])
            if time.monotonic() - start + last["epoch_seconds"] * 1.1 > 12 * 3600:
                stop_reason = "12h_budget_epoch_boundary"
                break
        epoch_start = time.monotonic()
        model.train()
        total_loss, examples = 0.0, 0
        for step, batch in enumerate(loader, 1):
            optimizer.zero_grad(set_to_none=True)
            loss = model.calculate_loss(batch)
            if not torch.isfinite(loss):
                raise ValueError("Non-finite training loss")
            loss.backward()
            if step == 1:
                assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
            optimizer.step()
            total_loss += loss.item() * len(batch)
            examples += len(batch)
            state["updates"] += 1
            if step % 200 == 0:
                progress = {"status": "training", "epoch": epoch, "batch": step,
                            "batches": len(loader), "seconds": time.monotonic() - start,
                            "epoch_seconds": time.monotonic() - epoch_start}
                save_json(output / "progress.json", progress)
                print(json.dumps(progress), flush=True)
            if time.monotonic() - start > 12 * 3600:
                state.update(epoch=epoch - 1, elapsed_seconds=time.monotonic() - start)
                checkpoint(output / "interrupted.pt", model, optimizer, loader,
                           {**state, "partial_epoch": epoch, "partial_batch": step, "resumable_epoch_boundary": False})
                save_json(output / "status.json", {"status": "paused_wallclock_limit", **state})
                return
        assert examples == len(train)
        summary, _, _ = evaluate(model, valid, pools["validation"], token_pools["validation"])
        improved = summary["ndcg@10"] > state["best_ndcg"]
        state.update(epoch=epoch, elapsed_seconds=time.monotonic() - start)
        if improved:
            state.update(best_ndcg=summary["ndcg@10"], best_epoch=epoch, stale=0)
        else:
            state["stale"] += 1
        row = {**state, "mean_loss": total_loss / examples, "validation": summary,
               "epoch_seconds": time.monotonic() - epoch_start,
               "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        with (output / "training.jsonl").open("a") as f:
            f.write(json.dumps(row) + "\n")
        checkpoint(output / "latest.pt", model, optimizer, loader, state)
        if improved:
            checkpoint(output / "best.pt", model, optimizer, loader, state)
        save_json(output / "status.json", {"status": "training", **state})
        print(json.dumps(row), flush=True)
        if epoch == 1:
            estimate = row["epoch_seconds"] * cfg["epochs"]
            save_json(output / "runtime_estimate.json", {"first_epoch_seconds": row["epoch_seconds"],
                      "maximum_200_epoch_hours": estimate / 3600,
                      "earliest_21_epoch_hours": row["epoch_seconds"] * 21 / 3600,
                      "note": "Extrapolation, actual early stopping time is unknown"})
            if estimate > 12 * 3600:
                save_json(output / "status.json", {"status": "paused_estimate_exceeds_approved_limit",
                          "estimated_maximum_hours": estimate / 3600, **state})
                return
        if state["stale"] >= cfg["stopping_step"]:
            stop_reason = "early_stopping"
            break
    # Only locally generated checkpoint; never deserialize a downloaded pickle.
    best = torch.load(output / "best.pt", map_location="cpu", weights_only=False)
    model.load_state_dict(best["model"])
    summary, ranks, scores = evaluate(model, test, pools["test"], token_pools["test"])
    pop_scores = np.array([[pop.get(int(i), 0) for i in row] for row in pools["test"]])
    pop_summary, pop_ranks = metrics(pop_scores, pools["test"])
    np.savez_compressed(output / "test_results.npz", users=users, scores=scores, ranks=ranks,
                        popularity_scores=pop_scores, popularity_ranks=pop_ranks)
    save_json(output / "results.json", {"sasrec": summary, "poprec": pop_summary,
              "paper": {"hit@10": 0.8245, "ndcg@10": 0.5905}, "selected_epoch": state["best_epoch"],
              "relative_gaps": {k: summary[k] / v - 1 for k, v in {"hit@10": .8245, "ndcg@10": .5905}.items()}})
    save_json(output / "status.json", {"status": "execution_complete", "stop_reason": stop_reason,
              "convergence_verified": stop_reason == "early_stopping", **state})


if __name__ == "__main__":
    main()
