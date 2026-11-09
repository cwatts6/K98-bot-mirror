"""Exact season observation package and unchanged sealed-result dependencies."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_d2h_hash, before_d2i_hash


def transition():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "p02_d2h_season_observation_v1"
    )


def test_prior_76_transitions_are_immutable():
    entries = updater.reviewed_transitions()
    assert len(entries) == 80
    assert hashlib.sha256(json.dumps(entries[:76], sort_keys=True).encode()).hexdigest() == (
        "bedacf8c4bb61e186e5af770fe5b5e799f694ec9e8eb6c08ca7d58c5d795969d"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    before, after, known = {}, {}, {}
    for member in transition()["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert before_d2i_hash(root, path) == member["after_sha256"], path
        if updater.sha256(after[path]) != member["after_sha256"]:
            after[path] = ("authenticated D2h postimage:" + path).encode()
            known[after[path]] = member["after_sha256"]
        assert before_d2h_hash(root, path) == member["before_sha256"]
        if member["before_sha256"] == member["after_sha256"]:
            before[path] = after[path]
        else:
            before[path] = ("inert D2h predecessor:" + path).encode()
            known[before[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return before, after


def changed_paths(before, after):
    return {path for path in after if before[path] != after[path]}


@pytest.mark.parametrize("crlf", [False, True])
def test_complete_package_and_dependencies_admitted(pair, crlf):
    before, after = pair
    if crlf:
        before = {path: raw.replace(b"\n", b"\r\n") for path, raw in before.items()}
        after = {path: raw.replace(b"\n", b"\r\n") for path, raw in after.items()}
    changed = {
        m["path"] for m in transition()["members"] if m["before_sha256"] != m["after_sha256"]
    }
    assert len(changed) == 3
    assert set(after) == updater.P02_D2H_SEASON_OBSERVATION_PATHS
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    updater.check_transition_inventory(changed, read, "before", "after")
    updater.check_source_only(changed, read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P02_D2H_SEASON_OBSERVATION_PATHS))
@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing"])
def test_changed_and_unchanged_members_are_authenticated(pair, path, damage):
    before, after = pair
    changed = changed_paths(before, after)
    if damage == "predecessor":
        before[path] = b"unreviewed predecessor"
    elif damage == "postimage":
        after[path] += b"# unreviewed postimage"
    else:
        del after[path]
    read = lambda revision, name: (before if revision == "before" else after).get(name)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(changed, read, "before", "after")


def test_partial_inventory_and_old_reader_cannot_admit_package(pair, monkeypatch):
    before, after = pair
    changed = changed_paths(before, after)
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    for path in changed:
        # All changed files are required; partial families cannot authorize a subset.
        with pytest.raises(ValueError):
            updater.source_plan({}, "1" * 40, "2" * 40, list(changed - {path}), read)
    old = [t for t in updater.reviewed_transitions() if t["id"] != transition()["id"]]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: old)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(changed, read, "before", "after")


@pytest.mark.parametrize("damage", ["missing", "extra", "duplicate", "renamed"])
def test_registry_cannot_widen_or_partially_describe_package(monkeypatch, damage):
    item = deepcopy(transition())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    elif damage == "duplicate":
        item["members"].append(dict(item["members"][0]))
    else:
        item["id"] = "p02_d2h_unreviewed"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


@pytest.mark.parametrize("path", sorted(updater.P02_D2H_SEASON_OBSERVATION_PATHS))
def test_historical_bridge_refuses_any_successor_drift(monkeypatch, path):
    root = Path(__file__).resolve().parents[1]
    before_d2h_hash(root, path)
    original = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: original(p) + b"# unreviewed" if p == root / path else original(p),
    )
    with pytest.raises(AssertionError, match=path):
        before_d2h_hash(root, path)
