# Research instructions

## 作業開始時の読み分け

研究判断の前に `ROADMAP.md`（Macro）と `research/research_state.md`（背景と採用前提）を読む。
対象versionの作業では、その `ROADMAP.md`（Micro）と対象Stepのplan / reportを確認する。
`research/decisions.md`は関係する判断を確認し、過去の議論全文を毎回読み込まない。

- 新規性や先行研究との差分：`research/literature.md`
- RQ、仮説、評価設計の変更：`research/hypotheses.md`
- 実行：対象versionの`RUNBOOK.md`
- 文書更新と相談の引き継ぎ：`research/README.md`

## 研究上の制約

v0はSASRec候補生成とNSGA-II再ランキングを接続した探索的integration baselineである。
FAS-MOEAの再現、指標の妥当性検証、experienced serendipityの改善実証として扱わない。
現行v0コードと旧保存結果はpositive定義と目的軸が異なるため、対象runの条件を先に確認する。
既存コード、環境、データ、出力を勝手に全面改修または上書きしない。
新規実験は承認された別設定と別出力先を使う。
別フォルダの1M実験の保存先は`ROADMAP.md`にある。v1への割り当ては未確定であり、自動移動しない。

Macroは`M1`〜`M5`、Microは`v0-S1`のようにversion付きで呼ぶ。
主作業は一つに絞るが、依存しない文献調査や設計まで直列化しない。
着手条件はMacroの依存関係とMicroの完了条件に従う。
人間評価前のLLMはprototypeであり、validated surrogateとしての最適化へ進まない。

algorithmic / offline / afforded serendipity（システム側の代理指標）と、
experienced serendipity（人間がFortuitous、Refreshing、Enrichingを伴う経験として報告するもの）を区別する。
代理指標の上昇を経験の改善と表現しない。
LLM出力はhuman appraisalを近似するcomputational surrogateであり、人間の経験そのものではない。

判断は「課題、仮説、根拠、結果」で残す。
major decisionは同じ作業内で`research/decisions.md`へ追記し、`research/research_state.md`の採用前提も照合して必要な変更を反映する。
進捗は対応するROADMAP、実測と検証証拠はreportに記録する。
未計測は未完とし、事後整理を事前計画や事前登録と呼ばない。
実行完了と検証完了を分け、検証の実施日、対象、根拠、未検証範囲を示す。

相談元の識別子と外部保存先はローカル専用の`research/local-context.md`を参照する。
更新の反映を依頼されたときだけ差分を照合し、ユーザーの決定、AIの提案、実測、未確認を区別する。
過去の実行指示を現在の許可とせず、同名Projectやサイドバー配置による自動同期を仮定しない。
