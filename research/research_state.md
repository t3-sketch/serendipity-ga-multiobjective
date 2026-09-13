# 研究背景と採用前提

最終更新：2026-09-13

## 2026-09-12に採用した研究の区切り

就活までにKGの比較研究をまとめ、Graph-Recを成果のデモにする。
その限界を出発点に、LLM評価器と人間のserendipityのずれを検証する後続研究を計画する。
この大枠はユーザーが採用し、Notionへの二つの計画草案の作成を依頼した。
映画での固定候補比較、flat属性対照、音楽への別ドメイン移行などの具体案は、まだ実験条件として採用していない。
対象領域、期限、Graph-Rec仕様、データ源は未確定。新versionや新規実験は未着手である。
既存M1の未完了事項は残り、人間評価前のLLMをprototypeとして扱う原則も変わらない。
2026-09-13のPhase 3 version 0.1はオフラインの`integration_test` / `synthetic`接続検証である。空の評定・予測ファイルは未取得であり、0点ではない。mock推薦のexportを実推薦成果やexperienced serendipityの改善と読まない。
2026-09-13のPhase 4はEngineeringデモである。40曲FMA、genre Jaccard、export 0.2（`purpose=engineering_demo`、`data_kind=real_catalog`）まで確認した。これは研究標本でも、推薦品質やexperienced serendipityの実証でもない。空の`human_ratings` / `llm_predictions`は未取得のままである。

2026-09-10に相談チャットと既存の対談記録を照合した。
相談元の識別子はローカル専用の`local-context.md`に保持する。
2026-09-10の文書再編で、進捗を[Macro](../ROADMAP.md)と[Micro](../v0/ROADMAP.md)へ分離した。
この文書は背景、概念、現在採用している研究上の前提を保持する。

## 研究のnarrative

この研究は、推薦システムが計算できる代理指標から、人間が実際に報告するserendipityへ評価対象を移す。
全体の流れは次のとおりである。

```text
system-side / afforded serendipity
    ↓ 妥当性の検証
experienced serendipity
    ↓ 人間評価を予測するmeasurement model
computational surrogate
    ↓ 検証後に推薦目的へ導入
optimization
```

従来のoffline serendipityは、novelty、unexpectedness、predicted relevance、contextなど、観測可能な特徴から構成されることが多い。
これらはserendipityを起こしやすくする条件を表せても、人間がFortuitous、Refreshing、Enrichingを伴う経験をしたことまでは保証しない。

したがって、研究の主たる新規性候補は「SASRecにserendipityを追加すること」ではない。
sequential multi-objective recommenderが最適化するsystem-side proxyと、human experienced serendipityのあいだにあるmeasurement gapを測り、そのgapを近似するcomputational surrogateを検証することに置く。

## 文書と研究対象の区別

背景はこの文書、進捗は[Macro](../ROADMAP.md)、version内の実験は[Micro](../v0/ROADMAP.md)、採用判断の経緯は[decisions.md](decisions.md)に置く。
人間向けの入口はREADME、AIへの規則はAGENTS、実行手順はRUNBOOKとする。
空のversionは作らず、目的と評価設計を決めてから追加する。
このフォルダと同名のChatGPT Projectや、別のCodex作業フォルダを自動同期済みとは扱わない。

## Baseline v0の範囲

v0は、MovieLens 1Mを用いてSASRecとNSGA-IIを接続した探索的なintegration baselineである。

```text
MovieLens 1M
    ↓ 全体時刻によるtrain / validation / test分割
RecBole SASRec
    ↓ 未視聴アイテムのうち上位100候補
weighted-sum または pymoo NSGA-II reranking
    ↓ K件
offline evaluation
```

SASRecの学習にNSGA-IIを組み込んだend-to-end方式ではない。
学習済みSASRecを固定し、その後段で推薦集合を選ぶ。
FAS-MOEAに着想を得た接続検証だが、FAS-MOEAの完全再現ではなく、公平性objectiveもv0には含めていない。
serendipity constructと指標の妥当性も詰めていない。
したがって、v0の研究上の成果範囲は次に限定する。

- SASRecの候補生成とNSGA-IIのsubset selectionを接続できること。
- 同じ候補集合でSASRec、加重和、NSGA-IIを比較できること。
- 採用した暫定proxyを最適化したときのoffline結果と計算費用を記録すること。
- 暫定proxyの改善がheld-out qualityやexperienced serendipityの改善を意味しないと示すこと。

