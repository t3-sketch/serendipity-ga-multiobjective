# 音楽の「出会えてよかった」を考える研究日記

知らなかったけれど、出会えてよかったと思える音楽を推薦したい。
特に、いつもの好みから少し外れた曲に興味を持ち、聴く音楽の幅が広がるような発見に関心がある。

このリポジトリは、そのために何を作り、何を測ればよいのかを考えていく研究日記として書きます。
完成した手法だけでなく、試した理由、実験結果、うまく説明できなかったこと、考えを変えた経緯も残します。

現在の実験結果は、MovieLens 1Mでの本比較とPhase 1診断です（推薦長K=10、候補100件）。
SASRecによる候補生成に加重和とNSGA-IIによる推薦集合の選択を接続し、同じ候補から選ぶ方法を比較しました。
初期の100K実験は過去の記録として残しています。
計算上の代理指標は上がりましたが、それを「価値ある発見が増えた」とは解釈できませんでした。

現在は、Taste-Broadening Serendipityを何として捉え、どう測るかを考えています。
SASRecやNSGA-IIを今後も使うかは、その問いに合わせて判断します。

## 研究の記録

### 2026-09-11

#### 今日やったこと

1Mの本比較とPhase 1の保存結果を振り返り、READMEと研究文書を最新結果に合わせて整理した。
研究日記の書式も統一した。

#### 仮説

当初は、SASRecの候補生成とNSGA-IIを接続することで、関連度とserendipity-orientedな目的のtrade-offを探索できると考えた。
今日はその仮説を保存結果から振り返った。

#### 実験

新規実験なし。以下の1M比較（K=10）とPhase 1の保存結果を確認した。

- SASRec
- SASRec + Weighted Sum
- SASRec + NSGA-II

Metrics:

- 保存済みのNDCG@10、Recall@10、Candidate Recall@100、平均ジャンル距離、heldout distanceなどを照合。
- 推薦の完全一致率と採用解の由来を保存CSVから再集計。
- 既存`check.py`を再実行し、Phase 1の内部整合性と、本比較からPhase 1への候補・推薦・既存指標の回帰一致を確認。

#### 分かったこと

1Mでも、ジャンル距離が増えた一方で、将来のpositiveを推薦する性能は下がった。
NSGA-IIの最終推薦は単純な加重和と98.56%一致し、NDCGの優位性は確認できなかった。
根拠と解釈は[v0から1M再実験までの研究記事](v0/README.md)と[1Mの保存記録](ROADMAP.md#external-1m)に残した。

#### 問題

ジャンル距離が増えたことを「よい発見が増えた」とは解釈できない。
普段聴かない曲への興味と、その後に聴く音楽の幅が広がることを、どう区別して測るかが残っている。

#### Next

Taste-Broadening Serendipityの定義と測定を整理する。
v0は探索的な実験として残し、SASRecやNSGA-IIを今後も使うかは評価したいものに合わせて判断する。

## このリポジトリの読み方

- 考えた経緯を読む：[v0の研究記事](v0/README.md)
- 研究全体の現在地を確認する：[Macroロードマップ](ROADMAP.md)
- 最新の1M結果を確かめる：[1Mの保存記録](ROADMAP.md#external-1m)
- 初期100Kの証拠を読む：[初回実験](v0/reports/S01-main.md)、[推薦リスト長の比較](v0/reports/S02-list-length.md)、[Microロードマップ](v0/ROADMAP.md)
- 保存済みコードを理解する：[v0の実行手順](v0/RUNBOOK.md)
- 背景を読む：[研究背景](research/research_state.md)、[先行研究](research/literature.md)、[記録の運用](research/README.md)

日記には、その時点の考えや未確定の仮説も含まれます。
採用した判断は[判断ログ](research/decisions.md)に、実験で確認した事実は各報告に分けて記録します。
1Mの成果物は別保存で、version割り当ては未確定です。
このリポジトリの現行100Kコード、旧100K結果、1M結果を同じ実行条件として読み替えないでください。

## 公開するものとデータの出典

この公開リポジトリにはコード、研究文書、集計結果の報告を収録する。
データ、checkpoint、ユーザー単位の出力、相談履歴は含めない。
報告内の`outputs/`と`data/`への参照は、ローカルに保存した証拠の位置を示すため、GitHub上では開けない。

MovieLensはGroupLens Research Projectのデータを使用する。
出典：F. Maxwell Harper and Joseph A. Konstan (2015), *The MovieLens Datasets: History and Context*, [DOI](https://doi.org/10.1145/2827872)。
既存100Kの[データ利用条件](v0/DATA_LICENSE.md)も参照し、データ、checkpoint、ユーザー単位の出力をこのREADMEと一緒に無条件で再配布しない。

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
