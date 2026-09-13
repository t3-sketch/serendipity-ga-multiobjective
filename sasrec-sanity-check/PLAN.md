# SASRec Sanity Check：MovieLens-1M

作成日：2026-09-11。状態：**承認済み／実装・事前検査完了、本学習開始**。
ID：sanity-S1。関連Macro：M1のbackbone診断。v1への割り当てや既存のcanonical条件変更は行わない。
承認者：ユーザー。承認日：2026-09-11。このタスクの「実行。」により本計画の実行を承認。既存ファイルを変更しない制約を維持する。

## 目的と判断

**RQ**：RecBole標準SASRecについて、原論文に近いデータ・評価条件を与えたとき、MovieLens-1Mのnext-item predictionで参考値に近い性能が得られるか。

- **課題**：既存1M実験は全体時刻分割、履歴平均超えpositive、独自の候補生成と評価を用いる。原論文の数値と直接比較できず、SASRec単体の動作を切り分けられていない。
- **仮説（提案）**：ユーザー別leave-one-out、全ratingのimplicit化、101候補の評価へ揃えると、RecBoleでも論文に近い水準のnext-item予測性能を確認できる。
- **根拠**：論文が使用したML-1Mなら、別ドメインへの一般化とbackboneの診断を混ぜずに確認できる。初回は標準モデルの設定変更を優先し、再実装による別の不具合を増やさない。
- **結果**：未計測。TODO：承認後に実装・実行・検証し、REPORT.mdへ記録する。

これは**原論文に近いprotocolでのRecBole sanity check**であり、原著実装の再現実験ではない。
「ほぼ同等」を学習目的・architectureの同等性まで含む意味で求める場合、下記の標準モデル案では足りず、実行前に計画を変更する。

## 調査で確認した差

| 条件 | 添付論文・著者実装 | 既存1M実験／RecBole | 今回の提案 |
|---|---|---|---|
| データ | MovieLens-1Mを含む4データセット | 既存本比較もML-1M | ML-1Mだけで開始 |
| positive | rating値に関係なく観測interaction | 既存評価は履歴平均超え | 全interactionを利用 |
| 分割 | ユーザーごとの最後=test、直前=valid | 既存は全体時刻分割 | 論文に合わせる |
| test入力 | train＋validの履歴 | 既存もtrain＋validだが分割単位が異なる | 論文に合わせる |
| 評価 | 正解1件＋ランダム100件 | 既存は未視聴catalogのスコアから上位候補を作る | 101候補に直接スコア付け |
| 損失 | 各有効位置のpositive/negativeにbinary cross entropy | 標準SASRecはCEまたはBPRのみ | CEを保持し相違を明記 |
| 学習単位 | 著者実装はユーザー系列をsampleし系列内の位置を同時に学習 | RecBoleはprefixを展開し末尾の次itemを学習 | 標準のprefix学習を保持 |
| モデル内部 | 左padding、入力embeddingのscale、block前の正規化等 | 右padding、正規化位置等が異なる | 標準実装を保持 |

**BPRは原論文のBCEと同じではない**ため、負例を使うという理由だけでBPRへ変更しない。
原論文のBCEだけを追加しても、学習単位・正規化位置等の差は残る。
原著の忠実な対照実験は別途計画・承認する。今回の結果が悪い場合にも自動で追加学習しない。

## データと評価protocol

1. 著者リポジトリの前処理済み `data/ml-1m.txt` を第一候補とする。承認後に取得し、commit、取得元、SHA-256、件数を保存する。現時点では未取得・未検証。
2. 添付版Table IIの6,040 users／3,416 itemsと照合する（padding IDを除く）。論文はuser/itemの5件未満除外を記述しているが、再帰的5-core等を独自に適用して同じ処理と仮定しない。配布データとの不一致は本学習前に調査し、解消できなければ停止する。
3. 配布ファイル内の各userの順序を保持し、RecBole用timestampにはuser内の連番を用いる。原timestampを復元したとは扱わない。勝手なdedupやrating閾値を追加しない。
4. user別に最後の1件をtest、その前をvalidation、残りをtrainとする。validation入力はtrain、test入力はtrain＋validation。語彙は前処理後の全catalogで固定し、held-out専用item数も記録する。未来のinteractionを学習targetや入力へ入れない。
5. 各user・各splitで、正解1件＋一様sampleした100件を保存する。全観測itemを負例から除外し、100件は重複なし。validationとtestは別の乱数系列を用い、全checkpoint・比較法で候補を固定する。
6. この負例規則は「未観測負例」という解釈を明示したもの。著者公開 `util.py` はtrain itemだけを除外し、重複やheld-out item混入を防いでいないため、**公開コードと完全一致しない**。候補の安全な生成と固定を今回の既知の差として報告する。`uni100`という設定名だけで一致を判断せず、実際の候補を検査する。
7. ML-1Mの評価可能な全userを対象とし、除外数と理由を出力する。SASRec上位100件を候補にする操作やrerankingは挟まない。

