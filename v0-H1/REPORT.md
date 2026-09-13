# v0-H1：候補生成器の比較結果

実施日：2026-09-12〜13。事前計画は[PLAN.md](PLAN.md)、実行の経緯は[HANDOFF.md](HANDOFF.md)。
この作業では`v0-H1/`の外にあるファイルを変更していない。既存文書への反映案は[REFLECTION.md](REFLECTION.md)。

## 結論

v0と同じ評価条件のもとで候補生成器をSASRecからComiRec-SAまたはeSASRecへ替えても、
**候補集合の天井（Candidate Recall@100）と精度に、測定できる差は生じなかった**。
事前に固定した規則はvalidationの点推定でeSASRecを選ぶが、
同一ユーザーでの対応付きbootstrapの95%区間は0を含み、
さらにtestでは差の符号が反転する。

一方で、3つのbackboneすべてで共通した所見が2つ得られた。

1. **validation NDCG@10はepoch 1が最良で、その後は単調に近く低下する**。
   これはv0のSASRecだけの性質ではなく、multi-interestでも強化transformerでも同じだった。
   この評価protocolでは、学習を進めるほど指標が下がる。
2. **NSGA-IIは加重和に対して測定できる利得を持たない**。
   v0で観測された所見が、3つのbackboneすべてで再現した。
   計算費用は1ユーザーあたり約1,000倍である。

したがって、この評価条件におけるボトルネックは候補生成のarchitectureではない。
KGの比較へ進む際に、候補生成器の選択に時間をかける根拠は得られなかった。

## 検証：harnessと学習の再現

### A0 再ランキングと評価の段

v0の保存済みcheckpoint（`ml-1m-rd-k10-resumed2`）を再構築環境で再利用した。
`recall`、`ndcg`、`candidate_recall`、`relevance`、`genre_distance`、`s_proxy`、`heldout_distance`の
7指標について、validationとtestの両方で**最大絶対差 0.000e+00**だった。

### A1 学習の段

同環境でSASRecをscratch再学習し、v0の`training.csv`と比較した。

| epoch | v0 validation NDCG@10 | A1 validation NDCG@10 | 差 |
|---|---:|---:|---:|
| 1 | 0.0755898615035552 | 0.0755898615035552 | 0.0 |
| 2 | 0.06454475599758709 | 0.06454475599758709 | 0.0 |
| 3 | 0.06237065517910619 | 0.06237065517910619 | 0.0 |
| 4 | 0.06289359665446789 | 0.06289359665446789 | 0.0 |
| 5 | 0.05864378902477502 | 0.05864378902477502 | 0.0 |
| 6 | 0.057745659318389736 | 0.057745659318389736 | 0.0 |
| 7 | 0.058860546389396265 | 0.058860546389396265 | 0.0 |

7 epochすべてが一致した。
再現に使った環境はpython 3.10.20、recbole 1.2.1、torch 2.5.1、numpy 1.26.4、CPU 2 threadsである。

これで**v0の再現確認は、学習と下流の両方で取れた**。
未確認のまま残るのは、当時の事前仕様と判断記録の照合である。

## 実装の契約検査

`check_models.py`の結果（全項目PASS）。

| 検査 | SASRec | ComiRec-SA | eSASRec |
|---|---|---|---|
| `full_sort_predict`の形状 | PASS | PASS | PASS |
| スコアが有限 | PASS | PASS | PASS |
| eval時に決定的 | PASS | PASS | PASS |
| 損失が下がる | 2.468→0.494 | 2.672→1.836 | 4.505→2.605 |
| interest collapseなし | — | routing比 0.295/0.366/0.091/0.248 | — |
| gateが飽和しない | — | — | 層ごと平均 0.478 / 0.491 |

実データ（test 974人）でのComiRecのinterest利用も別に測った。

| 指標 | 平均 | 中央値 | 最小 |
|---|---:|---:|---:|
| 候補100件に寄与したinterest数（設定4） | 3.64 | 4 | 2 |
| top-10に寄与したinterest数 | 2.20 | 2 | 1 |
| 候補内で最大のinterestの占有率 | 0.525 | 0.500 | 0.260 |

候補プール全体が単一interestから来たユーザーは0人だった。
つまりComiRecが劣った理由はinterest collapseではない。

