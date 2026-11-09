"""Exact, complete passive-health successor; historical authority stays immutable."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_p014_hash


def test_historical_61_transitions_unchanged():
    transitions = updater.reviewed_transitions()
    assert len(transitions) == 78
    assert hashlib.sha256(json.dumps(transitions[:61], sort_keys=True).encode()).hexdigest() == (
        "c161f4d47ee6b9204d51372df908d3a7f9b59d6182e0a8b51e3e97983b769f2e"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    fix = next(t for t in updater.reviewed_transitions() if t["id"] == "p013_passive_health_v1")
    old = {
        m["path"]: ("predecessor:" + m["path"]).encode() if m["before_sha256"] is not None else None
        for m in fix["members"]
    }
    new = {path: (root / path).read_bytes().replace(b"\r\n", b"\n") for path in old}
    known = {}
    for member in fix["members"]:
        path = member["path"]
        assert before_p014_hash(root, path) == member["after_sha256"], path
        known[new[path]] = member["after_sha256"]
        if old[path] is not None:
            known[old[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return old, new


def test_exact_complete_successor_admitted(pair):
    old, new = pair
    read = lambda commit, path: (old if commit == "before" else new).get(path)
    assert set(new) == updater.P013_PASSIVE_HEALTH_PATHS
    assert old["services/health_observation.py"] is None
    assert old["ui/views/health_view.py"] is None
    updater.check_transition_inventory(set(new), read, "before", "after")
    updater.check_source_only(set(new), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P013_PASSIVE_HEALTH_PATHS))
@pytest.mark.parametrize("damage", ["changed", "missing", "predecessor", "inventory"])
def test_every_peer_and_inventory_required(pair, path, damage):
    old, new = pair
    inventory = set(new)
    if damage == "changed":
        new[path] += b"# unreviewed drift"
    elif damage == "missing":
        del new[path]
    elif damage == "predecessor":
        old[path] = b"different predecessor"
    else:
        inventory.remove(path)
    read = lambda commit, member: (old if commit == "before" else new).get(member)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(inventory, read, "before", "after")


def test_target_registry_cannot_authorize_installed_reader(pair, monkeypatch):
    old, new = pair
    installed = [t for t in updater.reviewed_transitions() if t["id"] != "p013_passive_health_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda commit, path: (old if commit == "before" else new).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(new), read, "before", "after")


def test_fixed_family_cannot_be_shortened(monkeypatch):
    value = json.loads(Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes())
    next(t for t in value["transitions"] if t["id"] == "p013_passive_health_v1")["members"].pop()
    monkeypatch.setattr(Path, "read_bytes", lambda _: json.dumps(value).encode())
    with pytest.raises(ValueError, match=r"Complete fixed P01\.3"):
        updater.reviewed_transitions()


def test_registry_remains_size_bounded(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda _: b" " * 207873)
    with pytest.raises(ValueError, match="exceeds bound"):
        updater.reviewed_transitions()
