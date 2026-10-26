"""Exact WS3 bundle admission, without invoking bot code or a live updater."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from scripts.validate_k98_update_compatibility import classify
from tests.updater_source_assertions import before_startup_foundations_hash


def transition():
    return next(t for t in updater.reviewed_transitions() if t["id"] == "event_cache_readiness_v1")


def synthetic_bundle(monkeypatch):
    item = deepcopy(transition())
    blobs = {}
    for member in item["members"]:
        for revision, field in (("before", "before_sha256"), ("after", "after_sha256")):
            raw = None if member[field] is None else f"{revision}:{member['path']}\n".encode()
            blobs[revision, member["path"]] = raw
            member[field] = updater.sha256(raw) if raw is not None else None
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    return blobs


def test_registry_pins_complete_reviewed_feature():
    item = transition()
    root = Path(__file__).resolve().parents[1]
    assert {m["path"] for m in item["members"]} == updater.EVENT_CACHE_READINESS_PATHS
    for member in item["members"]:
        assert before_startup_foundations_hash(root, member["path"]) == member["after_sha256"]
        assert member["before_sha256"] != member["after_sha256"]
        assert (member["before_sha256"] is None) == (
            member["path"] == "services/event_cache_service.py"
        )


@pytest.mark.parametrize("defect", ["missing", "extra", "foreign", "duplicate", "renamed"])
def test_registry_rejects_partial_or_widened_bundle(monkeypatch, defect):
    item = deepcopy(transition())
    if defect == "missing":
        item["members"].pop()
    elif defect == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    elif defect == "foreign":
        item["members"][0]["path"] = "services/unreviewed.py"
    elif defect == "duplicate":
        item["members"].append(item["members"][0])
    else:
        item["id"] = "event_cache_readiness_unreviewed"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError, match=r"Complete fixed event-cache|Unique export protocol"):
        updater.reviewed_transitions()


@pytest.mark.parametrize("path", sorted(updater.EVENT_CACHE_READINESS_PATHS))
@pytest.mark.parametrize("revision", ["before", "after"])
@pytest.mark.parametrize("defect", ["changed", "missing"])
def test_either_protected_entry_rejects_any_damaged_dependency(monkeypatch, path, revision, defect):
    blobs = synthetic_bundle(monkeypatch)
    if blobs[revision, path] is None and defect == "missing":
        # The new service must be absent in the predecessor; pre-existing bytes
        # are the relevant negative case for that side of the transition.
        blobs[revision, path] = b"unexpected predecessor"
    else:
        blobs[revision, path] = b"unreviewed" if defect == "changed" else None
    for entry in ("bot_instance.py", "services/recovery_health.py"):
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(entry, lambda *key: blobs.get(key), "before", "after")


@pytest.mark.parametrize("crlf", [False, True])
def test_exact_bundle_accepts_authenticated_newline_forms(monkeypatch, crlf):
    blobs = synthetic_bundle(monkeypatch)
    if crlf:
        blobs = {
            key: raw.replace(b"\n", b"\r\n") if raw is not None else None
            for key, raw in blobs.items()
        }
    updater.check_source_only(
        sorted(updater.EVENT_CACHE_READINESS_PATHS),
        read_blob=lambda *key: blobs.get(key),
        before="before",
        target="after",
    )


def test_target_cannot_grant_its_own_transition(monkeypatch):
    old = [t for t in updater.reviewed_transitions() if t["id"] != "event_cache_readiness_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: old)
    result = classify(
        "before",
        "after",
        ["bot_instance.py"],
        lambda *args: b"before" if args[0] == "before" else b"target claims compatible",
    )
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"


@pytest.mark.parametrize("installed", ["old_policy", "old_registry", "candidate"])
def test_compatibility_requires_both_installed_policy_and_registry(monkeypatch, installed):
    blobs = synthetic_bundle(monkeypatch)
    files = {Path(p).name: "a" * 64 for p in updater.TOOL_SOURCE_PATHS}
    files["EmptyGitConfig.txt"] = updater.sha256(b"")
    if installed == "old_policy":
        files["prepare_k98_update.py"] = "b" * 64
    elif installed == "old_registry":
        files["k98_update_transitions.json"] = "b" * 64
    result = classify(
        "before",
        "after",
        sorted(updater.EVENT_CACHE_READINESS_PATHS),
        lambda *key: blobs.get(key),
        dict(version=1, files=files),
        policy_sha256="a" * 64,
        registry_sha256="a" * 64,
    )
    assert not result["blockers"]
    assert result["classification"] == (
        "ROUTINE_COMPATIBLE" if installed == "candidate" else "UPDATER_UPGRADE_REQUIRED"
    )


def test_registry_retains_a_bounded_inventory(monkeypatch):
    raw = json.loads(Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes())
    assert len(raw["transitions"]) == 43
    raw["transitions"].append(deepcopy(raw["transitions"][-1]))
    monkeypatch.setattr(Path, "read_bytes", lambda self: json.dumps(raw).encode())
    with pytest.raises(ValueError, match="Bounded installed transitions"):
        updater.reviewed_transitions()
