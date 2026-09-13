"""Does ComiRec-SA actually use several interests on MovieLens 1M?

If one interest wins almost every item, the arm is a single-readout model wearing a
multi-interest name, and any difference from SASRec cannot be attributed to the
multi-interest mechanism. Reads the finished A2 run; writes reports/comirec-interests.csv.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from experiment import (chronological_split, load_data, make_cases,  # noqa: E402
                        model_registry, score_cases)

RUN = ROOT / "outputs" / "A2-comirec-sa"


def main():
    config = json.loads((RUN / "config.json").read_text())
    from recbole.config import Config
    from recbole.data import create_dataset
    from recbole.utils import init_seed

    model_class, model_params = model_registry(config["model"])
    cfg = Config(model=model_class, dataset="temporal-movielens", config_dict={
        "data_path": str(RUN / "atomic"), "use_gpu": False, "seed": config["seed"],
        "load_col": {"inter": ["user_id", "item_id", "timestamp"]},
        "reproducibility": True, "epochs": config["epochs"],
        "train_neg_sample_args": None,
        "eval_args": {"split": {"RS": [1, 0, 0]}, "order": "TO", "group_by": None,
                      "mode": "full"},
        "show_progress": False, "log_wandb": False,
        "metrics": ["NDCG"], "topk": [config["model_selection_k"]],
        "valid_metric": f"NDCG@{config['model_selection_k']}",
        **model_params,
    })
    init_seed(config["seed"], True)
    dataset = create_dataset(cfg)
    model = model_class(cfg, dataset)
    metadata = json.loads((RUN / "checkpoint.json").read_text())
    state = torch.load(RUN / "checkpoints" / Path(metadata["path"]).name,
                       map_location="cpu", weights_only=False)
    model.load_state_dict(state["state_dict"])
    model.eval()

    data = Path(config["data_dir"])
    ratings, genres = load_data(data if data.is_absolute() else ROOT / data)
    (train, valid, test), _ = chronological_split(ratings)
    cases, _ = make_cases(pd.concat([train, valid]), test, train, genres, dataset,
                          config["top_k"])
    scored = score_cases(model, cases, dataset, genres, config["candidate_pool"])

    token_map = dataset.field2token_id["item_id"]
    rows = []
    with torch.no_grad():
        for case in scored:
            history = case["sequence"][-model.max_seq_length:]
            seq = torch.zeros((1, model.max_seq_length), dtype=torch.long)
            seq[0, :len(history)] = torch.tensor(history)
            tokens = torch.tensor([token_map[str(i)] for i in case["ids"]])
            owner = model.interest_assignment(seq, torch.tensor([len(history)]),
                                              tokens).numpy()[0]
            rows.append({"user_id": case["user"],
                         "distinct_interests_in_pool": len(set(owner.tolist())),
                         "distinct_interests_in_top10": len(set(owner[:10].tolist())),
                         "dominant_interest_share_in_pool": float(
                             np.bincount(owner, minlength=model.n_interests).max() / len(owner))})
    frame = pd.DataFrame(rows)
    (ROOT / "reports").mkdir(exist_ok=True)
    frame.to_csv(ROOT / "reports" / "comirec-interests.csv", index=False)
    print(f"users: {len(frame)}, interests configured: {model.n_interests}")
    print(frame[["distinct_interests_in_pool", "distinct_interests_in_top10",
                 "dominant_interest_share_in_pool"]].describe().to_string())
    print("\nusers whose whole pool comes from one interest: "
          f"{int((frame.distinct_interests_in_pool == 1).sum())}")


if __name__ == "__main__":
    main()
