"""Small runnable checks for the experiment's scientific and integration boundaries."""
from itertools import combinations
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import pandas as pd

from experiment import (COMPARISON_METHODS, FixedSizeRepair, NonDominatedSorting, SubsetProblem, baselines,
                        chronological_split, distance, evaluate_list, evolve,
                        make_cases, objectives, representative, reuse_model)


def check_centered_positives():
    columns = ["user_id", "item_id", "rating", "timestamp"]
    history = pd.DataFrame([
        [1, 1, 2, 1], [1, 2, 3, 2], [1, 3, 4, 3],
        [2, 1, 5, 1], [2, 2, 5, 2],  # Constant ratings: no above-mean history.
        [3, 1, 1, 1], [3, 2, 3, 2],  # Rating 3 can be relatively positive.
        [4, 1, 1, 1], [4, 2, 3, 2], [5, 1, 5, 1],
    ], columns=columns)
    future = pd.DataFrame([
        [1, 4, 3, 4], [1, 5, 4, 5], [1, 6, 5, 6],
        [1, 1, 5, 7], [1, 99, 5, 8],  # Seen and outside train vocabulary.
        [2, 4, 5, 4], [3, 4, 3, 4], [4, 4, 2, 4], [5, 4, 5, 4], [9, 4, 5, 4],
    ], columns=columns)
    dataset = SimpleNamespace(field2token_id={"item_id": {"[PAD]": 0, **{str(i): i for i in range(1, 8)}}})
    genres = pd.DataFrame([[1., 0.], [1., 0.], [0., 1.]] + [[.5, .5]] * 4, index=range(1, 8))
    cases, report = make_cases(history, future, history, genres, dataset, 1)
    users = {row["user_id"]: row for row in report["users"]}
    assert report["eligible_users"] == 2 and report["no_positive_history_users"] == 2
    assert report["no_eligible_positive_users"] == 1 and report["cold_user_users"] == 1
    assert users[1]["history_rating_mean"] == 3.0
    assert users[1]["positive_history_count"] == 1 and users[1]["future_positives_count"] == 2
    assert users[2]["status"] == users[5]["status"] == "no_positive_history"
    assert users[4]["status"] == "no_eligible_positive"  # Equality is not positive.
    assert users[9]["history_rating_mean"] is None
    json.dumps(report, allow_nan=False)
    assert cases[0]["positives"] == {5, 6} and cases[1]["positives"] == {4}
    assert cases[0]["sequence"] == [1, 2, 3]
    np.testing.assert_array_equal(cases[0]["available"], [4, 5, 6, 7])
    np.testing.assert_array_equal(cases[0]["profile"], [0, 1])

    changed = future.copy()
    changed.loc[(changed.user_id == 1) & changed.item_id.isin([4, 5, 6]), "rating"] = [5, 2, 4]
    assert changed.loc[changed.user_id == 1, "rating"].mean() != future.loc[future.user_id == 1, "rating"].mean()
    other, changed_report = make_cases(history, changed, history, genres, dataset, 1)
    assert other[0]["positives"] == {4, 6}
    for before, after in zip(report["users"], changed_report["users"]):
        assert before["history_rating_mean"] == after["history_rating_mean"]
        assert before["positive_history_count"] == after["positive_history_count"]
    for key in ("sequence", "available", "profile"):
        np.testing.assert_array_equal(cases[0][key], other[0][key])

    # Test uses train + validation, including out-of-vocabulary past ratings in the mean.
    validation = pd.DataFrame([[1, 7, 1, 4], [1, 99, 1, 5]], columns=columns)
    test = future.assign(timestamp=future.timestamp + 10)
    test_cases, test_report = make_cases(pd.concat([history, validation]), test, history, genres, dataset, 1)
    assert test_report["users"][0]["history_rating_mean"] == 11 / 5
    assert test_report["users"][0]["positive_history_count"] == 2
    assert test_cases[0]["positives"] == {4, 5, 6}
    assert test_cases[0]["sequence"] == [1, 2, 3, 7]
    np.testing.assert_array_equal(test_cases[0]["available"], [4, 5, 6])
    np.testing.assert_array_equal(test_cases[0]["profile"], [.5, .5])
    _, altered_test_report = make_cases(pd.concat([history, validation]), changed.assign(timestamp=changed.timestamp + 10),
                                       history, genres, dataset, 1)
    assert altered_test_report["users"][0]["history_rating_mean"] == 11 / 5

    # A checkpoint selected with absolute positives is not selected under the new labels.
    with TemporaryDirectory() as directory:
        run = Path(directory)
        config = dict(seed=42, epochs=1, patience=1, train_batch_size=1, threads=1, model_selection_k=10, top_k=10)
        (run / "completion.json").write_text(json.dumps({"status": "complete"}))
        (run / "config.json").write_text(json.dumps({**config, "smoke": False}))
        (run / "split.json").write_text(json.dumps({"validation": {"eligible_users": 69}}))
        try:
            reuse_model(run, None, None, config, run)
        except ValueError as error:
            assert str(error) == "Checkpoint positive definition does not match; train a new model"
        else:
            raise AssertionError("Checkpoint reuse accepted the old positive definition")


