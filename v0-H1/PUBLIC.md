# v0-H1 公開対象

未commit。フォルダ全体を一括追加しない。ユーザー単位出力は公開しない。

## 公開する

- `PLAN.md`、`REPORT.md`、`REFLECTION.md`、`HANDOFF.md`、`PUBLIC.md`
- `analyze.py`、`check_models.py`、`check_v0.py`、`diagnose_comirec.py`、`experiment.py`、`wait_and_analyze.sh`
- `config-sasrec.json`、`config-comirec.json`、`config-esasrec.json`
- `models/comirec.py`、`models/esasrec.py`
- 集計のみ:
  - `reports/pool-diagnostics.csv`
  - `reports/test-comparison.csv`
  - `reports/test-paired-bootstrap.csv`
  - `reports/training-reproduction.csv`
  - `reports/validation-decision.csv`
  - `reports/validation-paired-bootstrap.csv`

## 公開しない

- `reports/comirec-interests.csv`（`user_id`付きの個別結果）
- `outputs/`、`data/`、`.venv/`、`logs/`、`log_tensorboard/`
