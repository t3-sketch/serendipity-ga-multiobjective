# Research / Engineering 引き継ぎ計画

更新日：2026-09-13。設計担当：Astra。実装担当：Sol（Cursor等の実装agentにも同じ制約を適用）。

## 現在の実行モード

**PHASE_4_PLANNING_ONLY — Phase 1〜3はAstra再レビュー合格。現在はPhase 4の設計のみ。実装は未許可。**
2026-09-13のユーザー指示により公開checkpointをpush済み：Research `a117f75`、Engineering `45b436d`。Engineeringは https://github.com/t3-sketch/graph-rec （Public）。この記録が以下の過去の未公開・レビュー待ち記載に優先する。新規学習、人間参加者の募集、サービス接続、アプリdeployは自動実行しない。
モデル変更だけを開始指示と解釈しない。

## 目的と責務

就活を主目的に、既存Research repoを継続して公開再現性を整え、既存Graph-RecをEngineering repoとして育て、固定推薦ケースで両者を接続する。

| Track | 作業場所 | 責務 |
|---|---|---|
| Research | このrepo。ローカル名 `sasrec-serendipity`、GitHub `t3-sketch/serendipity-ga-multiobjective` | RQ、実験条件、人間評価、LLMの妥当性検証、過去実験の再現資産 |
| Engineering | 別プロジェクト `Graph-Rec`。製品名Sonder | 音楽探索UI、推薦実装、データ取り込み、API、推薦ケース出力 |

このファイルを全体計画の正本とする。Graph-Recの `PLAN.md` は担当範囲とこの正本への案内を持つ。
同じrepo名やアプリ上の配置は同期の証拠にならない。別プロジェクトが見つからない場合は、その作業場所を確認してから依存作業へ進む。
Researchのrepo名は当面維持。Engineeringは `t3-sketch/graph-rec`（Public）。
新しい推薦実装の正本はEngineering。Researchでは同じ実装を作り直さず、固定commit・設定からの出力を評価する。旧v0は歴史的snapshotとして保持する。

## Phase 0時点の記録（変更前）

- Research HEADは `7c158a0`。既存の `research/decisions.md` と `research/research_state.md` に未コミット変更がある。上書きしない。
- `v0-H1/` と `sasrec-sanity-check/` は未追跡。フォルダ全体を一括追加しない。
- 公開v0報告はMovieLens 1M、公開コードは100K用。1Mコードと出力は別保存。場所は非公開の `research/local-context.md` にある。
- H1報告にはSASRec再学習7 epochと下流7指標の再現一致があるが、公開文書への反映は未完。今回の計画作成では再実行していない。
- Graph-RecはGit未管理。Next.js / TypeScriptの探索UI、枝保持、再生、保存、イベント型、推薦器差し替え口がある。
- Graph-Recの推薦は架空640曲のmock。実サービス認証、SASRec、KGは未実装。探索経路の描画グラフをKnowledge Graphと呼ばない。
- Graph-RecのREADMEと `.codex/IMPLEMENTATION_STATE.md` にはアニメーションの現状について不一致がある。再開時に対象コードと照合する。

## Phase 1：資産と公開対象を確定

1. 上記の未コミット・未追跡資産について、コード、計画、集計報告、データ、生出力を分類する。
2. Graph-Recの状態文書と実装を照合し、既存の画面とprovider境界を維持する。
3. Graph-Recは現在の作業場所でGit管理する案とする。開始指示の範囲を確認し、公開対象から依存パッケージ、cache、秘密情報、ローカル固有情報を除く。
4. 新規repoの公開設定を確定してからGitHub作成へ進む。

完了条件：正本、実装済み範囲、公開対象、未公開成果が明確。既存成果を失わず、公開する差分をレビューできる。

2026-09-13実施結果：完了。分類と照合の正本は`docs/PROJECT_STATE.md`。フォルダ一括追加・GitHub作成・commitはしていない。

## Phase 2：Researchの公開再現性

