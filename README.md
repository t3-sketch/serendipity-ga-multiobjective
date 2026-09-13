# 音楽の「出会えてよかった」を考える研究日記

推薦の代理指標が高いことと、人が「価値ある偶然の発見をした」と感じることは同じだろうか。
この研究では、推薦システム側の評価と、人間が経験するserendipityの対応を検証する。

現在の正式結果は **v0 = MovieLens 1M canonical baseline** である。
SASRecによる候補生成とNSGA-IIによる再ランキングを接続し、同じ候補上で単純加重和と比較した。
人間評価による指標の妥当性検証と、LLMによる評価の近似は今後の研究である。

## MovieLens 1Mで分かったこと

履歴平均超えをpositiveとし、同じ100候補からK=10件を選ぶ条件で比較した。
Weighted SumとNSGA-IIはSASRecよりmean genre distanceが高い一方、NDCG@10が低かった。
NSGA-IIとWeighted SumのNDCG差の95%区間は0を跨ぎ、推薦品質上の優位性は確認できない。

これはsystem-side proxyと推薦品質のtrade-offの記録である。
FAS-MOEAの再現や、人間が経験するserendipityの改善を示した結果ではない。
条件、数値、証拠と検証範囲は[v0の正式baseline報告](v0/reports/S01-ml-1m-baseline.md)にまとめている。

## 研究の見取り図

| 研究テーマ | 現時点の到達点 |
|---|---|
| システム側の指標と推薦品質の関係 | 1M本比較と診断を完了し、v0として正式採用。事前の評価設計との照合は未完 |
| 代理指標と人間評価の対応 | 未完 |
| LLMによる人間評価の近似 | 未完 |
| Fortuitous / Refreshing / Enrichingの集約 | 未完 |
| 検証済みの近似評価を使う推薦 | 未完 |

研究全体の問いと依存関係は[Macroロードマップ](ROADMAP.md)、各実験の問いと結果は[v0のMicroロードマップ](v0/ROADMAP.md)を参照する。

## 研究の記録

### 2026-09-12

#### 今日やったこと

MovieLens 1Mの既知結果と保存済み成果物を照合し、v0の正式baselineを1Mへ一本化した。
100K中心の結果文書は現行mainから外し、Git historyへ残した。

#### 仮説

新しい仮説なし。
今回の作業は、採用済み結果と研究文書の不一致を解消する文書整理である。

#### 実験

新規実験なし。
1M本比較とPhase 1診断の保存済み設定、完了状態、集計結果を確認した。

Metrics:

- [正式baseline報告](v0/reports/S01-ml-1m-baseline.md)に記録したNDCG@10とmean genre distanceを保存CSVと照合した。

#### 分かったこと

1Mではgenre distanceが高い再ランキング結果ほどNDCG@10が低く、NSGA-IIのWeighted Sumに対するNDCG上の優位性も確認できない。
この結果はsystem-sideのtrade-offであり、experienced serendipityの改善を示さない。

#### 問題

公開コードは100K用であり、1M実験のコードと出力は別保存である。
当時の事前仕様との対応と、コードと環境を復元した再現確認は未完である。

#### Next

M1の事前判断記録と1M実験条件を照合する。
追加実験は、その照合後に必要性を判断する。

### 2026-09-13

#### 今日やったこと

1Mの別保存実装を特定し、公開snapshotを`v0/reproduce/`へ置いた。保存集計とS01報告値、H1の再現CSVを照合した。100Kコードを現行入口から外した。

#### 仮説

新しい仮説なし。公開対象だけで小規模確認と集計照合ができる状態を作る作業である。

#### 実験

フル再学習なし。`check.py`と`verify_saved.py`を実行する。H1の既存A0/A1結果を再現証拠として使う。

#### 分かったこと

S01の報告値は公開expected CSVと一致する。H1のSASRec行と7 epoch学習ログも一致する。公開`experiment.py`はresumed2記録hashともH1 harnessともバイト一致しない。

#### 問題

事前仕様との照合は未完。フル再学習は未実施。H1/sanityフォルダは未commitのまま選別だけした。

