# セレンディピティ指向推薦における遺伝的アルゴリズムによる多目的最適化の有効性

推薦の代理指標が高いことと、人が「価値ある偶然の発見をした」と感じることは同じだろうか。
この研究では、推薦システム側の評価と、人間が経験するserendipityの対応を検証する。

現在は、SASRecによる候補生成とNSGA-IIによる再ランキングを接続した探索的baselineを保存している。
人間評価に基づく指標の妥当性検証と、LLMによる評価の近似は今後の研究である。

## 最初の実験で分かったこと

MovieLens 100Kで、同じ100候補からSASRec、単純加重和、NSGA-IIが推薦を選ぶ比較を行った。
NSGA-IIが最適化した代理値は上昇したが、未使用の評価データに対するNDCGとRecallは低下した。
NSGA-IIの代表推薦は加重和と一致し、推薦件数を10から30へ増やしても同じ傾向が残った。

この結果から、代理指標の設計と代表解の選び方を見直す必要があると判断した。
FAS-MOEAの再現、指標の妥当性、人間が経験するserendipityの改善を示した結果ではない。
条件と数値は[v0の研究概要](v0/README.md)と[実験報告](v0/reports/S01-main.md)にまとめている。

## 研究の見取り図

| 研究テーマ | 現時点の到達点 |
|---|---|
| システム側の指標と推薦品質の関係 | 旧100Kのbaseline比較を完了。別保存の1M実験もあり、評価設計との照合が必要 |
| 代理指標と人間評価の対応 | 未完 |
| LLMによる人間評価の近似 | 未完 |
| Fortuitous / Refreshing / Enrichingの集約 | 未完 |
| 検証済みの近似評価を使う推薦 | 未完 |

研究全体の問いと依存関係は[Macroロードマップ](ROADMAP.md)、各実験の問いと結果は[v0のMicroロードマップ](v0/ROADMAP.md)を参照する。

## 実装と資料

SASRecの学習にはRecBole、再ランキングにはpymooのNSGA-IIを使用する。
学習済みモデルの後段で推薦集合を選ぶ構成であり、SASRec自体をNSGA-IIで学習する方式ではない。

- [実行手順](v0/RUNBOOK.md)：環境、現在のコードの条件、出力の読み方
- [研究背景](research/research_state.md)と[先行研究](research/literature.md)：概念、主張の範囲、関連文献
- [研究の進め方](research/README.md)：計画、報告、相談からの引き継ぎ

現在のコードと旧100K結果は評価条件が異なる。
保存済み結果の確認と、現在のコードによる新規実行を区別する。

この公開リポジトリにはコード、研究文書、集計結果の報告を収録する。
データ、checkpoint、ユーザー単位の出力、相談履歴は含めない。
報告内の`outputs/`と`data/`への参照は、ローカルに保存した証拠の位置を示すため、GitHub上では開けない。

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
