# 既存文書への反映案（未反映）

作成日：2026-09-12。
ユーザーの指示により、この作業では`v0-H1/`の外にある文書を一切変更していない。
以下は反映が承認された場合の差分案である。案であること自体を記録として残す。

反映するかどうか、どの文書に置くかはユーザーの判断とする。
反映する場合は、ユーザーの決定、AIの提案、実測、未確認を分けて記述する。

## 1. `research/decisions.md`への追記案

```markdown
## 2026-09-12：候補生成器を比較してから固定する（v0-H1）

**課題**：v0はSASRec候補への再ランキングbaselineであり、候補生成器自体を比較していない。
v0のCandidate Recall@100は0.192で、再ランキングは候補外のpositiveを取り戻せない。
KGで距離を精緻化する前に、どの候補生成器を固定するかを決める必要がある。

**判断（ユーザー採用）**：v0を締め、ComiRec/eSASRecと候補生成を比較し、
採用した候補生成器を固定してからKGの追加価値を比較する。
作業は`v0-H1/`内で完結させ、既存のコード・出力・文書は変更しない。
採用基準はvalidation Candidate Recall@100とし、testを見る前に固定した。

**仮説・根拠**：分割、positive定義、候補数、再ランキング条件を固定し、
モデルclassだけを替えれば、候補生成の違いに帰属できる比較になる。

**結果**：3 armを同条件で実行した。候補の天井（Candidate Recall@100）と精度に、
対応付きbootstrapで測定できる差は出なかった（全armの95%区間が0を含む）。
validationの点推定ではeSASRecが最上位（0.204790 対 SASRec 0.195638）だが、testでは符号が反転する。
ComiRec-SAは候補の被覆をむしろ狭めた（0.665 対 SASRec 0.720）。
NSGA-IIの加重和に対する利得の不在は3 backboneで再現した。
3 backboneすべてでvalidation NDCG@10はepoch 1が最良となった。

**未完**：学習seedは1つで、arm間差がseed変動を超えるかは未検証。
arm別のhyperparameter tuningは行っていない。
LiGR層とsampled softmaxの切り分け（SASRec+SS ablation）も未実施。
```

## 2. `v0/ROADMAP.md`の完了条件に関する案

v0-H1のA0（checkpoint再利用run）は、再構築した環境と改造後のコードで、
v0の`ml-1m-rd-k10-resumed2`の`validation/summary.csv`と`test/summary.csv`を
7指標すべてで差0.000e+00で再現した。

したがって次の更新が提案できる。

- 「当時のコードと環境を復元した再現確認を行う（未実施）」について、
  **再ランキングと評価の段は再現を確認した**と記録できる。
  ただし確認したのは保存済みcheckpointを入力とした下流であり、**学習の再現は別の証拠**である。
  学習側の再現はv0-H1のA1（scratch再学習）の`training.csv`との比較で判定する。
- 再現に使った環境（python 3.10.20、recbole 1.2.1、torch 2.5.1、numpy 1.26.4）と
  実施日を記録する。

**未確認のまま残るもの**：当時の事前仕様と判断記録の照合。
v0-S1が事後整理であるという既存の記述は変更する必要がない。

## 3. `ROADMAP.md`（Macro）への案

M1の「直近の主作業」に、候補生成器の比較（v0-H1）が加わったことを短く記す。
ただしM1の完了条件（RQの固定、weighted sumとNSGA-IIの必要性判定、system-sideへの限定）は
v0-H1では満たされない。候補生成の選択はM1の前提整備であり、M1の完了ではない。

## 4. `research/research_state.md`への案

「2026-09-12に採用した研究の区切り」の節に、KG比較の前段として
候補生成器の選択を置いた経緯を追記できる。
v0はcanonical baselineとして保持し、v0-H1はその上流を替えた比較であると位置づける。

## 5. 反映してはいけないこと

- 候補生成器のRecall@100やNDCGの改善を、experienced serendipityの改善と書かない。
- v0-H1の結果でv0のcanonical baselineを置き換えない。v0の正本は`v0/reports/S01-ml-1m-baseline.md`のままとする。
- publishedのleave-one-out数値（ComiRecやeSASRecの原論文の値）と本実験の数値を並べて比較しない。
  評価protocolが異なる。
