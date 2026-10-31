"""Exact release admission; no live updater, SQL or bot execution."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from scripts.validate_k98_update_compatibility import classify
from tests.updater_source_assertions import (
    before_finalisation_hash,
    installed_contract_archive_hash,
)


def transition():
    return next(item for item in updater.reviewed_transitions() if item["id"] == "p1_mge_a1b_v1")


def synthetic_bundle(monkeypatch):
    item = deepcopy(transition())
    blobs = {}
    for member in item["members"]:
        for rev, field in (("before", "before_sha256"), ("after", "after_sha256")):
            raw = None if member[field] is None else f"{rev}:{member['path']}\n".encode()
            blobs[rev, member["path"]] = raw
            member[field] = updater.sha256(raw) if raw is not None else None
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    return blobs


def test_complete_bundle_pins_current_source():
    item = transition()
    root = Path(__file__).resolve().parents[1]
    assert {m["path"] for m in item["members"]} == updater.MGE_A1B_PATHS
    for member in item["members"]:
        assert before_finalisation_hash(root, member["path"]) == member["after_sha256"]
        assert member["after_sha256"] is not None


def test_reviewed_history_and_mge_hashes_remain_exact():
    items = updater.reviewed_transitions()
    assert len(items) == 53
    # All fifty historical entries are immutable; this is one fixed successor.
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    assert (
        updater.sha256(canonical(items[:50]))
        == "893a98a56bf4dde2109e9dcd3e3f34d907fa2f823758386ba738ac001acb36d0"
    )
    assert (
        updater.sha256(canonical(items[50]))
        == "05647a03207f0f79a9055c828d6177fe904e3658ed470bc09a26bbe7200e723a"
    )


@pytest.mark.parametrize("extra_byte", [False, True])
def test_registry_byte_bound_is_enforced(monkeypatch, extra_byte):
    raw = Path(updater.__file__).with_name("k98_update_transitions.json").read_bytes()
    raw += b" " * (110592 - len(raw) + int(extra_byte))
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    if extra_byte:
        with pytest.raises(ValueError, match="registry exceeds bound"):
            updater.reviewed_transitions()
    else:
        assert len(updater.reviewed_transitions()) == 53


def test_fifty_fourth_registry_entry_is_rejected(monkeypatch):
    items = updater.reviewed_transitions()
    items.append(deepcopy(items[0]))
    raw = json.dumps(dict(version=1, transitions=items)).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError, match="Bounded installed transitions required"):
        updater.reviewed_transitions()


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
        item["id"] = "mge_unreviewed"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(
        ValueError,
        match=r"Complete fixed MGE A1b|Unique export protocol|Unique bounded transition",
    ):
        updater.reviewed_transitions()


@pytest.mark.parametrize("path", sorted(updater.MGE_A1B_PATHS))
@pytest.mark.parametrize("rev", ["before", "after"])
@pytest.mark.parametrize("defect", ["changed", "missing"])
def test_every_dependency_is_authenticated(monkeypatch, path, rev, defect):
    blobs = synthetic_bundle(monkeypatch)
    if blobs[rev, path] is None and defect == "missing":
        blobs[rev, path] = b"unexpected predecessor"
    else:
        blobs[rev, path] = b"unreviewed" if defect == "changed" else None
    for entry in (
        "core/interaction_safety.py",
        "mge/mge_embed_manager.py",
        "core/owned_work.py",
    ):
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
        sorted(updater.MGE_A1B_PATHS),
        read_blob=lambda *key: blobs.get(key),
        before="before",
        target="after",
    )


def test_target_cannot_grant_transition(monkeypatch):
    old = [item for item in updater.reviewed_transitions() if item["id"] != "p1_mge_a1b_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: old)
    result = classify(
        "before",
        "after",
        ["core/owned_work.py"],
        lambda *args: b"old" if args[0] == "before" else b"self admitted",
    )
    assert result["classification"] == "COORDINATED_RELEASE_REQUIRED"


@pytest.mark.parametrize("installed", ["old_policy", "old_registry", "candidate"])
def test_installed_policy_and_registry_must_match(monkeypatch, installed):
    blobs = synthetic_bundle(monkeypatch)
    files = {Path(p).name: "a" * 64 for p in updater.TOOL_SOURCE_PATHS}
    files["EmptyGitConfig.txt"] = updater.sha256(b"")
    files["contract_verifier.zip"] = installed_contract_archive_hash(
        Path(__file__).resolve().parents[1]
    )
    if installed == "old_policy":
        files["prepare_k98_update.py"] = "b" * 64
    elif installed == "old_registry":
        files["k98_update_transitions.json"] = "b" * 64
    result = classify(
        "before",
        "after",
        sorted(updater.MGE_A1B_PATHS),
        lambda *key: blobs.get(key),
        dict(version=1, files=files),
        policy_sha256="a" * 64,
        registry_sha256="a" * 64,
    )
    assert not result["blockers"]
    assert result["classification"] == (
        "ROUTINE_COMPATIBLE" if installed == "candidate" else "UPDATER_UPGRADE_REQUIRED"
    )