## Validation：採用判断の根拠

採用判断はvalidationのみで行い、testは見ていない（[PLAN.md](PLAN.md)で事前に固定）。

| arm | Candidate Recall@100（primary） | NDCG@10 | Recall@10 | genre distance | 選択epoch |
|---|---:|---:|---:|---:|---:|
| eSASRec | **0.204790** | 0.071308 | 0.047989 | 0.725324 | 1 |
| SASRec（scratch） | 0.195638 | 0.075590 | 0.064861 | 0.730998 | 1 |
| ComiRec-SA | 0.188588 | 0.066082 | 0.042455 | 0.721195 | 1 |

**事前規則の出力：eSASRecを採用**（primary最大、SASRecとの差0.009152は同点幅0.005を超える）。

同じ478人での対応付きbootstrap（2,000回、対SASRec）。

| arm | 指標 | 平均差 | 95%区間 | 0を除外 |
|---|---|---:|---|---|
| eSASRec | Candidate Recall@100 | +0.009152 | [−0.000850, +0.019108] | いいえ |
| eSASRec | NDCG@10 | −0.004282 | [−0.013501, +0.004459] | いいえ |
| ComiRec-SA | Candidate Recall@100 | −0.007050 | [−0.031148, +0.016706] | いいえ |
| ComiRec-SA | NDCG@10 | −0.009507 | [−0.022176, +0.002413] | いいえ |

規則は差の大きさだけで採用を決める形にしてあり、不確実性の条件を入れていなかった。
その結果、**規則はeSASRecを選ぶが、証拠は優位性を示していない**。
この不足は事前規則の設計上の問題であり、結果を見てから規則を変えた事実はない。

## Test：判断の後に一度だけ報告

`sasrec`という手法名は「その候補生成器自身のtop-10」を指す。

| arm | 手法 | NDCG@10 | Recall@10 | Candidate Recall@100 | genre distance | heldout distance |
|---|---|---:|---:|---:|---:|---:|
| SASRec | 生成器のtop-10 | 0.095103 | 0.039218 | 0.192242 | 0.727851 | 0.060336 |
| SASRec | 加重和 | 0.050995 | 0.014538 | 0.192242 | 0.930735 | 0.044923 |
| SASRec | NSGA-II | 0.051279 | 0.014576 | 0.192242 | 0.930735 | 0.045123 |
| ComiRec-SA | 生成器のtop-10 | 0.090552 | 0.032463 | 0.183060 | 0.720894 | 0.057936 |
| ComiRec-SA | 加重和 | 0.055431 | 0.017306 | 0.183060 | 0.937585 | 0.046787 |
| ComiRec-SA | NSGA-II | 0.055462 | 0.017314 | 0.183060 | 0.937585 | 0.046822 |
| eSASRec | 生成器のtop-10 | 0.098070 | 0.039085 | 0.186805 | 0.721804 | 0.059016 |
| eSASRec | 加重和 | 0.054779 | 0.015129 | 0.186805 | 0.922393 | 0.044615 |
| eSASRec | NSGA-II | 0.054578 | 0.014464 | 0.186805 | 0.922393 | 0.044651 |

同じ974人での対応付きbootstrap（2,000回、対SASRec）。

| arm | 指標 | 平均差 | 95%区間 | 0を除外 |
|---|---|---:|---|---|
| eSASRec | Candidate Recall@100 | −0.005437 | [−0.013021, +0.002374] | いいえ |
| eSASRec | NDCG@10 | +0.002967 | [−0.003247, +0.009340] | いいえ |
| ComiRec-SA | Candidate Recall@100 | −0.009182 | [−0.022211, +0.003442] | いいえ |
| ComiRec-SA | NDCG@10 | −0.004550 | [−0.013705, +0.004398] | いいえ |

primaryはvalidationでeSASRecが上、testではSASRecが上である。
どちらも区間が0を含む。**符号の反転は、この差がノイズの範囲にあることの現れとして読む。**

## NSGA-IIと加重和（各armの内部比較、test）

