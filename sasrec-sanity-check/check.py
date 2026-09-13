"""Runnable protocol and model checks; no writes to the existing project."""
from tempfile import TemporaryDirectory
from pathlib import Path
import json
import numpy as np
import torch
from run import ROOT, Config, create_dataset, SASRec, candidates, metrics, save_json, checkpoint, restore
from types import SimpleNamespace
from recbole.data.interaction import Interaction


def main():
    torch.set_num_threads(4)
    sequences = {1: [1, 2, 3, 4, 5], 2: [6, 7, 8, 9, 10]}
    pools = candidates(sequences, np.arange(1, 121), 1042)
    for name, rows in pools.items():
        for seq, row in zip(sequences.values(), rows):
            assert row[0] == seq[-2 if name == "validation" else -1]
            assert len(set(row)) == 101 and not set(seq) & set(row[1:])
    assert np.array_equal(pools["test"], candidates(sequences, np.arange(1, 121), 1042)["test"])
    ids = np.tile(np.arange(1, 102), (3, 1))
    scores = np.zeros((3, 101))
    scores[0, 0] = 1
    scores[1, 1:10] = 1
    scores[2, 1:11] = 1
    summary, ranks = metrics(scores, ids)
    assert ranks.tolist() == [1, 10, 11]
    assert np.isclose(summary["hit@10"], 2 / 3)
    assert np.isclose(summary["ndcg@10"], (1 + 1 / np.log2(11)) / 3)
    assert metrics(np.zeros((1, 3)), np.array([[9, 2, 11]]))[1].tolist() == [2]
    out = ROOT / "outputs"
    out.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=out) as td:
        directory = Path(td)
        atomic = directory / "toy"
        atomic.mkdir()
        (atomic / "toy.inter").write_text("user_id:token\titem_id:token\ttimestamp:float\n" +
              "".join(f"{u}\t{i}\t{p}\n" for u, seq in sequences.items() for p, i in enumerate(seq, 1)))
        cfg = Config(model="SASRec", dataset="toy", config_file_list=[str(ROOT / "config.yaml")],
                     config_dict={"data_path": str(directory)})
        dataset = create_dataset(cfg)
        train, valid, test = dataset.build()
        assert (len(train), len(valid), len(test)) == (4, 2, 2)
        imap = dataset.field2token_id["item_id"]
        for split, offset in [(valid, -2), (test, -1)]:
            for row, seq in zip(range(2), sequences.values()):
                inter = split.inter_feat[row]
                length = int(inter["item_length"])
                assert int(inter["item_id"]) == imap[str(seq[offset])]
                assert inter["item_id_list"][:length].tolist() == [imap[str(i)] for i in seq[:offset]]
        torch.manual_seed(42)
        model = SASRec(cfg, dataset)
        optimizer = torch.optim.Adam(model.parameters(), lr=.001)
        losses = []
        for _ in range(3):
            model.train()
            optimizer.zero_grad()
            loss = model.calculate_loss(train.inter_feat)
            assert torch.isfinite(loss)
            loss.backward()
            assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
            assert model.item_embedding.weight.grad.abs().sum() > 0
            optimizer.step()
            losses.append(loss.item())
        loader = SimpleNamespace(generator=torch.Generator().manual_seed(42))
        state = dict(epoch=1, best_epoch=1, best_ndcg=.5, stale=0, updates=3, elapsed_seconds=1.0)
        checkpoint(directory / "resume.pt", model, optimizer, loader, state)
        saved = torch.load(directory / "resume.pt", weights_only=False)
        model.train()
        optimizer.zero_grad()
        expected_loss = model.calculate_loss(train.inter_feat)
        expected_loss.backward()
        optimizer.step()
        expected_weights = {k: v.clone() for k, v in model.state_dict().items()}
        assert restore(saved, model, optimizer, loader) == state
        optimizer.zero_grad()
        resumed_loss = model.calculate_loss(train.inter_feat)
        resumed_loss.backward()
        optimizer.step()
        torch.testing.assert_close(resumed_loss, expected_loss, rtol=0, atol=0)
        for k, v in model.state_dict().items():
            torch.testing.assert_close(v, expected_weights[k], rtol=0, atol=0)
        model.eval()
        with torch.no_grad():
            batch = valid.inter_feat
            direct = model.predict(batch)
            gathered = model.full_sort_predict(batch).gather(1, batch["item_id"].unsqueeze(1)).squeeze(1)
            torch.testing.assert_close(direct, gathered)
        save_json(out / "checks.json", {"status": "passed", "synthetic_split": True,
              "negative_candidates": True, "metric_hand_calculation": True,
              "resume_next_step_bitwise_equal": True,
              "score_equivalence": True, "finite_loss_and_gradients": True, "smoke_losses": losses})
    print("PASS: split, candidates, hand-calculated metrics, 3-batch smoke, predict equivalence")


if __name__ == "__main__":
    main()
