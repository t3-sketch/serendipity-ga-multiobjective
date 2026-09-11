# 実行対象の選び方と保存済み100Kコードの手順

## 最新結果はMovieLens 1M

現在の結果を読む場合は、[1M本比較とPhase 1の保存記録](../ROADMAP.md#external-1m)を参照する。
対象runは`ml-1m-rd-k10-resumed2`と`ml-1m-rd-k10-phase1`で、いずれもK=10の実行は完了している。
1Mのコードと成果物は別保存であり、ローカルでの保存場所は`research/local-context.md`を参照する。
再実行する際は、その保存先のコード、config、実行記録を使う。
下記の100K用コマンドで1M結果を再現できるとは扱わない。

## このフォルダに残した100Kコード

SASRecで生成した同じ100候補からK件（既定10件）を選び、SASRec、Weighted Sum(r,d)、NSGA-II(r,d)を比較する。
研究上の問いは、SASRec relevanceとgenre-based taste distanceのトレードオフにおいて、NSGA-IIがrelevance-onlyと単純加重和より有用かどうかである。
MovieLens 100Kを使い、SASRecの学習はRecBole、NSGA-IIの探索はpymooで行う。

## 実行前の注意

この文書は現行100Kコードの手順であり、旧本実験の再現コマンドではない。
旧runのpositiveと目的は異なり、当時のコードsnapshotは未確認である。
以下のコマンドは実行例であって実行許可ではない。
新しい実験は[Micro](ROADMAP.md)と承認済みplanを確認し、既存出力を上書きしない。
2026-09-10の文書整理では学習も実験も再実行していない。

## 実行

Python 3.10で動作確認する。RecBole 1.2.1の依存制約に合わせ、NumPy 1.26 / PyTorch 2.5を専用環境に固定している。

```bash
cd v0  # cloneしたリポジトリのルートから実行
uv venv --python 3.10 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python check.py
.venv/bin/python experiment.py --smoke --output outputs/my-smoke
.venv/bin/python experiment.py --output outputs/rd-full
.venv/bin/python check.py outputs/rd-full
SERENDIPITY_RUN=outputs/rd-full .venv/bin/jupyter lab results.ipynb
```

この環境には`.venv`を準備済み。`config.json`の`data_dir`はプロジェクト内の`data/ml-100k`を指す（configファイルのある場所からの相対パス）。他の環境では[GroupLens公式配布](https://grouplens.org/datasets/movielens/100k/)から取得して同じ場所に展開する。既存出力は上書きしない。再実行は`--output outputs/run-02`のように新しい場所を指定する。

MovieLens 100KはMITではなく独自の研究利用条件。研究出版物での引用が必要で、再配布と商用利用には別途許可が必要。[利用条件と引用文](DATA_LICENSE.md)および[同梱README原文](data/ml-100k/README)を参照する。

本実験は、University of MinnesotaのGroupLens Research Projectが提供するMovieLens 100Kを使用した：F. Maxwell Harper and Joseph A. Konstan (2015), *The MovieLens Datasets: History and Context*, ACM TiiS 5(4), Article 19. [doi:10.1145/2827872](https://doi.org/10.1145/2827872)。

上の本実行を完了した後、モデルを固定して再ランキングだけを実行する場合は、`.venv/bin/python experiment.py --reuse-model-from outputs/rd-full --output outputs/rd-rerank-02`。
入力SHA256、分割、ID対応、学習設定、positive定義、主要ライブラリの版を照合する。
自分の実験で作った本実行checkpointを指定する（smoke checkpointは再利用対象外）。

positive定義は現在、履歴のユーザー別平均を超えたratingに変更している。旧`rating >= 4`定義でモデル選択した`outputs/full`等のcheckpointは再利用できない。新定義で本実行を行い、`--reuse-model-from`（一括比較では`--source`）にその出力先を指定する。既存の[v0-S1](reports/S01-main.md)と[v0-S2](reports/S02-list-length.md)は旧定義の結果。

最適化軸も現在は`(relevance, genre_distance)`。一括比較の`--source`とNotebookの`SERENDIPITY_RUN`には、この軸で再ランキングした出力を指定する。旧`(r, s_proxy)`の保存結果は新比較の結果として扱わない。履歴平均によるpositive定義が一致する本実行checkpointは、目的軸だけを変える再ランキングに再利用できる。

推薦リスト長10、15、20、25、30を一括比較する場合：

```bash
.venv/bin/python run_lengths.py --source outputs/rd-full --output outputs/rd-list-lengths
# 単独でK=20を実行する場合
.venv/bin/python experiment.py --top-k 20 --reuse-model-from outputs/rd-full --output outputs/rd-k20
# 本実行とリスト長比較をNotebookで確認する場合
SERENDIPITY_RUN=outputs/rd-full SERENDIPITY_LENGTHS_RUN=outputs/rd-list-lengths .venv/bin/jupyter lab results.ipynb
```

`top_k`は推薦長、`model_selection_k`は学習モデル選択時のNDCGの評価長（既定10）。
一括比較では指定したsourceのvalidation NDCG@10で選択したモデルを共通に使い、長さごとの再学習は行わない。
候補100件、評価ユーザー、入力データの一致と、K=10でのsourceの評価値との一致（処理時間を除く）を検証する。
上の例では`outputs/rd-list-lengths/`に`summary.csv`、`paired_bootstrap.csv`、`agreement.csv`、`comparison.png`と、各`k10/`〜`k30/`の詳細出力を残す。
`agreement.csv`はNSGA-IIと`weighted_distance_selected`の推薦一致数を記録する。
[既存の5条件の実測結果](reports/S02-list-length.md)は旧positive定義と旧目的軸による記録である。
以下の10件、@10という記述は既定設定の説明であり、推薦長を変えた実行では目的関数の平均、評価指標、関連度下限、Repairの選択件数にそのKを使う。

`--smoke`は全学習データで2 epoch、各評価区間の4ユーザー、1 seed、3世代。接続確認専用で、研究上の性能評価とは区別する。本実行は最大100 epoch、validation改善なしでearly stopping、探索は40個体・50世代・3 seed。CPU 2スレッドを使う。

## データと実行経路

```text
MovieLens → 全体の時刻で80/10/10分割 → trainだけをRecBole atomic形式へ
         → RecBole SequentialDataset / TrainDataLoader / SASRec / Trainer
         → validation NDCGでcheckpoint選択
         → 全既知カタログを採点・履歴除外 → 上位100候補
         → SASRec Top-K / 加重和(r,d) / NSGA-II(r,d) → K件 → held-out比較
```

RecBoleのTrainerを継承し、validation部分だけを本実験の「区間開始時の固定クエリ」に置き換える。学習、損失、Adam、early stopping、checkpoint保存はRecBoleに任せる。公式TensorFlow SASRecの再現ではなく、RecBole版のCE loss・既定の2層/2 heads/hidden 64/maxlen 50を使う。実際の設定は`recbole_config.txt`に残す。

- train/validation/testは同一timestampをまたがせずに分ける。MovieLensの時刻は評価時刻であり、視聴時刻とは限らない。同一ユーザー・時刻内はitem ID順として再現性を確保し、その順を行動順と解釈しない。
- vocabularyはtrainのみ。入力timestampをtrain内の時刻順位に変換し、RecBoleのfloat32変換によるUnix秒の丸めを避ける。
- validationはtrain終了時の履歴、testはvalidation終了時の履歴から、ユーザーごとに1回推薦する。評価区間内の未来イベントを履歴更新に使わない。
- 学習と入力sequenceには全ratingのinteractionを使う。ratingをSASRecの入力featureには追加しない。
- 新規ユーザー、新規アイテム、高評価履歴なし、評価正例なし、候補不足は明示的に集計する。cold user/item件数は重複するため足し合わせない。候補100件から漏れた正例はRecall/NDCGの分母に残す。

### 履歴平均によるpositive定義

各ユーザーの通常のrating水準に対する相対的な好意度を使うため、**positive**を「推薦時点までの本人の平均ratingを超える評価」と定義する。
平均はcatalogで絞る前の全履歴から計算する。
validationではtrain履歴、testではtrain＋validation履歴を使い、futureを平均の計算に含めない。

```python
user_mean = h.rating.mean()
positive_history = h[((h.rating - user_mean) > 0) & h.item_id.isin(catalog)]
positives = set(target.loc[
    ((target.rating - user_mean) > 0) & target.item_id.isin(catalog), "item_id"
])
positives -= set(h.item_id)
```

`positive_history`からgenre profileを作り、`positives`を未視聴かつtrain vocabulary内の評価正例とする。
例えば履歴が`[2, 3, 4]`なら平均は3で、履歴の4だけがpositiveになる。
futureが`[3, 4, 5]`でも同じ平均3を使い、4と5をpositiveと判定する。
平均と等しいratingはnon-positiveであり、一定ratingの履歴にはpositiveがない。
今回は二値判定だけなので、標準偏差で割るz-score化は行わない。

## 目的関数と選択

各アイテムのジャンルベクトル`g_i`は複数ジャンルに均等配分し、総和を1にする。ユーザープロフィール`p_u`は過去の高評価アイテムの`g_i`の平均。

```text
r(u,i) = 全未視聴・学習済みアイテム内のSASRecスコア順位値 [0,1]
d(u,i) = 0.5 × sum_g |p_u(g) - g_i(g)|
最大化: 推薦10件の平均r、平均d
補助診断のみ: s_proxy(u,i) = r(u,i) × d(u,i)
```

同スコアには平均順位を与え、選択の同点は元のitem ID昇順で決める。`r`は確率や予測ratingではない。低人気度を意外性と同一視せず、嗜好からのジャンル差を使う。

NSGA-IIはユーザーごとの候補選択bitsetを探索する。pymooの二点交叉・bit flip変異と、選択件数を10に戻す最小のRepairを使う。初期集団にはSASRec上位解・全加重和解とランダム解を入れる。過去世代と初期解も保存して非劣解集合を作るため、有限個体数による解の脱落で比較基準を失わない。

Pareto判定に渡す目的値と保存する目的値は小数点以下12桁に揃える。浮動小数点の加算順による約1e-16の差を、別のトレードオフとして扱わないための数値処理。

代表解はSASRec上位10件の平均`r`の95%以上を満たす解の中で平均`d`最大、同点なら平均`r`最大、最後にitem ID列の辞書順とする。表示順は全手法でSASRec順。加重和側の代表解も同じ規則で選ぶ。

**95%はNDCGを95%維持する保証ではない。** 上位100候補の順位値は元々高いので、この制約は緩くなることがある。実際のNDCG損失は別途測定する。提示の距離指標は粗いジャンル近似であり、音楽の知覚距離の検証は行っていない。

## 比較と読み方

1. `sasrec`: SASRec score順の上位10件。平均relevanceのみを最大化する基準。
2. `weighted_distance_selected`: `w*r + (1-w)*d`の上位10件を重みごとに作り、共通のrelevance floorで選んだ代表解。
3. `nsga2`: 平均relevanceと平均genre distanceの2目的探索から、同じfloorで選んだ代表解。

重みは0〜1を0.1刻みで固定。重み別の`weighted_distance:w`は詳細CSVに残し、summary・bootstrapは上記3手法で比較する。test正例で重みや代表解を選ばない。アイテム加算型の目的なので固定重みに対するtop-kは厳密最適解。NSGA-IIが必要かは得られた解と時間から判断する。

`weighted_proxy`は比較手法から削除した。
`s_proxy = r*d`を使うreranking baselineは生成しない。

- `recall`, `ndcg`: 区間内の既知・高評価・未視聴アイテムに対する@10。次の1件だけを当てる通常のSASRec評価とは異なる。
- `candidate_recall`: 候補100件によるRecall。
- `relevance`, `genre_distance`: 最適化する2軸の平均値。
- `s_proxy`: `r*d`の平均。補助診断値としてのみ保存し、最適化・代表選択・bootstrapには使わない。
- `heldout_distance`: `sum(hit_i * d_i) / 10`。予測関連度をheld-outの二値高評価で置き換えた代理評価。未観測は不評を意味しない。
- `seconds`: ユーザー当たりの選択処理時間。モデル推論は共通で、`inference.json`に別記する。加重和の代表解には重み掃引の時間も含める。

3 search seedsをまずユーザー内で平均してからユーザー間で集計する。対応付きbootstrap 2,000回の95%区間は探索seedを独立ユーザーとして水増ししない。主要指標はrecall、ndcg、relevance、genre_distance、heldout_distance、secondsで、対SASRecに加えてNSGA-II対加重和も出す。SASRec学習seedは42の1つであり、学習seedを変えた頑健性検証ではない。

## 成果物

`--output`で指定した場所（上の本実行例では`outputs/rd-full/`）に保存する。
省略時の設定値は`outputs/full/`だが、このworkspaceには旧実験があるため、新しい出力先を指定する。

| ファイル | 内容 |
|---|---|
| `config.json`, `environment.json`, `recbole_config.txt` | 実験設定・全依存バージョン・入力SHA256 |
| `split.json`, `split_assignments.csv`, `*_mapping.json` | 分割、対象外件数、元IDとRecBole ID対応 |
| `training.csv`, `checkpoint.json`, `checkpoints/` | validation推移、選択epoch、モデル・optimizer状態 |
| `{validation,test}/candidates.csv` | user/item ID・生score・r・d・s_proxy |
| `{validation,test}/recommendations.csv` | 手法・seed・ユーザーごとの推薦順位 |
| `{validation,test}/pareto.csv`, `convergence.csv` | relevance・genre_distanceの非劣解・採用点・同じ2軸の世代別population hypervolume |
| `{validation,test}/per_user.csv`, `summary.csv`, `paired_bootstrap.csv` | 個別評価・集計・対応差の区間 |
| `comparison.png`, `completion.json` | 図と正常完了マーカー |

`completion.json`のないディレクトリは未完了。`results.ipynb`は保存済み出力を読み込み、再学習なしで確認する。

Pareto図の横軸はMean relevance percentile、縦軸はMean genre distance。
`pareto.csv`も`relevance`と`genre_distance`を目的値として保存する。

`split.json`の`validation`・`test`には`positive_definition`、`eligible_users`、`no_positive_history_users`、`no_eligible_positive_users`を保存する。`users`には評価区間に現れる全ユーザーの`history_rating_mean`、`positive_history_count`、`future_positives_count`、`status`（採用／除外理由）を記録する。履歴のないcold userの平均は`null`。positive件数はcatalog・未視聴条件を適用後の件数（履歴側には未視聴条件を適用しない）。ユーザー除外件数はcold user→positive履歴なし→評価正例なし→候補不足の順に数えるため、後段条件を満たさない全ユーザー数とは異なる。

## 確認済みの変更結果

MovieLens 100Kの同じ時刻分割とK=10で、positive定義の変更によるfilter結果は次のとおり。
人数はsmoke用の4人への制限をかける前の全件集計である。

| 集計項目 | validation（旧絶対基準→履歴平均基準） | test（旧絶対基準→履歴平均基準） |
|---|---:|---:|
| eligible users | 69→69 | 51→47 |
| positive履歴なし | 0→0 | 1→1 |
| eligibleなfuture正例なし | 12→12 | 17→21 |

validationでは3人ずつ入れ替わり、testでは4人が対象外になった。
この変更の目的は対象人数を増やすことではなく、ユーザーごとの相対的な好意度を評価に使うことである。
新しい`(r,d)`目的軸への変更では、このfilter結果は変わらない。
個別の履歴平均とpositive件数は[現定義のsplit.json](outputs/rd-smoke/split.json)、変更前後の比較は[filter_comparison.json](outputs/mean-centered-smoke/filter_comparison.json)で確認できる。

`check.py`では、future ratingを変えても履歴平均が変わらないこと、toy caseの全組み合わせによる厳密な`(mean(r), mean(d))`非劣解との一致、固定weightのtop-K、K件制約、重複排除、代表選択のfloorと同点規則を検証している。
future positivesや積の診断値がなくても最適化できることも確認した。
[outputs/rd-smoke](outputs/rd-smoke/)では2 epochのsmoke実行、保存CSVの検証、Notebookの実行が完了し、候補とSASRec評価値が目的軸変更前と一致した。
この100K設定での3手法の本比較と5条件のリスト長比較は未実施である。
別保存の1M本比較とは区別する（[Macroの保存記録](../ROADMAP.md#external-1m)）。

保存済みのsmoke結果を確認する場合：

```bash
.venv/bin/python check.py outputs/rd-smoke
SERENDIPITY_RUN=outputs/rd-smoke .venv/bin/jupyter lab results.ipynb
```

## 研究メモ

- **課題:** SASRec relevanceとgenre-based taste distanceのトレードオフに、多目的最適化を使う価値があるか。
- **仮説:** NSGA-IIによる`(mean(r), mean(d))`の探索が、relevance-onlyや同じ2軸の単純加重和より有用な推薦集合を得られる。
- **根拠:** 3手法の候補集合と評価条件を揃え、加重和とNSGA-IIには共通のrelevance floorを適用する。探索法の有用性はheld-out指標・2目的値・処理時間で検証する。
- **結果:** この100K設定の新目的軸での本比較は未計測（TODO）。[v0-S1](reports/S01-main.md)と[v0-S2](reports/S02-list-length.md)は旧目的軸の記録。代理値の改善だけでは体験面の仮説を支持しない。

2025年論文のFortuitousness・Refreshing・Enrichingは体験の必要構成要素。本実験の`d`はRefreshingの一部、`r`はEnrichingの限定的代理で、Fortuitousnessは未測定。積の式は本実験の提案であり原論文の検証済み尺度ではない。2026年の紹介文論文が扱う主観体験・紹介文・音楽への効果は未検証。次段階は音楽の時刻付き履歴と特徴へ移植し、試聴後の3要素・総合発見感・後続探索を測ること。

### 参照

- [Notion 論文合宿](https://www.notion.so/3aa80c3dba238102907ccb65f4c8fc3b): 定義・先行実験の整理。
- [What Is Serendipity? (2025)](https://arxiv.org/abs/2505.15440)
- [Let Me Introduce You (2026)](https://arxiv.org/abs/2604.08385)
- [FAS-MOEA論文](https://doi.org/10.1016/j.ipm.2025.104604): 本実装は2目的・ユーザー別探索の派生実験で、数値再現ではない。
- [RecBole SASRec](https://recbole.io/docs/user_guide/model/sequential/sasrec.html)
- [pymoo NSGA-II](https://pymoo.org/algorithms/moo/nsga2.html) / [部分集合選択](https://pymoo.org/case_studies/subset_selection.html)
