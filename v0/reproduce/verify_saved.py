"""Compare S01 table cells and H1 training columns to public expected aggregates."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
EXPECTED = ROOT / "expected"
REPORT = ROOT.parent / "reports" / "S01-ml-1m-baseline.md"

METHOD_ALIASES = {
    "sasrec": "sasrec",
    "weighted sum": "weighted_distance_selected",
    "weighted_distance_selected": "weighted_distance_selected",
    "nsga-ii": "nsga2",
    "nsga2": "nsga2",
}
TABLE_COLUMNS = {
    "ndcg@10": "ndcg",
    "mean genre distance": "genre_distance",
    "heldout distance": "heldout_distance",
}
ROUND_DIGITS = 6


def _round_match(actual: float, published: float, digits: int = ROUND_DIGITS) -> bool:
    return round(float(actual), digits) == round(float(published), digits)


def _cells(line: str) -> list[str]:
    return [part.strip() for part in line.strip().strip("|").split("|")]


def parse_s01_test_table(text: str) -> dict[str, dict[str, float]]:
    section = text.split("## Test結果", 1)
    if len(section) != 2:
        raise AssertionError("S01 is missing the Test結果 section")
    body = section[1].split("\n## ", 1)[0]
    header = None
    parsed: dict[str, dict[str, float]] = {}
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = _cells(line)
        if header is None:
            if cells[:1] != ["手法"]:
                continue
            header = []
            for name in cells[1:]:
                key = TABLE_COLUMNS.get(name.lower())
                if key is None:
                    raise AssertionError(f"unexpected S01 column: {name}")
                header.append(key)
            continue
        if set("".join(cells)) <= set("-:"):
            continue
        method = METHOD_ALIASES.get(cells[0].lower())
        if method is None:
            raise AssertionError(f"unexpected S01 method: {cells[0]}")
        if len(cells) != 1 + len(header):
            raise AssertionError(f"S01 row has the wrong width: {cells}")
        parsed[method] = {key: float(value) for key, value in zip(header, cells[1:])}
    if set(parsed) != {"sasrec", "weighted_distance_selected", "nsga2"}:
        raise AssertionError(f"S01 table methods are incomplete: {sorted(parsed)}")
    return parsed


def parse_s01_candidate_recall(text: str) -> float:
    match = re.search(r"Candidate Recall@100は([0-9.]+)であり", text)
    if not match:
        raise AssertionError("S01 is missing Candidate Recall@100")
    return float(match.group(1))


def parse_s01_nsga_bootstrap(text: str) -> tuple[float, float, float]:
    match = re.search(
        r"NDCG@10差は([0-9.]+)、対応付きbootstrap 2,000回の95%区間は\[([−\-][0-9.]+), ([0-9.]+)\]",
        text,
    )
    if not match:
        raise AssertionError("S01 is missing the NSGA-II − Weighted Sum bootstrap line")
    mean_delta = float(match.group(1))
    ci_low = float(match.group(2).replace("−", "-"))
    ci_high = float(match.group(3))
    return mean_delta, ci_low, ci_high


def verify_summaries() -> None:
    pins = json.loads((EXPECTED / "environment-pins.json").read_text())
    snapshot = hashlib.sha256((ROOT / "experiment.py").read_bytes()).hexdigest()
    assert snapshot == pins["public_snapshot_experiment_sha256"], snapshot
    report_rows = parse_s01_test_table(REPORT.read_text())
    report_recall = parse_s01_candidate_recall(REPORT.read_text())
    report_delta, report_ci_low, report_ci_high = parse_s01_nsga_bootstrap(REPORT.read_text())
    for name in ("resumed2-test-summary.csv", "phase1-test-summary.csv"):
        summary = pd.read_csv(EXPECTED / name).set_index("method")
        for method, reported in report_rows.items():
            row = summary.loc[method]
            for key, reported_value in reported.items():
                assert _round_match(row[key], reported_value), (
                    name, method, key, float(row[key]), reported_value,
                )
            assert _round_match(row["candidate_recall"], report_recall), (name, method, float(row["candidate_recall"]))
        csv_delta = float(summary.loc["nsga2", "ndcg"] - summary.loc["weighted_distance_selected", "ndcg"])
        assert _round_match(csv_delta, report_delta), (name, csv_delta, report_delta)
    boot = pd.read_csv(EXPECTED / "resumed2-test-paired-bootstrap.csv")
    row = boot[(boot.method == "nsga2") & (boot.reference == "weighted_distance_selected") & (boot.metric == "ndcg")].iloc[0]
    assert _round_match(row.mean_delta, report_delta)
    assert _round_match(row.ci_low, report_ci_low)
    assert _round_match(row.ci_high, report_ci_high)
    assert int(row.users) == 974
    ckpt = json.loads((EXPECTED / "resumed2-checkpoint.json").read_text())
    assert ckpt["selected_epoch"] == 1
    training = pd.read_csv(EXPECTED / "resumed2-training.csv")
    assert _round_match(training.loc[training.epoch == 1, "validation_ndcg"].iloc[0], ckpt["validation_ndcg"])
    print("PASS S01 method×metric table and bootstrap match expected CSVs")


def verify_optional_h1() -> None:
    h1 = ROOT.parent.parent / "v0-H1" / "reports"
    if not (h1 / "test-comparison.csv").is_file():
        print("SKIP H1 reports (folder not present)")
        return
    report_rows = parse_s01_test_table(REPORT.read_text())
    test = pd.read_csv(h1 / "test-comparison.csv")
    sasrec = test[test.arm == "SASRec (scratch)"].set_index("method")
    for method, reported in report_rows.items():
        row = sasrec.loc[method]
        assert _round_match(row["ndcg@10"], reported["ndcg"])
        assert _round_match(row["genre_distance"], reported["genre_distance"])
        assert _round_match(row["heldout_distance"], reported["heldout_distance"])

    train = pd.read_csv(h1 / "training-reproduction.csv")
    saved = pd.read_csv(EXPECTED / "resumed2-training.csv")
    required = {"epoch", "v0_validation_ndcg", "a1_validation_ndcg"}
    assert required <= set(train.columns), train.columns
    assert list(train.epoch) == list(saved.epoch), (list(train.epoch), list(saved.epoch))
    assert len(train) == len(saved) == 7, (len(train), len(saved))
    for left, right in zip(train.itertuples(index=False), saved.itertuples(index=False)):
        v0 = float(left.v0_validation_ndcg)
        a1 = float(left.a1_validation_ndcg)
        recomputed = abs(v0 - a1)
        assert recomputed == 0.0, (int(left.epoch), v0, a1, recomputed)
        if "absolute_difference" in train.columns:
            assert float(left.absolute_difference) == recomputed, (int(left.epoch), left.absolute_difference, recomputed)
        assert v0 == float(right.validation_ndcg), (int(left.epoch), v0, right.validation_ndcg)
    print("PASS H1 training columns recompute to zero and match resumed2-training.csv")


def verify_optional_data() -> None:
    pins = json.loads((EXPECTED / "environment-pins.json").read_text())
    data = (ROOT / Path(json.loads((ROOT / "config.json").read_text())["data_dir"])).resolve()
    if not data.is_dir():
        print("SKIP MovieLens 1M data (not in public checkout)")
        return
    for name, digest in pins["input_sha256"].items():
        actual = hashlib.sha256((data / name).read_bytes()).hexdigest()
        assert actual == digest, (name, actual)
    print(f"PASS data hashes: {data}")


if __name__ == "__main__":
    verify_summaries()
    verify_optional_h1()
    verify_optional_data()
    if "--strict-data" in sys.argv and not (ROOT / Path(json.loads((ROOT / "config.json").read_text())["data_dir"])).is_dir():
        raise SystemExit("MovieLens 1M data missing")