1. `v0/RUNBOOK.md` と `research/local-context.md` から別保存の1M実装・設定・環境・出力を特定する。
2. H1の再現結果と照合し、正式1M baselineへ到達できる最小のコード・設定・環境情報を整える。元成果物は保持する。
3. データ取得、実行、集計、報告値照合の経路を文書化し、個人の絶対パスへの依存を解消する。
4. 小規模な動作確認と保存結果の照合を行う。フル再学習は費用を見積もった別実行単位とし、未実施なら明記する。
5. 1Mの経路を確認してから100Kを現行入口から退役させ、Git履歴に保持する。
6. H1・sanity checkの公開対象を選別し、正式報告と研究状態へ検証範囲を反映する。

完了条件：公開対象だけで小規模動作確認と集計を実行できる。本実験の取得・再現手順、照合済み証拠、未検証事項が追える。

2026-09-13実施結果：完了。現行入口は`v0/reproduce/`。`check.py`と`verify_saved.py`がPASS。フル再学習は未実施。元の1M保存物は移動していない。

研究上の解釈制約：
- H1は単一seed、arm別tuningなし、原論文と異なる実装を含む。「この条件で乗り換えを正当化する優位性を検出できなかった」と述べる。
- sanity checkの101候補next-item評価とv0の候補・positive・時間窓は異なる。NDCGの差からprotocolの分解能やモデル改善を結論しない。
- NSGA-IIの費用・優位性は当該目的、制約、代表解規則に限定する。
- proxy改善をexperienced serendipity改善と呼ばない。事後整理を事前計画と呼ばない。

## Phase 3：固定推薦ケースの契約

2026-09-13：仕様をEngineeringの `docs/research-export.md` に確定。version 0.1はmock推薦のオフラインexport/importに限定。本人評定・LLM予測は空ファイルとし、尺度の設計はPhase 5へ残す。実装担当はこの仕様の型・拒否条件・受入検査に従う。画面への配線はPhase 4。

Astraが仕様を確定してからSolが実装する。仕様の正本はEngineeringの `docs/research-export.md` version 0.1。Researchは仕様版を `studies/music-evaluator/README.md` に記録する。共通SDKは作らない。

2026-09-13実施結果：実装完了、Astraレビュー待ち。Engineering CLI `npm run export:research -- --output <未使用dir>` と Research `python -B studies/music-evaluator/validate_export.py <bundle-dir>`。実mock 2ケース（15候補）をreaderが読み、同一fixtureのbytes/hash一致、既存dir上書き拒否、破損fixture拒否を確認。Phase 4未着手。mock出力を実推薦成果としない。

| 形式案 | 内容 |
|---|---|
| `manifest.json` | schema版、生成元commit、設定、データ版、run ID |
| `cases.jsonl` | 匿名participant ID、case ID、曲ID、推薦前の入力、候補、順序、提示条件、mock/実データ区分 |
| `human-ratings.jsonl` | 本人のF/R/E・global評定。LLM入力とは分離 |
| `llm-predictions.jsonl` | case ID、model・prompt版、予測、失敗状態 |

既存の `Track` と `RecommendationContext` を再利用する。探索経路、聴取履歴、明示的なLike/Saveを区別し、クリックを好みラベルにしない。ノード座標を類似度・serendipityと解釈しない。
完了条件：小さな架空ケースをexport/importでき、版・ID・必須項目・対応漏れ・本人評定の入力混入を検査できる。mockケースは接続検証専用。

## Phase 4：Graph-Recの実データ探索経路

目標：曲を選ぶ → 候補を見る → 枝を探索する → 試聴可能な曲を聴く → 明示的反応を記録する → ケースを書き出す。

- 先にAstraとユーザーがデータ源、利用可能な履歴、baselineを確定する。未確定のサービスやモデルをSolが独自採用しない。
- 系列データが不足する場合は属性・関係による候補生成を最初の候補とする。
- SASRec採用時は音楽データで評価する。MovieLensの重み・評価値・positive定義を転用しない。
- KGは関係の定義と比較仮説を決めて追加する。NSGA-II等も比較上必要な場合に追加する。
- 既存 `RecommendationProvider` を利用する。UIの滑らかさ、次に速度という製品優先順位を維持する。
- サーバーが必要な場合に静的出力構成の変更を設計する。既存Site登録を重複作成しない。

完了条件：一往復が動き、枝保持・drag・復元・Like/Saveを維持し、候補取得時間を計測。UI性能はブラウザで未計測なら未計測と記す。

## Phase 5：最初のLLM評価研究

