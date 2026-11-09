"""Authenticate the complete P01.4 candidate without rewriting predecessor pins."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_p015_hash


def test_all_63_historical_transitions_unchanged():
    entries = updater.reviewed_transitions()
    assert len(entries) == 77
    assert hashlib.sha256(json.dumps(entries[:63], sort_keys=True).encode()).hexdigest() == (
        "3f7521d55f8836769937a921b45afe58b0aacd506d00709872ef8f5759d48ea2"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    transition = next(
        t
        for t in updater.reviewed_transitions()
        if t["id"] == "p014_upload_outcomes_optional_io_v1"
    )
    before, after, known = {}, {}, {}
    for member in transition["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert before_p015_hash(root, path) == member["after_sha256"], path
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


def test_exact_candidate_and_unchanged_dependencies_admitted(pair):
    before, after = pair
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    changed = {p for p in after if before[p] != after[p]}
    assert set(after) == updater.P014_UPLOAD_PATHS
    assert before["services/optional_upload_observations.py"] is None
    assert before["core/owned_work.py"] == after["core/owned_work.py"]
    updater.check_transition_inventory(changed, read, "before", "after")
    updater.check_source_only(changed, read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P014_UPLOAD_PATHS))
@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing"])
def test_every_candidate_member_is_exact(pair, path, damage):
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


def test_old_installed_reader_cannot_accept_new_target(pair, monkeypatch):
    before, after = pair
    installed = [
        t
        for t in updater.reviewed_transitions()
        if t["id"] != "p014_upload_outcomes_optional_io_v1"
    ]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")


@pytest.mark.parametrize("damage", ["missing_member", "extra_transition", "wrong_member"])
def test_registry_family_and_count_remain_fixed(monkeypatch, damage):
    registry = json.loads(
        Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes()
    )
    item = next(
        t for t in registry["transitions"] if t["id"] == "p014_upload_outcomes_optional_io_v1"
    )
    if damage == "missing_member":
        item["members"].pop()
    elif damage == "extra_transition":
        registry["transitions"].append(item)
    else:
        item["members"][0]["path"] = "services/unreviewed.py"
    monkeypatch.setattr(Path, "read_bytes", lambda _: json.dumps(registry).encode())
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
