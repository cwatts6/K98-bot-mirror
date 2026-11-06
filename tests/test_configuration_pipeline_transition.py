"""Updater admits the complete reviewed continuation bundle and no partial patch."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import historical_runtime_hash


def bundle():
    return next(
        t
        for t in updater.reviewed_transitions()
        if t["id"] == "configuration_pipeline_continuation_v1"
    )


def test_pipeline_bundle_pins_complete_runtime():
    item = bundle()
    assert {m["path"] for m in item["members"]} == updater.CONFIGURATION_PIPELINE_CONTINUATION_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert historical_runtime_hash(root, member["path"]) == member["after_sha256"]
        assert member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed", "duplicate"])
def test_incomplete_or_foreign_pipeline_bundle_refused(tmp_path, monkeypatch, damage):
    item = deepcopy(bundle())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "renamed":
        item["id"] = "unreviewed_pipeline"
    else:
        item["members"].append(item["members"][0])
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


@pytest.mark.parametrize("damage", [None, "before", "after", "missing"])
def test_every_pipeline_member_matches_both_revisions(monkeypatch, damage):
    item = deepcopy(bundle())
    values = {}
    for i, member in enumerate(item["members"]):
        for revision, field in (("old", "before_sha256"), ("new", "after_sha256")):
            raw = f"{revision}-{i}".encode()
            values[revision, member["path"]] = raw
            member[field] = updater.sha256(raw)
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    if damage:
        values["old" if damage == "before" else "new", item["members"][-1]["path"]] = (
            None if damage == "missing" else b"foreign"
        )
    read = lambda rev, path: values[rev, path]
    if damage:
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(item["members"][0]["path"], read, "old", "new")
    else:
        assert (
            updater.check_protocol_transition(item["members"][0]["path"], read, "old", "new")
            == updater.CONFIGURATION_PIPELINE_CONTINUATION_PATHS
        )
