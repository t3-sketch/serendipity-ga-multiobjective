# music-evaluator

Phase 3 の接続検証だけを置く。仕様版は **0.1**。正本は Engineering の `docs/research-export.md`。
共通SDKは作らない。Graph-Rec の絶対path、node_modules、MovieLens、旧v0環境に依存しない。

```sh
python -B studies/music-evaluator/validate_export.py <bundle-dir>
python -B studies/music-evaluator/test_validate_export.py
```

成功時は schema 版、case数、候補数だけを出す。モデル評価や human validity の数値は出さない。
`human-ratings.jsonl` と `llm-predictions.jsonl` が空でないと version 0.1 では失敗する。
