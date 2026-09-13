"""Compare the candidate generators under the rule fixed in PLAN.md.

Reads only the run directories under outputs/ and the stored v0 run, writes its
tables under reports/. Nothing outside v0-H1/ is touched.

Order of operations mirrors the plan: verify the reuse gate against v0, decide on
validation alone, then print the test table, then the pool diagnostics.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
V0_RUN = Path("/Users/macuser/Documents/Codex/2026-09-09/referenced-chatgpt-conversation-this-is-an-2/work/outputs/ml-1m-rd-k10-resumed2")
ARMS = {"A1-sasrec-scratch": "SASRec (scratch)",
        "A2-comirec-sa": "ComiRec-SA",
        "A3-esasrec": "eSASRec"}
PRIMARY = "candidate_recall"
TIE_MARGIN = 0.005
COMPARED = ["recall", "ndcg", "candidate_recall", "relevance", "genre_distance",
            "s_proxy", "heldout_distance"]


def summary(run, split):
    path = ROOT / "outputs" / run / split / "summary.csv"
    if not path.exists():
        return None
    return pd.read_csv(path).set_index("method")


def gate():
    print("== A0: reuse gate against the stored v0 run ==")
    ours_dir = ROOT / "outputs" / "A0-sasrec-reuse"
    if not (ours_dir / "completion.json").exists():
        print("A0 has not completed; gate not evaluated.")
        return False
    verdict = True
    for split in ["validation", "test"]:
        ours = summary("A0-sasrec-reuse", split)
        theirs = pd.read_csv(V0_RUN / split / "summary.csv").set_index("method")
        shared = [m for m in COMPARED if m in ours.columns and m in theirs.columns]
        diff = (ours.loc[theirs.index, shared] - theirs[shared]).abs().max().max()
        identical = bool(diff == 0)
        verdict &= identical
        print(f"{split}: max absolute difference over {len(shared)} metrics = {diff:.3e} "
              f"({'identical' if identical else 'DIFFERENT'})")
    return verdict


def training_reproduction():
    """A1 retrains SASRec from scratch; v0's per-epoch curve is the reference."""
    print("\n== A1: training reproduction against v0's curve ==")
    path = ROOT / "outputs" / "A1-sasrec-scratch" / "training.csv"
    if not path.exists():
        print("A1 has not produced a training curve yet.")
        return None
    ours = pd.read_csv(path)
    theirs = pd.read_csv(V0_RUN / "training.csv")
    shared = min(len(ours), len(theirs))
    merged = pd.DataFrame({"epoch": ours.epoch[:shared],
                           "v0_validation_ndcg": theirs.validation_ndcg[:shared],
                           "a1_validation_ndcg": ours.validation_ndcg[:shared]})
    merged["absolute_difference"] = (merged.a1_validation_ndcg
                                     - merged.v0_validation_ndcg).abs()
    print(merged.to_string(index=False))
    print(f"epochs run: v0 {len(theirs)}, A1 {len(ours)}; "
          f"max absolute difference {merged.absolute_difference.max():.3e}")
    return merged


def decision():
    print("\n== validation: the only evidence used to choose a generator ==")
    rows = []
    for run, label in ARMS.items():
        table = summary(run, "validation")
        if table is None:
            print(f"{label}: not available yet")
            continue
        checkpoint = json.loads((ROOT / "outputs" / run / "checkpoint.json").read_text())
        training = pd.read_csv(ROOT / "outputs" / run / "training.csv")
        rows.append({"arm": run, "model": label,
                     "candidate_recall@100": table.loc["sasrec", PRIMARY],
                     "ndcg@10 (generator)": table.loc["sasrec", "ndcg"],
                     "recall@10 (generator)": table.loc["sasrec", "recall"],
                     "genre_distance (generator)": table.loc["sasrec", "genre_distance"],
                     "selected_epoch": checkpoint["selected_epoch"],
                     "epochs_run": len(training)})
    if not rows:
        return None
    frame = pd.DataFrame(rows).sort_values("candidate_recall@100", ascending=False)
    print(frame.to_string(index=False))

    best = frame.iloc[0]
    within = frame[frame["candidate_recall@100"] >= best["candidate_recall@100"] - TIE_MARGIN]
    if len(within) > 1:
        print(f"\nArms within the {TIE_MARGIN} tie margin: {list(within['model'])}. "
              "The rule then prefers the simpler and faster arm, which is SASRec.")
        chosen = "SASRec (scratch)" if "SASRec (scratch)" in set(within["model"]) else best["model"]
    else:
        chosen = best["model"]
    print(f"Adopted candidate generator: {chosen}")
    return frame


