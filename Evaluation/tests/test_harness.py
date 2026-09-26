"""Leakage checks for the evaluation harness, on a small synthetic table.

Run:  .venv\\Scripts\\python.exe -m pytest tests   (or: .venv\\Scripts\\python.exe tests\\test_harness.py)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from v2k.evaluate import make_folds, oversample, score, select, subsample_tasks  # noqa: E402
from v2k.segments import (BLOCK_DIMS, FeatureBuilder, SegmentTable, TaskInfo,  # noqa: E402
                          parse_feature_set, pool_to_tasks)


def _table(n_tasks: int = 12, segs_per_task: int = 3) -> tuple[SegmentTable, dict[int, str]]:
    rng = np.random.RandomState(0)
    task_id, seg, text = [], [], []
    tasks, labels = {}, {}
    for t in range(n_tasks):
        label = ["alpha", "beta", "gamma"][t % 3]
        words = [f"{label}word", f"task{t}only"]
        for s in range(segs_per_task):
            task_id.append(t)
            seg.append(s)
            text.append(" ".join(words))
        tasks[t] = TaskInfo(t, "App", "App", f"instruction {label}", label,
                            [" ".join(words)] * segs_per_task, [" ".join(words)] * segs_per_task, segs_per_task)
        labels[t] = label
    n = len(task_id)
    blocks = {b: rng.rand(n, d).astype(np.float32) for b, d in BLOCK_DIMS.items() if not b.startswith("ocr")}
    table = SegmentTable(np.array(task_id), np.array(seg), np.zeros(n), np.ones(n), text, list(text), blocks, tasks)
    return table, labels


def test_folds_never_split_a_task():
    table, labels = _table()
    rows, y, _ = select(table, labels, min_tasks=2)
    groups = table.task_id[rows]
    for tr, te in make_folds(y, groups, k=4, seed=42):
        assert not set(groups[tr]) & set(groups[te])


def test_task_pooling_averages_only_within_a_recording():
    table, _ = _table(n_tasks=6, segs_per_task=3)
    pooled = pool_to_tasks(table)

    assert len(pooled) == 6
    assert list(pooled.task_id) == sorted(table.tasks)
    for row, t in enumerate(pooled.task_id):
        own = table.task_id == t
        for block in pooled.blocks:
            expected = table.blocks[block][own].mean(axis=0)
            assert np.allclose(pooled.blocks[block][row], expected, atol=1e-6)
        # A recording's text must not pick up words from any other recording.
        assert f"task{int(t)}only" in pooled.text[row]
        assert not any(f"task{o}only" in pooled.text[row] for o in table.tasks if o != t)


def test_oversampling_only_repeats_rows_it_was_given():
    rng = np.random.RandomState(1)
    X = rng.rand(120, 4)
    y = np.array([0] * 100 + [1] * 15 + [2] * 5)

    X_bal, y_bal = oversample(X, y, cap=2.0, seed=0)

    from collections import Counter
    counts = Counter(int(c) for c in y_bal)
    # Nothing below half the largest class any more.
    assert min(counts.values()) >= 50 - 1
    # The big class is untouched; only copies were added.
    assert counts[0] == 100
    assert len(X_bal) == len(y_bal) > len(X)
    # Every row is one of the originals - no synthetic points were invented.
    originals = {tuple(np.round(r, 12)) for r in X}
    assert all(tuple(np.round(r, 12)) in originals for r in X_bal)
    # Labels still match their rows after the shuffle.
    lookup = {tuple(np.round(r, 12)): int(c) for r, c in zip(X, y)}
    assert all(lookup[tuple(np.round(r, 12))] == int(c) for r, c in zip(X_bal, y_bal))


def test_sampling_keeps_whole_recordings_and_every_class():
    table, labels = _table(n_tasks=30, segs_per_task=4)
    rows, y, _ = select(table, labels, min_tasks=2)
    kept_rows, kept_y, n_kept = subsample_tasks(table, rows, y, n_tasks=12, seed=1)

    # A sampled recording brings all four of its segments, or the fold split
    # would no longer be able to keep a recording on one side.
    from collections import Counter

    per_task = Counter(int(t) for t in table.task_id[kept_rows])
    assert set(per_task.values()) == {4}
    assert len(per_task) == n_kept < 30
    # Every class survives, so the sample is still scorable.
    assert set(kept_y) == set(y)


def test_merging_joins_only_neighbours_and_keeps_every_step():
    from v2k.sop import Section, Step, merge_adjacent

    def sec(i, start, end, activity, conf, n_steps):
        return Section(index=i, start=start, end=end, activity=activity, confidence=conf,
                       steps=[Step(seconds=start + k, action="CLICK", text=f"s{i}.{k}")
                              for k in range(n_steps)])

    sections = [sec(0, 0, 5, "edit_content", 0.40, 2), sec(1, 6, 9, "edit_content", 0.80, 1),
                sec(2, 10, 12, "navigate_view", 0.50, 1), sec(3, 13, 20, "edit_content", 0.60, 3)]
    merged = merge_adjacent(sections)

    assert [s.activity for s in merged] == ["edit_content", "navigate_view", "edit_content"]
    assert [s.segments for s in merged] == [2, 1, 1]
    # A run is spanned end to end, and the two edit_content runs stay apart.
    assert (merged[0].start, merged[0].end) == (0, 9)
    assert (merged[2].start, merged[2].end) == (13, 20)
    # No step is lost or duplicated, and order is preserved.
    assert sum(len(s.steps) for s in merged) == 7
    assert [st.text for st in merged[0].steps] == ["s0.0", "s0.1", "s1.0"]
    # The merged confidence is the mean over the segments it covers, not the last one.
    assert merged[0].confidence == pytest_approx(0.60)
    assert merged[2].confidence == pytest_approx(0.60)


def pytest_approx(value, tol=1e-9):
    class _Approx:
        def __eq__(self, other):
            return abs(other - value) < tol

        def __repr__(self):
            return f"~{value}"

    return _Approx()


def test_grid_holds_each_library_default_exactly_once():
    from v2k.tune import DEFAULTS, GRIDS, expand

    grid = expand(list(GRIDS))
    # Without the default in the grid, "what tuning bought" has nothing to
    # subtract, and a best score alone cannot be told from a better default.
    for model in GRIDS:
        marked = [c for c in grid if c["model"] == model and c["is_default"]]
        assert len(marked) == 1, f"{model}: {len(marked)} configs marked default"
        assert marked[0]["params"] == DEFAULTS[model]


def test_shards_cover_every_configuration_exactly_once():
    from v2k.tune import GRIDS, expand

    grid = expand(list(GRIDS))
    for n_shards in (1, 4, 5, 7):
        seen = [c["id"] for s in range(n_shards) for c in grid if c["id"] % n_shards == s]
        assert sorted(seen) == [c["id"] for c in grid]
        # Interleaving, not slicing: a slice would put every slow config in one
        # shard and leave the others idle.
        for s in range(n_shards):
            models = {c["model"] for c in grid if c["id"] % n_shards == s}
            assert len(models) > 1 or len(grid) <= n_shards


def test_tfidf_vocabulary_comes_from_training_tasks_only():
    table, labels = _table()
    rows, y, _ = select(table, labels, min_tasks=2)
    groups = table.task_id[rows]
    tr, te = make_folds(y, groups, k=4, seed=42)[0]
    builder = FeatureBuilder(("ocr",), scale=False).fit(table, rows[tr])
    vocab = set(builder._ocr["ocr"]._tfidf.vocabulary_)
    for t in set(groups[te]):
        assert f"task{t}only" not in vocab, "a test task's own word leaked into the vocabulary"


def test_scaler_is_fitted_on_training_rows_only():
    table, labels = _table()
    rows = np.arange(len(table))
    train = rows[: len(rows) // 2]
    table.blocks["visual"][len(rows) // 2:] += 100.0  # test half lives somewhere else entirely
    X_tr = FeatureBuilder(("visual",)).fit(table, train).transform(table, train)
    assert np.allclose(X_tr.mean(axis=0), 0, atol=1e-5)


def test_classes_below_min_tasks_are_dropped():
    table, labels = _table()
    labels[0] = "rare"
    rows, y, dropped = select(table, labels, min_tasks=2)
    assert dropped == {"rare": 1}
    assert "rare" not in set(y)
    assert 0 not in set(table.task_id[rows])


def test_feature_sets_expand_in_backend_order():
    assert parse_feature_set("main150") == ("ocr", "ui", "visual", "interaction")
    assert parse_feature_set("native150+cnn") == ("ocr_native", "ui", "visual", "interaction", "cnn")
    assert FeatureBuilder(parse_feature_set("main150")).dim == 150


def test_task_accuracy_is_a_majority_vote():
    y_true = np.array(["a", "a", "a", "b", "b"], dtype=object)
    y_pred = np.array(["a", "a", "b", "b", "a"], dtype=object)
    groups = np.array([1, 1, 1, 2, 2])
    s = score(y_true, y_pred, groups, [(np.array([0]), np.arange(5))])
    assert s["segment_accuracy"] == 0.6
    assert s["task_accuracy"] in (0.5, 1.0)  # task 2 is a tie; task 1 is right


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok  {name}")
