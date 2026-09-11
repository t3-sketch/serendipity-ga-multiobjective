# v0：MovieLens 1M canonical baseline

v0の正式結果は、MovieLens 1MでSASRec、Weighted Sum、NSGA-IIを比較したK=10のbaselineである。
positiveは推薦時点までの履歴平均超え、目的はmean relevanceとmean genre distanceとする。

## 結果の要点

Weighted SumとNSGA-IIはSASRecよりgenre distanceが高い一方、NDCG@10が低かった。
NSGA-IIと加重和のNDCG差の95%区間は0を跨ぎ、品質上の優位性は確認できない。
これはsystem-sideのintegration baselineであり、人間のserendipity改善、音楽での効果、FAS-MOEAの再現を実証していない。

- [正式baseline報告](reports/S01-ml-1m-baseline.md)：実験条件、数値、解釈、証拠と未検証事項
- [Microロードマップ](ROADMAP.md)：実行と検証の状態
- [RUNBOOK](RUNBOOK.md)：保存結果の確認方法と公開コードの制約
- [データ出典と利用条件](DATA_LICENSE.md)

## 公開コードと保存結果

公開コードとconfigは100K用の既存実装を保持している。
1M版の実装と出力は別保存であり、このrepoだけで正式baselineを再現できる状態ではない。
2026-09-11の変更は文書のみで、コード、設定、既存出力を変更していない。
100Kの結果文書は現行mainの研究正本から外し、Git historyに残す。
