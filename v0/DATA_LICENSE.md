# MovieLens 100Kの利用条件と出典

確認日：2026-09-08。
本プロジェクトのMovieLens 100Kは、University of MinnesotaのGroupLens Research Projectが配布したデータである。
適用条件は配布物の [README](data/ml-100k/README) の「SUMMARY & USAGE LICENSE」に記載されている。
MITライセンスではない。推薦器のコードや依存ライブラリのライセンスが、このデータの条件を置き換えることはない。

## 今回のコピー

研究目的で、同じ利用者のローカル環境内の `Desktop/fas-moea-reproduction/data/ml-100k/` から当初の `sasrec-serendipity/data/ml-100k/` へコピーし、現在はv0一式として`sasrec-serendipity/v0/data/ml-100k/`に保管している。
研究利用の許諾に基づく内部コピーと判断している。第三者への配布や公開は行っていない。
配布時のREADMEを変更せず保存した。FAS-MOEAのPythonコードはコピーしていない。

## 必要な対応

- このデータを用いた出版物では、利用を明記し、下記HarperとKonstanの論文を引用する。
- University of MinnesotaまたはGroupLensによる推奨や承認があると述べたり、示唆したりしない。
- データの再配布には別途許可が必要。引用やREADMEの同梱だけでは再配布の許可にならない。
- 商用または収益を伴う目的には、GroupLens Research Projectの教員から事前許可を得る必要がある。
- 正確性、特定目的への適合性、このデータに基づく結果の妥当性は保証されない。

READMEの保持は条件の原文を残すための対応であり、MITの著作権表示義務として行ったものではない。
この条件は、追加実験や新しい研究の実施を義務づけていない。
今回追加したリスト長比較はユーザーの研究上の依頼による。

`data/` と `outputs/` は既存の `.gitignore` の除外対象。
特に `outputs/` の分割CSVや学習用atomicファイルには元の評価データが含まれるため、フォルダ一式の公開は避け、公開する成果物を個別に選ぶ。
`.gitignore` はZIP添付などの手動共有を制限する機能ではない。

## 論文や報告書に載せる表記

本研究は、University of MinnesotaのGroupLens Research Projectが提供するMovieLens 100Kデータセットを使用した（Harper and Konstan, 2015）。

F. Maxwell Harper and Joseph A. Konstan. 2015.
The MovieLens Datasets: History and Context.
ACM Transactions on Interactive Intelligent Systems 5, 4, Article 19, 19 pages.
https://doi.org/10.1145/2827872

```bibtex
@article{harper2015movielens,
  author = {Harper, F. Maxwell and Konstan, Joseph A.},
  title = {The MovieLens Datasets: History and Context},
  journal = {ACM Transactions on Interactive Intelligent Systems},
  year = {2015},
  volume = {5},
  number = {4},
  articleno = {19},
  numpages = {19},
  doi = {10.1145/2827872}
}
```

## 入手先と検証範囲

- [公式配布ページ](https://grouplens.org/datasets/movielens/100k/)
- [公式利用案内と許可申請へのリンク](https://grouplens.org/datasets/movielens/)
- [公式README](https://files.grouplens.org/datasets/movielens/ml-100k-README.txt)
- [公式ZIP](https://files.grouplens.org/datasets/movielens/ml-100k.zip)

確認日に公式配布ページと利用案内を閲覧した。公式案内も、各データセットのREADMEを利用条件として参照するよう求めている。
ファイル配信ホストへのHTTPSアクセスは証明書期限切れエラーになり、最新READMEの再取得はできなかった。
このコピーには、手元の配布ZIPと一致する同梱READMEの条件を用いた。

元ZIPのSHA256：`50d2a982c66986937beb9ffb3aa76efe955bf3d5c6b761f4e3a7cd717c6a3229`

| ファイル | SHA256 |
|---|---|
| u.data | 06416e597f82b7342361e41163890c81036900f418ad91315590814211dca490 |
| u.item | 553841ebc7de3a0fd0d6b62a204ea30c1e651aacfb2814c7a6584ac52f2c5701 |
| README | 4883b8cf340ed0059971b33f56ad3adc88a40792108ebca3d24aafc4c82e8b52 |