def check():
    check_centered_positives()
    ratings = pd.DataFrame({"user_id": [1] * 20, "item_id": np.arange(1, 21),
                            "timestamp": np.repeat(np.arange(10), 2), "rating": [5] * 20})
    (train, valid, test), cuts = chronological_split(ratings)
    assert train.timestamp.max() < valid.timestamp.min() < test.timestamp.min()
    assert len(train) + len(valid) + len(test) == len(ratings)
    assert not set(train.timestamp) & set(valid.timestamp)
    altered = ratings.copy()
    altered.loc[altered.timestamp >= cuts[1], "rating"] = 1
    assert chronological_split(altered)[0][0].equals(train)

    np.testing.assert_allclose(distance(np.array([1., 0.]), np.array([[1., 0.], [.5, .5], [0., 1.]])), [0, .5, 1])
    frame = pd.DataFrame([[1, 1, 5, 1], [1, 2, 2, 2], [2, 3, 5, 1]],
                         columns=["user_id", "item_id", "rating", "timestamp"])
    future = pd.DataFrame([[1, 3, 5, 3], [1, 99, 5, 4], [9, 1, 5, 4]], columns=frame.columns)
    dataset = SimpleNamespace(field2token_id={"item_id": {"[PAD]": 0, "1": 1, "2": 2, "3": 3}})
    genres = pd.DataFrame([[1., 0.], [0., 1.], [.5, .5]], index=[1, 2, 3])
    cases, counts = make_cases(frame, future, frame, genres, dataset, 1)
    assert len(cases) == 1 and cases[0]["positives"] == {3}
    assert cases[0]["sequence"] == [1, 2] and cases[0]["available"].tolist() == [3]
    assert counts["cold_user_users"] == 1 and counts["cold_item_events"] == 1
    np.testing.assert_array_equal(cases[0]["profile"], [1, 0])

    case = {"ids": np.arange(10, 16), "r": np.array([1., .9, .8, .6, .4, .2]),
            "d": np.array([0., .2, .4, .6, .8, 1.]), "positives": {10, 99}}
    # Optimization must work without the diagnostic product or future labels.
    starts, _ = baselines(case, 2)
    assert set(starts) == {"sasrec", *[f"weighted_distance:{w:.1f}" for w in np.linspace(0, 1, 11)]}
    all_lists = [np.array(idx) for idx in combinations(range(6), 2)]
    expected = np.round([[sum(case["r"][idx]) / 2, sum(case["d"][idx]) / 2] for idx in all_lists], 12)
    np.testing.assert_allclose(objectives(case, all_lists), expected)
    binary = np.zeros((len(all_lists), 6), dtype=bool)
    for row, idx in zip(binary, all_lists):
        row[idx] = True
    problem = SubsetProblem(case["r"], case["d"], 2)
    np.testing.assert_allclose(-problem.evaluate(binary), expected)
    almost_equal = SubsetProblem(np.array([.6, .2, .4 + 1e-16, .4]), np.array([.1, .1, .8, .8]), 2)
    costs = almost_equal.evaluate(np.array([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=bool))
    assert costs[0, 0] == costs[1, 0]
    assert NonDominatedSorting().do(costs, only_non_dominated_front=True).tolist() == [1]
    for weight in np.linspace(0, 1, 11):
        idx = starts[f"weighted_distance:{weight:.1f}"]
        assert len(idx) == len(set(case["ids"][idx])) == 2
        actual = (weight * case["r"][idx] + (1 - weight) * case["d"][idx]).mean()
        assert np.isclose(actual, (expected @ [weight, 1 - weight]).max())
    repair = FixedSizeRepair()._do(problem, np.array([[True] * 6, [False] * 6]))
    assert np.all(repair.sum(axis=1) == 2)
    config = {"top_k": 2, "population": 40, "generations": 3, "relevance_floor": .95}
    front, chosen, _ = evolve(case, starts, config, 42)
    exact = [i for i, point in enumerate(expected)
             if not any(np.all(other >= point) and np.any(other > point) for other in expected)]
    assert set(NonDominatedSorting().do(problem.evaluate(binary), only_non_dominated_front=True)) == set(exact)
    assert {tuple(x) for x in front} == {tuple(all_lists[i]) for i in exact}
    assert all(len(idx) == len(set(case["ids"][idx])) == 2 for idx in front)
    again, selected, _ = evolve(case, starts, config, 42)
    assert [tuple(x) for x in front] == [tuple(x) for x in again] and chosen == selected
    assert objectives(case, front)[chosen, 0] >= .95 * case["r"][:2].mean()
    assert chosen == representative(case, front, .95, 2)
    scalar_lists = [idx for name, idx in starts.items() if name.startswith("weighted_distance:")]
    scalar_choice = representative(case, scalar_lists, .95, 2)
    assert case["r"][scalar_lists[scalar_choice]].mean() >= .95 * case["r"][:2].mean()
    # Distance wins within the floor, then relevance, then lexicographic item IDs.
    ties = {"ids": np.array([10, 40, 30, 20, 50]), "r": np.array([1., .98, .96, .95, .94]),
            "d": np.array([0., .9, .9, .9, 1.])}
    choices = [np.array([i]) for i in range(5)]
    assert representative(ties, choices, .95, 1) == 1
    ties["r"][1] = .96
    assert representative(ties, choices, .95, 1) == 2
    changed_labels = {**case, "positives": {12, 13, 14, 15}}
    other, selected_other, _ = evolve(changed_labels, starts, config, 42)
    assert [tuple(x) for x in front] == [tuple(x) for x in other] and chosen == selected_other
    unlabeled = {key: value for key, value in case.items() if key != "positives"}
    unlabeled_starts, _ = baselines(unlabeled, 2)
    other, selected_other, _ = evolve(unlabeled, unlabeled_starts, config, 42)
    assert [tuple(x) for x in front] == [tuple(x) for x in other] and chosen == selected_other
    single = {"ids": np.array([4]), "r": np.array([1.]), "d": np.array([0.])}
    only, _, _ = evolve(single, {"sasrec": np.array([0])}, {**config, "top_k": 1}, 42)
    assert only[0].tolist() == [0]
    case["s"] = case["r"] * case["d"]
    scores = evaluate_list(case, np.array([1, 0]), 2)
    assert scores["recall"] == .5 and scores["candidate_recall"] == .5
    assert np.isclose(scores["ndcg"], 1 / (1 + 1 / np.log2(3)))
    assert scores["heldout_distance"] == 0
    try:
        problem.evaluate(np.ones((1, 6), dtype=bool))
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid subset cardinality was accepted")
    print("PASS: history-only centering, positive-definition checkpoint guard, time leakage, warm catalog, genre distance, exact objectives/front, scalarization, repair, seeds, held-out metrics")


def check_artifacts(run):
    config = json.loads((run / "config.json").read_text())
    assert json.loads((run / "completion.json").read_text())["status"] == "complete"
    if not config["smoke"]:
        changed = {**config, "model_selection_k": config.get("model_selection_k", config["top_k"]) + 1}
        try:
            reuse_model(run, None, None, changed, run)
        except ValueError as error:
            assert str(error) == "Checkpoint model-selection metric does not match"
        else:
            raise AssertionError("Checkpoint reuse accepted a different model-selection metric")
    assignments = pd.read_csv(run / "split_assignments.csv")
    train = assignments[assignments.split == "train"]
    valid = assignments[assignments.split == "validation"]
    test = assignments[assignments.split == "test"]
    assert len(assignments) == 100000
    assert train.timestamp.max() < valid.timestamp.min() <= valid.timestamp.max() < test.timestamp.min()
    k = config["top_k"]
    for stage in ["validation", "test"]:
        history = train if stage == "validation" else pd.concat([train, valid])
        candidates = pd.read_csv(run / stage / "candidates.csv")
        recs = pd.read_csv(run / stage / "recommendations.csv")
        seen = set(zip(history.user_id, history.item_id))
        assert not seen & set(zip(candidates.user_id, candidates.item_id))
        assert set(candidates.item_id) <= set(train.item_id)
        assert not candidates.duplicated(["user_id", "item_id"]).any()
        assert (recs.groupby(["user_id", "method", "seed"]).size() == k).all()
        assert not recs.duplicated(["user_id", "method", "seed", "item_id"]).any()
        joined = recs.merge(candidates, on=["user_id", "item_id"], validate="many_to_one")
        assert len(joined) == len(recs)
        np.testing.assert_allclose(candidates.s_proxy, candidates.relevance_rank * candidates.genre_distance)
        for _, group in joined.groupby(["user_id", "method", "seed"]):
            assert group.sort_values("rank").sasrec_score.is_monotonic_decreasing
        front = pd.read_csv(run / stage / "pareto.csv")
        baseline = pd.read_csv(run / stage / "per_user.csv")
        baseline = baseline[baseline.method == "sasrec"].set_index("user_id")
        for (user, seed), group in front.groupby(["user_id", "seed"]):
            values = group[["relevance", "genre_distance"]].to_numpy()
            assert len(NonDominatedSorting().do(-values, only_non_dominated_front=True)) == len(values)
            pool = candidates[candidates.user_id == user].set_index("item_id")
            for row in group.itertuples():
                ids = list(map(int, row.item_ids.split()))
                assert len(ids) == len(set(ids)) == k
                np.testing.assert_allclose([row.relevance, row.genre_distance],
                                          pool.loc[ids, ["relevance_rank", "genre_distance"]].mean())
            chosen = group[group.selected]
            assert len(chosen) == 1
            assert chosen.relevance.iloc[0] >= config["relevance_floor"] * baseline.loc[user, "relevance"] - 1e-12
            if not config["smoke"]:
                assert seed in config["search_seeds"]
        scores = pd.read_csv(run / stage / "per_user.csv")
        assert not scores.method.str.startswith("weighted_proxy").any()
        assert set(pd.read_csv(run / stage / "summary.csv").method) == set(COMPARISON_METHODS)
        bootstrap = pd.read_csv(run / stage / "paired_bootstrap.csv")
        assert set(zip(bootstrap.method, bootstrap.reference)) == {
            ("weighted_distance_selected", "sasrec"), ("nsga2", "sasrec"), ("nsga2", "weighted_distance_selected")}
        assert set(bootstrap.metric) == {"recall", "ndcg", "relevance", "genre_distance", "heldout_distance", "seconds"}
        for user, group in scores.groupby("user_id"):
            floor = config["relevance_floor"] * baseline.loc[user, "relevance"]
            scalar = group[group.method.str.startswith("weighted_distance:")]
            feasible = scalar[scalar.relevance >= floor - 1e-12]
            selected = group[group.method == "weighted_distance_selected"].iloc[0]
            assert selected.relevance >= floor - 1e-12
            assert np.isclose(selected.genre_distance, feasible.genre_distance.max())
        # Candidate coverage is identical across all methods; test misses remain misses.
        assert (scores.groupby("user_id").candidate_recall.nunique() == 1).all()
        assert scores.ndcg.between(0, 1).all() and scores.recall.between(0, 1).all()
    print(f"PASS artifacts: {run} (splits, catalog, histories, cardinality, score order, nondominance, selection floor)")


if __name__ == "__main__":
    check()
    if len(sys.argv) > 1:
        check_artifacts(Path(sys.argv[1]))
