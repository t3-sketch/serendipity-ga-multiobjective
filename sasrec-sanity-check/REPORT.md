# SASRec Sanity Check：実行記録

実施日：2026-09-11。対象：`outputs/ml1m-ce-seed42-20260911`。
状態（2026-09-12更新）：第1 epochを完了後、時間見積もり条件で一旦停止。ユーザーの「再開」により同じcheckpointから継続中。最新の実行状態は自動更新される[STATUS.md](STATUS.md)を参照。test未評価、性能の結論は未確定。

## 課題・仮説・根拠・結果

- 課題：既存実験の独自protocolでは、SASRec単体を原論文値と比較できない。
- 仮説：論文に近いML-1Mの分割・評価条件で、RecBole標準SASRecが近い性能水準に達する。
- 根拠：著者の前処理済みデータとユーザー別leave-one-outを使い、rerankingを取り除いて診断する。
- 結果：第1 epochのvalidation NDCG@10=0.581697、Hit@10=0.810762。これはvalidationの途中結果であり、論文のtest性能との一致を判定する値ではない。

## 確認済みのデータ・protocol

著者リポジトリcommit `e3738967fddab206d6eeb4fda433e7a7034dd8b1` の `data/ml-1m.txt` を使用。
SHA-256：`b725f3acb3986fe3130bffd1e77a74d182a1f51799567a236dbd60270f95b0a2`。

| 項目 | 実測 |
|---|---:|
| users | 6,040 |
| items（paddingを除く） | 3,416 |
| interaction | 999,611 |
| 重複user-item | 0 |
| 最小user interaction | 18 |
| 最小item interaction | 5 |
| 学習prefix | 981,491 |
| validation／test users | 各6,040 |
| 除外user／held-out専用item | ともに0 |
| batch／epoch | 7,668 |

ユーザー・アイテム数は添付論文Table IIと一致した。正確なinteraction数は配布ファイルからの実測であり、論文表の丸めた1.0Mから復元した値ではない。
RecBoleが作った全981,491学習prefixのtarget位置・履歴内容・paddingを元系列と照合した。
validationはtrain履歴、testはtrain＋validation履歴で、各userの最後の1件だけをtargetにしている。
候補は全観測itemを除く一様非復元抽出100件＋target。split別seedは1042／1043で固定・保存した。

## 実装と検証

RecBole 1.2.1、PyTorch 2.5.1、NumPy 1.26.4、pandas 2.2.3、Python 3.10.20。
既存v0の環境を読み取り利用し、packageの変更はしていない。Python bytecodeの書き込みも無効化した。
CPU 4 threads、inter-op 1 thread。変更と生成ファイルは新フォルダ内に限定した。

SASRec・prefix展開・train dataloaderはRecBole標準を使用する。
固定候補の評価と状態保存のため、train loopは新フォルダ内の `run.py` に置いた。
Adamはlr=0.001、betas=(0.9, 0.999)、eps=1e-8、weight_decay=0。
モデルの詳細は `config.yaml` とrun内の `recbole_config.txt` に保存。

`check.py` を実行し、次を確認した（`outputs/checks.json`）。

- 手作り系列でRecBoleのtrain／validation／test分割が期待どおりになる。
- 候補に既観測item・重複が混入せず、seed固定で再生成できる。
- 正解順位1・10・11のHit／NDCGが手計算と一致する。同点時はitem IDで順位を固定する。
- 3 batchのsmokeでloss・gradientが有限で、embeddingに勾配が流れる。
- `predict` と `full_sort_predict` からtarget scoreを取り出す処理が一致する。

本データについても全prefix・全候補を検査した（run内の `data_checks.json`）。
学習終了後のcheckpoint再読込・test出力再集計は未実施。

## 論文との既知の相違

添付版arXiv:1808.09781v1のML-1M参考値はHit@10=0.8245、NDCG@10=0.5905。
今回のCEは原論文の各位置BCEと異なる。prefix学習、padding、正規化位置、初期化、Adam beta2も完全一致しない。
著者の公開評価コードとは、負例除外範囲・重複禁止・候補固定が異なる。
50次元・seed42の1条件だけで、論文の次元探索や複数seed評価は行わない。
早期停止は承認計画に合わせ、validation NDCGの厳密な改善が20 epoch連続でなければ停止、同点なら早いepochを選ぶ。
既存1Mの独自評価値と比べた増減をモデル改善とは扱わない。

## 実行手順と未完事項

新フォルダをworking directoryにして実行：

```sh
PYTHONDONTWRITEBYTECODE=1 ../v0/.venv/bin/python -B check.py
PYTHONDONTWRITEBYTECODE=1 ../v0/.venv/bin/python -B run.py --config config.yaml --output outputs/ml1m-ce-seed42-20260911
```

同名outputへの再実行は拒否する。上の実行先は既に使用済みであり、新しいrunを無断で作って再学習しない。
進捗はrun内の `progress.json` と `status.json`、console logに記録する。
第1 epoch後、200 epochの外挿見積もりが12時間を超えれば、承認計画に従いepoch境界のmodel・optimizer・乱数状態を保存して停止する。
2026-09-12にresumeを追加し、同じrunへ `--resume` を付けて再開した。toyデータでmodel・Adam状態・乱数を復元した次の更新がbitwise一致することを確認した（`outputs/checks.json`）。
総学習12時間の範囲で継続し、epoch境界で次epochが残り時間に入らなければvalidation最良checkpointをtest評価する。時間上限による停止は収束確認未完とする。

第1 epoch実測：2457.43秒、7668 updates、平均loss=6.249753、ピークRSS=1,825,357,824 bytes。200 epochの外挿は136.52時間。
未完：承認時間内の学習、選択checkpointでのtest評価、PopRec比較、最終検証。

## 2026-09-12 中断指示

第6 epoch実行中、ユーザーが「このepochが終わったら中断し、新しいマシンで早く実行する」と決定した。
第6 epochのvalidation・checkpoint保存後に停止し、testは評価しない。
これは計算環境移行のための中断であり、収束または研究上の停止規則による終了ではない。
別マシンへの手順と必要成果物はHANDOFF.md、停止後の確定値はrun内のhandoff.jsonに記録する。
