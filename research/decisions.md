# 研究判断ログ

判断が変わった場合、過去の記録を消さず、新しい項目として追記する。
過去のStep名、文書名、順序は当時の記録である。
現在の採用判断は[2026-09-12の1M canonical化](#canonical-1m)と[Macro](../ROADMAP.md)を参照する。
過去の「100Kを保持」「canonical未採用」「version未確定」と削除済み文書名は、現在の運用指示ではない。
100K結果の記録は[移行前のGit履歴](https://github.com/t3-sketch/serendipity-ga-multiobjective/tree/067d4641aa4ccb7ffae353db9ae31b026d7e837d/v0)で参照できる。

## 2026-09-09：共有研究文書とversion固有成果物を分離する

**課題**：研究全体の判断とv0固有のコード、データ、結果が同じ階層にあり、LLMが何を先に読むか不明確だった。

**判断**：ルートの`AGENTS.md`と`research/`を共有入口にし、v0固有の一式を`v0/`へまとめる。
LLMは共有文書を読んだ後、対象versionの`RESEARCH.md`と`README.md`へ進む。

**根拠**：研究programの現在地と、再現対象となる各versionの条件を分けることで、v0を保持したまま後継研究を追加できる。

**結果**：v0の実装、仮想環境、データ、結果、旧文書を`v0/`へ移動した。
`v1/`は未作成であり、Step 1の目的と評価設計を固定した時点で作る。

## 2026-09-09：v0の主張範囲をintegration baselineへ限定する

**課題**：v0の実装にはSASRecとNSGA-IIの接続、暫定proxy、offline結果が混在しており、FAS-MOEAの再現やserendipity指標の妥当性まで検証したように読める危険がある。

**判断**：v0は「SASRec候補生成とNSGA-II subset selectionを接続し、同じ候補上で加重和と比較した探索的研究」としてまとめる。
指標は暫定であり、experienced serendipityを測ったとは扱わない。

**根拠**：Notionの実験記録では、最適化した`s_proxy`は上昇した一方、NDCG、Recall、高評価を伴うジャンル距離は低下し、NSGA-II代表解は加重和と一致した。
これは接続とobjective behaviorの検証にはなるが、serendipity construct validityの証拠にはならない。

**結果**：v0専用の要約を`v0/RESEARCH.md`へ作成し、研究全体を`research/steps.md`で段階管理する。
実験結果の人間向け正本は[Notionの2026-09-08ページ](https://app.notion.com/p/3d580c3dba23812e8675d003042b15f1?pvs=204)とする。

## 2026-09-09：v0を捨てずbaselineとしてfreezeする

**課題**：DMORec、Sparks of Surprise、MODT4Rを踏まえると、現在のSASRecとNSGA-IIの接続だけでは新規性が弱い。

**判断**：現在の実装、条件、保存済み出力をbaseline v0として残す。
全面的に作り直さず、後続研究が比較できる基準にする。

**根拠**：v0にはcandidate generation、reranking、Pareto analysis、held-out evaluationまでの動く経路がある。
proxyの改善とheld-out性能の悪化が同時に起きた結果は、system-side metricの妥当性を問う具体的な出発点になる。

**結果**：本判断を`AGENTS.md`と`research/research_state.md`へ固定した。
このフォルダにはGit metadataがないため、現時点のfreezeは文書上の運用規則であり、Git tagによる固定ではない。

## 2026-09-09：まずv0実験を取る

**課題**：LLM evaluatorを先に完成させないとbaselineを評価できないように見えていた。

**判断**：LLMを使わず、Step 1でproxyと評価条件を固定したalgorithmic baselineを先に実行する。

**根拠**：先にsystem-side metricsを固定すると、後からLLMまたは人間で再評価した際にsystem-side improvementとexperienced-side improvementを分離できる。

**結果**：v0の探索的実験はNotion、`v0/RESULTS.md`、`v0/LENGTH_RESULTS.md`に保存済み。
履歴平均positive定義と`(relevance, genre_distance)`を使う案は未計測であり、Step 1の設計判断を経るまでcanonicalとは呼ばない。

## 2026-09-09：LLM evaluatorはbaselineの前提ではない

**課題**：LLM evaluatorを「baselineを回すための評価器」と捉えると、prototypeの未検証出力がbaselineの成立条件になる。

**判断**：baselineはconventional offline metricsで独立して取得する。
LLM evaluatorは、baseline出力を別の測定モデルで再評価する後続研究として扱う。

**根拠**：LLM score自体のhuman validityが未確認であり、baselineとevaluator validationを同時に依存させると、どちらの誤差か分離できない。

**結果**：実行順を「baseline、文献、prototype、baseline再評価、human validation、optimization」とした。

## 2026-09-09：LLM scoreをoptimizationへ使う前にhuman validationを行う

**課題**：LLMがF/R/Eらしい数値を返しても、その数値が人間のappraisalと一致する保証はない。

**判断**：prototype evaluatorとvalidated evaluatorを区別する。
human F/R/Eとの比較、識別性能、誤差、calibrationを確認する前にLLM scoreを推薦objectiveへ採用しない。

**根拠**：未検証のLLM objectiveを最適化すると、LLM固有のbiasやprompt artifactを増幅する可能性がある。

**結果**：validation指標の候補をSpearman、Kendall、MAE、AUC、Brier score、calibrationとした。
具体的なannotation protocolとsample sizeは未決定。

## 2026-09-09：measurement modelとconstruct ruleを分離する

**課題**：LLMにglobal serendipity scoreを一発で出させると、constructのどこで誤ったかを特定できない。

**判断**：`f_LLM(H_u,i,c) -> (F,R,E)`と`g(F,R,E) -> X`を分離する。

**根拠**：構成要素別のvalidationと、mean、product、min、geometric mean、thresholdのaggregation比較を独立して行える。

**結果**：設計原則を`research_state.md`、仮説を`hypotheses.md`に記録した。
最終aggregationは未決定。

## 2026-09-09：主たる新規性候補をmeasurement gapへ移す

**課題**：Sparks of SurpriseはSASRecを含むsequential backboneとserendipityを扱い、DMORecとMODT4Rもsequential multi-objective recommendationを扱っている。

**判断**：研究の主たる新規性候補を、system-side proxyからexperienced-serendipity surrogateへのmeasurement gapへ移す。

**根拠**：既存研究の多くは計算可能なobjectivesの最適化を扱う一方、BinstらはserendipityをFortuitous、Refreshing、Enrichingからなるsubjective experienceとして定義する。
両者の対応は部分的であり、human validityが未解決である。

**結果**：研究を五つのStepに分割した。
Step 2のgapが確認できず、既存metricがhuman judgmentを十分予測する場合は、このnovelty claimを修正する。

## 2026-09-09：音楽ではbehavior sourceとaudio representation sourceを分ける

**課題**：streaming APIのmetadataや利用履歴だけでは、候補曲を聴いた際のauditory experienceを表せない。

**判断**：Spotify、Apple Music、SoundCloudなどから得るplaylist、likes、library、top / recent itemsをbehavioral profileに使い、CLAPなどのMIR representationをaudio-content profileに使う方向を採る。

**根拠**：利用者の行動と音響的なtaste distanceは異なる情報源であり、一つのAPIですべてを代替すると測定対象が曖昧になる。

**結果**：将来設計として採用。
OAuth scope、データ保持、各serviceの利用条件、audio取得権限は実装時に公式仕様を再確認する。

## 2026-09-10：相談チャットと開発フォルダの引き継ぎを既存文書へ統合する

**課題**：ChatGPT「研究の現在地整理」、ChatGPT Project「Serendipity」、開発フォルダ、別Codexタスクの1M成果物が別々に存在し、引き継ぎ状況と実験の現在地が分かりにくかった。

**判断**：既存の`AGENTS.md`と`research/`を引き継ぎ入口として再利用する。
ユーザーが望む「通常チャットで相談し、Codexで実装する」運用に合わせ、相談元の識別子と更新方法を追記した。
古い対談は経緯として保持し、現在の進行判断では`steps.md`を確認する。

**根拠**：元チャットの研究narrative、v0保持、F/R/EとLLM surrogateの区別は既存文書にすでに記録されていた。
一方、対談に残る「すぐ実験する」という順序は、後に文書化されたStep 1の設計gateと一致していなかった。
Project名やサイドバーの配置だけでは、ローカル文書と会話履歴の同期を保証しない。

**結果**：相談元リンク、文書の優先関係、開発フォルダの場所を追記した。
ルートと`v0/`にGit metadataがないことを確認した。
ローカルProject登録は利用可能なアプリ操作では実行できず、ユーザーによるフォルダ選択が残っている。

## 2026-09-10：別作業フォルダの1M完了結果を現在地へ反映する

**課題**：「履歴平均positiveと(r,d)の本比較は未実施」という記述が、研究全体の状況としては古くなっていた。

**判断**：100K版の未実施条件と、別作業フォルダの完了済み1M実験を区別する。
既存の100K結果を置き換えず、`research_state.md`へ1M版README・出力先・確認した主要指標を記録する。

**根拠**：タスク「MovieLens 1M実験を実行」のユーザー依頼、保存済みREADME、本比較と診断追加runの`completion.json`、診断追加runの設定・分割・checkpoint・test集計を照合した。
両runは非smokeの完了状態であり、1M・履歴平均positive・(r,d)・K=10という旧100Kとは異なる実験条件だった。

**結果**：実験の完了事実を現在地・Step状況・RQ5へ反映した。
事前仕様と採否記録の対応は未確認のため、研究Step 1の完了とは扱わない。
TODO：既存1M実験とStep 1の完了条件を照合する。
実験の「Phase 1」と研究の「Step 1」を区別し、過去結果を事後的な事前登録として扱わない。

## 2026-09-10：MacroとMicro、計画と報告を分離する

**課題**：研究全体と個別実験が同じStep番号で呼ばれ、READMEには紹介、実行説明、AIへの指示が混在していた。

**仮説**：Macroをルート、Microをversion内に置き、紹介、規則、計画、報告を分ければ、問いと証拠を辿りやすくなる。

**判断**：ユーザーの「この案でいこう。実装を開始」という承認に基づき、文書再編を実施した。
ルートROADMAPはM1〜M5、v0 ROADMAPはv0-S1〜S3を管理する。
旧Step 0はv0 baselineとしてM1の基盤に位置づけた。
READMEを人間向けにし、旧v0 READMEの実行説明はRUNBOOKへ、旧RESULTSとLENGTH_RESULTSはreportsへ移した。
旧RESEARCHの詳しい解釈はreports/baseline-overview.mdに保持した。
旧パスは案内のみを残し、進捗や結果の正本を二重管理しない。
research_stateは背景と採用前提、decisionsは判断履歴、discussionsは長い経緯とする。
新規実験の計画は各versionのplansに記し、既存実験を事前登録済みとは扱わない。

**根拠**：参照した研究workflowの短い指示、計画と理由の記録、証拠付きの検証を取り入れる。
全面的な直列進行は依存関係に置き換え、文献調査と設計は独立に進められるようにした。
M5には引き続きM3のhuman validationとM4の採用規則を必要とする。
人間が研究の採否を判断し、エージェントの作業完了を研究上の妥当性と混同しない。

**結果**：Macro、Micro、Portfolio向けREADME、RUNBOOK、plansの記入項目、3件のStep報告を整備した。
旧100Kの数値と実験条件を保持し、現行100Kコードとの違いを明記した。
別保存の1M記録はMacroへ移し、実ファイルの保存先は変更していない。
1Mのversion割り当てとcanonical条件の採否は未確定のままとした。
追加実験、学習、v1作成、Notion更新、Git初期化は実施していない。
運用による読み取り量やtoken削減の効果は未計測である。

**文書移行の検証（2026-09-10）**：ローカル参照127件に欠落はなく、Markdownのコード囲みも整合した。
S01、S02、baseline概要、Macroの1M表の数値137セルを保存CSVと照合し、一致した。
リスト長比較の推薦一致件数、完了マーカー、smoke区分、現行100Kの対象人数も確認した。
変更前後で、v0のコードと保存出力など324ファイル（Markdown、データ配布フォルダ、仮想環境、cacheを除く）のSHA256が一致した。
学習、実験、当時のcheckとNotebookの再実行による検証ではない。

**未完**：M1の1M実験と当時の判断記録の照合、canonical条件とversion配置の判断。
この文書整理の承認は、これらの採用判断や新規実験の実行許可には拡張しない。

## 2026-09-11：公開リポジトリを作成する

**課題**：研究文書とコードを公開したいが、ローカルには相談履歴、個別ユーザーの出力、再配布対象外のデータもある。
**仮説**：公開対象をコードと研究文書に限定すれば、内部記録を保持したまま研究を紹介できる。
**根拠**：ユーザーがリポジトリ名`serendipity-ga-multiobjective`と公開設定を承認した。
**判断**：Git管理を開始し、相談元の識別子と外部保存先をローカル専用メモへ分離する。
データ、checkpoint、実験出力、相談履歴、サービス固有の登録記録は公開対象から除外する。
**結果**：READMEに日本語の研究タイトルと参考文献8本を収録し、公開対象を選別した。
旧実験時点のコードsnapshotを復元したわけではなく、今回の初回commitは現在のコードと文書の保存である。

## 2026-09-11：最新結果の参照を1M再実験とPhase 1へ訂正する

**課題**：1M再実験の存在はMacroに記録済みだったが、README文章案が旧100Kの数値と「加重和と全件一致」を中心にしており、現在の研究経緯を正しく伝えていなかった。
**仮説**：研究背景の冒頭と個人メモリに最新実験への参照を置けば、旧結果を現在の結果として再利用する混同を減らせる。
**根拠**：ユーザーが「100Kのあと1Mデータセットでやり直した」と明示し、Notion「実践」を参照してメモリを更新するよう依頼した。
Notionの1M子ページと保存済み本比較・診断runの完了記録を照合した。
**判断**：現在の結果の説明は1M本比較とPhase 1診断を起点にし、100Kは初期実験として保持する。
1MのCandidate Recall@100は0.192242、加重和との推薦完全一致率は98.56%であり、旧100Kの0.355381・全件一致で代用しない。
これは参照優先順位の訂正であり、canonical条件、version配置、Macro完了判定は変更しない。
**結果**：研究背景、ローカル参照先、個人メモリへ訂正を反映した。README改稿は引き続き保留し、既存の結果やコードを変更していない。
**検証**：2026-09-11、両runのcomplete/non-smoke、診断runのconfig・split・checkpoint・test summary・bootstrapを確認。
推薦CSVから2,880/2,922 user×seedのID・順序一致を再集計し、採用解由来2,874 weighted_sum / 6 sasrec / 42 evolvedを確認した。
学習・実験・全件回帰検査の再実行ではない。Notionのpositive説明と保存先コードの履歴範囲の差も背景文書へ記録した。
参照：[Macroの1M記録](../ROADMAP.md#external-1m)。

## 2026-09-11：構造を保ったままREADMEを研究日記と研究記事にする

**課題**：READMEが完成した手法の概要に寄っており、何を試したかったか、結果を見てどこを考え直したかが伝わりにくかった。
**仮説**：入口の短い日記とversion内の研究記事を分ければ、読み手が思考の経緯を追いつつ、既存reportで証拠を確認できる。
**根拠**：ユーザーが提示文を編集したうえで「構造はそのまま、READMEを入口と研究記事にする」案の実装を承認した。
最新結果の参照先は1M本比較とPhase 1であるという、直前の訂正を引き継ぐ。
**判断**：ルートREADMEには研究日記であること、現在の関心、日付付きの短い考察を置く。
v0 READMEは100Kの接続実験から1M再実験と診断までを辿り、技術選定の理由、暫定指標の限界、結果、保留判断を文章で残す。
過去の実験は事後整理と明示し、READMEから既存reportへリンクする。日記の毎日更新や新しい管理システムは導入しない。
**結果**：二つのREADMEと研究文書の運用説明を更新し、背景文書の役割説明を整合させた。
1MのCandidate Recall@100=0.192242と推薦完全一致率98.56%を反映し、100Kの「全件一致」と区別した。
フォルダ、コード、環境、実験出力、既存report、Macro/Microの完了判定は変更していない。
1Mのversion割り当てやcanonical設計の採否、外部同期、新規実験は承認範囲に含めない。
**検証（2026-09-11）**：1M集計表15セル、分割件数、Candidate Recall、bootstrap区間を保存済みCSV/JSONと照合した。
推薦CSVから2,880/2,922組の順序込み一致、由来CSVから採用解の内訳を再確認した。
ローカルリンク53件の参照先、コード囲み、参考文献の保持、変更が対象文書5件のみであることを確認し、`git diff --check`も通過した。
学習や実験の再実行、全件回帰検査、外部リンクの公開アクセス確認、読みやすさの効果測定はこの文書更新では行っていない。

## 2026-09-11：ROADMAPと説明用背景も1Mを起点に訂正する

**課題**：README以外の入口が100K中心で、説明用背景には旧positive、旧目的、旧結果が残っていた。
**仮説**：最新1Mの到達点と過去100Kの記録を見出しから分ければ、現在の結果の取り違えを減らせる。
**根拠**：ユーザーがmain READMEに加え、v0 ROADMAPなども1Mへ訂正するよう依頼した。
**判断**：main README、Macro、Micro、研究背景、説明用背景を1M中心に更新する。
RUNBOOKは最新1Mへの案内を先頭へ追加し、既存コマンドが100K用であることを明示する。

**結果**：対象文書を更新し、100Kの実測report、データ利用条件、コード、出力は保持した。1Mのversion配置とM1完了判定は変更していない。
今回の訂正は保存済み記録に基づく文書更新であり、新規実験は行っていない。GitHub反映はEnd-of-Day handoffの公開境界検査対象とした。

**検証（2026-09-11 End-of-Day）**：既存`check.py`を保存済みPhase 1成果物へ再実行し、内部整合性と、本比較からPhase 1へのcandidate score、全推薦ID・順序、既存全指標の回帰一致を確認した。
学習と実験は再実行していない。K=15〜30、学習seed間の頑健性、外部リンクの公開アクセスは未検証である。

<a id="canonical-1m"></a>

## 2026-09-12：MovieLens 1Mをv0の正式baselineへ一本化する

**課題**：公開repoの入口と結果reportが100K中心で、現在の1M研究結果が補足記録に留まり、研究正本が混在していた。

**仮説**：v0の条件と結果を1Mの単一reportに集約すれば、初見でも研究の現在地と根拠を辿れる。

**根拠**：ユーザーが1Mをcanonical baselineとして採用し、100KはGit historyに残せばよいと明示した。
1M本比較とPhase 1診断の保存出力を参照でき、指定されたNDCGとgenre distanceは両runの集計と一致した。

**判断**：v0 = MovieLens 1M canonical baselineとする。
positiveは推薦時点までの履歴平均超え、目的はmean rとmean d、K=10、候補100とし、r×dは診断専用に保つ。
旧100Kの結果reportと案内は現行mainから削除し、Git historyに保持する。
これは文書上の正式採用であり、100Kの旧Stepを1Mの実行完了として読み替えるものではない。

**結果**：[1M正式baseline報告](../v0/reports/S01-ml-1m-baseline.md)を作成し、入口、Macro、Micro、背景、仮説、RUNBOOKの参照を統一した。
コード、config、Notebook、データ、保存出力は変更せず、学習と新規実験も実行していない。
proxy改善をexperienced serendipity改善と呼ばず、M1〜M5、measurement gap、human validation前のLLMはprototypeというnarrativeを維持した。

**検証（2026-09-12）**：両runのconfig、完了マーカー、test集計、診断runのsplit、checkpoint、bootstrapを照合した。
ローカルリンク、Markdownの囲み、指定6指標、削除したreportへの現行リンクがないことを確認した。
コード、config、Notebookを含むMarkdown以外のtrackedファイルは変更していない。
当時の回帰検査と実験は再実行していない。

**未完**：当時の事前仕様と判断記録の照合、コードと環境を復元した再現確認。
canonical採用は完了したが、M1全体の完了とhuman validityは未達である。
