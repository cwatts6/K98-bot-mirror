"""The installed updater admits exactly the reviewed intent and replay bundle."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def bundle():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "configuration_intent_replay_v1"
    )


def test_complete_runtime_is_pinned_to_actual_sources():
    item = bundle()
    assert {m["path"] for m in item["members"]} == updater.CONFIGURATION_INTENT_REPLAY_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed", "duplicate"])
def test_partial_or_unreviewed_transition_is_refused(tmp_path, monkeypatch, damage):
    item = deepcopy(bundle())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "renamed":
        item["id"] = "unreviewed_intent_replay"
    else:
        item["members"].append(item["members"][0])
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
