# Serendipity Recommendation — 推薦の評価指標を問い直す

推薦の代理指標が高いことと、人が「価値ある偶然の発見をした」と感じることは同じだろうか。
この研究では、推薦システム側の評価と、人間が経験するserendipityの対応を検証する。

現在の正式結果は **v0 = MovieLens 1M canonical baseline** である。
SASRecによる候補生成とNSGA-IIによる再ランキングを接続し、同じ候補上で単純加重和と比較した。
人間評価による指標の妥当性検証と、LLMによる評価の近似は今後の研究である。

**個人研究：問い・比較条件の整理、推薦実験と結果の検証。** 音楽探索を問題意識とし、現在のオフライン比較には映画データのMovieLens 1Mを使用しています。

**[正式な結果](v0/reports/S01-ml-1m-baseline.md)** · [再現の入口](v0/reproduce/) · [確認手順](v0/RUNBOOK.md) · [音楽探索デモ Sonder](https://github.com/t3-sketch/graph-rec)

*An exploratory comparison of SASRec candidate generation and multi-objective reranking, separating system-side proxies from human-experienced serendipity.*

## MovieLens 1Mで分かったこと

履歴平均超えをpositiveとし、同じ100候補からK=10件を選ぶ条件で比較した。
Weighted SumとNSGA-IIはSASRecよりmean genre distanceが高い一方、NDCG@10が低かった。
NSGA-IIとWeighted SumのNDCG差の95%区間は0を跨ぎ、推薦品質上の優位性は確認できない。

| 手法 | NDCG@10（既知の好みへの適合） | mean genre distance（履歴からのジャンル距離） |
| --- | ---: | ---: |
| SASRec | 0.095103 | 0.727851 |
| Weighted Sum | 0.050995 | 0.930735 |
| NSGA-II | 0.051279 | 0.930735 |

評価対象はtest 974人、学習seedは1つ。ジャンル距離はシステム側の代理指標であり、高いほど人にとって良いとは限りません。NSGA-IIとWeighted SumのNDCG差は0.000284、95%CIは[−0.000067, 0.000919]でした。

これはsystem-side proxyと推薦品質のtrade-offの記録である。
FAS-MOEAの再現や、人間が経験するserendipityの改善を示した結果ではない。
条件、数値、証拠と検証範囲は[v0の正式baseline報告](v0/reports/S01-ml-1m-baseline.md)にまとめている。

<a id="evidence"></a>
## 判断から結果・コードを確認する

| 評価からの判断 | 結果の根拠 | 実装・検証の入口 |
| --- | --- | --- |
| ジャンル距離の上昇だけで推薦品質の改善とは判断しない | [正式報告のTest結果](v0/reports/S01-ml-1m-baseline.md#test結果)：距離とNDCGが逆方向に変化 | [公開実装の指標計算](https://github.com/t3-sketch/serendipity-ga-multiobjective/blob/985bfc534c6dbaa53c835239fd45ae73f460d004/v0/reproduce/experiment.py#L387) |
| NSGA-IIの複雑さを、加重和より良いという根拠なしに正当化しない | [保存bootstrap集計](v0/reproduce/expected/resumed2-test-paired-bootstrap.csv)：差の区間が0をまたぐ | [baselineの選択処理](https://github.com/t3-sketch/serendipity-ga-multiobjective/blob/985bfc534c6dbaa53c835239fd45ae73f460d004/v0/reproduce/experiment.py#L209)、[報告値の照合](https://github.com/t3-sketch/serendipity-ga-multiobjective/blob/985bfc534c6dbaa53c835239fd45ae73f460d004/v0/reproduce/verify_saved.py#L93) |
| 人間の発見体験との対応は、別途検証する問いとして残す | [正式報告の研究上の解釈](v0/reports/S01-ml-1m-baseline.md#研究上の解釈) | [既存の判断記録](research/decisions.md)、[研究全体の計画](ROADMAP.md) |

コードリンクは2026-09-14に照合した公開snapshotです。当時の実行コードとのバイト一致を保証するものではありません。

### 確認済みと未検証の境界

| 範囲 | 確認状況 |
| --- | --- |
| 保存集計と正式報告の一致 | 2026-09-13に照合済み。[検証範囲の記録](v0/reports/S01-ml-1m-baseline.md#証拠と検証範囲) |
| 公開資料だけでできる確認 | [check.py](v0/reproduce/check.py)による小規模な境界検査と、[verify_saved.py](v0/reproduce/verify_saved.py)による公開集計・報告値の照合。手順は[再現の入口](v0/reproduce/) |
| 公開snapshotからのフル再学習・本実験の再実行 | 未実施。データ・checkpoint・ユーザー別出力は同梱しない |
| 複数学習seedでの安定性・人間評価との対応 | 未検証。代理指標の上昇をexperienced serendipityの改善とは呼ばない |

## 研究の見取り図

| 研究テーマ | 現時点の到達点 |
|---|---|
| システム側の指標と推薦品質の関係 | 1M本比較と診断を完了し、v0として正式採用。事前の評価設計との照合は未完 |
| 代理指標と人間評価の対応 | 未完 |
| LLMによる人間評価の近似 | 未完 |
| Fortuitous / Refreshing / Enrichingの集約 | 未完 |
| 検証済みの近似評価を使う推薦 | 未完 |

研究全体の問いと依存関係は[Macroロードマップ](ROADMAP.md)、各実験の問いと結果は[v0のMicroロードマップ](v0/ROADMAP.md)を参照する。

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

## 研究の記録

過去の日記は[2026-09-12](research/logs/2026-09-12.md)・[2026-09-13](research/logs/2026-09-13.md)に分けています。当時の状態を残した記録で、現行の結果・検証範囲は上記の正式報告を参照してください。

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
