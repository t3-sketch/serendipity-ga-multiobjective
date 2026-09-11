# 主要文献と本研究との差分

最終更新：2026-09-09

この文書は、新規性を主張する前に確認する先行研究の索引である。
リンクは2026-09-09時点で確認できたarXiv、DOI、著者所属機関の公開ページを記載する。

## SASRec

Wang-Cheng Kang and Julian McAuley, “Self-Attentive Sequential Recommendation,” ICDM 2018.
[arXiv:1808.09781](https://arxiv.org/abs/1808.09781)

### 何を解いているか

SASRecは、ユーザーのinteraction sequenceから次のitemを予測するsequential recommenderである。
Self-attentionによって、履歴中のどのitemを次item予測に使うかを適応的に重みづけし、Markov Chainの局所性とRNNの長期依存表現のあいだを狙う。

### 本研究との差分

本研究ではSASRecをrelevance-oriented candidate generatorとして使う。
SASRec自体はFortuitous、Refreshing、Enrichingを目的にせず、人間がserendipityを経験したかも測らない。
したがって、SASRecは研究の新規性ではなく、system-side relevanceを作るbaseline backboneである。

## FAS-MOEA

Shresth Khaitan and Rahul Shrivastava, “Developing Fairness, Accuracy, and Serendipity Objective Functions for Recommendation System and Establishing Trade-off through Multi-Objective Evolutionary Optimization,” Information Processing & Management, 2026.
[DOI:10.1016/j.ipm.2025.104604](https://doi.org/10.1016/j.ipm.2025.104604)

### 何を解いているか

FAS-MOEAはAccuracy、Fairness、Serendipityを別々のobjectivesとして定義し、NSGA-IIでPareto trade-offを探索する。
Serendipity objectiveは、未接触itemかつpredicted relevanceがthreshold以上であることをgateとし、inverse-popularity型のnoveltyとuser / temporal context multiplierを掛ける形で整理できる。

### 本研究との差分

FAS-MOEAが最適化するserendipityは、観測可能なsystem-side variablesから作ったafforded serendipityのproxyである。
Fortuitous、Refreshing、Enrichingというhuman experienceを直接測ってはいない。

ローカルv0はFAS-MOEAの完全再現ではない。
RecBole SASRecの候補をpymoo NSGA-IIでrerankする派生的な接続検証であり、現行目的はrelevanceとgenre distanceの二目的、公平性は除外している。

## What Is Serendipity?

Brett Binst, Lien Michiels, and Annelien Smets, “What Is Serendipity? An Interview Study to Conceptualize Experienced Serendipity in Recommender Systems,” UMAP 2025.
[arXiv:2505.15440](https://arxiv.org/abs/2505.15440) / [DOI:10.1145/3699682.3728325](https://doi.org/10.1145/3699682.3728325)

### 何を解いているか

17人へのsemi-structured interviewとgrounded theory analysisから、experienced serendipityを「意図せず出会った内容がFortuitous、Refreshing、Enrichingだと感じられる経験」として概念化する。
三つのmain componentsはすべて必要で、各componentは複数のconditionによって満たされるfamily-resemblance型の構造を持つ。

Fortuitousにはunintentional、difficult-to-find、unexpected、uncoveringが含まれる。
Refreshingにはnovel、unusual、taste reincarnationが含まれる。
Enrichingにはintriguing、inspiring、impact、relevance、resonanceなどが含まれる。
NovelとUnusualを分け、global popularityや初見であることだけではtasteからの距離を表せないと整理できる。

### 本研究との差分

この論文はconstructを定義するが、個々の推薦候補についてF/R/Eを自動推定する計算モデルや、それを推薦objectiveとして最適化する方法は提供しない。
本研究は、このconstructをhuman ratingでoperationalizeし、LLMがそのappraisalをどこまで予測できるかを検証する。

## Let Me Introduce You

Brett Binst, Ulysse Maes, Martijn C. Willemsen, and Annelien Smets, “Let Me Introduce You: Stimulating Taste-Broadening Serendipity Through Song Introductions,” UMAP 2026.
[arXiv:2604.08385](https://arxiv.org/abs/2604.08385)

### 何を解いているか

普段のtasteから外れた曲がinterestをsparkするTaste-Broadening Serendipityを、song introductionによって刺激できるかをuser studyで調べる。
operationalizationでは、普段と異なること、interestをsparkすること、surprise、unexpected、difficult-to-discover、new perspective、noticed detailsの少なくとも一つを満たすことを要求する。

SEMはintroductionからTBSへ至る心理的な仕組みを扱う。
Transportationは曲や物語世界への没入、Cognitive Elaborationはアーティストや社会的文脈について学び考える過程、Perceived Complexityは曲を深く複雑だと捉えるappraisalである。
TransportationはTBSへの強いpredictorとして働き、Cognitive Elaborationは比較的小さい直接効果と間接経路を持つ。
Perceived ComplexityはTBSを説明し、Transportationとのinteractionにも関与する。

### 本研究との差分

同論文は音楽でexperienced TBSを測り、紹介文による介入と心理機序を検証する。
本研究が目指すのは、履歴、候補曲、contextからTBSまたはF/R/Eをofflineで予測し、その予測のhuman validityを測ること、その後に推薦最適化へ戻すことである。
metadataだけを入力したLLMは実際の聴覚経験を再現しないため、同論文のuser studyを置き換えたとは主張できない。

## DMORec

Wei Zhou et al., “Dynamic Multi-Objective Optimization Framework With Interactive Evolution for Sequential Recommendation,” IEEE Transactions on Emerging Topics in Computational Intelligence, 2023.
[DOI:10.1109/TETCI.2023.3251352](https://doi.org/10.1109/TETCI.2023.3251352)

### 何を解いているか

DMORecは、sequential recommendationでrelevanceだけでなくdiversity、tail novelty、recencyなどの変化する複数目的を扱うdynamic multi-objective recommendation frameworkである。
sequential interactionから利用者のobjective-level preferenceを捉え、二つを超える目的のPareto-optimal solutionsを得るためにsupervised learningを組み合わせたevolutionary approachを用いる。

### 本研究との差分

DMORecによって「sequential recommendationにmulti-objective evolutionary optimizationを入れること」自体は既出である。
したがって、SASRecとNSGA-IIを接続しただけでは強いnovelty claimにならない。
本研究との差分候補は、最適化対象をsystem-side objectivesからhuman experienced-serendipity surrogateへ移し、そのmeasurement validityを先に検証する点にある。

## Sparks of Surprise

Jie Wang, Alexandros Karatzoglou, Ioannis Arapakis, Xin Xin, Xuri Ge, and Joemon M. Jose, “Sparks of Surprise: Multi-Objective Recommendations with Hierarchical Decision Transformers for Diversity, Novelty, and Serendipity,” CIKM 2024.
[DOI:10.1145/3627673.3679533](https://doi.org/10.1145/3627673.3679533) / [University of Glasgow repository](https://eprints.gla.ac.uk/330233/)

### 何を解いているか

Personalized Session-based Recommendationをmulti-objective化し、過去sessionと現在sessionをHierarchical Decision Transformerで扱う。
accuracyに加えてdiversity、novelty、serendipityをreturnsとして調整し、SASRecを含む複数のsequential backbonesへ適用している。

### 本研究との差分

この論文により、SASRecを含むsequential backboneとserendipityの組み合わせはすでに扱われている。
そのserendipityはunexpectednessとrelevanceなどから計算するsystem-side objectiveであり、Fortuitous、Refreshing、Enrichingというhuman appraisalの予測妥当性までは扱わない。
本研究のfrontierは、同種のobjectiveが高くなることと、人間のexperienced serendipityが高くなることのgapに置く。

## MODT4R

Jie Wang, Alexandros Karatzoglou, Ioannis Arapakis, Joemon M. Jose, and Xuri Ge, “Beyond Accuracy: Decision Transformers for Reward-Driven Multi-Objective Recommendations,” IEEE Transactions on Knowledge and Data Engineering, 2025.
[DOI:10.1109/TKDE.2025.3582506](https://doi.org/10.1109/TKDE.2025.3582506) / [University of Glasgow repository](https://eprints.gla.ac.uk/357379/)

### 何を解いているか

MODT4RはMulti-objective Sequential Recommendationをoffline RLではなくreturn-conditioned sequence modelingとして扱う。
user trajectoryにaccuracy、diversity、noveltyなどの複数returnsを条件として与え、inference時に目的間の重みを調整できるDecision Transformer frameworkである。

### 本研究との差分

MODT4Rによって、sequential recommendationとmulti-objective optimizationの統合はend-to-endな学習枠組みでも既出である。
一方、returnsは計算可能なsystem-side rewardであり、human experienced serendipityの構成要素を測定、校正する研究ではない。
本研究はoptimizerの新規性よりも、optimizerへ渡す目的変数のconstruct validityとhuman validityを研究対象にする。

## 先行研究を並べたときのfrontier

```text
SASRec
    sequential relevance prediction

DMORec / Sparks of Surprise / MODT4R
    sequential + multi-objective optimization は既出

FAS-MOEA
    Accuracy / Fairness / system-side Serendipity のPareto optimization

What Is Serendipity? / Let Me Introduce You
    experienced constructと音楽での心理的生成過程

本研究
    system-side objectiveとhuman experienced serendipityのmeasurement gap
    → validated computational surrogate
    → surrogateを用いたoptimization
```

「SASRec + serendipity」または「sequential + multi-objective」だけを新規性として主張しない。