論文ではAmazon Beauty／Games、Steamも使用するが、初回は追加しない。
ML-1Mだけの結果から疎なデータでの性能や論文全体の追試成功は主張しない。

## モデルと学習の固定案

RecBole 1.2.1の標準SASRecを使用する。下記は**実装前の設定案**で、動作確認済みの実行用ファイルではない。

```yaml
MAX_ITEM_LIST_LENGTH: 200
n_layers: 2
n_heads: 1
hidden_size: 50
inner_size: 50
hidden_act: relu
hidden_dropout_prob: 0.2
attn_dropout_prob: 0.2
layer_norm_eps: 1.0e-8
loss_type: CE
train_neg_sample_args: null
learner: adam
learning_rate: 0.001
weight_decay: 0.0
train_batch_size: 128
epochs: 200
eval_step: 1
stopping_step: 20
seed: 42
reproducibility: true
metrics: [Hit, NDCG]
topk: [10]
valid_metric: NDCG@10
eval_args:
  split: {LS: valid_and_test}
  order: TO
  group_by: user
  mode: uni100
```

標準evaluatorの負例規則が上記protocolに合わなければ、保存した101候補へ `predict` でスコア付けする最小の評価処理を使う。解決後の設定と実効値を全て保存する。
hidden_size=50は著者コードのdefaultを用いた初回固定案。論文の比較は10／20／30／40／50のvalidation探索を含むため、その探索結果の再現ではない。
200 epochは今回の上限。原論文の20 epoch改善なし停止に合わせて毎epoch validationを行うが、RecBoleの停止条件の境界も確認する。
著者コードのAdam beta2=0.98に対し、標準Trainerのdefaultを保持する場合は0.999という差をreportに残す。初期化も標準のinitializer_range=0.02を明示的に保存する。
RecBoleと著者実装では1 epochの更新回数が異なるため、epoch数だけで学習量を同等とせず、更新回数・学習例数・実時間を併記する。

学習seedは42の1本。validation NDCG@10最大のcheckpointを選び、同値なら早いepochを採る。
testは条件とcheckpointを固定した後に一度だけ評価する。学習中のtest確認やtestによる設定選択はしない。
上限でvalidationが改善中なら「未収束の可能性」を報告し、自動延長しない。

## 比較と判定

| 指標 | 定義・値域 | 役割 |
|---|---|---|
| NDCG@10 | 正解の1始まり順位rが10以下なら1/log2(r+1)、それ以外0。user平均、0〜1 | primary、checkpoint選択 |
| Hit@10 | 正解が上位10に含まれれば1、それ以外0。user平均、0〜1 | secondary |
| 学習loss／epoch／更新数／時間 | 学習と収束の記録 | diagnostic |

同じ候補でtrain interaction数によるPopRecを計算する。ランダム順位の期待Hit@10=10/101も参照する。
同点は候補順によらずitem IDで順位を固定し、同点率を記録する。
論文の全baselineの再学習は今回含めない。

添付PDFは **arXiv:1808.09781v1（2018-08-20）**。Table IIIのML-1M参考値：

| 手法 | Hit@10 | NDCG@10 |
|---|---:|---:|
| SASRec | 0.8245 | 0.5905 |
| PopRec | 0.4329 | 0.2377 |

**二つの判定を分離する。**

- protocol検証：系列・分割・候補・指標・checkpointの検査を全て通過したか。値が近くても漏洩や候補の不整合があれば無効。
- 性能診断：論文値との絶対差・相対差を報告する。仮の調査基準として両指標が参考値の±10%以内なら「この1条件では近い水準」とする。これは提案する便宜的基準であり、論文由来でも統計的同等性検定でもない。範囲外は差分調査の対象とし、実装不良と即断しない。大幅な上振れも確認対象。

単一seedでは学習変動の頑健性を示せない。既存1MのNDCG=0.095103との増減をモデル改善と解釈しない。
既存の同じML-1M上の別protocol結果は既に参照している。本計画は未実施protocolの内部計画であり、新しい独立データや外部事前登録ではない。
serendipity、人間の経験、M1全体の完了はこの実験の評価対象に含めない。

## 承認後の実行範囲と保存

1. 既存環境とデータの利用可能性を確認し、新フォルダ内にデータ・実効設定を保存する。既存環境へのpackage更新はしない。必要なら隔離環境を使う。
2. 最小runnerと一つの検証スクリプトを作成する。小さい手作り系列でsplit／target漏洩／101候補／指標の手計算一致を検証し、数batchのsmokeでloss・gradientが有限であることを確認する。
3. full-dataの1 epochで所要時間・メモリを計測し、そのcheckpointと乱数状態から同じrunを継続する。別の本学習を追加しない。
4. 上記1 seedを学習し、選択checkpointでtest評価、PopRec比較、report作成、検証記録を残す。

保存予定：

```text
sasrec-sanity-check/
  PLAN.md                     今回作成した承認用計画
  run.py / check.py            承認後に必要な最小実装
  config.yaml                 承認した実行設定
  data/                       出典・hashを付けた入力
  outputs/ml1m-ce-seed42-<日時>/
    実効設定、環境情報、split、候補、学習log、checkpoint、user別rank、集計
  REPORT.md                   結果、論文との差、検証日と未検証範囲
```

