# 研究文書の運用

## 文書の役割

| 読みたいこと | 保存先 |
|---|---|
| 他人向けの研究紹介 | [ルートREADME](../README.md)、[v0 README](../v0/README.md) |
| 研究全体の問い、依存関係、現在地 | [ルートROADMAP](../ROADMAP.md)：Macro `M1`〜`M5` |
| 各versionの問い、短い結果、完了条件 | [v0 ROADMAP](../v0/ROADMAP.md)：Micro `v0-S1`など |
| 背景、概念、採用前提 | [research_state.md](research_state.md) |
| 採用した判断と理由の履歴 | [decisions.md](decisions.md) |
| 文献と未検証仮説 | [literature.md](literature.md)、[hypotheses.md](hypotheses.md) |
| 実験前の計画 | version内の`plans/`。[記入項目](../v0/plans/README.md) |
| 実験後の報告と検証証拠 | version内の`reports/`。[既存報告](../v0/reports/S01-main.md) |
| コマンドと環境 | [v0 RUNBOOK](../v0/RUNBOOK.md) |
| AIが守る規則と読み先 | [AGENTS.md](../AGENTS.md) |
| 長い相談の経緯 | `discussions/`（ローカル専用） |

Macroとversionは一対一ではない。
一つのversionが複数のMacroに関わる場合は、Micro側で関連するMacro IDを記す。
既存の`hypotheses.md`のRQ番号は変更しない。
対応はM1→RQ5、M2→RQ1、M3→RQ2、M4→RQ3、M5→RQ4である。

## 計画から報告まで

1. Macroの依存条件と対象Microを確認し、今回の主作業を一つ決める。
2. 未実施の実験は、RQ、固定条件、変更条件、評価指標、保存先、完了条件を`plans/Sxx-名前.md`に記す。
3. 計画の承認者、日付、承認範囲を残してから、その範囲で実行する。
4. `reports/Sxx-名前.md`にRQ、短い結論、課題、仮説、根拠、結果、限界、証拠、検証範囲を記す。
5. Microの実行状態と検証状態を更新する。研究全体の到達点が変わった場合はMacroも更新する。
6. 採用判断が変われば`decisions.md`へ追記し、`research_state.md`の前提を照合する。

計画は外部の事前登録と同義ではない。
過去の実験は「事後整理」と記し、当時の計画や承認記録を確認できない項目は未確認とする。
test結果を見た後の条件選択を事前固定として扱わない。

長い作業を中断するときは、そのplanに「完了したこと、残り、判断理由、次に読むファイル」を追記する。
新しい記憶システムや細かな作業ログは作らない。
検証には実施日、対象run、実行した確認、根拠ファイル、未確認範囲を残す。
過去のPASS記録を読んだだけの場合と、今回再検証した場合を分ける。

## 相談チャットからの引き継ぎ

相談元の識別子とローカル保存先は`local-context.md`、長い対談は`discussions/`に保持する。
これらはGitHubの公開対象外である。
相談では必要なROADMAP、背景、対象reportだけを共有し、全文を毎回読み込まない。
反映時はユーザーの決定、AIの提案、実測、未確認を区別する。
Projectの名称や配置だけでは同期されず、採用済み判断を明示的に更新する。

## 移行した文書と保存上の注意

```text
sasrec-serendipity/
├── README.md                 人間向けの研究紹介
├── ROADMAP.md                Macro M1〜M5
├── AGENTS.md                 AIの規則と読み先
├── research/                 背景、文献、仮説、判断、相談履歴
└── v0/
    ├── README.md             v0の研究紹介
    ├── ROADMAP.md            Micro v0-S1〜S3
    ├── RUNBOOK.md            実行手順
    ├── plans/                計画の入口。新規計画は必要時に作成
    ├── reports/              各Stepの結果と検証証拠
    └── 既存コードとoutputs/  実験成果物を保持
```

旧`research/steps.md`はMacroへ、旧`v0/README.md`の実行説明はRUNBOOKへ再編した。
旧`RESULTS.md`と`LENGTH_RESULTS.md`はreportsへ移し、旧パスには参照用の案内だけを残した。
旧`RESEARCH.md`の詳しい解釈も[baseline概要記録](../v0/reports/baseline-overview.md)に保持した。
古い対談、判断ログ、NotebookLMへの登録記録は当時の履歴として読む。
ローカルreportは作業用の最新報告とし、Notionの既存報告は当時の公開用記録として参照する。自動同期はしない。

2026-09-10の文書再編時点ではGit metadataがなかった。
2026-09-11の公開準備でルートのGit管理を開始した。
保存済み出力は残っているが、旧実験時点のコードをGit履歴から復元できる状態ではない。
既存run内の絶対パスは移設前を指すことがあり、出力ファイル自体を書き換えずreportに現在の場所を記す。

構成の参考：[AGENTS.mdによる研究運用例](https://note.com/genkaijokyo/n/n76d27b3e66a8)、[Sant'Annaの研究workflow](https://psantanna.com/claude-code-my-workflow/workflow-guide.html)。
短い指示、計画と理由の記録、証拠を伴う検証を採用した。
自動agent群、独自採点、hooksは導入しない。
