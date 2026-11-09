"""Exact personal-stats successor, preserving all prior release transitions."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_d2a_hash


def test_all_66_historical_transitions_unchanged():
    entries = updater.reviewed_transitions()
    assert len(entries) == 73
    assert hashlib.sha256(json.dumps(entries[:66], sort_keys=True).encode()).hexdigest() == (
        "1d31dce46f54023a020f8e34373deaf2084356747f20200190794d629a155f78"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    transition = next(
        t
        for t in updater.reviewed_transitions()
        if t["id"] == "p016_personal_stats_render_submission_v1"
    )
    before, after, known = {}, {}, {}
    for member in transition["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert before_d2a_hash(root, path) == member["after_sha256"], path
        if updater.sha256(after[path]) != member["after_sha256"]:
            after[path] = ("inert P01.6 reference:" + path).encode()
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
    assert set(after) == updater.P016_PERSONAL_STATS_PATHS
    updater.check_transition_inventory(changed, read, "before", "after")
    updater.check_source_only(changed, read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P016_PERSONAL_STATS_PATHS))
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
        t
        for t in updater.reviewed_transitions()
        if t["id"] != "p016_personal_stats_render_submission_v1"
    ]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")


@pytest.mark.parametrize(
    "path", ["player_self_service/stats_runtime.py", "ui/views/player_self_service_stats_views.py"]
)
def test_historical_bridge_authenticates_render_successor_before_original_assertion(
    path, monkeypatch
):
    from tests.updater_source_assertions import before_p016_hash

    root = Path(__file__).resolve().parents[1]
    original = next(
        t for t in updater.reviewed_transitions() if t["id"] == "p016_personal_stats_ownership_v1"
    )
    member = next(m for m in original["members"] if m["path"] == path)
    assert before_p016_hash(root, path) == member["before_sha256"]
    read_bytes = Path.read_bytes

    def changed_bytes(file):
        raw = read_bytes(file)
        return raw + b"# unreviewed bytes" if file == root / path else raw

    monkeypatch.setattr(Path, "read_bytes", changed_bytes)
    with pytest.raises(AssertionError, match=path):
        before_p016_hash(root, path)
