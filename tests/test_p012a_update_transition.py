"""The installed updater requires the entire exact P01.2a source transition."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def transition():
    return next(t for t in updater.reviewed_transitions() if t["id"] == "p012a_evidence_bundle_v1")


@pytest.fixture
def source_pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    members = transition()["members"]
    old = {
        m["path"]: None if m["before_sha256"] is None else ("prior:" + m["path"]).encode()
        for m in members
    }
    after = {m["path"]: (root / m["path"]).read_bytes() for m in members}
    original_hash = updater.sha256
    historical_hashes = {
        old[m["path"]]: m["before_sha256"] for m in members if old[m["path"]] is not None
    }
    monkeypatch.setattr(
        updater, "sha256", lambda raw: historical_hashes.get(raw, original_hash(raw))
    )
    return old, after


def test_complete_actual_candidate_and_inventory_are_required(source_pair):
    old, after = source_pair
    read = lambda commit, path: (old if commit == "before" else after).get(path)
    assert set(after) == updater.P012A_EVIDENCE_BUNDLE_PATHS
    assert old["services/recovery_evidence_bundle.py"] is None
    assert old["services/startup_outcome_projection.py"] is None
    for path in after:
        assert updater.check_protocol_transition(path, read, "before", "after") == set(after)
    updater.check_transition_inventory(set(after), read, "before", "after")
    updater.check_source_only(set(after), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P012A_EVIDENCE_BUNDLE_PATHS))
@pytest.mark.parametrize("damage", ["changed", "missing", "predecessor", "inventory"])
def test_each_peer_is_authenticated_and_inventory_cannot_omit_it(source_pair, path, damage):
    old, after = source_pair
    inventory = set(after)
    if damage == "changed":
        after[path] += b"\n# drift\n"
    elif damage == "missing":
        after.pop(path)
    elif damage == "predecessor":
        old[path] = b"unreviewed predecessor"
    else:
        inventory.remove(path)
    read = lambda commit, member: (old if commit == "before" else after).get(member)
    with pytest.raises(ValueError, match=r"not installed/reviewed|Incomplete reviewed"):
        updater.check_transition_inventory(inventory, read, "before", "after")


def test_target_cannot_authorize_transition_when_installed_registry_lacks_it(
    source_pair, monkeypatch
):
    old, after = source_pair
    installed = [t for t in updater.reviewed_transitions() if t["id"] != "p012a_evidence_bundle_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda commit, path: (old if commit == "before" else after).get(path)
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition("core/owned_work.py", read, "before", "after")


def test_registry_requires_fixed_complete_family(monkeypatch):
    value = json.loads(Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes())
    item = next(t for t in value["transitions"] if t["id"] == "p012a_evidence_bundle_v1")
    item["members"].pop()
    raw = json.dumps(deepcopy(value)).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda _: raw)
    with pytest.raises(ValueError, match=r"Complete fixed P01\.2a"):
        updater.reviewed_transitions()


def test_historical_bridge_requires_successor_for_its_own_source_family(monkeypatch):
    from tests.updater_source_assertions import before_p012a_hash

    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [])
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(AssertionError, match="Required p012a_evidence_bundle_v1"):
        before_p012a_hash(root, "core/owned_work.py")
