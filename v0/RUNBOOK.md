# v0 MovieLens 1M baselineの確認手順

正式結果は[1M baseline報告](reports/S01-ml-1m-baseline.md)を正本とする。
現行の公開入口は[reproduce/](reproduce/)である。

## 公開repoから確認できる範囲

1. `v0/reproduce/check.py`で、データなしの境界検査を実行する。
2. `v0/reproduce/verify_saved.py`で、公開した集計抜粋とS01の報告値を照合する。
3. MovieLens 1Mを`v0/data/ml-1m/`へ置けば、配布ファイルのSHA-256を追加確認できる。

データ、checkpoint、ユーザー単位出力は同梱しない。
`v0/experiment.py`と`v0/config.json`は100K用の歴史的snapshotであり、現行入口ではない。
100Kの結果文書はGit historyで参照する。

## データ取得

GroupLensのMovieLens 1Mを取得し、`ratings.dat`と`movies.dat`だけを`v0/data/ml-1m/`へ置く。
利用条件は[DATA_LICENSE.md](DATA_LICENSE.md)。

| ファイル | SHA-256 |
|---|---|
| ratings.dat | `506d64ca44484487c11dc2d9a28de5c54948213e6b96285e298afe28d6ea4e0f` |
| movies.dat | `0140fc2356357c1a851d0f52e893a1e4d3696df632c4141cea8d5bc3d621f0b9` |

## 保存済み1M証拠

本比較のrun IDは`ml-1m-rd-k10-resumed2`、診断追加は`ml-1m-rd-k10-phase1`である。
公開repoには`v0/reproduce/expected/`に集計抜粋がある。
所有者のローカル環境では`research/local-context.md`に元の保存先を保持する（公開対象外）。
両runを別々に確認し、保存ファイルを上書きしない。

| 確認対象 | 確認する内容 |
|---|---|
| completion.json | status=complete、smoke=false。実行完了と再現検証を区別する |
| config.json | data/ml-1m、K=10、候補100、floor=0.95、40個体、50世代、探索seed 42/43/44 |
| split.json | history_mean_centered_gt_0、validation 478人、test 974人 |
| checkpoint.json | selected epoch 1、validation NDCG@10=0.075590 |
| test/summary.csv | sasrec、weighted_distance_selected、nsga2をS01と照合する |
| test/paired_bootstrap.csv | NSGA-IIと加重和のNDCG差および95%区間 |
| environment.json | python 3.10.20、recbole 1.2.1、torch 2.5.1、numpy 1.26.4 |

positiveの基準は推薦時点までの本人の全履歴平均である。
validationはtrain、testはtrain＋validationを使い、未来のratingを含めない。
目的はmean rとmean dであり、r×dは診断専用とする。

## 再現の範囲

2026-09-13のPhase 2で、公開対象だけで`check.py`と`verify_saved.py`を実行した。
H1のA0は保存checkpoint再利用で下流7指標が差0.0、A1はscratch 7 epochの`training.csv`が差0.0だった。
公開snapshotの`experiment.py`は、resumed2が記録したsource hashともH1 harnessともバイト一致しない。
一致したのは保存集計とH1再実行の指標である。

フル再学習とNSGA-II本実験の再実行は別単位である。Phase 2では未実施。
H1 A1は7 epochの学習と974人の再ランキングまで完了している。
sanity checkの1 epochは別protocolで約37〜44分だった。v0条件の100 epoch予算を埋める再学習の費用は、その数字から外挿するだけで確定しない。

再実行が必要な場合は[plans](plans/README.md)に目的、未使用の出力先、確認範囲を記し、実行の承認を得る。
