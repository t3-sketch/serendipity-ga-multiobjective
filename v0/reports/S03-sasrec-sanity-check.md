# SASRec sanity checkの公開要約

実施日：2026-09-11〜12。詳細は未追跡の`sasrec-sanity-check/REPORT.md`と`STATUS.md`。
これは原論文に近いnext-item protocolの途中記録であり、v0のcanonical結果ではない。

## 状態

第6 epochのあとユーザー指定で停止。validation NDCG@10=0.621652、Hit@10=0.831457。
**test未評価。論文値との一致は判断できない。**

## 公開対象

公開候補：`PLAN.md`、`REPORT.md`、`HANDOFF.md`、`STATUS.md`、実行・検査スクリプト、`config.yaml`、`requirements.txt`、`handoff/manifest.json`、`handoff/archive.sha256`。
非公開：`data/`、`outputs/`、checkpointを含む`handoff/*.tar.gz`。

## 解釈制約

評価は正解1件＋ランダム100件である。v0の未視聴catalog上位100候補、履歴平均超えpositive、全体時刻分割とは条件が違う。
validation NDCGの差を、v0 protocolの分解能やモデル改善の証拠にしない。
