from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_exact_startup_cache_transition_matches_reviewed_sources():
    transition = next(
        t for t in updater.reviewed_transitions() if t["id"] == "startup_cache_completion_v1"
    )
    assert {m["path"] for m in transition["members"]} == updater.STARTUP_CACHE_COMPLETION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in transition["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("change", ["missing", "extra", "renamed"])
def test_incomplete_or_foreign_startup_transition_refused(tmp_path, monkeypatch, change):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "startup_cache_completion_v1")
    )
    if change == "missing":
        item["members"].pop()
    elif change == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    else:
        item["id"] = "foreign_startup"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
