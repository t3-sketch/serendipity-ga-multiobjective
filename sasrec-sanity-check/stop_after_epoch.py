"""Stop the approved run after an epoch checkpoint, then package a portable handoff."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tarfile
import time
import torch

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "outputs/ml1m-ce-seed42-20260911"
TARGET_EPOCH = 6
PID = 47755


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def command(pid):
    return subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True,
                          text=True, check=False).stdout.strip()


while True:
    state = read(RUN / "status.json")
    if state.get("epoch", 0) >= TARGET_EPOCH:
        break
    if not command(PID):
        raise SystemExit("Training process ended before the target epoch checkpoint")
    time.sleep(5)

expected = f"run.py --config config.yaml --output outputs/ml1m-ce-seed42-20260911 --resume"
if expected not in command(PID):
    raise SystemExit("PID no longer belongs to the approved training command")
latest = torch.load(RUN / "latest.pt", map_location="cpu", weights_only=False)
if latest["epoch"] != TARGET_EPOCH or state["epoch"] != TARGET_EPOCH:
    raise SystemExit("Epoch checkpoint/status mismatch; refusing to stop")
os.kill(PID, signal.SIGTERM)
for _ in range(60):
    if not command(PID):
        break
    time.sleep(.5)
else:
    raise SystemExit("Training process did not stop after SIGTERM")

state.update(status="paused_by_user_after_epoch", stop_reason="move_to_faster_machine",
             convergence_verified=False, test_evaluated=False,
             stopped_after_epoch=TARGET_EPOCH)
write(RUN / "status.json", state)

handoff = ROOT / "handoff"
handoff.mkdir(exist_ok=True)
training = [json.loads(line) for line in (RUN / "training.jsonl").read_text().splitlines()]
summary = {"status": state["status"], "stopped_after_epoch": TARGET_EPOCH,
           "latest_epoch": latest["epoch"], "best_epoch": state["best_epoch"],
           "best_validation_ndcg@10": state["best_ndcg"],
           "latest_validation": training[-1]["validation"], "test_evaluated": False,
           "resume_command": "python -B run.py --config config.yaml --output outputs/ml1m-ce-seed42-20260911 --resume"}
write(RUN / "handoff.json", summary)

top = [".gitignore", "PLAN.md", "REPORT.md", "STATUS.md", "HANDOFF.md", "config.yaml",
       "requirements.txt", "run.py", "check.py", "check_status.py", "status.py",
       "stop_after_epoch.py"]
data = ["data/ml-1m.txt", "data/source.json"]
artifacts = ["latest.pt", "best.pt", "training.jsonl", "status.json", "progress.json",
             "handoff.json", "data_checks.json", "environment.json", "source_hashes.json",
             "resume_source_hashes.json", "recbole_config.txt", "validation_candidates.npz",
             "test_candidates.npz", "run-initial.py", "check-initial.py"]
files = [ROOT / p for p in top + data] + [RUN / p for p in artifacts if (RUN / p).exists()]
files += [p for p in [ROOT / "outputs/checks.json", ROOT / "outputs/resume-check.log",
                      ROOT / "outputs/ml1m-ce-seed42-20260911-console.log"] if p.exists()]
manifest = {str(p.relative_to(ROOT)): {"sha256": digest(p), "bytes": p.stat().st_size} for p in files}
write(handoff / "manifest.json", manifest)
files.append(handoff / "manifest.json")
archive = handoff / "sasrec-sanity-check-epoch6.tar.gz"
with tarfile.open(archive, "w:gz") as tar:
    for path in files:
        tar.add(path, arcname=str(Path("sasrec-sanity-check") / path.relative_to(ROOT)), recursive=False)
with tarfile.open(archive, "r:gz") as tar:
    names = set(tar.getnames())
    if not all(str(Path("sasrec-sanity-check") / p.relative_to(ROOT)) in names for p in files):
        raise SystemExit("Handoff archive verification failed")
(handoff / "archive.sha256").write_text(f"{digest(archive)}  {archive.name}\n")
print(json.dumps({**summary, "archive": str(archive), "archive_sha256": digest(archive)}), flush=True)
