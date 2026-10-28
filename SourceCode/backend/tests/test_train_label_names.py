"""--load-features names the cached (already renumbered) classes from the cache, not ACTIVITY_LABELS."""
from __future__ import annotations

import json

import pytest

from app.train import cached_label_names


def test_names_come_from_the_file_written_with_the_cache(tmp_path):
    (tmp_path / "feature_labels.json").write_text(json.dumps(["coding_editing", "terminal_ops"]))
    (tmp_path / "label_names.json").write_text(json.dumps(["git_operations", "docker_workflow"]))

    assert cached_label_names(tmp_path) == ["coding_editing", "terminal_ops"]


def test_an_older_cache_falls_back_to_the_models_label_names(tmp_path):
    (tmp_path / "label_names.json").write_text(json.dumps(["coding_editing", "documentation"]))

    assert cached_label_names(tmp_path) == ["coding_editing", "documentation"]


def test_without_any_names_it_stops_instead_of_guessing(tmp_path):
    with pytest.raises(SystemExit, match="feature_labels.json"):
        cached_label_names(tmp_path)