| arm | NDCG@10の差（NSGA-II − 加重和） | 95%区間 | genre distanceの差 | 1ユーザーあたり秒（NSGA-II / 加重和） |
|---|---:|---|---:|---|
| SASRec | +0.000284 | [−0.0000671, +0.000919] | 0（float精度内） | 0.306 / 0.000266 |
| ComiRec-SA | +0.0000309 | [−0.000151, +0.000244] | 0（float精度内） | 0.483 / 0.000415 |
| eSASRec | −0.000201 | [−0.001028, +0.000285] | 0（float精度内） | 0.183 / 0.000165 |

v0で「NSGA-IIの加重和に対するNDCG優位性は未確認」とした所見は、
**3つのbackboneすべてで再現した**。
どのbackboneでも、代表解の目的値は加重和とNSGA-IIで一致し、費用だけが約1,000倍になる。

これはNSGA-IIが常に不要という結論ではない。
目的がitem加算的で、制約が1本（relevance floor）で、代表解規則が同一である限り、
加重和の掃引が同じ解に到達する、という範囲の主張である。

## 候補プールの診断（採用判断に使わない）

| arm | プールのmean genre distance | プールのmean self-information | 異なるitem数 | catalog被覆率 |
|---|---:|---:|---:|---:|
| SASRec | 0.739165 | 11.140761 | 2,638 | 0.720371 |
| ComiRec-SA | 0.733314 | 10.679948 | 2,437 | 0.665483 |
| eSASRec | 0.734620 | 11.075230 | 2,677 | 0.731021 |

self-informationは`-log2(train内でのitemの出現割合)`の平均で、値が小さいほど人気itemに寄る。

ComiRec-SAは**最も被覆が狭く、最も人気に寄った**。
multi-interestは「広く拾う」ことを意図した機構だが、この設定では反対の結果になった。
argmax routingが学習中に人気itemを説明しやすいinterestへ勾配を集める挙動が候補にも表れた、
という解釈は可能だが、本実験では検証していない。

genre distanceはどのarmもほぼ同じで、backboneを替えることは
「履歴から遠い候補を増やす」手段として機能しなかった。

## 全armに共通した学習曲線

| epoch | SASRec | ComiRec-SA | eSASRec |
|---|---:|---:|---:|
| 1 | **0.075590** | **0.066082** | **0.071308** |
| 2 | 0.064545 | 0.063539 | 0.062784 |
| 3 | 0.062371 | 0.061073 | 0.064617 |
| 4 | 0.062894 | 0.062774 | 0.064414 |
| 5 | 0.058644 | 0.056464 | 0.057896 |
| 6 | 0.057746 | 0.057409 | 0.061992 |
| 7 | 0.058861 | 0.059673 | 0.063032 |

3つすべてがepoch 1で最良となり、以後は下がる。
architectureを替えてもこの形は変わらなかった。

この評価は「区間開始時点で固定した1つのqueryから、10%の時間窓に現れる本人のpositiveを当てる」形である。
学習が進むと直近の系列に強く適合し、窓全体に広がるpositiveの当て方は悪くなる、という説明と整合する。
ただし本実験はこの機構を検証していない。
同じデータで通常のnext-item評価（leave-one-out）を行った別作業では、
同じRecBole SASRecがepoch 6でvalidation NDCG@10 = 0.62を示している。
評価protocolを替えれば桁が変わる指標であり、**v0の0.0756とpublishedの数値を並べて比較してはならない**。

## 実行費用

| arm | 学習と準備 | run全体 | 1 epochの目安 |
|---|---:|---:|---|
| A0（再利用） | 23秒 | 826秒 | — |
| A1 SASRec | 9,911秒 | 11,279秒 | 約13分（単独時） |
| A2 ComiRec-SA | 1,266秒 | 3,423秒 | 約4分 |
| A3 eSASRec | 10,612秒 | 11,511秒 | 約25分 |

A1とA3の時間は3 run並行実行中の値を含むため、単独実行の下限ではない。
候補生成の推論費用は1ユーザーあたりSASRec 3.59ms、ComiRec-SA 4.82ms、eSASRec 3.07msだった。

## 研究上の解釈

