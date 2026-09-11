# Research instructions

## 作業開始時の読み分け

研究判断の前に `ROADMAP.md`（Macro）と `research/research_state.md`（背景と採用前提）を読む。
対象versionの作業では、その `ROADMAP.md`（Micro）と対象Stepのplan / reportを確認する。
`research/decisions.md`は関係する判断を確認し、過去の議論全文を毎回読み込まない。

- 新規性や先行研究との差分：`research/literature.md`
- RQ、仮説、評価設計の変更：`research/hypotheses.md`
- 実行：対象versionの`RUNBOOK.md`
- 文書更新と相談の引き継ぎ：`research/README.md`

## 研究日記の出力形式

研究日記を作成または更新する際は、毎回 `research/journal-template.md` を読んで従う。
日付と「今日やったこと」「仮説」「実験」「分かったこと」「問題」「Next」の6項目をこの順で出力する。
通常の会話回答やversionの長い研究記事には強制しない。
日記の作成依頼や研究の節目で適用し、毎回答の日記追加や外部同期は行わない。

## 研究上の制約

v0はMovieLens 1Mのcanonical baselineであり、SASRec候補生成とNSGA-II再ランキングを接続した探索的integration baselineである。
結果の正本は`v0/reports/S01-ml-1m-baseline.md`とする。
FAS-MOEAの再現、指標の妥当性検証、experienced serendipityの改善実証として扱わない。
正式条件は履歴平均超えpositive、目的(mean r, mean d)、K=10、候補100。r×dは診断専用とする。
公開コードとconfigは100K用の既存実装であり、1M結果の再現コードとは扱わない。
100Kの結果文書はGit historyで参照し、現行の研究結果として引用しない。
既存コード、環境、データ、出力を勝手に全面改修または上書きしない。
新規実験は承認された別設定と別出力先を使う。
1Mのversion配置はv0に確定した。別保存のコード、データ、出力は自動移動しない。
保存証拠の確認は`v0/RUNBOOK.md`、ローカル保存場所は公開対象外の`research/local-context.md`を参照する。

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
