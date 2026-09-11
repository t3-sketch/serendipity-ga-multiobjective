# MovieLens 1Mの利用条件と出典

v0のcanonical baselineは、University of MinnesotaのGroupLens Research Projectが配布するMovieLens 1Mを使用した。
2026-09-11に別保存の1M配布物の`data/ml-1m/README`を確認した。
適用条件の原文は同梱READMEのUSAGE LICENSEを参照する。
公開repoにはデータ自体を同梱しない。

## 保存READMEに記載された条件

- 出版物でデータセットの使用を明記し、HarperとKonstanの論文を引用する。
- University of MinnesotaやGroupLensによる推奨や承認を示唆しない。
- データの再配布には別途許可が必要である。
- 商用または収益を伴う利用には、GroupLensの教員から事前許可が必要である。
- データの正確性、用途への適合性、結果の妥当性は保証されない。

コードのライセンスはデータの利用条件を置き換えない。
`data/`と`outputs/`はGit管理対象外とし、元データを含む分割CSVや学習用ファイルも一式公開しない。

## 出版物での引用

本研究は、University of MinnesotaのGroupLens Research Projectが提供するMovieLens 1Mを使用した（Harper and Konstan, 2015）。

F. Maxwell Harper and Joseph A. Konstan. 2015.
The MovieLens Datasets: History and Context.
ACM Transactions on Interactive Intelligent Systems 5, 4, Article 19, 19 pages.
[DOI](https://doi.org/10.1145/2827872)

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

## 公式参照先と確認範囲

- [MovieLens 1M公式配布ページ](https://grouplens.org/datasets/movielens/1m/)
- [MovieLens 1M公式README](https://files.grouplens.org/datasets/movielens/ml-1m-README.txt)

今回確認したのは保存済み配布READMEである。
公式READMEの再取得はタイムアウトしたため、最新版との一致は未確認である。
旧100Kの利用記録はGit historyに残す。
