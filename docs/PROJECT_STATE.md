# プロジェクト状態

最終更新：2026-09-13。全体計画の正本はルートの`PLAN.md`。Graph-Recの実装状態は`.codex/IMPLEMENTATION_STATE.md`を再利用し、こちらへ複製しない。

## 実行モード

Phase 1〜3はAstra再レビュー合格。Phase 4は実装とブラウザ検証まで完了、Astraレビュー待ち。Phase 5、deploy、募集、学習は未許可。
0.1はディレクトリreaderのまま。0.2は単一`bundle.json`。仕様正本はEngineeringの `docs/research-export.md` と `docs/research-export-v0.2.md`。Research側の入口は `studies/music-evaluator/README.md`。
公開checkpointはResearch `a117f75`、Engineering `45b436d`。今回commit/pushしていない。Engineeringは https://github.com/t3-sketch/graph-rec （Public）。

## Phase 1で確定した正本

| 対象 | 正本 | 備考 |
|---|---|---|
| 全体計画 | このResearchの`PLAN.md` | Graph-Recの`PLAN.md`は案内と担当範囲 |
| v0結果 | `v0/reports/S01-ml-1m-baseline.md` | 現行入口は`v0/reproduce/` |
| 1M保存場所 | `research/local-context.md` | 公開対象外。元成果物は未移動 |
| H1公開要約 | `v0/reports/S02-h1-candidate-generators.md` | 詳細は未追跡の`v0-H1/REPORT.md` |
| sanity公開要約 | `v0/reports/S03-sasrec-sanity-check.md` | test未評価 |
| Graph-Rec実装 | `research/local-context.md`に記録 | 状態は`.codex/IMPLEMENTATION_STATE.md` |

## Phase 2で整えた1M経路

特定した別保存物：1Mの`experiment.py`、`check.py`、`config.json`（`data/ml-1m`）、run `ml-1m-rd-k10-resumed2` / `ml-1m-rd-k10-phase1`、環境 python 3.10.20 / recbole 1.2.1 / torch 2.5.1 / numpy 1.26.4。

公開snapshot：`v0/reproduce/`。元フォルダは保持。`v0/experiment.py`は100K歴史的snapshot。

データ取得：GroupLens MovieLens 1Mを`v0/data/ml-1m/`へ置く。hashは`v0/reproduce/expected/environment-pins.json`。

## H1・sanityの公開選別

H1の明示一覧は`v0-H1/PUBLIC.md`。公開する集計は`pool-diagnostics.csv`、`test-comparison.csv`、`test-paired-bootstrap.csv`、`training-reproduction.csv`、`validation-decision.csv`、`validation-paired-bootstrap.csv`だけ。`comirec-interests.csv`は`user_id`付きのため公開しない。
sanity公開候補：計画、報告、STATUS、スクリプト、config、requirements、`handoff/manifest.json`、`archive.sha256`。非公開：`data/`、`outputs/`、`*.tar.gz`。
フォルダ全体を一括追加していない。

## 検証（2026-09-13）

- `v0/reproduce/check.py`：PASS（合成データ。履歴平均positive、時間漏洩、目的、floor）。
- `v0/reproduce/verify_saved.py`：S01の手法×指標表とexpected CSVを照合。H1はv0/A1の2列から差を再計算し、`resumed2-training.csv`とepoch対応を確認。
- 別保存の`ratings.dat` / `movies.dat`：記録hashと一致。公開checkoutにはデータなし。
- フル再学習：未実施。H1 A1は7 epochまで完了済み。sanityは別protocolで1 epoch約37〜44分。

## 未検証

事前仕様との照合。公開snapshotとresumed2当時`experiment.py`のバイト一致。フル再学習。GitHub公開設定。Graph-Recのブラウザ再検証。H1/sanityのcommit。

## Phase 3（2026-09-13）

入口：`python -B studies/music-evaluator/validate_export.py <bundle-dir>`。標準ライブラリのみ。
実mock 2ケースを読み、`schema_version=0.1 case_count=2 recommendation_count=15`。seedは`sonder-1` limit 8、次seedは第一候補`sonder-2` limit 7。評定/予測ファイルは0 bytes。
破損fixture（未知schema、余分key、NaN、重複key、rank、既探索曲、hash改変、非空評定ファイル）は拒否。hash再計算後も構造違反は失敗する。
mock bundleを実推薦やexperienced serendipityの証拠としない。

## Phase 4（2026-09-13）

Engineeringの別作業コピーで静的previewを確認した。
40曲、音源合計 30,254,221 bytes。開始曲は The Factory / I Want To Destroy Something Beautiful / I'm Not Lazy。各8候補。The Factory経路で2回以上展開し23曲。試聴成功2、再生失敗表示あり。Like/Saveは明示反応。reloadで23曲を復元。legacy mockセッションは「older catalog」で拒否。
UI export：`schema_version=0.2 case_count=3 recommendation_count=22 event_count=31`。`purpose=engineering_demo`、`data_kind=real_catalog`、`provider.id=genre-jaccard-v1`、`dataset.id=sonder-fma-40-v1`。評定/予測は空。Research reader 12/12。
候補取得時間、500-node FPS、主観品質、experienced serendipityは未計測。genre Jaccardの上昇を推薦品質や経験の改善と呼ばない。
Graph-Rec本体はcatalog・音源・0.2モジュールの一部のみ同期。DocumentsのI/O timeoutでUI/store上書きが残る。仕様書は実装証拠に書き換えていない。

## 次の再開点

AstraがPhase 4を仕様照合する。Graph-Rec本体へ未同期のUI/storeを入れる。Phase 5、commit、push、募集は未許可。
