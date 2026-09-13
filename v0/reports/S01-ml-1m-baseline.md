# v0-S1：MovieLens 1M canonical baseline

正式採用日：2026-09-11。関連：[Micro](../ROADMAP.md)、[Macro M1](../../ROADMAP.md#m1)、[採用判断](../../research/decisions.md#canonical-1m)。
本報告は実施済み実験の事後整理であり、事前計画や事前登録ではない。

## 問いと結論

同じSASRec候補に対し、関連度とgenre distanceを最適化すると推薦品質はどう変わるか。
MovieLens 1Mでは、Weighted SumとNSGA-IIのmean genre distanceはSASRecより高い一方、NDCG@10は低かった。
NSGA-IIとWeighted SumのNDCG差は小さく、保存済みの95% bootstrap区間は0を跨ぐ。
この比較からNSGA-IIの推薦品質上の優位性は確認できない。

## 実験条件

| 項目 | 正式baselineの条件 |
|---|---|
| Dataset | MovieLens 1M |
| Positive | rating > 推薦時点までの本人の履歴平均rating |
| 履歴 | validationはtrain、testはtrain＋validation。未来のratingを平均に含めない |
| Split | 全体時刻による80/10/10分割。同一timestampを跨がせない |
| 候補生成 | RecBole SASRec。train vocabulary内の未視聴Top-100 |
| 推薦長 | K=10 |
| 最適化目的 | mean relevance r、mean genre distance d |
| 診断のみ | s_proxy = r×d。最適化と代表解選択には使わない |
| 比較手法 | SASRec、Weighted Sum(r,d)、NSGA-II(r,d) |
| Relevance floor | SASRec Top-10のmean rの0.95倍 |
| Weighted Sum | w×r + (1−w)×d、w=0〜1を0.1刻みで掃引 |
| NSGA-II | 40個体、50世代、search seeds 42/43/44 |
| 学習seed | 42の1つ。学習seed間の頑健性は未検証 |
| モデル選択 | validation NDCG@10、selected epoch 1、0.075590 |
| 評価対象 | validation 478人、test 974人 |

`r`は全未視聴かつ学習済みカタログ内のSASRecスコア順位値であり、確率や予測ratingではない。
`d`はpositive履歴のgenre profileと候補のgenre vectorの0.5×L1距離（値域0〜1）である。
代表解はfloorを満たす中でmean d最大、同点ならmean r最大、最後にitem ID列の辞書順で選ぶ。
Weighted SumとNSGA-IIに同じ規則を使い、推薦の表示順はSASRec順に揃える。
順位値の95%維持はNDCGの95%維持を保証しない。

## Test結果

3 search seedsをユーザー内で平均してからユーザー間で集計する。
NDCGは区間内の既知かつ未視聴のpositiveを対象とする@10であり、通常の次の1件を予測する評価とは条件が異なる。
候補外の正例も評価の分母に残す。

| 手法 | NDCG@10 | mean genre distance | heldout distance |
|---|---:|---:|---:|
| SASRec | 0.095103 | 0.727851 | 0.060336 |
| Weighted Sum | 0.050995 | 0.930735 | 0.044923 |
| NSGA-II | 0.051279 | 0.930735 | 0.045123 |

`heldout distance = sum(hit_i × d_i) / 10`は、held-out positiveを伴う距離の代理評価である。
未観測を不評とは解釈しない。
Candidate Recall@100は0.192242であり、再ランキングは候補外のpositiveを取り戻せない。

NSGA-II − Weighted SumのNDCG@10差は0.000284、対応付きbootstrap 2,000回の95%区間は[−0.000067, 0.000919]である。
探索seedを独立ユーザーとして扱った区間ではない。
丸めた距離平均が同じことから、個々の推薦も全件同じとは推論しない。

## 本比較とPhase 1診断

| Run ID | 役割 | 保存状態 |
|---|---|---|
| ml-1m-rd-k10-resumed2 | 1M本比較 | complete、smoke=false |
| ml-1m-rd-k10-phase1 | 同条件の探索追跡を追加。上記checkpointを再利用 | complete、smoke=false |

Phase 1は診断追加runの名称であり、Macro M1の完了や別versionを意味しない。
上表の結果は両runの保存集計と一致する。
当時の1M版READMEには、診断追加前後の候補、推薦IDと順序、既存指標の回帰検査PASSが記録されている。
その全件回帰検査は今回再実行していない。

## 研究上の解釈

- **課題**：関連度と嗜好からの距離を考慮した再ランキングのtrade-offを明らかにする。
- **仮説**：NSGA-IIの2目的探索が、SASRecと単純加重和より有用な推薦集合を得る可能性がある。
- **根拠**：同じ候補、評価対象、代表解規則で加重和と比較し、探索法の追加効果を評価する。
- **結果**：距離は上昇したが、NDCGとheldout distanceはSASRecを下回った。加重和に対するNDCGの優位性も確認できない。

これはsystem-sideの探索的integration baselineである。
proxy向上をhuman experienced serendipity改善とは表現しない。
FAS-MOEAの完全再現、公平性objective、音楽での効果、人間のFortuitous / Refreshing / Enrichingは検証していない。
NSGA-IIが別の目的関数や制約でも不要だとは結論しない。

## 証拠と検証範囲

2026-09-11に、ユーザー指定の既知結果と両runの保存済み`test/summary.csv`を照合した。
両runの`config.json`と`completion.json`、診断runの`split.json`、`checkpoint.json`、`test/paired_bootstrap.csv`も確認した。

2026-09-13（Phase 2）：公開入口を`v0/reproduce/`にした。公開集計抜粋とS01報告値を`verify_saved.py`で再照合した。
H1 A0は保存checkpoint再利用で下流7指標が差0.0、A1はscratch 7 epochの`training.csv`が差0.0だった。
公開`experiment.py`はresumed2記録hashともH1 harnessともバイト一致しない。一致したのは指標である。
フル再学習と本実験の再実行は未実施。データ、checkpoint、個別ユーザー出力は同梱しない。
手順は[RUNBOOK](../RUNBOOK.md)。H1とsanityの範囲は[S02](S02-h1-candidate-generators.md)、[S03](S03-sasrec-sanity-check.md)。

## 未検証事項

- 当時の事前仕様と判断記録の対応。primary outcome、代表解規則、許容accuracy lossをいつ固定したかの照合。
- 公開snapshotとresumed2当時の`experiment.py`をバイト一致させた復元。H1は指標再現であり、同一ファイルの復元ではない。
- 1MでのK=10〜30の頑健性。旧100Kのリスト長比較を1Mの証拠として流用しない。
- M2の人間評価、M3のLLM human validation、M4の集約規則。検証前のLLMはprototypeである。

canonical採用は報告対象とversion配置の決定であり、M1全体の検証完了ではない。
