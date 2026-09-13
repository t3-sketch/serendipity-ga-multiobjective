# music-evaluator

Research reader for Graph-Rec export contracts. **0.1** is a mock directory. **0.2** is a single `bundle.json`.
正本は Engineering の `docs/research-export.md` と `docs/research-export-v0.2.md`。
共通SDKは作らない。Graph-Rec の絶対path、node_modules、MovieLens、旧v0環境に依存しない。

```sh
python -B studies/music-evaluator/validate_export.py <bundle-dir>
python -B studies/music-evaluator/validate_export.py <bundle.json>
python -B studies/music-evaluator/test_validate_export.py
```

成功時は schema 版、case数、候補数（0.2は event 数も）だけを出す。モデル評価や human validity の数値は出さない。
0.1の評定/予測ファイルと 0.2の評定/予測配列が空でないと失敗する。