- **課題**：KGで距離を精緻化する前に、候補生成器を決める必要があった。v0のCandidate Recall@100は0.192で、再ランキングは候補外のpositiveを取り戻せない。
- **仮説**：multi-interest（ComiRec-SA）または強化transformer（eSASRec）は、候補の天井を上げる。
- **根拠**：分割、positive定義、候補数、再ランキング、hyperparameterを固定し、モデルclassだけを替えた。harnessがv0を完全再現することを先に確認した。
- **結果**：どのarmもSASRecに対して測定できる差を示さなかった。validationの点推定ではeSASRecが上、testではSASRecが上で、いずれも区間は0を含む。ComiRec-SAは候補の被覆をむしろ狭めた。NSGA-IIの利得の不在は3 backboneで再現した。

## 限界

- 学習seedは1つである。arm間差がseed変動を超えるかは検証していない。armごとのhyperparameter tuningも行っていない。
- eSASRecはLiGR層とsampled softmaxの2変更を同時に含む。SASRec+SSのablationがないため、どちらの寄与かは切り分けられない。
- eSASRecの学習目的は、RecBoleのprefix拡張による次item予測で代替した。原論文の全位置同時のshifted sequenceとは計算単位が異なる。mixed negative samplingとlogQ補正は使っていない。
- ComiRec-SAは原論文のsampled softmaxではなく全catalog softmaxで学習し、λによるaggregationも切った。原論文の完全再現ではない。
- 評価protocolはv0固有である。published leave-one-out数値と比較しない。
- 「差が検出できなかった」ことは「差が無い」ことではない。testでの区間幅はCandidate Recall@100で約±0.008であり、これより小さい差はこの人数では判定できない。
- 候補生成の指標が上がっても、それはexperienced serendipityの改善ではない。この区別はM2以降の人間評価まで保持する。

## 次に決めること（2026-09-13時点で未決）

KG比較で固定する候補生成器を決める必要がある。
事前規則の出力はeSASRecだが、証拠は優位性を示していない。
どれを選んでも本報告の測定結果は変わらない。

| 選択肢 | 根拠 | 費用 |
|---|---|---|
| SASRecに固定 | v0 canonical baselineとの連続性が保てる。他armの優位性が未検出なので替える利益がない。実装が最も単純で1 epochが最短（約13分） | なし（既存checkpointが使える） |
| eSASRecに固定 | 事前規則の出力を守る。事後の変更を避けるという規律の観点では最も安全 | 1 epochが約25分。KG比較の各runが約2倍重くなる |
| 評価protocolを先に見直す | 3 backboneすべてでepoch 1が最良になるという所見は、backboneでなくprotocol側の問題を示す。この状態でKGを比較しても、KGの寄与が指標に現れない可能性がある | 新規設計と再実行が必要 |

**この作業での推奨はSASRecへの固定である。**
理由は3つある。
第一に、eSASRecの優位性はvalidationの点推定にしか存在せず、testでは反転する。
第二に、v0が正本であり、正本と同じ候補生成器を使えばKGの寄与だけを差分として読める。
第三に、eSASRecは1 epochが約2倍かかるため、KG比較の反復速度が落ちる。

ただし、事前規則の出力に反する選択になる。
選ぶ場合は「規則の出力はeSASRec、採用はSASRec、理由は優位性が未検出でありv0との連続性を優先」と、
逸脱として`research/decisions.md`に明記する必要がある。この文書への反映は未実施である。

3番目の選択肢を採るなら、`../sasrec-sanity-check/`のnext-item評価が比較対象になる。
同じRecBole SASRecが同じデータでvalidation NDCG@10 = 0.62に達しており、
v0のprotocolが指標の分解能を大きく下げていることの傍証になる。

## 参照した生成物

| ファイル | 内容 |
|---|---|
| `reports/validation-decision.csv` | 採用判断に使ったvalidation集計 |
| `reports/validation-paired-bootstrap.csv` | validationの対SASRec対応付きbootstrap |
| `reports/test-comparison.csv` | testの3 arm × 3手法の集計 |
| `reports/test-paired-bootstrap.csv` | testの対SASRec対応付きbootstrap |
| `reports/training-reproduction.csv` | A1とv0の学習曲線の照合 |
| `reports/pool-diagnostics.csv` | 候補プールの被覆とself-information |
| `reports/comirec-interests.csv` | ユーザーごとのinterest利用（974行）。`user_id`付きのため非公開 |
| `outputs/A*/` | 各armの生出力（`training.csv`、`checkpoint.json`、`validation/`、`test/`） |
| `logs/` | 各runの標準出力と`analyze.log` |