2026-09-11にユーザーがこの1Mの実施条件と結果を **canonical baseline v0** として採用した。
全面改修や既存出力の上書きは行わず、後続手法は別設定と別出力先で比較可能にする。

### 保存結果と現行コード

正式結果は[MovieLens 1M baseline報告](../v0/reports/S01-ml-1m-baseline.md)に集約する。
positiveは推薦時点までの履歴平均超え（testはtrain＋validation）、目的はmean rとmean d、K=10、候補100とする。
r×dは診断専用である。
本比較とPhase 1診断は実行完了し、保存集計を照合した。
2026-09-13に公開入口を`v0/reproduce/`へ移し、公開集計抜粋とS01報告値を再照合した。
H1 A0/A1により下流7指標と7 epochの`training.csv`は差0.0で再現した。
公開snapshotと当時の`experiment.py`のバイト一致、事前仕様との照合、フル再学習は未検証である。
canonical採用をM1の完了とは扱わない。

100Kの結果文書は現行mainから削除し、Git historyに保持する。
`v0/experiment.py`は100K用の歴史的snapshotであり、現行入口ではない。
データ、positive、目的が異なる100Kとの比較から、一つの変更の因果効果を主張しない。
1Mの元コードと生出力は別保存のまま移動していない。
再現上の制約は[RUNBOOK](../v0/RUNBOOK.md)、今回の採用理由は[判断ログ](decisions.md#canonical-1m)を参照する。

## 概念の対応関係

FAS-MOEA原論文のPareto objectivesは、Accuracy、Fairness、Serendipityである。
Serendipity objectiveは概念的に次の形で整理できる。

```math
s_{u,i,t}
=
\mathbf{1}[i \notin H_u \land \hat r_{u,i} \ge \lambda]
\,N(i)\,c(u,t)
```

ここで、未接触かつrelevance thresholdを満たすことがgateとなり、noveltyとcontext multiplierが掛かる。
これはsystem-sideのoperationalizationであり、人間の経験を直接測る尺度ではない。

『What Is Serendipity?』は、experienced serendipityを次の三構成要素で捉える。

```math
Experienced\ Serendipity
=
Fortuitous \land Refreshing \land Enriching
```

三要素はすべて必要であり、各要素は複数の条件によって満たされる。

- **Fortuitous**：unintentionalを前提とし、difficult-to-find、unexpected、uncoveringなどを含む。
- **Refreshing**：novel、unusual、taste reincarnationなどを含む。
- **Enriching**：intriguing、inspiring、impact、relevance、resonanceなどを含み、負の経験ではないことを要する。

NovelとUnusualは同義ではない。
新しく知った人気曲が普段の好みに近い場合はnovelでもunusualではない。
マイナー曲でも既知ならnovelではなく、利用者のtasteから外れるかどうかも別に判定する必要がある。

FAS-MOEAとBinstらの枠組みは、次のように部分対応する。

| FAS-MOEA側 | Experienced Serendipity側 | 解釈 |
|---|---|---|
| Novelty | Refreshingの一部 | global rarityは、user-relativeなnovelやunusualの限定的proxyである。 |
| Relevance gate | Enrichingの一部 | predicted preferenceはEnriching内のrelevanceしか近似せず、intrigueやimpactを保証しない。 |
| Context multiplier | 上流条件 | 構成要素ではなく、各appraisalが成立する確率を変える条件として扱う。 |
| 未見条件と低人気度 | Fortuitousの一部 | difficult-to-findやunexpectedを弱く近似できるが、unintentionalやlatent interestのuncoveringはほぼ表現しない。 |

『Let Me Introduce You』が扱うTaste-Broadening Serendipity（TBS）は、普段と異なる音楽が興味を引く経験に焦点を当てる。
実運用上は、次の条件を満たすbinary compositeとして扱われる。

1. 普段聴く音楽と異なる。
2. interestをsparkする。
3. surprise、unexpected、difficult-to-discover、new perspective、noticed detailsの少なくとも一つを満たす。

そのため、TBSの中心はunusualとintriguing / interestingの両立である。
genre distanceだけでもpredicted relevanceだけでも十分ではない。

同論文のSEMでは、song introductionからTBSに至る心理過程を扱う。
Transportationは物語や曲世界への没入を表し、TBSへの最も強いpredictorとして位置づけられる。
Cognitive Elaborationはアーティストや社会的文脈について学び、考える過程であり、直接効果は比較的小さい一方、informative introductionから刺激しやすい。
Perceived Complexityは曲を深く複雑だと捉えるappraisalで、TBSへの経路に入り、Transportationとのinteractionも持つ。
これらはTBSの定義要素そのものではなく、unusualな曲がintriguingになる仕組みを説明する変数である。

## LLM evaluatorの設計原則

LLMに一度だけ「serendipityを1から10で採点せよ」と求める設計を主方式にしない。
measurement modelとconstruct ruleを分離する。

```math
f_{LLM}(H_u, i, c)
\rightarrow
(\hat F_{uic}, \hat R_{uic}, \hat E_{uic})
```

```math
\hat X_{uic}
=
g(\hat F_{uic}, \hat R_{uic}, \hat E_{uic})
```

`f_LLM`はhuman appraisalを予測するmeasurement modelであり、`g`はserendipity constructのoperational ruleである。
この分離により、どの構成要素で誤差が大きいか、aggregation ruleだけを変更した場合に何が変わるかを追跡できる。

コードが応答を返す状態は **prototype evaluator** と呼ぶ。
人間との一致度、確率校正、別サンプルでの再現性を確認した後だけ **validated evaluator** と呼ぶ。

候補となる`g`は次のとおりである。

```math
g_{mean} = (F+R+E)/3
```

```math
g_{product} = FRE
```

```math
g_{min} = \min(F,R,E)
```

```math
g_{geo} = (FRE)^{1/3}
```

```math
g_{threshold} = \mathbf{1}[F\ge\tau_F \land R\ge\tau_R \land E\ge\tau_E]
```

meanは一要素の低さを他要素の高さが補償できるため、三要素をnecessaryとする理論には弱い。
product、min、geometric mean、thresholdはconjunctiveな性質を異なる強さで表す。
どれを採るかは理論だけで固定せず、human global judgmentへの適合も比較する。

## Human validation

同じ`(H_u, i, c)`に対して、人間とLLMのF/R/Eを取得する。
評価指標は出力の型に合わせる。

- ordinalまたはcontinuous rating：Spearman、Kendall、MAE。
- binary classification：AUC。必要ならF1も補助的に用いる。
- probability prediction：Brier score、calibration curve、calibration error。
- global serendipity：aggregationごとの人間総合判断への適合と、構成要素別の誤差を分けて報告する。

相関だけでvalidation済みとはしない。
順位の一致、絶対誤差、識別、calibrationを分け、LLM model、prompt、history representation、item representationの変更に対する頑健性も記録する。

## 音楽へ移る際の入力設計

LLMにartist、genre、descriptionなどのmetadataだけを渡す場合、評価対象はauditory experienceではなくtext surrogateである。
この限界を明示し、behavioral taste profileとaudio representationを別のsourceから作る。

```text
Spotify / Apple Music / SoundCloud OAuth
    ↓ playlists, likes, library, top items, recent history
behavioral taste profile

licensed audio / preview / MIR dataset
    ↓ CLAPなどのmusic embedding
audio-content profile
```

Spotify、Apple Music、SoundCloudは将来のuser behavior source候補である。
取得可能範囲、OAuth scope、研究利用条件は実装時点の公式仕様で再確認する。
初回連携ではplaylist、likes、library、top items、recent historyからcold-start profileを作り、利用開始後は自前のinteraction logを蓄積する方向を想定する。

音響側はCLAPなどの外部MIR representationを候補とする。
候補曲embeddingと履歴曲embeddingの距離はRefreshing / unusualnessの一proxyになり得るが、距離そのものをexperienced serendipityと同一視しない。

## 研究の依存条件

大枠の問いと依存関係は[Macro](../ROADMAP.md)を正本とする。
文献調査と設計は依存しない範囲で進められるが、人間評価前のLLMをvalidated surrogateとして推薦の最適化へ使わない。
各versionの実行許可と完了条件はそのMicroと承認済みplanで確認する。

## Portfolioと研究での扱い

就活Portfolioでは、v0だけでも「問題設定、実装、比較実験、失敗を含む結果解釈」が揃っており公開価値がある。
proxy改善とheld-out悪化、加重和に対するNSGA-IIのNDCG優位性が未確認であることを隠さず、何を実証していないかまで説明する。

研究ではv0を捨てず、後続のLLM evaluatorとexperienced-serendipity optimizationを比較するbaselineとして残す。
v0の限界が、そのままmeasurement gapを研究する動機になる。
