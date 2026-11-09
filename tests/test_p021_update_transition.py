"""Exact P02.1 source family; no target-controlled policy or partial update."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def transition():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "p021_observer_snapshots_v1"
    )


def test_all_67_predecessor_entries_remain_unchanged():
    entries = updater.reviewed_transitions()
    assert len(entries) == 78
    assert hashlib.sha256(json.dumps(entries[:67], sort_keys=True).encode()).hexdigest() == (
        "c567936cdac7aca194c86065b4ff75da4e3982810bfc083801e524c4198f7e2f"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    before, after, known = {}, {}, {}
    for member in transition()["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        from tests.updater_source_assertions import before_phase1_hash

        assert before_phase1_hash(root, path) == member["after_sha256"], path
        if updater.sha256(after[path]) != member["after_sha256"]:
            # Exact historical P02.1 reference; never claim current Phase 1
            # bytes can be installed under the earlier release definition.
            after[path] = ("inert P02.1 reference:" + path).encode()
            known[after[path]] = member["after_sha256"]
        if member["before_sha256"] is None:
            before[path] = None
        else:
            before[path] = ("inert predecessor:" + path).encode()
            known[before[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return before, after


def test_complete_candidate_and_new_helpers_required(pair):
    before, after = pair
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    assert set(after) == updater.P021_OBSERVER_SNAPSHOT_PATHS
    assert {p for p, raw in before.items() if raw is None} == {
        "core/recovery_sql_snapshot.py",
        "services/legacy_snapshot_admission.py",
    }
    updater.check_transition_inventory(set(after), read, "before", "after")
    updater.check_source_only(set(after), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P021_OBSERVER_SNAPSHOT_PATHS))
@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing", "omitted_inventory"])
def test_every_member_and_inventory_are_exact(pair, path, damage):
    before, after = pair
    changed = set(after)
    if damage == "predecessor":
        before[path] = b"unreviewed predecessor"
    elif damage == "postimage":
        after[path] += b"# unreviewed bytes"
    elif damage == "missing":
        del after[path]
    else:
        changed.remove(path)
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(changed, read, "before", "after")


def test_installed_predecessor_refuses_new_family(pair, monkeypatch):
    before, after = pair
    installed = [t for t in updater.reviewed_transitions() if t["id"] != transition()["id"]]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")


@pytest.mark.parametrize("path", sorted(updater.P021_OBSERVER_SNAPSHOT_PATHS))
def test_history_bridge_rejects_drift(path, monkeypatch):
    from tests.updater_source_assertions import before_p021_hash

    root = Path(__file__).resolve().parents[1]
    member = next(m for m in transition()["members"] if m["path"] == path)
    assert before_p021_hash(root, path) == member["before_sha256"]
    original = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: original(p) + b"# unreviewed" if p == root / path else original(p),
    )
    with pytest.raises(AssertionError, match=path):
        before_p021_hash(root, path)