def test_table():
    print("\n== test: reported after the decision, one pass per arm ==")
    frames = []
    for run, label in ARMS.items():
        table = summary(run, "test")
        if table is None:
            continue
        for method in ["sasrec", "weighted_distance_selected", "nsga2"]:
            if method not in table.index:
                continue
            frames.append({"arm": label, "method": method,
                           "ndcg@10": table.loc[method, "ndcg"],
                           "recall@10": table.loc[method, "recall"],
                           "candidate_recall@100": table.loc[method, "candidate_recall"],
                           "genre_distance": table.loc[method, "genre_distance"],
                           "heldout_distance": table.loc[method, "heldout_distance"]})
    if not frames:
        print("no test summaries yet")
        return None
    frame = pd.DataFrame(frames)
    print(frame.to_string(index=False))
    return frame


def paired_bootstrap(split, reference="A1-sasrec-scratch", samples=2000, seed=42):
    """Per-user differences against the SASRec arm; the arms score the same users."""
    print(f"\n== {split}: paired bootstrap against SASRec over the same users ==")
    per_user = {}
    for run in ARMS:
        path = ROOT / "outputs" / run / split / "per_user.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        generator = frame[(frame.method == "sasrec") & (frame.seed == -1)]
        per_user[run] = generator.set_index("user_id")[["candidate_recall", "ndcg"]]
    if reference not in per_user or len(per_user) < 2:
        print("not enough arms to compare")
        return None
    base = per_user[reference]
    rng = np.random.default_rng(seed)
    rows = []
    for run, frame in per_user.items():
        if run == reference:
            continue
        users = base.index.intersection(frame.index)
        for metric in ["candidate_recall", "ndcg"]:
            difference = (frame.loc[users, metric] - base.loc[users, metric]).to_numpy()
            draws = rng.integers(0, len(difference), size=(samples, len(difference)))
            means = difference[draws].mean(axis=1)
            low, high = np.percentile(means, [2.5, 97.5])
            rows.append({"arm": ARMS[run], "metric": metric, "users": len(users),
                         "mean_difference": difference.mean(),
                         "ci_low": low, "ci_high": high,
                         "excludes_zero": bool(low > 0 or high < 0)})
    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False))
    return frame


def pool_diagnostics():
    """Diagnostics on the 100-item pools. Not part of the adoption rule."""
    print("\n== candidate pool diagnostics (test split, diagnostic only) ==")
    rows = []
    for run, label in ARMS.items():
        path = ROOT / "outputs" / run / "test" / "candidates.csv"
        if not path.exists():
            continue
        candidates = pd.read_csv(path)
        assignments = pd.read_csv(ROOT / "outputs" / run / "split_assignments.csv")
        train = assignments[assignments.split == "train"]
        share = train.item_id.value_counts() / len(train)
        popularity = candidates.item_id.map(share)
        catalog = train.item_id.nunique()
        rows.append({"arm": label,
                     "pool_mean_genre_distance": candidates.genre_distance.mean(),
                     "pool_mean_self_information": float(-np.log2(popularity.dropna()).mean()),
                     "distinct_items_in_pools": candidates.item_id.nunique(),
                     "pool_item_coverage": candidates.item_id.nunique() / catalog,
                     "users": candidates.user_id.nunique()})
    if not rows:
        print("no candidate files yet")
        return None
    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False))
    return frame


def main():
    passed = gate()
    curve = training_reproduction()
    validation = decision()
    validation_ci = paired_bootstrap("validation")
    test = test_table()
    test_ci = paired_bootstrap("test")
    pools = pool_diagnostics()
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    for name, frame in [("validation-decision", validation), ("test-comparison", test),
                        ("pool-diagnostics", pools), ("training-reproduction", curve),
                        ("validation-paired-bootstrap", validation_ci),
                        ("test-paired-bootstrap", test_ci)]:
        if frame is not None:
            frame.to_csv(reports / f"{name}.csv", index=False)
    print(f"\nreuse gate passed: {passed}")


if __name__ == "__main__":
    main()
