# v0：SASRecとNSGA-IIの接続実験

旧100K baselineの総括記録。K=10本実験とK=10〜30比較は完了。
2026-09-10に旧RESEARCH.mdから移転した。[現在の進捗](../ROADMAP.md)と区別して読む。

当時の人間向け報告：[Notion「SASRec × NSGA-II：推薦リスト長10〜30の実験結果と考察（2026-09-08）」](https://app.notion.com/p/3d580c3dba23812e8675d003042b15f1?pvs=204)

## v0の問い

SASRecが生成した同じ候補集合から、NSGA-IIでrelevanceと暫定serendipity proxyを考慮した推薦集合を選べるか。
その代表解はSASRec top-Kおよび単純加重和と比べて、objective、held-out metrics、計算時間でどう異なるか。

## v0が作ったもの

```text
MovieLens 100K
    ↓ temporal split
RecBole SASRec
    ↓ top 100 unseen candidates
pymoo NSGA-II
    ↓ K-item subset
offline comparison
```

SASRecのparameter learningとNSGA-IIのsubset searchは別段階である。
FAS-MOEAの完全再現ではなく、公平性objectiveも含めていない。

## 実施した条件

- positive：未観測区間のrating 4以上で、学習済みかつ履歴にないitem。
- `r`：SASRec scoreを全未視聴かつ学習済みcatalog内で0から1へ変換した順位値。確率でも予測ratingでもない。
- `d`：過去rating 4以上のgenre profileと候補itemのgenre vectorの`0.5 × L1`距離。
- `s_proxy = r × d`。
- NSGA-II objectives：推薦K件の平均`r`と平均`s_proxy`。
- 代表解：SASRec top-Kの平均`r`の95%以上を満たす解の中で平均`s_proxy`最大。
- 比較：SASRec top-K、`w*r + (1-w)*s_proxy`の加重和、NSGA-II。
- K：10、15、20、25、30。
- candidate pool：100件。
- NSGA-II：40個体、50世代、search seeds 42、43、44。
- test対象：51人。学習seedは42の一つ。

この条件は、現在の[RUNBOOK](../RUNBOOK.md)にある履歴平均positiveと`(r,d)`のworking proposalとは異なる。
v0の結果を後者の実験結果として読み替えない。

## 主結果

| K | SASRec NDCG | NSGA-II NDCG | SASRec Recall | NSGA-II Recall |
|---:|---:|---:|---:|---:|
| 10 | 0.105176 | 0.022050 | 0.090679 | 0.001013 |
| 15 | 0.125423 | 0.040717 | 0.152287 | 0.014761 |
| 20 | 0.134382 | 0.044276 | 0.184754 | 0.020627 |
| 25 | 0.142146 | 0.047302 | 0.211867 | 0.026355 |
| 30 | 0.144130 | 0.053468 | 0.217896 | 0.034290 |

| K | SASRec `s_proxy` | NSGA-II `s_proxy` | SASRec 高評価×距離/K | NSGA-II 高評価×距離/K |
|---:|---:|---:|---:|---:|
| 10 | 0.738042 | 0.925682 | 0.046970 | 0.014944 |
| 15 | 0.740860 | 0.910524 | 0.050093 | 0.021581 |
| 20 | 0.745376 | 0.898041 | 0.049108 | 0.022931 |
| 25 | 0.745438 | 0.886806 | 0.047537 | 0.024305 |
| 30 | 0.746949 | 0.876422 | 0.045436 | 0.026278 |

候補Recall@100は全Kで0.355381だった。
NSGA-IIの代表推薦は、加重和の代表推薦と全件一致した。
K=10の選択時間は、NSGA-IIが約133.6 ms/user/seed、加重和が約0.151 ms/userだった。
リスト長比較ではNSGA-IIが約120から129 ms/user/seed、加重和が約0.15から0.17 ms/userだった。

## 結果の解釈

**課題**：関連度を保ちながら、普段のgenre profileから離れた高評価itemを推薦したい。

**仮説**：`r × d`を含むmulti-objective selectionにより、高評価を伴う嗜好外推薦が増える可能性がある。

**根拠**：`r`をrelevanceの暫定proxy、`d`をtaste-broadeningの暫定proxyとして組み合わせた。

**結果**：定義した`s_proxy`は全Kで上昇したが、NDCG、Recall、高評価を伴う距離は全KでSASRecを下回った。
今回のproxyを最大化することが研究目的につながるという仮説は支持されなかった。

関連度95%条件はNDCGを95%保つ制約ではない。
候補100件内の順位値`r`はもともと高く、`s_proxy`単独最大の解が全test userで条件を通過したため、proxy優先を十分に抑制しなかった。

目的がitemごとの値の平均であり、採用点が加重和の重み0でも得られたため、現在の目的と代表解規則ではNSGA-IIの追加効果が確認できなかった。
これは非加算的なlist-level objective、別の制約、別の運用点でもNSGA-IIが不要だという結果ではない。

## v0で言えること

- SASRec候補生成とNSGA-II subset selectionを接続できた。
- 同じ候補と評価条件でSASRec、加重和、NSGA-IIを比較できた。
- 暫定proxyを高めてもheld-out qualityが高まるとは限らなかった。
- 現在の目的と代表解規則では、NSGA-II代表解は単純加重和と一致した。
- Kを30まで増やすだけでは、proxyとheld-out qualityの乖離は解消しなかった。

## v0で言えないこと

- FAS-MOEAを再現したとは言えない。
- serendipity指標を確立したとは言えない。
- human experienced serendipityを改善したとは言えない。
- `r`が人間のrelevance、`d`がRefreshing、`r × d`がTBSを妥当に測るとは言えない。
- NSGA-IIがsequential recommendationで一般に不要とは言えない。
- MovieLensの結果を音楽推薦へ一般化できない。

## v0の完了条件

- [x] 実装経路と実験設定、保存出力を記録した（当時のコード復元と再実行による再現確認は未実施）。
- [x] K=10の本実験を保存した。
- [x] K=10から30の比較を保存した。
- [x] 加重和を同条件の比較対象にした。
- [x] 結果とclaim boundaryをNotionとローカルへ記録した。
- [x] v0を後続の指標設計と混同しないようscopeを固定した。

ここで完了とするのは旧条件のintegration baselineである。
現行条件の100K本比較まで完了したことにはならない。
次の判断は[Macro M1](../../ROADMAP.md#m1)、個別実験の状況は[Micro](../ROADMAP.md)で管理する。
数値の根拠と検証範囲は[S01](S01-main.md)と[S02](S02-list-length.md)を参照する。
