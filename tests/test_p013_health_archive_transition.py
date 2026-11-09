"""Authenticate the narrow archive successor without rewriting installed history."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def test_historical_62_transitions_remain_immutable():
    entries = updater.reviewed_transitions()
    assert len(entries) == 80
    assert hashlib.sha256(json.dumps(entries[:62], sort_keys=True).encode()).hexdigest() == (
        "4b36fd4a0996b43ebe5e81303b5813ee54f5e0499d9097a487d8273c783648c9"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    entries = updater.reviewed_transitions()
    correction = next(t for t in entries if t["id"] == "p013_health_archive_v1")
    assert {m["path"] for m in correction["members"]} == updater.P013_HEALTH_ARCHIVE_PATHS
    member = correction["members"][0]
    path = member["path"]
    assert member["before_sha256"] == next(
        m["after_sha256"] for t in reversed(entries[:62]) for m in t["members"] if m["path"] == path
    )
    before = b"inert exact predecessor"
    after = (root / path).read_bytes().replace(b"\r\n", b"\n")
    assert hashlib.sha256(after).hexdigest() == member["after_sha256"]
    original = updater.sha256
    monkeypatch.setattr(
        updater, "sha256", lambda raw: member["before_sha256"] if raw == before else original(raw)
    )
    return {path: before}, {path: after}


def test_exact_archive_successor_admitted(pair):
    before, after = pair
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    updater.check_transition_inventory(set(after), read, "before", "after")
    updater.check_source_only(set(after), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing", "unreviewed_peer"])
def test_archive_source_drift_is_refused(pair, damage):
    before, after = pair
    path = next(iter(after))
    inventory = set(after)
    if damage == "predecessor":
        before[path] = b"unexpected predecessor"
    elif damage == "postimage":
        after[path] += b"# unexpected change"
    elif damage == "missing":
        del after[path]
    else:
        peer = "services/recovery_evidence_bundle.py"
        inventory.add(peer)
        before[peer], after[peer] = b"old peer", b"new peer"
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(inventory, read, "before", "after")


def test_old_installed_reader_cannot_use_target_transition(pair, monkeypatch):
    before, after = pair
    installed = [t for t in updater.reviewed_transitions() if t["id"] != "p013_health_archive_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")


@pytest.mark.parametrize("damage", ["wrong_member", "extra_transition"])
def test_registry_correction_is_fixed_and_count_bounded(monkeypatch, damage):
    registry = json.loads(
        Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes()
    )
    if damage == "wrong_member":
        registry["transitions"][-1]["members"][0]["path"] = "services/recovery_report.py"
    else:
        registry["transitions"].append(registry["transitions"][-1])
    monkeypatch.setattr(Path, "read_bytes", lambda _: json.dumps(registry).encode())
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
