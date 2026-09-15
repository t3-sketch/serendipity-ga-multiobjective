# Serendipity Recommendation — 推薦の評価指標を問い直す

推薦の代理指標が高いことと、人が「価値ある偶然の発見をした」と感じることは同じだろうか。
この研究では、推薦システム側の評価と、人間が経験するserendipityの対応を検証する。

現在の正式結果は **v0 = MovieLens 1M canonical baseline** である。
SASRecによる候補生成とNSGA-IIによる再ランキングを接続し、同じ候補上で単純加重和と比較した。
人間評価による指標の妥当性検証と、LLMによる評価の近似は今後の研究である。

**個人研究：問い・比較条件の整理、推薦実験と結果の検証。** 音楽探索を問題意識とし、現在のオフライン比較には映画データのMovieLens 1Mを使用しています。

**[正式な結果](v0/reports/S01-ml-1m-baseline.md)** · [再現の入口](v0/reproduce/) · [確認手順](v0/RUNBOOK.md) · [音楽探索デモ Sonder](https://github.com/t3-sketch/graph-rec)

*An exploratory comparison of SASRec candidate generation and multi-objective reranking, separating system-side proxies from human-experienced serendipity.*

## 今回のSerendipityの定義

今回は、**ユーザーの普段の好みを表す嗜好ベクトルと、候補作品のジャンルベクトルとのL1距離**を、Serendipityの代理指標として用いる。実装では値域を0〜1にするため、L1距離に1/2を掛ける。
音楽に置き換えると「普段好んで聴いている曲のジャンル傾向から、候補曲がどれだけ離れているか」に相当する。ただし、現在のv0実験はMovieLens 1Mの映画データを用いている。

### 嗜好ベクトルとジャンル距離

作品 $i$ のジャンルベクトルを $\mathbf{g}_i$ とする。所属ジャンルを1、それ以外を0とした18次元ベクトルを、成分の和が1になるよう正規化する。
ユーザー $u$ の推薦時点までの履歴のうち、本人の履歴平均評価を超える、学習済みカタログ内の作品集合を $H_u^+$ とし、その平均を嗜好ベクトルとする。

$$
\mathbf{p}_u = \frac{1}{|H_u^+|}\sum_{j\in H_u^+}\mathbf{g}_j
$$

候補作品との距離と、推薦リスト $L_u$ の平均距離は次のとおり。

$$
d(u,i)=\frac{1}{2}\lVert\mathbf{p}_u-\mathbf{g}_i\rVert_1
=\frac{1}{2}\sum_{c=1}^{18}|p_{u,c}-g_{i,c}|,
\qquad
D(u,L_u)=\frac{1}{K}\sum_{i\in L_u}d(u,i)
$$

#### 数式の記号の読み方

表では、たとえば `p_u` の `_u` は「ユーザーuに対応する」という添字を表す。

| 記号 | 意味 |
| --- | --- |
| `u` | 推薦を受けるユーザー |
| `i` | 推薦候補の作品。今回の実験では映画、音楽への応用では曲に相当する |
| `g_i` | 候補作品iの特徴ベクトル。今回は、成分の和を1に正規化したジャンルベクトル |
| `p_u` | ユーザーuの嗜好ベクトル。好意的に評価した過去作品のジャンルベクトルの平均 |
| `d(u,i)` | ユーザーuの嗜好と作品iとの距離。今回はL1距離の1/2 |
| `∥・∥₁` | L1ノルム。2つのベクトルの差に適用すると、各成分の差の絶対値を足したL1距離（Manhattan distance）になる |
| `c` | 特徴の次元番号。今回はジャンルの番号 |
| `18` | MovieLens 1Mのジャンル特徴が18次元あることを表す |
| `p_{u,c}` | ユーザーuの嗜好ベクトルの第c成分 |
| `g_{i,c}` | 作品iのジャンルベクトルの第c成分 |
| `abs(p_{u,c} − g_{i,c})` | 数式中の縦棒で囲んだ差の絶対値。そのジャンルについての隔たりを、符号を除いて表す |
| `Σ` | 指定した範囲の値を足し合わせる記号。距離の式ではc=1から18まで足す |
| `1/2` | 正規化したジャンルベクトル間のL1距離を、0〜1に収める係数 |
| `H_u⁺` | 推薦時点までに、本人の履歴平均評価を超える評価を付けた、学習済みカタログ内の作品集合 |
| `∣H_u⁺∣` | 集合H_u⁺に含まれる作品数。集合を囲む縦棒は、絶対値ではなく要素数を表す |
| `j ∈ H_u⁺` | 嗜好ベクトルの式で、履歴集合H_u⁺に含まれる各作品jを対象とすること |
| `L_u` | ユーザーuへの推薦リスト |
| `K` | 推薦する作品数。今回は10件 |
| `D(u,L_u)` | 推薦リスト内の各作品との距離d(u,i)を平均した値 |

今回の結果表の **mean genre distance** は、K=10（推薦10件）のリスト平均を評価対象ユーザー間で平均した値である。値が大きいほど過去の好みからジャンルが離れている。
ただし、この距離だけでは「好みに合う」「価値ある偶然の発見だった」ことは示せない。人間が経験するSerendipityとは区別し、推薦品質はNDCGでも評価する。最適化目的は関連度と距離の2つであり、関連度と距離の積 $r\times d$ は診断専用である。

### NDCG@10：好みに合う作品を上位に推薦できたか

評価期間内の作品のうち、推薦時点の履歴平均評価を超え、未視聴かつ学習済みカタログ内にある作品を正解集合 $P_u$ とする。順位 $j$ の推薦作品が $P_u$ に含まれるとき $y_{u,j}=1$、それ以外は0とする。

$$
\mathrm{DCG@K}(u)=\sum_{j=1}^{K}\frac{y_{u,j}}{\log_2(j+1)}
$$

$$
\mathrm{IDCG@K}(u)=\sum_{j=1}^{\min(K,|P_u|)}\frac{1}{\log_2(j+1)},
\qquad
\mathrm{NDCG@K}(u)=\frac{\mathrm{DCG@K}(u)}{\mathrm{IDCG@K}(u)}
$$

正解を上位に並べるほど高く、理想的な順位で1になる。今回は $K=10$、正解集合が空でないユーザーを対象とし、推薦の表示順はSASRecの順位に揃える。正解集合にはTop-100候補に入らなかった作品も含めるため、候補生成での取りこぼしも評価に残る。未観測作品を嫌いと判断する指標ではない。
NSGA-IIは3つの探索seedの値をユーザー内で平均した後、評価対象974人で平均する。

定義は公開実装の[ジャンルの正規化](v0/reproduce/experiment.py#L52)、[嗜好ベクトルと距離](v0/reproduce/experiment.py#L115)、[NDCG計算](v0/reproduce/experiment.py#L387)と照合した。詳細な評価条件は[正式報告](v0/reports/S01-ml-1m-baseline.md)を参照。

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

### 人間が経験するserendipity

- Brett Binst, Lien Michiels, and Annelien Smets (2025). [What Is Serendipity? An Interview Study to Conceptualize Experienced Serendipity in Recommender Systems](https://arxiv.org/abs/2505.15440). UMAP.
- Brett Binst, Ulysse Maes, Martijn C. Willemsen, and Annelien Smets (2026). [Let Me Introduce You: Stimulating Taste-Broadening Serendipity Through Song Introductions](https://arxiv.org/abs/2604.08385). UMAP.

### データセット

- F. Maxwell Harper and Joseph A. Konstan (2015). [The MovieLens Datasets: History and Context](https://doi.org/10.1145/2827872). ACM Transactions on Interactive Intelligent Systems.
