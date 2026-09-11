# v0-S3：評価条件の変更と接続確認

関連：[Micro](../ROADMAP.md)、[Macro M1](../../ROADMAP.md#m1)。
計画区分：事後整理。当時の独立した事前計画書と承認の対応は未確認。
実行状態：smoke完了。100K本比較は未完。

## RQと簡潔な結果

履歴平均positiveと目的(r,d)へ変更しても、実行と評価の接続が保たれるか。
保存記録ではsmokeが完了している。
性能上の優劣は未計測であり、旧100Kの本実験結果を流用しない。

## 判断と実施条件

- 課題：旧条件ではr×dが上昇してもheld-out品質が低下し、代理定義と代表選択の解釈に問題が残った。
- 仮説：本人の通常のrating水準を基準にpositiveを定義し、rとdを別軸にすれば、関連度と距離のトレードオフを個別に調べられる。
- 根拠：ユーザーごとの評価水準と、最適化軸を明示的に分離する。ただし、これだけで指標の妥当性や推薦品質が改善する根拠にはならない。
- 結果：接続確認まで完了。性能比較の仮説は未検証。

対象はMovieLens 100K。
positiveは推薦時点までの全履歴の平均ratingを超える評価とする。
validationはtrain履歴、testはtrain＋validation履歴を使い、未来のratingを平均に含めない。
目的は平均rと平均d、r×dは診断値とする。

smokeは2 epoch、各評価区間の4ユーザー、1 search seed、3世代であり、本比較ではない。
全件filter集計ではtestの対象が51人から47人へ変わり、validationは69人のまま構成員が入れ替わった。
詳しい定義と集計は[RUNBOOK](../RUNBOOK.md#確認済みの変更結果)を参照する。

## 証拠と検証範囲

- [rd-smoke config](../outputs/rd-smoke/config.json)
- [rd-smoke completion](../outputs/rd-smoke/completion.json)：status=complete、smoke=true
- [rd-smoke split](../outputs/rd-smoke/split.json)：現行positiveと対象者の記録
- [filter比較](../outputs/mean-centered-smoke/filter_comparison.json)
- 当時のcheck、Notebook、変更前後の一致検証の記録：[RUNBOOK](../RUNBOOK.md#確認済みの変更結果)

2026-09-10の確認は保存済み設定、完了マーカー、分割記録の照合である。
check、Notebook、学習、実験は今回再実行していない。
別保存の1M本比較は条件と保存先が異なるため、この100K本比較の完了証拠にはしない。

## 未完事項

canonical条件の採否と追加実験の必要性をM1で判断する。
実施する場合は事前計画を承認し、新しい出力先で本比較を行う。
