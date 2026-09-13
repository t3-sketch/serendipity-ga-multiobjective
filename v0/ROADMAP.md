# v0のMicroロードマップ

最終更新：2026-09-13。v0 = MovieLens 1M canonical baseline。
関連Macro：[M1：システム側の比較](../ROADMAP.md#m1)。

## 問いと結果

| ID | Research Question | 実行状態 | 結果 | 検証状態 | 報告 |
|---|---|---|---|---|---|
| v0-S1（1M） | 同じ候補に対する関連度とgenre distanceの最適化は推薦品質をどう変えるか | 本比較とPhase 1診断が完了 | 距離上昇、NDCG低下。NSGA-IIの加重和に対するNDCG優位性は未確認 | 保存集計とH1の指標再現を照合。事前判断記録の照合は未完 | [1M baseline](reports/S01-ml-1m-baseline.md) |

本比較とPhase 1診断は同じbaselineの証拠である。
Phase 1はMacro番号ではない。
2026-09-11以前のv0-S1〜S3は100K実験を指す歴史的IDであり、[移行前のGit履歴](https://github.com/t3-sketch/serendipity-ga-multiobjective/tree/27a4066b506199af377201edd2c4a0ae9588d9e6/v0)に保持する。
旧100KのS2/S3を1Mの完了Stepとして付け替えない。

## 完了条件

- [x] 1Mの本比較と診断runの完了マーカーを確認した。
- [x] 実施条件と3手法の保存集計を正式reportへまとめた。
- [x] ユーザーが1Mをv0のcanonical baselineとして採用した。
- [x] system-sideに限定した結果解釈と検証範囲を記録した。
- [x] H1 A0/A1で下流7指標と7 epoch学習ログを差0.0で再現した（2026-09-12〜13）。公開snapshotと当時ソースのバイト一致は未確認。
- [ ] 当時の事前仕様と判断記録をM1の評価設計と照合する。

次の主作業は[Macro M1](../ROADMAP.md#m1)の未確認事項の照合である。
現行入口は[reproduce/](reproduce/)。[plans](plans/README.md)は将来の未実施実験に使い、既存結果から事前計画を作らない。
フル再学習と生出力の移動は含まない。
