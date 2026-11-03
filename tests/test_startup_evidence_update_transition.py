"""Only the exact installed startup custody correction may cross its source pin."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from tests.test_updater_transition_inventory import AFTER, BEFORE
from tests.updater_source_assertions import before_startup_evidence_hash


def bundle():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "startup_evidence_custody_v1"
    )


def test_missing_custody_transition_has_explicit_diagnostic(monkeypatch):
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [])
    with pytest.raises(AssertionError, match="Required startup_evidence_custody_v1"):
        before_startup_evidence_hash(
            Path(__file__).resolve().parents[1], "scripts/run_export_startup_issuer.py"
        )


def test_custody_transition_pins_exact_corrected_issuer():
    item = bundle()
    assert {m["path"] for m in item["members"]} == updater.DRAINED_ISSUER_TRANSITION_PATHS
    member = item["members"][0]
    raw = (Path(__file__).resolve().parents[1] / member["path"]).read_bytes()
    assert updater.sha256(raw.replace(b"\r\n", b"\n")) == member["after_sha256"]
    assert member["before_sha256"] == (
        "e701d805aa8103cdf62827b23fd50852bc0bfb9488e97352ae9ef689164495ea"
    )


@pytest.mark.parametrize("damage", [None, "before", "after", "uninstalled", "altered_pin"])
def test_custody_transition_requires_exact_installed_pair(monkeypatch, damage):
    item = deepcopy(bundle())
    member = item["members"][0]
    path = member["path"]
    blobs = {BEFORE: b"# previous\n", AFTER: b"# corrected\n"}
    member["before_sha256"] = updater.sha256(blobs[BEFORE])
    member["after_sha256"] = updater.sha256(blobs[AFTER])
    previous = {"AutomaticStartupPolicy.json": {"source_hashes": {path: member["before_sha256"]}}}
    if damage == "before":
        blobs[BEFORE] += b"# altered\n"
    elif damage == "after":
        blobs[AFTER] += b"# altered\n"
    elif damage == "altered_pin":
        previous["AutomaticStartupPolicy.json"]["source_hashes"][path] = "f" * 64
    monkeypatch.setattr(
        updater, "reviewed_transitions", lambda: [] if damage == "uninstalled" else [item]
    )
    monkeypatch.setattr(updater, "coordinated_policy", lambda: None)
    read = lambda revision, member_path: blobs[revision] if member_path == path else None
    if damage:
        with pytest.raises(ValueError):
            updater.source_plan(previous, BEFORE, AFTER, [path], read)
    else:
        plan, payload = updater.source_plan(previous, BEFORE, AFTER, [path], read)
        assert payload == {path: blobs[AFTER]}
        assert plan["new_pins"][path] == member["after_sha256"]


@pytest.mark.parametrize("damage", ["missing", "extra", "renamed", "other_script"])
def test_custody_registry_cannot_authorize_other_source(tmp_path, monkeypatch, damage):
    item = deepcopy(bundle())
    if damage == "missing":
        item["members"].clear()
    elif damage == "extra":
        item["members"].append(
            dict(path="services/export_foreign.py", before_sha256=None, after_sha256="a" * 64)
        )
    elif damage == "renamed":
        item["id"] = "other_custody"
    else:
        item["members"][0]["path"] = "scripts/run_export_authority.py"
    (tmp_path / "k98_update_transitions.json").write_text(
        json.dumps(dict(version=1, transitions=[item]))
    )
    monkeypatch.setattr(updater, "__file__", str(tmp_path / "prepare_k98_update.py"))
    with pytest.raises(ValueError):
        updater.reviewed_transitions()
