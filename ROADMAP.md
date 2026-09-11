# 研究全体のMacroロードマップ

最終更新：2026-09-11

研究テーマを`M1`〜`M5`、各versionの実験を`v0-S1`のように区別する。
旧文書のStep 1〜5はM1〜M5に対応する。
旧Step 0は[v0のbaseline実験](v0/ROADMAP.md)としてM1の基盤に位置づける。
実験名の「Phase 1」は診断追加runの名称であり、MacroでもMicroでもない。

## 大枠の問いと現在地

| ID | Research Question | 状態と簡潔な結果 | 研究記録 |
|---|---|---|---|
| M1 | sequential backbone上で、proxy最適化はどんな推薦品質のトレードオフを作るか | 部分完了。最新1Mの本比較とPhase 1は実行完了。距離上昇とheld-out品質低下を観測。採用設計との照合は未完 | [1M保存記録](#external-1m)、[v0 Microと初期100Kの履歴](v0/ROADMAP.md)、[仮説RQ5](research/hypotheses.md) |
| M2 | offline metricは人間のF/R/Eと総合serendipityに対応するか | 未完。人間評価未取得 | [仮説RQ1](research/hypotheses.md) |
| M3 | LLMは人間のFortuitous / Refreshing / Enrichingを予測できるか | 未完。human-validated evaluatorなし | [仮説RQ2](research/hypotheses.md) |
| M4 | F/R/Eをどう集約すると人間の総合判断に適合するか | 未完。集約規則未採用 | [仮説RQ3](research/hypotheses.md) |
| M5 | 検証済みsurrogateによる推薦は人間のserendipityを改善するか | 未完。最適化への導入前 | [仮説RQ4](research/hypotheses.md) |

Macroとversionは別の分類である。
v0はM1のintegration baselineであり、v1の目的と所属テーマは未確定。
1Mの実行完了だけでM1全体の設計と検証が完了したとは扱わない。

## 依存関係

```text
M1：システム側の比較 ── 候補とproxyの定義 ──┐
                                           ↓
                                 M2：人間評価との対応
                                           │
                       ┌───────────────────┴─────────────────┐
                       ↓                                     ↓
             M3：LLMの人間評価検証                 M4：人間F/R/Eの集約比較
                       └──────── 検証済みLLM出力 ─────────────→ M4
                       │                                     │
                       └────────── 両方の条件成立 ─────────────┘
                                           ↓
                              M5：surrogateを用いた推薦評価
```

文献調査、human study設計、LLM入力設計は依存しない範囲で進められる。
M4は人間のF/R/Eと総合判断が揃えば進められ、LLM出力を使う比較だけがM3の検証に依存する。
M5はM3のhuman validationとM4の採用規則が揃うまで実装へ進まない。
主作業は一つに絞り、着手可能な設計と実行許可を混同しない。

## 直近の主作業

実施済み1Mの評価条件、事前の判断記録、結果をM1の完了条件と照合する。
RQ、positive、目的、primary outcome、代表解規則、許容する品質低下について、
「事前に決定」「事後の解釈」「未確認」を区別する。
その後にcanonical条件とversion配置をユーザーが判断する。
追加実験、v1作成、既存出力の移動はまだ承認された作業ではない。

### 現在の研究ハンドオフ（2026-09-11）

- **Macro Stage**：M1は部分完了。1M本比較とPhase 1診断は実行・保存済みだが、M1の評価設計との照合は未完。
- **Micro Stage**：v0-S1とv0-S2は旧100Kの保存結果として完了。v0-S3は100K smokeの接続確認までで、1M成果物のversion割り当ては未決定。
- **Current Milestone**：既存1M実験について、RQ、positive、目的、primary outcome、代表解規則、許容accuracy lossが事前決定・事後解釈・未確認のどれかを確定する。
- **Next Milestone**：照合結果を根拠に、canonical評価条件と1M成果物のversion配置をユーザーが判断する。
- **Critical Path**：既存記録の照合 → canonical条件とversion配置の判断 → 必要な場合だけ別設定・別出力先の実験計画を承認する。
- **Major Blocker**：1M条件とM1完了条件を結ぶ、日付付きの採否記録がまだ揃っていない。
- **Minor Blockers**：1MのK=15〜30、学習seed間の頑健性、外部リンクの公開アクセスは未確認。Notionのpositive説明と保存先コードのtest履歴範囲にも差がある。
- **Research Debt**：旧100K実験時点のコードsnapshotがなく、保存結果と完全な再現検証を同義にできない。

**Next Actions**：

1. 1Mの計画・設定・結果をM1の完了条件へ対応付ける → 未確認の事前決定と事後解釈を分離し、canonical条件の判断を可能にする。
2. canonical条件と1Mのversion配置を判断する → 正式なreport配置と、M1で追加実験が必要かの判定を可能にする。
3. 必要と判断した検証だけを計画化する → K・学習seed・比較条件のどれを追加測定するかを限定し、新規実験の承認へ進める。

<a id="m1"></a>

## M1：Sequential multi-objective system-side study

**目的**：指標を詰めないまま再実験せず、まずsystem-side studyとして何を測るかを決める。

**このMacroで決めること**：

- RQを「探索法の比較」「objectiveの妥当性」「sequential backbone上のtrade-off」のどこに置くか。
- positive definitionをrating 4以上、履歴平均超え、別の定義のどれにするか。
- serendipity proxyをpopularity novelty、genre distance、unexpectedness、FAS型scoreのどれで構成するか。
- primary outcomeとsecondary diagnosticsを分ける。
- SASRec、加重和、NSGA-IIの比較が同じcandidate poolと制約を使うこと。
- NSGA-IIを使う理由がitem-additive objectiveだけで成立するか。
- testを見る前に代表解規則と許容accuracy lossをvalidationで固定すること。

**最小成果物**：

- 1ページ程度の実験計画（内部の事前計画と外部の事前登録を区別する）。
- 指標ごとの定義、単位、値域、何のproxyか、何を表さないかの表。
- 比較手法とablation。
- 実行command、保存先、完了判定。
- 本実験結果と「課題、仮説、根拠、結果」の解釈。

**完了条件**：

- [ ] RQと主張範囲を一文で固定した。
- [ ] 未実施の確認実験ではproxy、positive、primary outcomeをtest結果を見る前に固定した。既存実験は当時の記録を照合し、未確認なら事後整理と明記した。
- [ ] weighted sumとNSGA-IIの必要性を判定できる比較を置いた。
- [ ] 現行RUNBOOKのworking proposalを採用または却下した理由を[判断ログ](research/decisions.md)へ記録した。
- [ ] 新しい出力先で本実験を完走し、v0を上書きしていない。
- [ ] M1の結論をsystem-sideに限定した。

<a id="m2"></a>

## M2：Algorithmic metricとhuman experienced serendipityのvalidity

**依存**：人間評価を集める前に、対象候補、proxy、対象者と提示条件を固定する。
M1全体の完了を待たず、文献調査とprotocol設計は進められる。

**目的**：conventional offline metricとhuman F/R/E、human global serendipityの一致度を測る。

**最小成果物**：human study protocol、annotation items、sampling plan、offline metricとの対応表、analysis plan。

**完了条件**：

- [ ] Fortuitous、Refreshing、Enrichingを人間が回答できるitemへoperationalizeした。
- [ ] global serendipityを構成要素と別に取得した。
- [ ] 同じ候補にoffline metricsとhuman ratingsを揃えた。
- [ ] Spearman / Kendall、誤差、分類またはcalibrationを出力型に合わせて評価した。
- [ ] measurement gapの有無を反証可能な形で結論づけた。

<a id="m3"></a>

## M3：LLM experienced-serendipity evaluator

**依存**：human validationにはM2のhuman labelsとprotocolが必要。
文献調査、入力schema、prototype設計は先行可能だが、検証済みとは扱わない。

**目的**：`f_LLM(H_u,i,c) -> (F,R,E)`がhuman appraisalをどこまで予測できるかを検証する。

**最小成果物**：入力schema、prompt、structured output、prototype、human validation report。

**完了条件**：

- [ ] model、prompt、temperature、history representation、item representationを記録した。
- [ ] F/R/Eを別々に予測した。
- [ ] human F/R/Eに対するSpearman、Kendall、MAEまたはAUCを評価した。
- [ ] probabilityを出す場合はBrier scoreとcalibrationを評価した。
- [ ] metadata-only評価をauditory experienceと表現していない。
- [ ] prototypeまたはvalidatedのどちらかを明記した。

<a id="m4"></a>

## M4：F/R/E aggregation

**依存**：M2のhuman global judgment。LLM outputを使う比較はM3完了後。

**目的**：mean、product、min、geometric mean、thresholdのどれがhuman global serendipityに適合するかを比較する。

**完了条件**：

- [ ] conjunctiveとcompensatoryの理論差を明記した。
- [ ] thresholdを含む候補規則を事前に固定した。
- [ ] held-out participantまたはnested validationで比較した。
- [ ] construct definitionへの適合とpredictive performanceを分けて報告した。
- [ ] 採用した`g(F,R,E)`と理由を[判断ログ](research/decisions.md)へ記録した。

<a id="m5"></a>

## M5：Predicted experienced serendipity optimization

**依存**：M3のevaluatorがhuman validationを通過し、M4のaggregationが固定されていること。

**目的**：validated surrogateを最適化したrerankingが、conventional proxy optimizationよりhuman-rated serendipityを高めるかを検証する。

**完了条件**：

- [ ] SASRec、conventional proxy reranker、experienced-surrogate rerankerを同条件で比較した。
- [ ] relevanceと`X`の重複を処理した。
- [ ] optimizerが加重和で足りるか、NSGA-IIが必要かをobjective structureから再判定した。
- [ ] human-rated F/R/Eとglobal serendipityを主要評価に含めた。
- [ ] satisfactionとaccuracy lossの許容範囲を事前に固定した。
- [ ] surrogateの改善だけでhuman outcomeの改善を主張していない。

<a id="external-1m"></a>

## 別保存のMovieLens 1M実験

別保存のMovieLens 1M実験は、次の二つのrunとして保持している。

- 本比較：`ml-1m-rd-k10-resumed2`
- 診断追加：`ml-1m-rd-k10-phase1`

実ファイルは公開リポジトリに同梱しない。
ローカル作業時の保存場所とタスク識別子は`research/local-context.md`に保持する。

両runの`completion.json`で`status=complete`、`smoke=false`を確認した。
診断追加runの`config.json`、`split.json`、`checkpoint.json`、`test/summary.csv`も照合した。
条件はMovieLens 1M、履歴平均超えpositive、目的`(mean r, mean d)`、K=10、候補100、relevance floor 0.95、40個体・50世代・search seeds 42/43/44である。
`s_proxy=r*d`は診断値であり、旧100Kの最適化目的とは異なる。
診断追加はselected epoch 1のcheckpointを再利用し、validation NDCG@10は0.075590、validation対象478人、test対象974人である。

| 手法 | Test NDCG@10 | mean genre distance | heldout distance |
|---|---:|---:|---:|
| SASRec | 0.095103 | 0.727851 | 0.060336 |
| Weighted Sum | 0.050995 | 0.930735 | 0.044923 |
| NSGA-II | 0.051279 | 0.930735 | 0.045123 |

この1M条件でも、ジャンル距離の上昇をheld-out qualityやexperienced serendipityの改善とは扱えない。
元タスクと1M版READMEには、診断追加前後の候補・推薦・既存指標の回帰検査PASSが記録されている。
2026-09-11のEnd-of-Day確認では、保存済みPhase 1成果物に対して既存`check.py`を再実行し、history-only centering、positive-definition checkpoint guard、time leakage、warm catalog、genre distance、目的値とfront、scalarization、repair、seed、held-out metricsを検査した。
さらに本比較からPhase 1へのcandidate score、全推薦ID・順序、既存全指標の回帰一致を確認した。
学習と実験は再実行しておらず、外部リンクの公開アクセス、K=15〜30、学習seed間の頑健性は未検証である。

「現行目的の本比較はすべて未実施」という研究全体の説明は更新が必要だったが、旧100Kの結果はそのまま保持する。
実験名の「Phase 1」は探索追跡の追加段階であり、Macro M1の完了を意味しない。
M1の事前仕様・採否記録との対応は未確認で、事後的に事前登録済みとは扱わない。
次の判断ではこの1M結果も読み、既存実験の評価設計を照合する。
コード・大容量成果物の移動や`v1`への昇格は、この文書更新では行っていない。

## 更新方法

大枠の問いと依存条件を変える場合は[判断ログ](research/decisions.md)へ追記する。
背景や採用前提の変更は[research_state.md](research/research_state.md)へ反映する。
個別runの詳細はversion内のreportに置き、このMacroには短い結論と参照だけを残す。
1Mの詳細はversion未確定のため暫定的に本節へ保持し、配置決定後に対応versionのreportへ移す。
