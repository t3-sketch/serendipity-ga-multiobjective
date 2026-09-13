"""Refresh a human-readable status file without any LLM calls."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text()) if path.exists() else {}


def render(run, pid):
    state = read(run / "status.json")
    progress = read(run / "progress.json")
    try:
        os.kill(pid, 0)
        alive = True
    except ProcessLookupError:
        alive = False
    code = state.get("status", "preparing")
    ended = code.startswith("paused") or code == "execution_complete"
    if not ended and progress.get("epoch", 0) <= state.get("epoch", 0):
        progress = {"epoch": state.get("epoch", 0) + 1, "batch": 0, "batches": 7668,
                    "seconds": state.get("elapsed_seconds", 0), "epoch_seconds": 0}
    label = {"training": "学習中", "execution_complete": "学習・test評価の実行完了（最終検証待ち）",
             "paused_estimate_exceeds_approved_limit": "停止済み：所要時間見積もりが承認条件を超過",
             "paused_wallclock_limit": "停止済み：12時間上限に到達"}.get(code, code)
    if not alive and not ended:
        label = "プロセス終了：正常完了を確認できません。console logを確認してください"
    batch, total = progress.get("batch", 0), progress.get("batches", 7668)
    elapsed = progress.get("seconds", 0)
    epoch_elapsed = progress.get("epoch_seconds", elapsed)
    rate = epoch_elapsed / batch if batch else 0
    eta = f"約{rate * (total - batch) / 60:.1f}分" if batch else "次の進捗log待ち"
    if ended:
        detail = f"完了epoch：{state.get('epoch', 0)}。経過：{state.get('elapsed_seconds', 0) / 60:.1f}分。"
    else:
        detail = (f"epoch {progress.get('epoch', 1)}：**{batch:,} / {total:,} batch（{100 * batch / total:.1f}%）**\n\n"
                  f"総学習時間：約{elapsed / 60:.1f}分。現在のepochの学習終了まで：{eta}。\n"
                  "進捗は200 batchごとのlogに基づく概算です。最後にvalidationとcheckpoint保存が加わります。")
    training = run / "training.jsonl"
    validation = "まだepochが完了していないため、validationの性能は未確定です。"
    if training.exists():
        rows = [json.loads(x) for x in training.read_text().splitlines() if x]
        if rows:
            row = rows[-1]
            validation = (f"最後のvalidation：NDCG@10 = **{row['validation']['ndcg@10']:.6f}**、"
                          f"Hit@10 = **{row['validation']['hit@10']:.6f}**。\n\n"
                          f"選択epoch：{row['best_epoch']}。学習loss：{row['mean_loss']:.6f}。")
    results = read(run / "results.json")
    test = "**test未評価。論文と同等の性能かは、まだ判断できません。**"
    if results:
        test = f"Test結果：{json.dumps(results['sasrec'], ensure_ascii=False)}"
    text = f"""# SASRec 学習状況

更新：{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}（約15秒ごとに自動更新）

**状態：{label}**

{detail}

{validation}

{test}

## この後の動作

2026-09-12の「再開」により、保存済み第1 epochから継続します。総学習12時間の上限を維持します。
早期停止、または次epochが上限に収まらない見込みの時点で学習を止め、validation最良checkpointをtest評価します。
時間上限による停止では、収束確認済みとは扱いません。停止理由：`{state.get('stop_reason', '未確定')}`。

停止後もこのファイルは残ります。学習・この状態表示の更新にはLLM呼び出しを使わず、Codexの会話tokenを消費しません。
Macの終了・スリープやプロセス終了では計算が停止または中断するため、その間も進むことは保証しません。

## 次のタスクへの引き継ぎ

- 作業場所：`{ROOT}`
- 対象run：`{run}`
- PID：`{pid}`（この実行中のみ有効）
- [計画と承認範囲](PLAN.md)、[実験記録](REPORT.md)
- [進捗JSON]({run.relative_to(ROOT)}/progress.json)、[状態JSON]({run.relative_to(ROOT)}/status.json)
- [console log](outputs/ml1m-ce-seed42-20260911-console.log)
- epoch完了後：`latest.pt` と `best.pt` にmodel・optimizer・乱数状態を保存。
- 既存ファイル・既存環境は変更禁止。変更先はこの新フォルダのみ。
- 停止後に再開する場合は、状態と承認を確認して `--resume` を使う。同じoutputに新規学習を開始しない。完了runの再開は拒否する。

事前検査：データ件数一致、全981,491学習prefix、全評価候補、手計算指標、3 batch smokeを確認済み。
設定：RecBole 1.2.1の標準SASRec／CE、ML-1M、seed42、系列長200、次元50、CPU 4 threads。
"""
    temporary = ROOT / "STATUS.md.tmp"
    temporary.write_text(text)
    temporary.replace(ROOT / "STATUS.md")
    return ended or not alive


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--pid", type=int, required=True)
    args = parser.parse_args()
    while True:
        if render(args.run.resolve(), args.pid):
            break
        time.sleep(15)
