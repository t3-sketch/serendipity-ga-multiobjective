"""Status display handles a resumed epoch and a terminal pause."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import status

with TemporaryDirectory(dir=status.ROOT / "outputs") as temporary:
    original = status.ROOT
    status.ROOT = Path(temporary)
    run = status.ROOT / "run"
    run.mkdir()
    (run / "status.json").write_text(json.dumps({"status": "training", "epoch": 1, "elapsed_seconds": 2400}))
    (run / "progress.json").write_text(json.dumps({"epoch": 1, "batch": 7600}))
    assert not status.render(run, os.getpid())
    text = (status.ROOT / "STATUS.md").read_text()
    assert "epoch 2" in text and "次の進捗log待ち" in text
    (run / "status.json").write_text(json.dumps({"status": "paused_wallclock_limit", "epoch": 2}))
    assert status.render(run, os.getpid())
    assert "停止済み" in (status.ROOT / "STATUS.md").read_text()
    status.ROOT = original
print("PASS: resumed epoch and terminal status rendering")
