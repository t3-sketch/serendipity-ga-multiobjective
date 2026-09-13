# v0 1M reproduction entry

Current public entry for the MovieLens 1M baseline. The files here are a snapshot of the separately stored 1M implementation. The original store is not moved.

`v0/experiment.py` and `v0/config.json` remain as a 100K historical snapshot. Do not run them as the current baseline.

## What this snapshot is

- `experiment.py` / `check.py`: copy of the 1M work files after the Phase 1 diagnostic addition.
- `expected/`: public aggregates copied from `ml-1m-rd-k10-resumed2` and `ml-1m-rd-k10-phase1`. No ratings, checkpoints, or per-user outputs.
- The `resumed2` run recorded a different `experiment.py` hash than this snapshot. H1 reproduced the saved metrics with a third harness. The three files are not byte-identical.

## Data

Do not commit MovieLens files. Download MovieLens 1M from GroupLens, keep `ratings.dat` and `movies.dat`, and place them at `v0/data/ml-1m/` (gitignored).

Expected SHA-256:

- `ratings.dat`: `506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f`
- `movies.dat`: `0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9`

License and citation: [DATA_LICENSE.md](../DATA_LICENSE.md).

## Environment

Python 3.10.20, RecBole 1.2.1, PyTorch 2.5.1, NumPy 1.26.4, pymoo 0.6.1.5, 2 threads. See `expected/environment-pins.json`.

An existing `v0/.venv` or `v0-H1/.venv` may be reused if those pins match. Do not overwrite another run's output directory.

## Small-scale checks (no full retrain)

```sh
cd v0/reproduce
# from repo root, with a pinned venv:
../.venv/bin/python -B check.py
../.venv/bin/python -B verify_saved.py
```

`check.py` uses synthetic tables. `verify_saved.py` reads the S01 method×metric table and compares each cell to the expected CSVs. If `v0-H1/reports/` exists, it recomputes H1 training differences from the v0 and A1 columns and checks `resumed2-training.csv`. If `v0/data/ml-1m/` exists, it checks the data hashes.

## Full experiment (separate unit)

```sh
cd v0/reproduce
<venv>/python -B experiment.py --smoke --output ../outputs/ml-1m-smoke-<date>
<venv>/python -B experiment.py --output ../outputs/ml-1m-<new-id>
```

Smoke and full runs are not the canonical result. The published numbers come from the saved `ml-1m-rd-k10-resumed2` / `ml-1m-rd-k10-phase1` aggregates. Full retraining is a costed separate job and was not run in Phase 2.

Local owners may keep the original store path in `research/local-context.md` (not public). Public docs do not embed that path.
