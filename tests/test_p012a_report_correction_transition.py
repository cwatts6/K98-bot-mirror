"""Correction is an exact successor; installed evidence-bundle pins stay immutable."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.updater_source_assertions import before_p012a_contract_hash


def test_all_58_deployed_transitions_remain_immutable():
    transitions = updater.reviewed_transitions()
    assert len(transitions) == 85
    assert (
        hashlib.sha256(json.dumps(transitions[:58], sort_keys=True).encode()).hexdigest()
        == "f1f98d3fe67cb67f25cd451693e5522193f97c5a76a449323fdb5afba7b99373"
    )


@pytest.fixture
def pair(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    transitions = updater.reviewed_transitions()
    prior = next(t for t in transitions if t["id"] == "p012a_evidence_bundle_v1")
    fix = next(t for t in transitions if t["id"] == "p012a_report_correction_v1")
    old = {m["path"]: ("predecessor:" + m["path"]).encode() for m in fix["members"]}
    new = {path: (root / path).read_bytes().replace(b"\r\n", b"\n") for path in old}
    known = {}
    for member in fix["members"]:
        path = member["path"]
        assert member["before_sha256"] == next(
            m["after_sha256"] for m in prior["members"] if m["path"] == path
        )
        assert before_p012a_contract_hash(root, path) == member["after_sha256"]
        known[new[path]] = member["after_sha256"]
        known[old[path]] = member["before_sha256"]
    original = updater.sha256
    monkeypatch.setattr(updater, "sha256", lambda raw: known.get(raw, original(raw)))
    return old, new


def test_exact_correction_family_admitted(pair):
    old, new = pair
    read = lambda commit, path: (old if commit == "before" else new).get(path)
    assert set(new) == updater.P012A_REPORT_CORRECTION_PATHS
    updater.check_transition_inventory(set(new), read, "before", "after")
    updater.check_source_only(set(new), read_blob=read, before="before", target="after")


@pytest.mark.parametrize("path", sorted(updater.P012A_REPORT_CORRECTION_PATHS))
@pytest.mark.parametrize("damage", ["changed", "missing", "predecessor", "inventory"])
def test_peer_or_inventory_drift_refused(pair, path, damage):
    old, new = pair
    inventory = set(new)
    if damage == "changed":
        new[path] += b"# drift"
    elif damage == "missing":
        del new[path]
    elif damage == "predecessor":
        old[path] = b"different predecessor"
    else:
        inventory.remove(path)
    read = lambda commit, member: (old if commit == "before" else new).get(member)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(inventory, read, "before", "after")


def test_installed_registry_without_correction_cannot_accept_target(pair, monkeypatch):
    old, new = pair
    installed = [
        t for t in updater.reviewed_transitions() if t["id"] != "p012a_report_correction_v1"
    ]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: installed)
    read = lambda commit, path: (old if commit == "before" else new).get(path)
    with pytest.raises(ValueError):
        updater.check_transition_inventory(set(new), read, "before", "after")


def test_fixed_family_required(monkeypatch):
    value = json.loads(Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes())
    item = next(t for t in value["transitions"] if t["id"] == "p012a_report_correction_v1")
    item["members"].pop()
    raw = json.dumps(value).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda _: raw)
    with pytest.raises(ValueError, match=r"Complete fixed P01\.2a report-correction"):
        updater.reviewed_transitions()
