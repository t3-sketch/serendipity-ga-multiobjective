# v0-H1：他のagentへの引き継ぎ

最終更新：2026-09-12。作業場所は`/Users/macuser/dev/sasrec-serendipity/v0-H1`のみ。
この作業では`v0-H1/`の外にあるファイルを一切変更していない。
既存文書へ反映すべき内容は[REFLECTION.md](REFLECTION.md)に案として置いてあり、反映は未実施である。

## 結論の要約（詳細は[REPORT.md](REPORT.md)）

候補生成器をSASRecからComiRec-SA / eSASRecへ替えても、
候補の天井と精度に測定できる差はなかった（対応付きbootstrapの95%区間がすべて0を含む）。
事前規則はvalidationの点推定でeSASRecを選ぶが、testでは差の符号が反転する。
3 backboneすべてでvalidation NDCG@10はepoch 1が最良で以後低下し、
NSGA-IIは加重和に対する測定可能な利得を持たなかった。
harnessと学習はv0を差0.0で再現した。

## 何をした作業か

v0（MovieLens 1M canonical baseline）の候補生成器を替えたときに、
候補集合の品質と再ランキング後のトレードオフがどう変わるかを比較した。
比較対象はSASRec（v0のbackbone）、ComiRec-SA、eSASRecである。
評価条件、分割、positive定義、再ランキングはv0と同一に固定し、モデルclassだけを替えた。

事前に固定した判断規則、指標の定義、限界は[PLAN.md](PLAN.md)にある。
結果と解釈は[REPORT.md](REPORT.md)にある。
このファイルは「何を実行し、どこで何を判断したか」を残す。

## 最初に読む順番

1. [PLAN.md](PLAN.md)：RQ、固定した条件、事前に決めた採用規則。
2. [REPORT.md](REPORT.md)：実測値と結論、限界。
3. このファイル：実行の経緯、判断、落とし穴。
4. [REFLECTION.md](REFLECTION.md)：既存文書への反映案（未反映）。

## 環境（再現に必要）

v0の`environment.json`に記録されたversionへ合わせてある。ここを崩すと再現できない。

```sh
cd v0-H1
uv python install 3.10.20
uv venv --python 3.10.20 .venv
uv pip install --no-cache --python .venv/bin/python \
  torch==2.5.1 numpy==1.26.4 pandas==2.2.3 scipy==1.15.3 scikit-learn==1.7.2 \
  pymoo==0.6.1.5 matplotlib==3.9.4 tqdm==4.70.0 colorlog==4.7.2 colorama==0.4.6 \
  pyyaml==6.0.3 tensorboard==2.21.0 thop==0.1.1-2209072238 tabulate==0.10.0 \
  texttable==1.7.0 psutil==7.2.2 plotly==7.0.0
uv pip install --no-cache --no-deps --python .venv/bin/python recbole==1.2.1
```

`ray`はrecboleの宣言依存だが、使うのは`quick_start`だけなので`--no-deps`で外した。
`reuse_model()`が一致を要求するのはrecbole、torch、numpyの3つである。
データは外部保存の1Mを`data/ml-1m`へsymlinkしている。コピーも移動もしていない。

## 実行したコマンド

```sh
.venv/bin/python -B check_models.py                                              # 実装の契約検査
.venv/bin/python -B experiment.py --config config-sasrec.json  --output outputs/A0-sasrec-reuse \
    --reuse-model-from <v0の ml-1m-rd-k10-resumed2>                              # gate
.venv/bin/python -B experiment.py --config config-sasrec.json  --output outputs/A1-sasrec-scratch
.venv/bin/python -B experiment.py --config config-comirec.json --output outputs/A2-comirec-sa
.venv/bin/python -B experiment.py --config config-esasrec.json --output outputs/A3-esasrec
.venv/bin/python -B analyze.py                                                   # 採用判断とtest集計
```

ログは`logs/`、runの出力は`outputs/<run-id>/`にある。
`outputs/`と`data/`と`.venv/`はrepo直下の`.gitignore`で除外される。

## 判断したこと

### 既存実装の変更を4箇所に限定した

`experiment.py`は外部保存の1M実装のコピーである（コピー元のSHA-256は
`f9d4d17d90227f6296e83e248cd53328ffc06ae52655f9b2b5c88614e02a1e12`）。
変更したのは次だけで、`score_cases`、`make_cases`、再ランキング、指標、bootstrapは触っていない。

1. `model_registry()`と`build_model()`を追加した。backbone hyperparameterはRecBoleの
   `SASRec.yaml`がv0に与えた値をそのまま定数`BACKBONE_PARAMS`に書き、armごとに上書きする。
