from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as update
from scripts.validate_k98_update_compatibility import classify
from tests.test_update_application_compatibility import installed_manifest

BEFORE, AFTER = "a" * 40, "b" * 40
PROTOCOL = "services/export_execution_protocol.py"
READER = "services/export_reader_protocol.py"


@pytest.fixture
def transition(monkeypatch):
    before = {PROTOCOL: b"old\n"}
    after = {PROTOCOL: b"new\n", READER: b"reader\n"}
    policy = [
        dict(
            id="fixture",
            members=[
                dict(
                    path=p,
                    before_sha256=update.sha256(before[p]) if p in before else None,
                    after_sha256=update.sha256(after[p]),
                )
                for p in after
            ],
        )
    ]
    monkeypatch.setattr(update, "reviewed_transitions", lambda: policy)
    return before, after, lambda c, p: (before if c == BEFORE else after).get(p)


def test_exact_protocol_bundle_updates_pins_and_preserves_predecessor(transition):
    before, after, read = transition
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {PROTOCOL: update.sha256(before[PROTOCOL])}
        }
    }
    original = deepcopy(previous)
    plan, payload = update.source_plan(previous, BEFORE, AFTER, list(after), read)
    assert previous == original
    assert plan["new_pins"][READER] == update.sha256(after[READER])
    assert plan["new_pins"][PROTOCOL] == update.sha256(after[PROTOCOL])
    assert payload == after


@pytest.mark.parametrize("damage", ["wrong-old", "wrong-new", "missing-peer", "partial-inventory"])
def test_unreviewed_or_partial_protocol_bundle_is_refused(transition, damage):
    before, after, read = transition
    previous = {
        "AutomaticStartupPolicy.json": {
            "source_hashes": {PROTOCOL: update.sha256(before[PROTOCOL])}
        }
    }
    paths = list(after)
    if damage == "wrong-old":
        before[PROTOCOL] = b"other"
    if damage == "wrong-new":
        after[PROTOCOL] = b"other"
    if damage == "missing-peer":
        del after[READER]
    if damage == "partial-inventory":
        paths.remove(READER)
    with pytest.raises(ValueError, match="transition"):
        update.source_plan(previous, BEFORE, AFTER, paths, read)


def test_registry_matches_delivered_protocol_and_is_not_target_metadata():
    root = Path(update.__file__).resolve().parents[1]
    expected = {}
    for transition in update.reviewed_transitions():
        for member in transition["members"]:
            path = member["path"]
            if path in expected:
                # Alternate predecessors may converge on the same image; later
                # releases must continue from that image, not replace it blindly.
                assert expected[path] in {member["before_sha256"], member["after_sha256"]}
            expected[path] = member["after_sha256"]
    for path, checksum in expected.items():
        assert update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n")) == checksum
    with pytest.raises(ValueError, match="contract change"):
        update.check_source_only(["scripts/k98_update_transitions.json"])


def test_candidate_registry_change_requires_installed_updater_upgrade():
    installed = installed_manifest()
    result = classify(
        BEFORE,
        AFTER,
        ["commands/example.py"],
        lambda c, p: c.encode(),
        installed,
        registry_sha256="f" * 64,
    )
    assert result["classification"] == "UPDATER_UPGRADE_REQUIRED"
    assert "scripts/k98_update_transitions.json" in result["updater_members"]


def additive_fixture():
    table = dict(
        schema="KVK",
        name="HistoryFixture",
        columns=[dict(name="ID", type="int", nullable=False, collation=None)],
        primary_key=dict(name="PK_HistoryFixture", columns=["ID"]),
        unique_keys=[],
        checks=[],
        foreign_keys=[],
    )
    profile = dict(
        version=1,
        profile="additive_tables_v1",
        migration_id="20261013_901_fixture",
        database_collation="Latin1_General_CI_AS",
        tempdb_collation="Latin1_General_CI_AS",
        compatibility_level=160,
        tables=[table],
        requires=[],
    )
    raw = json.dumps(profile).encode()
    description = dict(
        version=1,
        profile="additive_tables_v1",
        bot_predecessors=[BEFORE],
        sql_commit=AFTER,
        migrations=[dict(id=profile["migration_id"], sha256=update.sha256(raw))],
    )
    files = {"deploy/" + p: p.encode() for p in (*update.SQL_TOOLS, "SqlDeploy.TableRelease.ps1")}
    files["migrations/" + profile["migration_id"] + ".release.json"] = raw
    return description, profile, files


def test_additive_profile_packages_pinned_runner_and_declaration_without_sql_text():
    d, p, files = additive_fixture()
    assert update.combined_description(json.dumps(d).encode(), BEFORE) == d
    bindings, payload = update.combined_payload(d, files.get)
    assert "SqlDeploy.TableRelease.ps1" in payload
    assert len(payload) == 4
    assert bindings["profiles"][0]["sha256"] == d["migrations"][0]["sha256"]


@pytest.mark.parametrize(
    "damage",
    [
        "protected",
        "duplicate",
        "raw-sql",
        "identifier",
        "wrong-profile",
        "missing-runner",
        "wrong-hash",
    ],
)
def test_additive_acquisition_rejects_unsafe_or_unbound_profile(damage):
    d, p, files = additive_fixture()
    protected = []
    if damage == "protected":
        protected = ["KVK.HistoryFixture"]
    if damage == "duplicate":
        p["tables"] *= 2
    if damage == "raw-sql":
        p["tables"][0]["sql"] = "DROP TABLE dbo.Example"
    if damage == "identifier":
        p["tables"][0]["name"] = "Bad]; DROP TABLE X"
    if damage == "wrong-profile":
        p["profile"] = "module_grants_v1"
    if damage == "missing-runner":
        del files["deploy/SqlDeploy.TableRelease.ps1"]
    raw = json.dumps(p).encode()
    files["migrations/" + p["migration_id"] + ".release.json"] = raw
    d["migrations"][0]["sha256"] = update.sha256(raw) if damage != "wrong-hash" else "f" * 64
    with pytest.raises(ValueError):
        update.combined_payload(d, files.get, protected_objects=protected)
