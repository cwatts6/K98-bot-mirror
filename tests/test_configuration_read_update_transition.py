"""Only the complete, exact configuration read recovery patch is admitted."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def bundle():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "configuration_read_request_v1"
    )


def test_configuration_read_transition_pins_current_sources():
    transition = bundle()
    assert {m["path"] for m in transition["members"]} == updater.CONFIGURATION_READ_REQUEST_PATHS
    root = Path(__file__).resolve().parents[1]
    for member in transition["members"]:
        expected = member["after_sha256"]
        for successor in updater.reviewed_transitions():
            if successor["id"] not in {"configuration_intent_replay_v1", "publication_detail_v1"}:
                continue
            for update in successor["members"]:
                if update["path"] == member["path"]:
                    assert update["before_sha256"] == expected
                    expected = update["after_sha256"]
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")) == expected
        )
        assert member["before_sha256"] and member["before_sha256"] != member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed", "duplicate"])
def test_partial_or_foreign_configuration_read_transition_refused(tmp_path, monkeypatch, damage):
    transition = deepcopy(bundle())
    if damage == "missing":
        transition["members"].pop()
    elif damage == "extra":
        transition["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "duplicate":
        transition["members"].append(transition["members"][0])
    else:
        transition["id"] = "foreign_configuration_read"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[transition]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


@pytest.mark.parametrize("damage", [None, "before", "after", "missing"])
def test_transition_checks_every_member_on_both_sides(monkeypatch, damage):
    transition = deepcopy(bundle())
    values = {}
    for i, member in enumerate(transition["members"]):
        for revision, field in (("old", "before_sha256"), ("new", "after_sha256")):
            raw = f"{revision}-{i}".encode()
            values[revision, member["path"]] = raw
            member[field] = updater.sha256(raw)
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [transition])
    last = transition["members"][-1]["path"]
    if damage:
        values["old" if damage == "before" else "new", last] = (
            None if damage == "missing" else b"changed"
        )
    read = lambda revision, path: values[revision, path]
    first = transition["members"][0]["path"]
    if damage:
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(first, read, "old", "new")
    else:
        assert (
            updater.check_protocol_transition(first, read, "old", "new")
            == updater.CONFIGURATION_READ_REQUEST_PATHS
        )