2. `prepare_recbole()`が`Config(model=<class>)`にモデルclassとそのparameterを渡す。
3. `fit_model()`と`reuse_model()`が`build_model()`を使う。`reuse_model()`は
   checkpointのモデル種別が一致しないと拒否する。
4. `main()`に`--model`を追加し、`config.json`へ記録する。

`score_cases`が使うのは`full_sort_predict`だけなので、この差し替えで再ランキング以降は無改造で動く。
relevance `r`は生スコアではなく全未視聴itemに対する順位パーセンタイルなので、モデル間で比較できる。

### A0をgateにした

先にv0のcheckpointを再利用したrunを流し、v0の保存集計と一致することを確認してから
新しいモデルの学習に時間を使った。
結果は`validation`と`test`の7指標すべてで差0.000e+00だった。
これは再ランキングと評価の段の再現確認である。
学習の再現はA1で別に判定し、7 epochすべてがv0の`training.csv`と一致した。

### 差にbootstrap区間を付けた

各armのsummaryを点推定で並べるだけでは採用判断ができないため、
`analyze.py`に同一ユーザーでの対応付きbootstrap（2,000回、seed 42）を足した。
armは同じ分割の同じユーザーを評価しているので、per-userの差を取れる。
結果、全armの全指標で区間が0を含んだ。

事前規則には不確実性の条件を入れていなかった。
そのため規則の出力（eSASRec）と証拠の状態（差は未検出）が食い違う。
結果を見てから規則を変えていないので、両方をそのまま[REPORT.md](REPORT.md)に記録した。
次に同種の比較を設計するときは、採用規則に区間の条件を含めるべきである。

### 損失関数の扱い

- ComiRec-SAは原論文のsampled softmaxではなく、v0と同じ全catalog softmaxで学習した。
  catalogが3,662 itemと小さく、A1との差を「architectureだけ」に限定したかったためである。
- eSASRecは定義どおりsampled softmax（uniform負例256、logQ補正なし、mixed negativesなし）にした。
  そのためA3はLiGR層とlossの2変更を含み、単独では原因を切り分けられない。
  切り分けにはSASRec+SSのablationが必要で、今回は入れていない（ユーザーの判断）。

### ComiRecのaggregation moduleを切った

ComiRecはλで多様性を制御するgreedy aggregationを持つが、これは部分集合選択であり、
本実験が固定している再ランキング段と役割が重複する。
そのためscoreは`max_k v_k . e_i`だけを使い、多様化はNSGA-IIと加重和に任せた。

### 出力の手法名について

`summary.csv`の`sasrec`という行名は「その候補生成器自身のtop-K」を意味する。
列名を変えると既存の集計・作図コードに波及するため、名前は変更していない。

## 落とし穴

- **長時間runがシェル終了で死ぬ**。`nohup ... &`では落ちた。`setsid`はmacOSに無い。
  Cursorのシェルツールでバックグラウンドへ移行させる形にすると生き残る。
- **sandbox内でtorchのimportがSIGSEGVする**。python実行は必ずsandbox外で行う必要がある。
- **RecBoleは`loss_type`から入力形式を推論する**。CEとBPRしか知らないため、
  sampled softmaxを使うmodelには`input_type = InputType.POINTWISE`をclass属性で明示する。
  さらにRecBoleのSASRecのコンストラクタはCE/BPR以外を拒否するので、
  eSASRecは親の初期化中だけ`loss_type`をCEに置いてから戻している。
- **ディスクが満杯だった**。実行前に空きを2 GB以上確保する必要がある。
  1 runの出力は約90 MB、venvは約725 MBである。
- **メモリは8 GB**。学習runの同時実行は2本までにした。3本目でswapが増える見込みだった。

## 次にやること

1. KG比較で固定する候補生成器を決める。規則の出力はeSASRecだが優位性は未検出であり、
   v0との連続性を採るならSASRecでもよい。この判断はユーザーに委ねてある。
2. この評価protocolでは、どのbackboneでもepoch 1が最良になる。
   backboneの良さを測りたいなら、protocol側（区間内positive）を検討する必要がある。
   同じデータのnext-item評価では同じSASRecがvalidation NDCG@10 = 0.62に達する
   （`../sasrec-sanity-check/`の別作業）。
3. LiGR層とsampled softmaxを切り分けるSASRec+SSのablation。
4. 学習seedを増やし、arm間差がseed変動を超えるかの確認。
5. 反映が承認されたら[REFLECTION.md](REFLECTION.md)の案を既存文書へ入れる。

候補生成の指標が上がっても、それはexperienced serendipityの改善ではない。
この区別はM2以降の人間評価まで保持する。
