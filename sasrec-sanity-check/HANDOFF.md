# SASRec sanity check：別マシンへの引き継ぎ

## 現在の判断

- 課題：現マシンのCPUでは1 epochが約37〜44分かかる。
- 仮説：同じcheckpoint・データ・設定を別マシンへ移せば、完了済みepochを捨てずに継続できる。
- 根拠：`latest.pt`にmodel、Adam、Python／NumPy／Torch／DataLoaderの乱数状態をepoch境界で保存している。toyデータでは再開後の次の更新がbitwise一致した。
- 結果：第6 epoch完了後に停止予定。停止後の確定値はrun内の`handoff.json`と`status.json`を参照する。

## 移すもの

停止監視が完了すると、`handoff/sasrec-sanity-check-epoch6.tar.gz`が作られる。
これには再開に必要なコード、設定、著者配布データ、固定候補、`latest.pt`、`best.pt`、学習履歴、検証記録を含む。
`handoff/archive.sha256`で転送後の破損を確認する。

チェックポイントは、この実験自身が生成したPyTorchファイルである。
出所不明のpickleへ差し替えず、転送後にhashを検証してから読み込む。

## 別マシンでの最短手順

Python 3.10を使う。

```sh
shasum -a 256 -c handoff/archive.sha256
tar -xzf handoff/sasrec-sanity-check-epoch6.tar.gz
cd sasrec-sanity-check
python3.10 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B check.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B run.py --config config.yaml --output outputs/ml1m-ce-seed42-20260911 --resume
```

WindowsではvenvのPythonパスだけ読み替える。
再開前に`check.py`がPASSすること、`data/source.json`のSHA-256、`handoff/manifest.json`を確認する。
runは同名outputの`status=paused_by_user_after_epoch`とepoch一致を検査してから再開する。

## 高速化について

現在のrunは承認済み計画どおりCPU 4 threadsであり、機器を変えても同じ設定ならCPUを使う。
新マシンのCPUが速ければ、そのまま同条件で短縮できる。
GPUへ切り替えるには実装と再現条件が変わるため、新マシンのOS・CPU・GPUを確認後に明示的に設定する。
CPUからGPUへ切り替えた継続はbitwise再現ではなく、controlled continuationとして記録する。

## 研究上の注意

原論文とRecBoleでは1 epochの定義が異なる。
今回の1 epochは981,491 prefix、batch size 128、7,668 batchである。
第6 epochでの停止はユーザー指定による計算環境の移行で、早期終了や収束を意味しない。
testはまだ見ない。別マシンで学習条件を固定してからvalidation最良checkpointを選び、最後に一度だけtest評価する。
既存v0や研究文書は変更しない。作業対象はこの新フォルダだけとする。
