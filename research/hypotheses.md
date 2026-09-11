# 仮説とResearch Questions

最終更新：2026-09-10

仮説は採用済みの結論ではない。
各項目について、測定対象、比較条件、反証可能な結果を実験前に固定する。
RQ番号は仮説の識別子であり、ロードマップの順番ではない。
対応はMacro M1→RQ5、M2→RQ1、M3→RQ2、M4→RQ3、M5→RQ4である。

## RQ1：Offline metricのhuman validity

**問い**：conventional offline serendipity metricsは、human experienced serendipityとどの程度一致するか。

**H1**：novelty、unexpectedness、predicted relevance、genre / embedding distance、FAS型serendipityなどのoffline metricsは、human global serendipity judgmentおよびhuman F/R/Eと完全には一致しない。

**根拠**：offline metricsはsystem-side featuresを測る一方、experienced serendipityはunintentionalな遭遇とsubjective appraisalを必要とする。
特にglobal rarityとuser-relative novelty / unusualness、predicted preferenceとintrigue / impactは同じ変数ではない。

**評価候補**：構成要素別のSpearman / Kendall、global judgmentのAUCまたは回帰性能、calibration、metric間のdisagreement caseの質的分析。

**反証または修正条件**：複数データセットと利用者群でoffline metricsがhuman judgmentを高精度かつ良好にcalibrateして予測する場合、measurement gapを主たる新規性とする根拠は弱くなる。

**状態**：未検証。

## RQ2：LLMはどの構成要素を予測できるか

**問い**：LLMはhuman Fortuitous、Refreshing、Enrichingを同じ精度で予測するか。

**H2**：LLMによる再現精度はF/R/Eで異なる。
履歴とmetadataから推定しやすいRefreshingに比べ、意図性を含むFortuitousと、実際の感情や価値を含むEnrichingでは誤差が大きくなる可能性がある。

**評価候補**：各構成要素のSpearman、Kendall、MAE、binary化した場合のAUC、probability outputのBrier scoreとcalibration。
zero-shot、few-shot、persona-conditioned、history-conditionedの差も比較する。

**反証または修正条件**：構成要素間の性能差が信頼区間内で一貫して小さい場合、dimension-specific limitationの仮説は支持されない。

**状態**：未検証。

## RQ3：F/R/Eのaggregation

**問い**：どのaggregation ruleがhuman global serendipity judgmentに最も適合するか。

**H3**：product、min、thresholdなどのconjunctive aggregationは、compensatory meanよりhuman global serendipity judgmentに適合する可能性がある。

**根拠**：BinstらのconceptualizationではFortuitous、Refreshing、Enrichingがすべて必要である。
meanでは、一要素の欠如を他二要素の高さが補償できる。

**比較候補**：arithmetic mean、product、minimum、geometric mean、component-specific threshold、必要なら学習済みmodel。
学習済みmodelを使う場合も、held-out participantで検証し、単純規則との性能差を報告する。

**反証または修正条件**：meanがheld-out human judgmentを一貫して最もよく予測する場合、necessary-conditionという理論的定義と日常的なglobal ratingのoperationalizationが異なる可能性を検討する。

**状態**：未検証。

## RQ4：Experienced-serendipity optimization

**問い**：predicted experienced serendipityを最適化するrerankingは、conventional proxy optimizationよりhuman-rated serendipityを高めるか。

**H4**：human-validatedなpredicted experienced-serendipity surrogateを用いたrerankingは、novelty、relevance、context、taste distanceなどのconventional proxyを最適化するrerankingより、human-rated experienced serendipityを高める可能性がある。

**評価候補**：同一candidate poolとrelevance条件の下で、SASRec、conventional proxy reranker、predicted experienced-serendipity rerankerを比較する。
human F/R/E、human global serendipity、satisfaction、後続探索行動を主要または補助outcomeとして事前に区別する。

**反証または修正条件**：human-rated serendipityが改善しない、またはrelevance / satisfactionの損失が許容範囲を超える場合、surrogate optimizationの有効性は支持されない。

**前提**：H4の検証前にH2とH3のhuman validationを行う。
LLM evaluator prototypeだけを根拠にoptimizationへ進まない。

**状態**：未検証。

## RQ5：Sequential backbone上のsystem-side trade-off

**問い**：SASRec候補に対するmulti-objective rerankingは、relevanceとsystem-side taste distance / serendipity proxyのどのtrade-offを作るか。

**H5**：NSGA-IIは複数の非劣解を生成できるが、item-additiveな目的と現在の代表解規則では、単純加重和を上回る運用点を作らない可能性がある。

**既存結果**：旧設定ではNSGA-II代表解と加重和代表解が全件一致した。
proxyは上昇したがNDCGとheld-out高評価を伴う距離は低下した。

**追加の既存結果（2026-09-10確認）**：別作業フォルダでMovieLens 1M、履歴平均positive、`(relevance, genre_distance)`、K=10の本比較が完了している。
保存場所と指標は[Macroの1M記録](../ROADMAP.md#external-1m)を参照する。
1Mの保存済みtest集計でも、NSGA-IIはSASRecより平均genre distanceが高い一方、NDCGとheldout distanceは低い。
旧100Kとデータ・positive・目的が異なるため、設定変更単独の効果とは解釈しない。

**次の評価**：実施済み1M実験とMacro M1の評価設計を照合し、採用条件と未検証事項を整理する。

**状態**：旧100Kと別作業フォルダの1Mで部分的に検証済み。Macro M1の完了およびcanonical設定の採用は未確認。
