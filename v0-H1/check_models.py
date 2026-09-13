"""Pre-run checks for the two new candidate generators.

Runs on a tiny synthetic RecBole dataset so it finishes in seconds. It verifies the
contract experiment.py relies on (full_sort_predict shape, finite scores, padding
handled, loss decreases on a memorisable batch) plus the failure modes specific to
each architecture: interest collapse for ComiRec-SA and a dead gate for eSASRec.
"""
from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from experiment import model_registry  # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}{(': ' + detail) if detail else ''}")
    if not condition:
        FAILURES.append(name)


def toy_dataset(directory, n_users=40, n_items=30, length=12):
    """Every user walks a shifted arithmetic cycle, so the next item is learnable."""
    atomic = directory / "toy"
    atomic.mkdir(parents=True)
    rows = ["user_id:token\titem_id:token\ttimestamp:float"]
    for user in range(1, n_users + 1):
        for step in range(length):
            item = 1 + ((user + step * 3) % n_items)
            rows.append(f"u{user}\ti{item}\t{step + 1}")
    (atomic / "toy.inter").write_text("\n".join(rows) + "\n")
    return atomic


def build(model_name, atomic, seed=42):
    from recbole.config import Config
    from recbole.data import create_dataset
    from recbole.data.dataloader import TrainDataLoader
    from recbole.utils import init_seed

    model_class, model_params = model_registry(model_name)
    cfg = Config(model=model_class, dataset="toy", config_dict={
        "data_path": str(atomic.parent), "use_gpu": False, "seed": seed,
        "load_col": {"inter": ["user_id", "item_id", "timestamp"]},
        "reproducibility": True, "epochs": 1, "train_batch_size": 64,
        "train_neg_sample_args": None,
        "eval_args": {"split": {"RS": [1, 0, 0]}, "order": "TO", "group_by": None,
                      "mode": "full"},
        "MAX_ITEM_LIST_LENGTH": 10, "show_progress": False, "log_wandb": False,
        "metrics": ["NDCG"], "topk": [10], "valid_metric": "NDCG@10",
        **model_params,
    })
    init_seed(seed, True)
    dataset = create_dataset(cfg)
    loader = TrainDataLoader(cfg, dataset.build()[0], sampler=None, shuffle=True)
    return cfg, dataset, model_class(cfg, dataset), loader


def train_briefly(model, loader, steps=60):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    model.train()
    losses = []
    step = 0
    while step < steps:
        for interaction in loader:
            loss = model.calculate_loss(interaction)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss))
            step += 1
            if step >= steps:
                break
    return losses


def main():
    directory = Path(tempfile.mkdtemp(prefix="v0h1-check-"))
    try:
        atomic = toy_dataset(directory)
        for name in ["sasrec", "comirec", "esasrec"]:
            print(f"\n--- {name} ---")
            cfg, dataset, model, loader = build(name, atomic)
            n_items = dataset.num("item_id")

            # The reranking harness calls full_sort_predict on one padded sequence.
            seq = torch.zeros((1, model.max_seq_length), dtype=torch.long)
            seq[0, :4] = torch.tensor([3, 7, 11, 15])
            model.eval()
            with torch.no_grad():
                scores = model.full_sort_predict({model.ITEM_SEQ: seq,
                                                  model.ITEM_SEQ_LEN: torch.tensor([4])})
            check(f"{name}: score shape", tuple(scores.shape) == (1, n_items),
                  f"{tuple(scores.shape)} vs (1, {n_items})")
            check(f"{name}: scores finite", bool(torch.isfinite(scores).all()))

            # Padding must not change the answer: the same history in a longer window.
            long_seq = torch.zeros((1, model.max_seq_length), dtype=torch.long)
            long_seq[0, :4] = seq[0, :4]
            with torch.no_grad():
                repeat = model.full_sort_predict({model.ITEM_SEQ: long_seq,
                                                  model.ITEM_SEQ_LEN: torch.tensor([4])})
            check(f"{name}: deterministic in eval mode",
                  bool(torch.allclose(scores, repeat, atol=1e-6)))

            losses = train_briefly(model, loader)
            early, late = float(np.mean(losses[:10])), float(np.mean(losses[-10:]))
            check(f"{name}: loss decreases", late < early, f"{early:.4f} -> {late:.4f}")

            if name == "comirec":
                usage = model.interest_usage.detach().numpy()
                share = usage / max(1, usage.sum())
                check("comirec: more than one interest used", int((usage > 0).sum()) > 1,
                      f"routing share {np.round(share, 3).tolist()}")
                with torch.no_grad():
                    interests = model.forward(seq, torch.tensor([4]))
                spread = float(torch.cdist(interests[0], interests[0]).max())
                check("comirec: interests are not identical", spread > 1e-3,
                      f"max pairwise distance {spread:.4f}")

            if name == "esasrec":
                with torch.no_grad():
                    hidden = model.item_embedding(seq)
                    gates = [float(torch.sigmoid(layer.attn_gate(hidden)).mean())
                             for layer in model.trm_encoder.layer]
                check("esasrec: gates are not saturated",
                      all(0.02 < g < 0.98 for g in gates),
                      f"mean attention gate per layer {np.round(gates, 3).tolist()}")
                check("esasrec: sampled softmax is in use",
                      model.loss_type == "SS" and model.n_negatives == 256,
                      f"loss={model.loss_type}, negatives={model.n_negatives}")
                check("esasrec: LiGR replaced the encoder",
                      type(model.trm_encoder).__name__ == "LiGREncoder")
    finally:
        shutil.rmtree(directory, ignore_errors=True)

    print()
    if FAILURES:
        print(f"FAILED: {FAILURES}")
        return 1
    print("All model checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
