"""The installed updater admits only the complete reviewed P03a.2 source pair."""

from copy import deepcopy
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.test_updater_transition_inventory import AFTER, BEFORE
from tests.updater_source_assertions import before_startup_evidence_hash


@pytest.mark.parametrize("identity", sorted(updater.REQUEST_SETTLEMENT_TRANSITIONS))
def test_settlement_bundle_pins_every_actual_runtime_dependency(identity):
    root = Path(__file__).resolve().parents[1]
    item = next(t for t in updater.reviewed_transitions() if t["id"] == identity)
    assert {m["path"] for m in item["members"]} == updater.REQUEST_SETTLEMENT_PATHS
    for member in item["members"]:
        assert before_startup_evidence_hash(root, member["path"]) == member["after_sha256"]


@pytest.mark.parametrize(
    "damage", [None, "omitted", "altered_dependency", "partial_registry", "uninstalled"]
)
def test_settlement_source_preparation_requires_complete_installed_pair(monkeypatch, damage):
    item = deepcopy(
        next(t for t in updater.reviewed_transitions() if t["id"] == "request_settlement_v1")
    )
    blobs = {}
    for member in item["members"]:
        unchanged = member["before_sha256"] == member["after_sha256"]
        for revision, field in ((BEFORE, "before_sha256"), (AFTER, "after_sha256")):
            identity = "unchanged" if unchanged else revision
            raw = None if member[field] is None else f"# {identity}:{member['path']}\n".encode()
            blobs[revision, member["path"]] = raw
            member[field] = updater.sha256(raw) if raw is not None else None
    paths = sorted(updater.REQUEST_SETTLEMENT_PATHS)
    changed = [path for path in paths if blobs[BEFORE, path] != blobs[AFTER, path]]
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {
                path: updater.sha256(blobs[BEFORE, path])
                for path in paths
                if blobs[BEFORE, path] is not None
            }
        }
    }
    monkeypatch.setattr(updater, "coordinated_policy", lambda: None)
    if damage == "omitted":
        changed.remove("services/export_request_settlement.py")
    if damage == "altered_dependency":
        blobs[AFTER, "services/export_execution_protocol.py"] = b"# unreviewed\n"
    if damage == "partial_registry":
        item["members"].pop()
        import json

        monkeypatch.setattr(
            Path, "read_bytes", lambda _: json.dumps(dict(version=1, transitions=[item])).encode()
        )
        with pytest.raises(ValueError, match="Complete fixed"):
            updater.reviewed_transitions()
        return
    monkeypatch.setattr(
        updater, "reviewed_transitions", lambda: [] if damage == "uninstalled" else [item]
    )
    read = lambda revision, path: blobs.get((revision, path))
    if damage:
        with pytest.raises(ValueError):
            updater.source_plan(previous, BEFORE, AFTER, changed, read)
    else:
        plan, payload = updater.source_plan(previous, BEFORE, AFTER, changed, read)
        assert set(payload) == set(changed)
        assert {row["path"] for row in plan["source_members"]} == set(changed)
        assert set(plan["new_pins"]) == set(paths)