RQ案：推薦前の履歴と曲情報を与えたLLMは、本人の聴取後F/R/E評定を、単純なproxyよりどの程度よく予測できるか。

Astraが対象者、質問項目、提示条件、主指標、参加者単位split、人数・採否基準を確定し、Solが実装する。最初はpilotで質問と提示条件を検証する。製品の一般利用者獲得を前提にしない。
本人回答を入力へ混ぜない。prompt調整と最終評価を分離する。metadataだけなら聴覚経験そのものではなく、その予測と明記する。
最初はM2・M3を中心とし、M4の集約探索とM5の最適化は後続。human validation前はprototype。
完了条件：同一ケースで本人評定・proxy・LLM予測が揃い、一致・誤差・不確実性・限界を報告できる。

## Phase 6：就活向けの入口

Engineering：デモ、起動、構成、品質・速度の実測。Research：問い、完了結果、再現方法、限界。
技術選定は「課題・仮説・根拠・結果」で記録し、両repoを相互リンクする。未実装技術や未検証成果を実績に数えない。

## 実行順・設計判断

Phase 1 → 2 → Astraレビュー → 3 → 4。Phase 5の設計は独立に進められるが、募集・データ取得はprotocol確定後。Phase 6は各成果に合わせる。
SolのPhase 1・2・3は実装済み。Phase 3はAstraレビュー待ち。Phase 4には進まない。残る設計判断：GitHub公開設定、音楽データ源、baseline、KG関係、実データ用schema拡張、human protocol、費用・期限。
Solは技術的障害のない限り再設計しない。障害時は証拠、影響、最小代替案を記録してAstraへ返す。複雑な設計変更は実装前にこの計画を更新する。

## 再開チェックポイント

2026-09-13最新：Phase 3のP2 2件は再レビュー合格。Engineering test 9/9・typecheck、Research test 10/10を確認。buildとブラウザは再レビューで再実行していない。両repoの公開checkpointは上記のとおり完了。次はAstraがデータ源・baseline・最初の完成範囲を提案し、ユーザー合意後に実装仕様を確定する。SolによるPhase 4実装は未許可。以下はPhase 3提出時の記録であり、最新の許可・状態として使わない。

- 許可範囲：2026-09-13のPhase 3実装指示。実施済みはPhase 1、Phase 2、Phase 3実装。Phase 4は未許可。
- 完了：計画文書化、Phase 1、Phase 2、Phase 3（mock CLI export、Python reader、仕様の受入検査）。
- レビュー完了：Phase 1・2の前回3件を再検査し合格。Phase 3初回レビューはP2 2件。エスケープ重複キーと実在日時を両側で揃えて再提出。
- 設計完了：Phase 3 version 0.1。正本はGraph-Recの `docs/research-export.md`。
- 未着手：Phase 4〜6、GitHub作成・公開・push、commit、新規学習、データ収集。
- 次の一手：AstraがPhase 3実装をレビューする。Phase 4には進まない。
- 変更ファイル（レビュー戻し）：Researchは `studies/music-evaluator/{validate_export.py,test_validate_export.py,README.md}`、`docs/PROJECT_STATE.md`、`research/decisions.md`、`research/research_state.md`、この`PLAN.md`。Engineeringは `src/research-export/*`、`scripts/export-research.ts`、`scripts/isolated-run.py`、`tests/research-export.test.ts`、`package.json`、`PLAN.md`、`AGENTS.md`、`.codex/IMPLEMENTATION_STATE.md`。
- 検証：Graph-Rec `python3 scripts/isolated-run.py test` 9/9、`typecheck` PASS、`build` PASS。Research `python3 -B studies/music-evaluator/test_validate_export.py` 9/9。実mock bundleをreaderが `schema_version=0.1 case_count=2 recommendation_count=15`。同一fixtureのcases bytes/hash一致。既存dir再実行は拒否し4ファイルhash不変。ブラウザ検証は未実施（UI未変更）。
- 未検証：Astraによる仕様照合レビュー、事前仕様との照合、公開snapshotとresumed2当時ソースのバイト一致、フル再学習、GitHub公開設定、ブラウザ再検証、H1/sanityのcommit。

研究の実測は各report、背景は `research/research_state.md`、進捗は `ROADMAP.md` に置き、ここへ数値を重複管理しない。
