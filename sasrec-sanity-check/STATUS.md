# SASRec 学習状況

更新：2026-09-12 11:20:19 JST（約15秒ごとに自動更新）

**状態：paused_by_user_after_epoch**

完了epoch：6。経過：245.9分。

最後のvalidation：NDCG@10 = **0.621652**、Hit@10 = **0.831457**。

選択epoch：6。学習loss：5.666693。

**test未評価。論文と同等の性能かは、まだ判断できません。**

## この後の動作

2026-09-12の「再開」により、保存済み第1 epochから継続します。総学習12時間の上限を維持します。
早期停止、または次epochが上限に収まらない見込みの時点で学習を止め、validation最良checkpointをtest評価します。
時間上限による停止では、収束確認済みとは扱いません。停止理由：`move_to_faster_machine`。

停止後もこのファイルは残ります。学習・この状態表示の更新にはLLM呼び出しを使わず、Codexの会話tokenを消費しません。
Macの終了・スリープやプロセス終了では計算が停止または中断するため、その間も進むことは保証しません。

## 次のタスクへの引き継ぎ

- 作業場所：`/Users/macuser/dev/sasrec-serendipity/sasrec-sanity-check`
- 対象run：`/Users/macuser/dev/sasrec-serendipity/sasrec-sanity-check/outputs/ml1m-ce-seed42-20260911`
- PID：`47755`（この実行中のみ有効）
- [計画と承認範囲](PLAN.md)、[実験記録](REPORT.md)
- [進捗JSON](outputs/ml1m-ce-seed42-20260911/progress.json)、[状態JSON](outputs/ml1m-ce-seed42-20260911/status.json)
- [console log](outputs/ml1m-ce-seed42-20260911-console.log)
- epoch完了後：`latest.pt` と `best.pt` にmodel・optimizer・乱数状態を保存。
- 既存ファイル・既存環境は変更禁止。変更先はこの新フォルダのみ。
- 停止後に再開する場合は、状態と承認を確認して `--resume` を使う。同じoutputに新規学習を開始しない。完了runの再開は拒否する。

事前検査：データ件数一致、全981,491学習prefix、全評価候補、手計算指標、3 batch smokeを確認済み。
設定：RecBole 1.2.1の標準SASRec／CE、ML-1M、seed42、系列長200、次元50、CPU 4 threads。
