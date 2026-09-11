"""Compare five recommendation lengths with one fixed, locally trained SASRec."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pandas as pd

from check import check_artifacts
from experiment import ROOT, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "outputs/full")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/list-lengths")
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if json.loads((source / "completion.json").read_text())["status"] != "complete":
        raise ValueError("Source run must be complete")
    if "genre_distance" not in pd.read_csv(source / "test" / "pareto.csv", nrows=0).columns:
        raise ValueError("Source run must use (relevance, genre_distance) objectives; rerank it first")
    output.mkdir(parents=True, exist_ok=False)
    lengths = [10, 15, 20, 25, 30]
    summaries, intervals, agreement = [], [], []
    expected_inputs = json.loads((source / "environment.json").read_text())["input_sha256"]
    for k in lengths:
        run = output / f"k{k}"
        print(f"Starting K={k}; log: {output / f'k{k}.log'}", flush=True)
        with (output / f"k{k}.log").open("w") as log:
            subprocess.run([sys.executable, str(ROOT / "experiment.py"),
                            "--top-k", str(k), "--reuse-model-from", str(source),
                            "--output", str(run)], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        check_artifacts(run)
        config = json.loads((run / "config.json").read_text())
        checkpoint = json.loads((run / "checkpoint.json").read_text())
        assert config["top_k"] == k and config["model_selection_k"] == 10
        assert checkpoint["selection_metric"] == "NDCG@10"
        assert Path(checkpoint["reused_from"]) == source
        assert json.loads((run / "environment.json").read_text())["input_sha256"] == expected_inputs
        for stage in ("validation", "test"):
            # Identical users, items and scores ensure this isolates list length.
            pd.testing.assert_frame_equal(pd.read_csv(run / stage / "candidates.csv"),
                                          pd.read_csv(source / stage / "candidates.csv"))
            summary = pd.read_csv(run / stage / "summary.csv")
            summaries.append(summary.assign(top_k=k, split=stage))
            intervals.append(pd.read_csv(run / stage / "paired_bootstrap.csv").assign(top_k=k, split=stage))
            recs = pd.read_csv(run / stage / "recommendations.csv")
            scalar = recs[recs.method == "weighted_distance_selected"]
            nsga = recs[recs.method == "nsga2"]
            pairs = nsga.merge(scalar[["user_id", "rank", "item_id"]],
                               on=["user_id", "rank"], suffixes=("_nsga", "_scalar"),
                               validate="many_to_one")
            assert len(pairs) == len(nsga)
            same = pairs.item_id_nsga == pairs.item_id_scalar
            list_matches = pairs.assign(same=same).groupby(["user_id", "seed"]).same.all()
            agreement.append({"top_k": k, "split": stage,
                              "matching_positions": int(same.sum()), "positions": len(pairs),
                              "matching_lists": int(list_matches.sum()), "lists": len(list_matches)})
            if k == 10:
                previous = pd.read_csv(source / stage / "summary.csv")
                pd.testing.assert_frame_equal(summary.drop(columns="seconds"), previous.drop(columns="seconds"))
        print(f"Verified K={k}: same candidates/model; exact list sizes and saved artifacts", flush=True)
    summary = pd.concat(summaries, ignore_index=True)
    summary.to_csv(output / "summary.csv", index=False)
    pd.concat(intervals, ignore_index=True).to_csv(output / "paired_bootstrap.csv", index=False)
    pd.DataFrame(agreement).to_csv(output / "agreement.csv", index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    for ax, metric, title in zip(axes, ["ndcg", "recall", "genre_distance"],
                                 ["Held-out NDCG@K", "Held-out Recall@K", "Mean genre distance"]):
        for method, marker in [("sasrec", "o"), ("weighted_distance_selected", "s"), ("nsga2", "x")]:
            rows = summary[(summary.split == "test") & (summary.method == method)]
            ax.plot(rows.top_k, rows[metric], marker=marker, label=method)
        ax.set(title=title, xlabel="Recommendation length K", xticks=lengths)
    axes[0].legend(fontsize=7)
    fig.savefig(output / "comparison.png", dpi=160)
    plt.close(fig)
    write_json(output / "completion.json", {
        "status": "complete", "lengths": lengths, "source_run": str(source),
        "model_selection_metric": "NDCG@10", "same_candidates_verified": True,
        "k10_prior_metrics_verified": True,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    print(f"Completed all lengths: {output}", flush=True)


if __name__ == "__main__":
    main()