#### Next

AstraレビューのあとPhase 3。Phase 2の範囲ではM1の事前判断照合へ戻れる。

## 実装と資料

SASRecの学習にはRecBole、再ランキングにはpymooのNSGA-IIを使用する。
学習済みモデルの後段で推薦集合を選ぶ構成であり、SASRec自体をNSGA-IIで学習する方式ではない。

- [結果の確認手順](v0/RUNBOOK.md)：現行の1M入口と保存集計の照合
- [研究背景](research/research_state.md)と[先行研究](research/literature.md)：概念、主張の範囲、関連文献
- [研究の進め方](research/README.md)：計画、報告、相談からの引き継ぎ

現行の公開入口は[v0/reproduce/](v0/reproduce/)である。
公開対象だけで小規模な境界検査と報告値照合ができる。フル再学習は未実施。
`v0/experiment.py`は100K用の歴史的snapshotである。100Kの結果文書はGit historyに残す。

この公開リポジトリにはコード、研究文書、集計結果の報告を収録する。
データ、checkpoint、ユーザー単位の出力、相談履歴は含めない。
報告内のrun IDと証拠ファイル名は別保存の記録を識別するもので、GitHubに出力を同梱したことを意味しない。

MovieLensはGroupLens Research Projectのデータを使用する。
出典：F. Maxwell Harper and Joseph A. Konstan (2015), *The MovieLens Datasets: History and Context*, [DOI](https://doi.org/10.1145/2827872)。
公開時は[データ利用条件](v0/DATA_LICENSE.md)を確認し、データ、checkpoint、ユーザー単位の出力をこのREADMEと一緒に無条件で再配布しない。

## 参考文献

現在の研究背景、手法設計、比較対象として参照している論文を示す。
各論文と本研究の関係は[先行研究の整理](research/literature.md)を参照する。

### 推薦モデルと多目的最適化

- Wang-Cheng Kang and Julian McAuley (2018). [Self-Attentive Sequential Recommendation](https://arxiv.org/abs/1808.09781). ICDM.（SASRec）
- Shresth Khaitan and Rahul Shrivastava (2026). [Developing Fairness, Accuracy, and Serendipity Objective Functions for Recommendation System and Establishing Trade-off through Multi-Objective Evolutionary Optimization](https://doi.org/10.1016/j.ipm.2025.104604). Information Processing & Management.（FAS-MOEA）
- Wei Zhou et al. (2023). [Dynamic Multi-Objective Optimization Framework With Interactive Evolution for Sequential Recommendation](https://doi.org/10.1109/TETCI.2023.3251352). IEEE Transactions on Emerging Topics in Computational Intelligence.（DMORec）
- Jie Wang et al. (2024). [Sparks of Surprise: Multi-Objective Recommendations with Hierarchical Decision Transformers for Diversity, Novelty, and Serendipity](https://doi.org/10.1145/3627673.3679533). CIKM. [公開版](https://eprints.gla.ac.uk/330233/)
- Jie Wang et al. (2025). [Beyond Accuracy: Decision Transformers for Reward-Driven Multi-Objective Recommendations](https://doi.org/10.1109/TKDE.2025.3582506). IEEE Transactions on Knowledge and Data Engineering.（MODT4R）[公開版](https://eprints.gla.ac.uk/357379/)

### 人間が経験するserendipity

- Brett Binst, Lien Michiels, and Annelien Smets (2025). [What Is Serendipity? An Interview Study to Conceptualize Experienced Serendipity in Recommender Systems](https://arxiv.org/abs/2505.15440). UMAP.
- Brett Binst, Ulysse Maes, Martijn C. Willemsen, and Annelien Smets (2026). [Let Me Introduce You: Stimulating Taste-Broadening Serendipity Through Song Introductions](https://arxiv.org/abs/2604.08385). UMAP.

### データセット

- F. Maxwell Harper and Joseph A. Konstan (2015). [The MovieLens Datasets: History and Context](https://doi.org/10.1145/2827872). ACM Transactions on Interactive Intelligent Systems.