予定command：`python run.py --config config.yaml --output outputs/ml1m-ce-seed42-<日時>`。
現時点ではrunnerは未作成であり、このcommandは実行可能な完成手順ではない。承認後に実装したCLIで確定する。
既存v0、外部1Mのコード・checkpoint・出力は上書きも移動もしない。生成データとcheckpointは公開Gitに追加しない。

資源は既存ローカルCPU環境を第一候補とし、有料cloudは使わない。
系列長200のprefix学習は既存runより重くなり得る。所要時間は未計測で、現時点で完走時間を断定できない。
提案する上限は本runのwall-clock 12時間。見積もりが超過する場合はcheckpointを保持して継続条件を相談し、batch・系列長・datasetを黙って縮小しない。
件数不一致、split不整合、NaN/Inf、メモリ不足も停止条件とする。

完了は「実行完了」と「検証完了」を分ける。REPORTには実施日、対象run、実行した検査、根拠ファイル、未確認範囲を記載する。
ユーザーの追加指示により、既存ファイルは一切変更しない。承認範囲と理由はこの新フォルダのPLAN.mdに記録し、既存のresearch/decisions.md、research_state.md、ROADMAP.md、.gitignore等にも追記しない。既存環境を更新せず、変更・出力・必要な隔離環境は新フォルダ内に限定する。

## 参照と引き継ぎ

- 添付：`/Users/macuser/Desktop/SASRec.pdf`、III-E、IV-A/C/D、Table II/III（p.5〜7）。Table II/IIIは画像でも確認済み。
- [著者実装・配布データの入口](https://github.com/kang205/SASRec)
- [著者model.py：BCE・Adam](https://github.com/kang205/SASRec/blob/master/model.py)
- [著者util.py：split・候補生成](https://github.com/kang205/SASRec/blob/master/util.py)
- [著者main.py：default設定・評価頻度](https://github.com/kang205/SASRec/blob/master/main.py)
- [RecBole 1.2.1 SASRec](https://github.com/RUCAIBox/RecBole/blob/v1.2.1/recbole/model/sequential_recommender/sasrec.py)
- [RecBole標準設定](https://github.com/RUCAIBox/RecBole/blob/v1.2.1/recbole/properties/model/SASRec.yaml)
- [RecBole prefix展開](https://github.com/RUCAIBox/RecBole/blob/v1.2.1/recbole/data/dataset/sequential_dataset.py)
- 既存条件：`../research/local-context.md`から外部1Mのexperiment.py／config.jsonを確認。ローカルRecBoleのmodel設定とlayers.pyも照合した。

実装時の確定事項（2026-09-11）：配布データは6,040 users、3,416 items、999,611 interactionsで一致した。RecBole標準のdataset.buildとTrainDataLoader・SASRec.calculate_lossを使い、固定負例の評価とcheckpoint保存のため小さい学習loopを設けた。Adamは標準Trainerと同じdefaults。早期停止は承認計画の「20回連続改善なし・同点は早いepoch」を厳密に使う（標準utilityの同点更新・max_step超過停止とは異なる）。評価はfull_sort_predictの出力から101候補をgatherし、predictとの一致をtoyデータで確認した。

完了したこと：論文・公式コード・既存設定の差分調査、承認、データ照合、最小実装、手作り系列での分割／候補／指標検査、3 batchのloss・gradient検査。
残り：本データの全prefix検査、1 epochの資源見積もり、承認上限内での学習、評価、report。
次に読むもの：本PLAN、承認メッセージ、research/research_state.md、必要な公式コード。

## 2026-09-12 再開

第1 epochは2457.43秒（約41分）で完了し、200 epoch外挿136.52時間のため予定どおり停止した。
ユーザーの「再開」を受け、同じrunのlatest.ptからmodel・optimizer・乱数状態を復元して継続する。
総学習12時間の上限は維持する。次epochの見積もり（直近epoch時間の1.1倍）が残り予算に入らなければepoch境界で止め、validation最良checkpointをtest評価する。
早期停止に届かず時間上限で止まる場合は、収束確認未完と明記する。200 epochや追加seedへ無制限に延長する承認ではない。
再開処理はtoyデータで次の1更新が保存前の継続とbitwise一致することを検査する。
ユーザーの「学習状況わかるようにして」に対応し、STATUS.mdをPythonプロセスで自動更新する。LLMや外部同期は使わない。

## 2026-09-12 第6 epoch後の中断

ユーザーの指示により、第6 epochのvalidationとepoch境界checkpointが保存された直後に中断する。
理由は新しい高速なマシンへの移行であり、早期終了や収束とは扱わない。
中断時点ではtestを評価せず、同じrunを`latest.pt`から再開できる成果物とhashを新フォルダ内へ保存する。
再開の固定条件はHANDOFF.md、実測状態はrun内のhandoff.jsonを正本とする。
