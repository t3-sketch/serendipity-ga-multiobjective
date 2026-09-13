# v0-H1：候補生成器比較の公開要約

実施日：2026-09-12〜13。詳細は未追跡の`v0-H1/REPORT.md`。この文書は公開repoへ載せる検証範囲と解釈制約である。
v0の正本は[S01](S01-ml-1m-baseline.md)のままである。H1はv0を置き換えない。

## 結論

v0と同じ評価条件でSASRecをComiRec-SAまたはeSASRecへ替えても、
**この条件で乗り換えを正当化する優位性は検出できなかった**。

単一seed、arm別tuningなし、原論文と異なる実装を含む。
validationの点推定はeSASRecのCandidate Recall@100が最大だが、対応付きbootstrapの95%区間は0を含み、testでは差の符号が反転する。
proxy改善をexperienced serendipity改善とは呼ばない。

## v0再現として使った範囲

- A0：保存checkpoint再利用。validation/testの7指標が差0.0。
- A1：同環境scratch 7 epoch。`training.csv`が差0.0。
- 環境：python 3.10.20、recbole 1.2.1、torch 2.5.1、numpy 1.26.4、CPU 2 threads。

当時の事前仕様と判断記録の照合は未完である。

## 公開対象

明示一覧は[`v0-H1/PUBLIC.md`](../../v0-H1/PUBLIC.md)。集計CSVだけを公開し、`reports/comirec-interests.csv`は`user_id`付きのため公開しない。
フォルダ全体を一括追加しない。

## 解釈制約

- NSGA-IIの費用と加重和に対する非優位は、当該目的・制約・代表解規則に限定する。
- sanity checkの101候補next-item評価と、v0の候補・positive・時間窓は異なる。NDCGの差からprotocolの分解能やモデル改善を結論しない。
