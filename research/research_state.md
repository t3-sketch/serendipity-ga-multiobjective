# 研究背景と採用前提

最終更新：2026-09-11

2026-09-10に相談チャットと既存の対談記録を照合した。
相談元の識別子はローカル専用の`local-context.md`に保持する。
2026-09-10の文書再編で、進捗を[Macro](../ROADMAP.md)と[Micro](../v0/ROADMAP.md)へ分離した。
この文書は背景、概念、現在採用している研究上の前提を保持する。

## 最初に確認する現在の実験参照先（2026-09-11訂正）

ユーザーは旧100K実験の後、MovieLens 1Mで本実験をやり直し、同条件のPhase 1診断も完了している。
今後「今回の結果」「最新の結果」やREADMEの考察を扱うときは、**1Mの本比較とPhase 1診断を先に参照する**。
100Kだけを現在の到達点として説明しない。
経緯は「旧100Kの接続実験 → 1Mの現行(r,d)本比較 → 同条件のPhase 1追跡」である。
直前のREADME文章案は100K中心で、この進展を十分反映していなかったため、未適用の旧案として扱う。
その後、同日のユーザー承認に基づき、100Kから1MとPhase 1までを扱う研究記事としてREADMEを改稿した。

- 本比較：`ml-1m-rd-k10-resumed2`。診断：`ml-1m-rd-k10-phase1`。保存場所はローカル専用の`local-context.md`を参照する。
- 条件：MovieLens 1M、履歴平均超えpositive、目的は平均`r`と平均`d`。`r×d`は診断値のみ。K=10、候補100、floor 0.95、40個体、50世代、探索seed 42/43/44。
- selected epoch 1、validation NDCG@10=0.075590。評価対象はvalidation 478人、test 974人。
- Test Candidate Recall@100=0.192242（ユーザーごとのRecallの平均）。旧100Kの0.355381を1M結果として使わない。
- Test NDCG@10はSASRec 0.095103、Weighted Sum 0.050995、NSGA-II 0.051279。距離上昇とheld-out品質低下を観測した。
- NSGA-IIとWeighted Sumの推薦ID・順序は2,880/2,922 user×seedで完全一致（98.56%）。旧100Kの「全件一致」を1Mへ引き継がない。
- NSGA-II−Weighted SumのNDCG差は+0.000284、95% bootstrap区間は[-0.000067, +0.000919]。優位性は確認できず、同等性が証明されたとも扱わない。
- Phase 1の採用解はweighted_sum由来2,874、sasrec由来6、探索中初出42。generation 0由来の98.56%と加重和との推薦一致率は、数値が同じでも別の診断である。

公開用の確認記録：[Macroの1M記録](../ROADMAP.md#external-1m)。ローカル成果物の位置は非公開の`local-context.md`に保持する。
2026-09-11に保存済みconfig、completion、split、checkpoint、test集計とbootstrapを照合し、推薦CSVから一致件数、由来CSVから採用解の内訳を再集計した。
同日のEnd-of-Day確認では既存`check.py`も再実行し、Phase 1成果物の内部整合性と、本比較からPhase 1へのcandidate score、全推薦ID・順序、既存全指標の回帰一致を確認した。
学習と実験は再実行しておらず、K=15〜30、学習seed間の頑健性、外部リンクの公開アクセスは未検証である。
Notionにはpositiveを「train履歴平均超え」とする記述があるが、1M保存先コードのtest入力はtrain＋validation履歴である。
実装に即して「推薦時点までの履歴平均超え（validationはtrain、testはtrain＋validation）」と記憶し、Notion本文は未訂正とする。

これは説明時の参照優先順位の訂正であり、canonical評価設計の採用、M1の完了、1Mのversion割り当てを意味しない。
旧100KのK=10〜30比較と、今回確認した1MのK=10比較は別の証拠である。
このメモリ訂正時点ではREADME本文の改稿は行わず、その後の承認を受けて文書のみ更新した。
成果物の移動、新規実験、Notionへの書き込みは行っていない。

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
ルートREADMEは研究日記の入口と日付付きの短い考察、versionのREADMEは動機から結果までを辿る研究記事とする。
日記の未確定な考えと採用判断を分け、記録の運用は[research README](README.md)に従う。
2026-09-11のv0記事は別保存の1MとPhase 1も経緯として扱うが、成果物のversion割り当ては変更しない。
現在の関心はTaste-Broadening Serendipityの定義と測定にあり、今後のSASRecやNSGA-IIの採用は固定しない。
この関心の記録を、新規実験やMacro完了判定の承認とは扱わない。
AIへの規則はAGENTS、実行手順はRUNBOOKとする。
空のversionは作らず、目的と評価設計を決めてから追加する。
このフォルダと同名のChatGPT Projectや、別のCodex作業フォルダを自動同期済みとは扱わない。

## 最新1M実験と初期baselineの範囲

現在参照する本比較はMovieLens 1Mで、SASRec候補生成と加重和／NSGA-IIを接続した探索的なintegration baselineである。
初期の100Kコードと結果はv0フォルダに保持し、1Mのコードと成果物は別保存に保持する。

```text
MovieLens 1M（最新本比較。初期接続実験は100K）
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

この実装と既存出力を **baseline v0** として論理的にfreezeする。
全面改修や既存出力の上書きは行わず、後続手法は別設定と別出力先で比較可能にする。

### 保存結果と現行コード

旧100Kの本実験はrating 4以上をpositiveとし、平均`r`と平均`r×d`を最適化した。
実測と限界は[v0-S1](../v0/reports/S01-main.md)と[v0-S2](../v0/reports/S02-list-length.md)に保持する。
人間向けの当時の記録は[Notionの2026-09-08報告](https://app.notion.com/p/3d580c3dba23812e8675d003042b15f1?pvs=204)にある。
既存runには移設前のパスがあり、旧コードのGit snapshotもないため、保存と再現検証を同義にしない。

現行100Kコードは履歴平均超えpositiveと目的`(r,d)`へ変更済みである。
その状態と未完事項は[v0-S3](../v0/reports/S03-definition-smoke.md)に置く。
旧結果を置き換えるcanonical baselineとしては未採用であり、M1で採否を決める。

最新の本比較とPhase 1診断は、別フォルダの1M実験で完了している。
保存先と確認した条件は[Macroの1M記録](../ROADMAP.md#external-1m)を参照する。
1Mはv1と同義ではなく、配置とversion割り当ては未確定である。
データ、positive、目的が同時に異なる旧100Kとの比較から、一つの変更の因果効果を主張しない。

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
proxy改善とheld-out悪化、加重和とNSGA-IIの一致を隠さず、何を実証していないかまで説明する。

研究ではv0を捨てず、後続のLLM evaluatorとexperienced-serendipity optimizationを比較するbaselineとして残す。
v0の限界が、そのままmeasurement gapを研究する動機になる。
