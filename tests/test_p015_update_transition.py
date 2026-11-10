"""Exact local calendar successor; predecessor release hashes remain immutable."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_p016_hash


def test_all_64_historical_transitions_unchanged():
    entries = updater.reviewed_transitions()
    assert len(entries) == 86
    assert (
        hashlib.sha256(json.dumps(entries[:64], sort_keys=True).encode()).hexdigest()
        == "a5807e2a3f3e7e2eade256b4118630c78887b74bd3584d245ce0e286fda9c763"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    transition = next(
        t for t in updater.reviewed_transitions() if t["id"] == "p015_calendar_ownership_v1"
    )
    before, after, known = {}, {}, {}
    for member in transition["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert before_p016_hash(root, path) == member["after_sha256"], path
        known[after[path]] = member["after_sha256"]
        if member["before_sha256"] == member["after_sha256"]:
            before[path] = after[path]
        elif member["before_sha256"] is None:
            before[path] = None
        else:
            before[path] = ("inert predecessor:" + path).encode()
            known[before[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return before, after


def test_complete_candidate_admitted(pair):
    before, after = pair
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    changed = {p for p in after if before[p] != after[p]}
    assert set(after) == updater.P015_CALENDAR_PATHS
    updater.check_transition_inventory(changed, read, "before", "after")
    updater.check_source_only(changed, read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P015_CALENDAR_PATHS))
@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing"])
def test_every_member_is_exact(pair, path, damage):
    before, after = pair
    changed = {p for p in after if before[p] != after[p]}
    if damage == "predecessor":
        before[path] = b"unreviewed predecessor"
    elif damage == "postimage":
        after[path] += b"# unreviewed postimage"
    else:
        del after[path]
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(changed, read, "before", "after")


def test_old_reader_refuses_new_candidate(pair, monkeypatch):
    before, after = pair
    installed = [
        t for t in updater.reviewed_transitions() if t["id"] != "p015_calendar_ownership_v1"
    ]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")
