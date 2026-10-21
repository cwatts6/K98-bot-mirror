"""Only a complete exact diagnostic runtime bundle crosses the protected update boundary."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def bundle():
    return next(t for t in updater.reviewed_transitions() if t["id"] == "publication_detail_v1")


def test_complete_detail_runtime_matches_actual_sources_and_prior_reconciliation():
    item = bundle()
    assert {m["path"] for m in item["members"]} == updater.PUBLICATION_DETAIL_PATHS
    root = Path(__file__).resolve().parents[1]
    previous = next(
        t for t in updater.reviewed_transitions() if t["id"] == "configuration_intent_replay_v1"
    )
    prior = {m["path"]: m["after_sha256"] for m in previous["members"]}
    successor = next(
        t for t in updater.reviewed_transitions() if t["id"] == "publication_readback_batches_v1"
    )
    for member in item["members"]:
        expected = member["after_sha256"]
        for update in successor["members"]:
            if update["path"] == member["path"]:
                assert update["before_sha256"] == expected
                expected = update["after_sha256"]
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")) == expected
        )
        assert member["before_sha256"] != member["after_sha256"]
        if member["path"] in prior:
            assert member["before_sha256"] == prior[member["path"]]


@pytest.mark.parametrize("damage", ["missing", "extra", "duplicate", "invalid_hash"])
def test_partial_or_corrupt_detail_transition_is_refused(tmp_path, monkeypatch, damage):
    item = deepcopy(bundle())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "duplicate":
        item["members"].append(item["members"][0])
    else:
        item["members"][0]["after_sha256"] = "not a hash"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
