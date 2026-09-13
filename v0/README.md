# v0：MovieLens 1M canonical baseline

v0の正式結果は、MovieLens 1MでSASRec、Weighted Sum、NSGA-IIを比較したK=10のbaselineである。
positiveは推薦時点までの履歴平均超え、目的はmean relevanceとmean genre distanceとする。

## 結果の要点

Weighted SumとNSGA-IIはSASRecよりgenre distanceが高い一方、NDCG@10が低かった。
NSGA-IIと加重和のNDCG差の95%区間は0を跨ぎ、品質上の優位性は確認できない。
これはsystem-sideのintegration baselineであり、人間のserendipity改善、音楽での効果、FAS-MOEAの再現を実証していない。

- [正式baseline報告](reports/S01-ml-1m-baseline.md)：実験条件、数値、解釈、証拠と未検証事項
- [H1公開要約](reports/S02-h1-candidate-generators.md)：候補生成器比較の検証範囲
- [sanity公開要約](reports/S03-sasrec-sanity-check.md)：別protocolの途中記録
- [Microロードマップ](ROADMAP.md)：実行と検証の状態
- [RUNBOOK](RUNBOOK.md)と[reproduce/](reproduce/)：現行の1M確認入口
- [データ出典と利用条件](DATA_LICENSE.md)

## 公開コードと保存結果

現行入口は`v0/reproduce/`である。公開対象だけで`check.py`と保存集計の照合ができる。
データ、checkpoint、ユーザー単位出力は同梱しない。
`v0/experiment.py`と`v0/config.json`は100K用の歴史的snapshotであり、現行入口ではない。
100Kの結果文書はGit historyに残す。
1Mの元コードと生出力は別保存のまま移動していない。
