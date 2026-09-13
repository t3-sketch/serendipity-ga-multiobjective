# v0-H1：候補生成器の比較（SASRec / ComiRec-SA / eSASRec）

ID：v0-H1。関連Macro：[M1](../ROADMAP.md#m1)。作成日：2026-09-12。状態：承認済み・実施中。
承認者：ユーザー。承認日：2026-09-12。この文書は実行前に固定した判断の記録である。

この作業は`v0-H1/`の中だけで完結させる。
`v0/`、`research/`、`ROADMAP.md`、外部の1M保存出力は読み取りのみで、変更しない。
既存文書へ反映すべき内容は[REFLECTION.md](REFLECTION.md)に案として置き、反映自体は行わない。

## 課題

v0はSASRec候補に対する再ランキングのbaselineであり、候補生成器そのものを比較していない。
v0のCandidate Recall@100は0.192であり、再ランキングは候補外のpositiveを取り戻せない。
KGによる距離の精緻化へ進む前に、どの候補生成器を固定するかを決める必要がある。

## RQ

v0と同じ評価条件のもとで、候補生成器をSASRecからComiRec-SA / eSASRecへ替えると、
候補集合の品質（Recall@100）と再ランキング後の関連度・genre distanceのトレードオフはどう変わるか。

## 仮説と根拠

- ComiRec-SAは利用者の履歴を複数のinterestベクトルへ分解する。単一の系列表現より広い範囲の候補を拾い、Recall@100を上げる可能性がある。
- eSASRecはLiGR層とsampled softmaxでSASRecを強化した構成であり、公開benchmarkでSASRecを上回ると報告されている。
- 根拠は同一の分割、positive定義、候補数、再ランキング条件を保ち、モデルclassだけを替えることに置く。

## 反証条件

どのarmもvalidation Candidate Recall@100でSASRecを上回らない場合、
「この評価条件では新しいbackboneは候補の天井を上げない」と結論し、KG比較はSASRec候補固定で進める。

## 固定する条件（v0と同一）

| 項目 | 値 |
|---|---|
| Dataset | MovieLens 1M（外部保存の`data/ml-1m`をsymlinkで参照） |
| 分割 | 全体時刻による80/10/10。同一timestampを跨がせない |
| Positive | rating > 推薦時点までの本人の履歴平均。validationはtrain、testはtrain＋validation |
| 系列長 | MAX_ITEM_LIST_LENGTH=50 |
| backbone | n_layers 2、n_heads 2、hidden 64、inner 256、dropout 0.5、lr 1e-3、batch 256 |
| 学習 | epochs 100、patience 5、学習seed 42、CPU 2 threads |
| checkpoint選択 | validation NDCG@10（本研究のpositive定義による） |
| 候補 | train語彙内の未視聴Top-100 |
| 再ランキング | K=10、relevance floor 0.95、加重和w=0〜1（0.1刻み）、NSGA-II 40個体×50世代、探索seed 42/43/44 |
| bootstrap | 2,000回 |

## 変更する条件

モデルclassと、そのモデル固有のhyperparameterのみ。

| arm | run ID | 内容 |
|---|---|---|
| A0 | A0-sasrec-reuse | SASRec。v0の`ml-1m-rd-k10-resumed2`のcheckpointを再利用。harnessの検証（gate） |
| A1 | A1-sasrec-scratch | SASRec。同環境でscratch再学習 |
| A2 | A2-comirec-sa | ComiRec-SA。interest数4、attention隠れ次元256、損失は全catalog softmax |
| A3 | A3-esasrec | eSASRec。LiGR層（ff_emb_mult 4）＋sampled softmax（負例256、uniform、logQ補正なし） |

## 事前に固定した判断規則

- **Primary**：validation Candidate Recall@100。再ランキングで取り戻せない候補の天井を測る。
- **Secondary**：validation NDCG@10（候補生成器のtop-10、再ランキングなし）。
- **採用規則**：validation Recall@100が最大のarmを採用する。差が0.005以内なら実装が単純で学習が速い方を採る。
- **testの使用時点**：採用判断はvalidationのみで行い、その後にtestを一度だけ報告する。
- **診断（採用判断に使わない）**：候補集合のmean genre distance、popularity novelty、item coverage、ComiRecのinterest利用分布、NSGA-IIと加重和の差。

## 指標の意味

| 指標 | 定義 | 何を測るか | 何を測らないか |
|---|---|---|---|
| Candidate Recall@100 | 候補100件に入ったpositiveの割合 | 候補生成の天井 | 順序の質 |
| NDCG@10 | 区間内の既知かつ未視聴positiveに対する@10 | 上位の関連度 | 次の1件を当てる通常のLOO性能 |
| mean genre distance | positive履歴のgenre profileとの0.5×L1距離 | 履歴からの離れ具合 | 人間が感じるserendipity |
| heldout distance | sum(hit×d)/K | 当たった推薦の距離 | 未観測itemの評価 |

出力CSVの`sasrec`という手法名は「その候補生成器自身のtop-K」を指す。列名は既存コードのまま変更していない。

## 実行手順

```sh
cd v0-H1
.venv/bin/python -B check_models.py                       # 実装の契約検査
.venv/bin/python -B experiment.py --config config-sasrec.json --output outputs/A0-sasrec-reuse \
    --reuse-model-from <v0の保存run>                      # gate
.venv/bin/python -B experiment.py --config config-sasrec.json --output outputs/A1-sasrec-scratch
.venv/bin/python -B experiment.py --config config-comirec.json --output outputs/A2-comirec-sa
.venv/bin/python -B experiment.py --config config-esasrec.json --output outputs/A3-esasrec
.venv/bin/python -B analyze.py                            # 採用判断とtest集計
```

概算：1 epoch約13分、1 armの学習約90分、再ランキング約45分。合計で半日程度。
停止条件：A0がv0の保存集計と一致しない、`check_models.py`が失敗する、ディスク残が300MB未満、1 armが4時間を超える。

## 完了条件

- [x] A0がv0の`test/summary.csv`と一致した（7指標で差0.000e+00）。
- [x] 3 armのvalidationとtestを同一条件で取得した。
- [x] validation primaryによる採用判断を、testを見る前に記録した。
- [x] 実装の契約検査（形状、値域、interest collapse、gate飽和）を記録した。
- [x] 結果と限界を[REPORT.md](REPORT.md)に、実行と判断の経緯を[HANDOFF.md](HANDOFF.md)に残した。

## 実施後に判明した計画の不備

採用規則を「primaryの点推定の差」だけで書き、区間の条件を入れていなかった。
実測では全armの95%区間が0を含み、規則の出力と証拠の状態が食い違った。
結果を見てから規則を変更してはいないが、次の比較では採用規則に不確実性の条件を含める。

## 限界（事前に明記）

- 評価protocolはv0固有である。published leave-one-out数値と比較しない。
- 学習seedは1つで、arm間差がseed変動を超えるかは検証しない。
- hyperparameterはv0の値を流用し、arm別のtuningをしていない。ComiRec / eSASRecに不利な可能性がある。
- A3はLiGR層とsampled softmaxの2変更を同時に含む。SASRec+SSのablationは今回入れないため、原因の切り分けはできない。
- 候補生成の改善はexperienced serendipityの改善を意味しない。
