"""Exact installed admission of reviewed portable schema-reader source."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater

PATHS = frozenset(
    {
        "services/export_contract_resources.py",
        "services/export_execution_dal.py",
        "services/export_runtime_composition.py",
        "services/export_schema_fingerprint.py",
        "services/export_sql_direct_permissions.py",
    }
)


def transition():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == "application_schema_portable_v1"
    )


def synthetic(monkeypatch):
    item = deepcopy(transition())
    blobs = {}
    for member in item["members"]:
        for revision, field in [("before", "before_sha256"), ("after", "after_sha256")]:
            raw = None if member[field] is None else f"# {revision}:{member['path']}\n".encode()
            blobs[revision, member["path"]] = raw
            member[field] = None if raw is None else updater.sha256(raw)
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: [item])
    return blobs


def test_exact_reviewed_family_and_prior_history():
    items = updater.reviewed_transitions()
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    assert len(items) == 53
    assert (
        updater.sha256(canonical(items[:52]))
        == "cf3ae28f7d563acaad9106bbfd6cc60402d9d267522e9654963a8ab1adb1164b"
    )
    assert (
        updater.sha256(canonical(items[52]))
        == "b0af31f66e925704359a34ac2aab58f410cd8b9410214810e023cf006d94b045"
    )
    item = transition()
    assert (
        {m["path"] for m in item["members"]} == PATHS == updater.APPLICATION_SCHEMA_PORTABLE_PATHS
    )
    assert {m["path"] for m in item["members"] if m["before_sha256"] is None} == {
        "services/export_schema_fingerprint.py",
        "services/export_contract_resources.py",
    }
    root = Path(__file__).resolve().parents[1]
    for member in item["members"]:
        assert (
            updater.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )


@pytest.mark.parametrize("defect", ["missing", "extra", "duplicate", "foreign"])
def test_family_cannot_be_partial_or_widened(monkeypatch, defect):
    item = deepcopy(transition())
    if defect == "missing":
        item["members"].pop()
    elif defect == "extra":
        item["members"].append(dict(item["members"][0], path="services/export_unreviewed.py"))
    elif defect == "duplicate":
        item["members"].append(item["members"][0])
    else:
        item["members"][0]["path"] = "services/export_unreviewed.py"
    raw = json.dumps(dict(version=1, transitions=[item])).encode()
    monkeypatch.setattr(Path, "read_bytes", lambda self: raw)
    with pytest.raises(ValueError, match=r"Complete fixed portable schema|Unique export protocol"):
        updater.reviewed_transitions()


@pytest.mark.parametrize("path", sorted(PATHS))
@pytest.mark.parametrize("revision", ["before", "after"])
@pytest.mark.parametrize("damage", ["changed", "missing"])
def test_every_dependency_and_required_absence_is_authenticated(
    monkeypatch, path, revision, damage
):
    blobs = synthetic(monkeypatch)
    raw = blobs[revision, path]
    blobs[revision, path] = b"unexpected" if damage == "changed" or raw is None else None
    for entry in PATHS:
        with pytest.raises(ValueError, match="not installed/reviewed"):
            updater.check_protocol_transition(entry, lambda *key: blobs.get(key), "before", "after")


@pytest.mark.parametrize("crlf", [False, True])
def test_exact_bundle_is_admitted_without_target_imports(monkeypatch, crlf):
    blobs = synthetic(monkeypatch)
    if crlf:
        blobs = {key: raw.replace(b"\n", b"\r\n") if raw else raw for key, raw in blobs.items()}
    updater.check_source_only(
        sorted(PATHS), read_blob=lambda *key: blobs.get(key), before="before", target="after"
    )
    updater.check_transition_inventory(
        sorted(PATHS), lambda *key: blobs.get(key), "before", "after"
    )


@pytest.mark.parametrize("omitted", sorted(PATHS))
def test_changed_member_cannot_be_omitted(monkeypatch, omitted):
    blobs = synthetic(monkeypatch)
    with pytest.raises(ValueError, match="Incomplete reviewed protocol transition inventory"):
        updater.check_transition_inventory(
            sorted(PATHS - {omitted}), lambda *key: blobs.get(key), "before", "after"
        )


def test_target_cannot_supply_its_own_admission(monkeypatch):
    old = [t for t in updater.reviewed_transitions() if t["id"] != "application_schema_portable_v1"]
    monkeypatch.setattr(updater, "reviewed_transitions", lambda: old)
    with pytest.raises(ValueError, match="non-routine release"):
        updater.check_source_only(
            ["services/export_schema_fingerprint.py"],
            read_blob=lambda *key: b"target self approval",
            before="before",
            target="after",
        )


def test_unrelated_source_is_still_refused(monkeypatch):
    blobs = synthetic(monkeypatch)
    with pytest.raises(ValueError, match="non-routine release"):
        updater.check_source_only(
            sorted(PATHS | {"services/export_unreviewed.py"}),
            read_blob=lambda *key: blobs.get(key),
            before="before",
            target="after",
        )
