# v0：SASRecとNSGA-IIの探索的baseline

同じ推薦候補に対して、関連度と嗜好からの距離を考慮する再ランキングは何を変えるか。
MovieLens 100KでSASRec、単純加重和、NSGA-IIを比較した。

## 結果の要点

旧条件（rating 4以上をpositive、目的を平均`r`と平均`r×d`とする条件）の本実験は完了している。
K=10では、NSGA-IIはSASRecより代理値が高く、NDCGとRecallが低かった。
推薦件数10〜30の全条件で、NSGA-IIの代表推薦は加重和と一致した。

これはSASRecとNSGA-IIの接続と、代理目的が推薦に与える影響の記録である。
人間のserendipity、音楽での効果、FAS-MOEAの再現は検証していない。
NSGA-IIが一般に不要だと結論するものでもない。

## 問いから証拠を読む

- [Microロードマップ](ROADMAP.md)：各StepのRQ、短い結果、実行状態、検証状態
- [v0-S1の報告](reports/S01-main.md)：K=10の比較
- [v0-S2の報告](reports/S02-list-length.md)：K=10〜30の比較
- [v0-S3の報告](reports/S03-definition-smoke.md)：現在の評価条件への変更と接続確認
- [baseline全体の詳しい解釈](reports/baseline-overview.md)

## 現在のコードとの違い

| 対象 | positive | 最適化する軸 | 保存状況 |
|---|---|---|---|
| 旧本実験の保存結果 | rating ≥ 4 | 平均`r`、平均`r×d` | K=10とK=10〜30の本実験 |
| 現在の100Kコード | 推薦時点までの本人の平均rating超え | 平均`r`、平均`d` | smokeのみ。本比較は未完 |

`r`はSASRecスコアの順位値、`d`は高評価履歴のgenre profileからの距離である。
順位値の95%維持はNDCGの95%維持を保証しない。
旧結果を現行コードの実行結果と読み替えず、[RUNBOOK](RUNBOOK.md)で対象条件を確認する。

別保存のMovieLens 1M実験はこの100K結果と分けて扱う。
保存先と未確定のversion割り当ては[研究全体のMacro](../ROADMAP.md)にある。
データと実験出力の公開条件は[DATA_LICENSE.md](DATA_LICENSE.md)を参照する。
