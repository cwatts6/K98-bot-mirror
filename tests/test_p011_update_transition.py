"""The P01.1 updater exception admits only the complete reviewed source pair."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_p012a_hash


def transition():
    return next(
        row for row in updater.reviewed_transitions() if row["id"] == "p011_startup_outcomes_v1"
    )


@pytest.fixture
def source_pair(monkeypatch):
    members = transition()["members"]
    root = Path(__file__).resolve().parents[1]
    old = {
        row["path"]: None if row["before_sha256"] is None else ("prior:" + row["path"]).encode()
        for row in members
    }
    after = {row["path"]: (root / row["path"]).read_bytes() for row in members}
    original_hash = updater.sha256
    hashes = {
        raw.replace(b"\r\n", b"\n"): before_p012a_hash(root, path) for path, raw in after.items()
    }
    hashes.update(
        {old[row["path"]]: row["before_sha256"] for row in members if old[row["path"]] is not None}
    )
    # Fixtures stand in only for historical bytes. Successor bytes use real SHA256.
    monkeypatch.setattr(updater, "sha256", lambda raw: hashes.get(raw, original_hash(raw)))
    return old, after


def test_complete_runtime_inventory_matches_pinned_successor(source_pair):
    old, after = source_pair
    read = lambda commit, path: (old if commit == "before" else after).get(path)
    assert (
        updater.check_protocol_transition("core/owned_work.py", read, "before", "after")
        == updater.P011_STARTUP_OUTCOME_PATHS
    )
    updater.check_transition_inventory(set(after), read, "before", "after")
    updater.check_source_only(set(after), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("mutation", ["changed_peer", "missing_peer", "wrong_predecessor"])
def test_unknown_or_incomplete_source_is_refused(source_pair, mutation):
    old, after = source_pair
    if mutation == "wrong_predecessor":
        old["core/owned_work.py"] = b"different deployed source"
    elif mutation == "missing_peer":
        after.pop("services/operation_diagnostics.py")
    else:
        after["core/operation_evidence.py"] += b"\n# drift\n"
    read = lambda commit, path: (old if commit == "before" else after).get(path)
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition("core/owned_work.py", read, "before", "after")


def test_registry_cannot_omit_or_add_a_family_member(monkeypatch):
    value = json.loads(Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes())
    item = next(row for row in value["transitions"] if row["id"] == "p011_startup_outcomes_v1")
    item["members"].pop()
    raw = json.dumps(deepcopy(value)).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda _: raw)
    with pytest.raises(ValueError, match=r"Complete fixed P01\.1"):
        updater.reviewed_transitions()
