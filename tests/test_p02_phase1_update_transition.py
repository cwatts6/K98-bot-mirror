"""Complete exact Phase 1 source package; no installed policy widening."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


def transition():
    return next(t for t in updater.reviewed_transitions() if t["id"] == "p02_phase1_sql_exports_v1")


def test_all_68_prior_definitions_are_immutable():
    entries = updater.reviewed_transitions()
    assert len(entries) == 69
    assert hashlib.sha256(json.dumps(entries[:68], sort_keys=True).encode()).hexdigest() == (
        "e597ff1675273105575034624721bd81205a795e6d9fde30cc96ffa8d4f113b5"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    before, after, known = {}, {}, {}
    for member in transition()["members"]:
        path = member["path"]
        after[path] = (root / path).read_bytes().replace(b"\r\n", b"\n")
        assert updater.sha256(after[path]) == member["after_sha256"], path
        before[path] = (
            None if member["before_sha256"] is None else ("inert predecessor:" + path).encode()
        )
        if before[path] is not None:
            known[before[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return before, after


def test_entire_phase1_family_is_admitted_together(pair):
    before, after = pair
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    assert set(after) == updater.P02_PHASE1_SQL_EXPORT_PATHS
    assert len(after) == 25
    assert {p for p, raw in before.items() if raw is None} == {
        "core/recovery_sql_snapshot.py",
        "services/legacy_snapshot_admission.py",
        "core/export_numeric.py",
        "services/export_output_dal.py",
        "services/export_phase1_contract.py",
        "deploy/p02_phase1_activation_scope.json",
        "deploy/p02_phase1_application_sources.json",
        "deploy/p02_phase1_legacy_source.json",
    }
    updater.check_transition_inventory(set(after), read, "before", "after")
    updater.check_source_only(set(after), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P02_PHASE1_SQL_EXPORT_PATHS))
@pytest.mark.parametrize("damage", ["predecessor", "postimage", "missing", "omitted_inventory"])
def test_every_dependency_and_inventory_is_exact(pair, path, damage):
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


def test_installed_predecessor_still_refuses_phase1(pair, monkeypatch):
    before, after = pair
    old = [t for t in updater.reviewed_transitions() if t["id"] != transition()["id"]]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: old)
    read = lambda revision, path: (before if revision == "before" else after).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(after), read, "before", "after")


@pytest.mark.parametrize("damage", ["missing", "extra", "duplicate", "renamed"])
def test_registry_cannot_widen_or_partially_describe_phase1(monkeypatch, damage):
    item = deepcopy(transition())
    if damage == "missing":
        item["members"].pop()
    elif damage == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    elif damage == "duplicate":
        item["members"].append(dict(item["members"][0]))
    else:
        item["id"] = "p02_phase1_unreviewed"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError):
        updater.reviewed_transitions()


@pytest.mark.parametrize("path", sorted(updater.P02_PHASE1_SQL_EXPORT_PATHS))
def test_history_bridge_authenticates_actual_phase1_bytes(path, monkeypatch):
    from tests.updater_source_assertions import before_phase1_hash

    root = Path(__file__).resolve().parents[1]
    before_phase1_hash(root, path)
    original = Path.read_bytes
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda p: original(p) + b"# unreviewed" if p == root / path else original(p),
    )
    with pytest.raises(AssertionError, match=path):
        before_phase1_hash(root, path)
