# v0 MovieLens 1M baselineの確認手順

正式結果は[1M baseline報告](reports/S01-ml-1m-baseline.md)を正本とする。
この文書は保存済み証拠の確認方法を示す。

## 公開repoから確認できる範囲

公開repoには集計報告と既存コードを収録する。
`config.json`は`data/ml-100k`を指し、公開実装は100K用である。
1Mで使った実装と保存出力は別環境にあり、現行コードを実行しても1M canonical baselineの再現にはならない。
1Mへのコード移植、config変更、依存環境の構築、新規実験は2026-09-11の文書更新で行っていない。
従来の100K実行例はGit historyで参照できる。

## 保存済み1M証拠の確認

本比較のrun IDは`ml-1m-rd-k10-resumed2`、診断追加は`ml-1m-rd-k10-phase1`である。
所有者のローカル環境では`research/local-context.md`に実際の保存先を保持する（公開対象外）。
両runを別々に確認し、保存ファイルを上書きしない。

| 確認対象 | 確認する内容 |
|---|---|
| completion.json | status=complete、smoke=false。実行完了と再現検証を区別する |
| config.json | data/ml-1m、K=10、候補100、floor=0.95、40個体、50世代、探索seed 42/43/44 |
| split.json | history_mean_centered_gt_0、validation 478人、test 974人 |
| checkpoint.json | selected epoch 1、validation NDCG@10=0.075590、診断runの再利用元 |
| test/summary.csv | sasrec、weighted_distance_selected、nsga2の指標をreportと照合する |
| test/paired_bootstrap.csv | NSGA-IIと加重和のNDCG差および95%区間 |
| 1M版README | 定義と当時の回帰検査記録。今回の再検証と区別する |

positiveの基準は推薦時点までの本人の全履歴平均である。
validationはtrain、testはtrain＋validationを使い、未来のratingを含めない。
目的はmean rとmean dであり、r×dは診断専用とする。
代表選択と集計方法は正式reportに記す。

## 再現確認に必要なもの

1M版のコード、config、入力データ、環境記録、分割とcheckpointの対応を揃える必要がある。
現行公開コードのデータパスだけを変更すれば再現できるとは扱わない。
再実行が必要な場合は[plans](plans/README.md)に目的、未使用の出力先、確認範囲を記し、実行の承認を得る。
保存済み結果の確認と、再学習や再ランキングを伴う新しいrunは別作業である。

データ、checkpoint、ユーザー単位出力は公開repoに同梱しない。
データ出典と利用条件は[DATA_LICENSE.md](DATA_LICENSE.md)を参照する。
