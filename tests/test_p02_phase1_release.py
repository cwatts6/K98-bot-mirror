"""Fixed combined admission and runtime contract selection; no database writes."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from services.export_execution_protocol import encode
from services.export_phase1_contract import (
    ACTIVATION_SCOPE_SHA256,
    MIGRATION_ID,
    phase1_contract,
)
from services.export_runtime_composition import validate_application_installation_contract
from services.export_sql_direct_permissions import validate_contract

ROOT = Path(__file__).resolve().parents[1]


def descriptor():
    return dict(
        version=3,
        profile="p02_phase1_v1",
        bot_predecessors=[updater.PHASE1_PREDECESSOR],
        sql_commit=updater.PHASE1_SQL_COMMIT,
        migrations=[dict(id=MIGRATION_ID, sha256=updater.PHASE1_PROFILE_HASH)],
        contract_transition=updater.PHASE1_CONTRACT_TRANSITION,
    )


def test_exact_descriptor_requires_fixed_family_and_explicit_commit():
    value = descriptor()
    assert updater.combined_description(encode(value), updater.PHASE1_PREDECESSOR) == value


@pytest.mark.parametrize("field", list(descriptor()) + ["extra"])
def test_descriptor_drift_is_refused(field):
    value = descriptor()
    value[field] = "unreviewed"
    with pytest.raises(ValueError):
        updater.validate_combined_description(encode(value))


@pytest.mark.parametrize("version", [1, 2, True, 4])
def test_phase1_cannot_use_an_older_descriptor(version):
    value = descriptor()
    value["version"] = version
    with pytest.raises(ValueError):
        updater.validate_combined_description(encode(value))


def test_source_only_and_incomplete_adoption_are_refused():
    files = {"services/export_phase1_contract.py": b"fixture"}
    read = lambda rev, path: files.get(path) if rev == "target" else None
    with pytest.raises(ValueError, match="combined SQL descriptor"):
        updater.check_phase1_release_binding(updater.PHASE1_PREDECESSOR, "target", files, read)
    files[updater.RELEASE_DESCRIPTION] = encode(descriptor())
    with pytest.raises(ValueError, match="Complete Phase 1 source"):
        updater.check_phase1_release_binding(updater.PHASE1_PREDECESSOR, "target", files, read)
    updater.check_phase1_release_binding(
        updater.PHASE1_PREDECESSOR, "target", updater.P02_PHASE1_SQL_EXPORT_PATHS, read
    )


@pytest.fixture
def contract_pair(monkeypatch):
    # Synthetic identities keep production seed data private. The real complete
    # before/after digests are verified separately against the private receipts.
    bot = {
        key: dict(principal="fixture", metadata_hash="before")
        for key in updater.PHASE1_CONTRACT_PINS
    }
    bot["sql_contract"] = {"principal": "fixture-coordinator"}
    expected = deepcopy(bot)
    for key, updates in updater.PHASE1_CONTRACT_UPDATES.items():
        expected[key].update(updates)
        if key in updater.PHASE1_SOURCE_FILES:
            field, path = updater.PHASE1_SOURCE_FILES[key]
            expected[key][field] = json.loads((ROOT / path).read_bytes())
    monkeypatch.setattr(
        updater,
        "PHASE1_CONTRACT_PINS",
        {
            key: dict(
                before=updater.sha256(encode(bot[key])), after=updater.sha256(encode(expected[key]))
            )
            for key in updater.PHASE1_CONTRACT_PINS
        },
    )
    return bot, expected


def read_source(_revision, path):
    return (ROOT / path).read_bytes()


def test_complete_contract_transition_preserves_original_and_coordination(contract_pair):
    bot, expected = contract_pair
    original = deepcopy(bot)
    result = updater.phase1_contract_transition(
        {"bot-template.json": bot}, descriptor(), read_source, "target"
    )
    assert {key: pair["after"] for key, pair in result["contracts"].items()} == expected
    assert (
        result["contracts"]["sql_contract"]["before"]
        == result["contracts"]["sql_contract"]["after"]
    )
    result["contracts"]["sql_contract"]["after"]["principal"] = "mutated"
    assert bot == original


@pytest.mark.parametrize("key", list(updater.PHASE1_CONTRACT_PINS))
def test_any_predecessor_contract_drift_refuses_transition(contract_pair, key):
    bot, _ = contract_pair
    bot[key]["principal"] = "unreviewed"
    with pytest.raises(ValueError, match="predecessor startup contract"):
        updater.phase1_contract_transition(
            {"bot-template.json": bot}, descriptor(), read_source, "target"
        )


@pytest.mark.parametrize("key", list(updater.PHASE1_SOURCE_FILES))
def test_any_candidate_source_drift_refuses_transition(contract_pair, key):
    bot, _ = contract_pair
    damaged = updater.PHASE1_SOURCE_FILES[key][1]
    read = lambda rev, path: b"{}" if path == damaged else read_source(rev, path)
    with pytest.raises(ValueError, match="successor startup contract"):
        updater.phase1_contract_transition({"bot-template.json": bot}, descriptor(), read, "target")


def application_contract():
    return dict(
        version=3,
        server="fixture",
        database="ROK_TRACKER",
        principal="fixture",
        sources=json.loads((ROOT / "deploy/p02_phase1_application_sources.json").read_bytes()),
        dynamic_objects=[],
        metadata_hash="a" * 64,
        permissions_hash="b" * 64,
        review_id="01414528-bdf0-4000-8000-999999999999",
        fingerprint_format="application_schema_v2",
        scope_hash=ACTIVATION_SCOPE_SHA256,
        phase1_installation=MIGRATION_ID,
    )


def legacy_contract():
    return dict(
        version=2,
        server="fixture",
        database="ROK_TRACKER",
        principal="fixture",
        login_sid="ab" * 16,
        source=json.loads((ROOT / "deploy/p02_phase1_legacy_source.json").read_bytes()),
        migration_hash="a" * 64,
        metadata_hash="b" * 64,
        recovery_installation="20261022_001_p0_pipeline_receipts",
        phase1_installation=MIGRATION_ID,
    )


@pytest.mark.parametrize(
    "factory,validator",
    [
        (application_contract, validate_application_installation_contract),
        (legacy_contract, validate_contract),
    ],
)
def test_exact_runtime_amendment_selects_only_qualified_sources(factory, validator):
    approved = factory()
    validator(approved)
    assert phase1_contract(approved)
    for damage in ("missing", "unknown", "source"):
        bad = deepcopy(approved)
        if damage == "missing":
            del bad["phase1_installation"]
        elif damage == "unknown":
            bad["phase1_installation"] = "unreviewed"
        else:
            bad["sources" if factory is application_contract else "source"] = []
        with pytest.raises(ValueError):
            validator(bad)


def test_phase1_refuses_legacy_application_fingerprint_format():
    approved = application_contract()
    approved["version"] = 2
    with pytest.raises(ValueError, match="portable"):
        validate_application_installation_contract(approved)


def test_phase1_has_no_coordination_installation_objects():
    from services.export_execution_dal import INSTALLATION_OBJECTS

    assert len(updater.PHASE1_OBJECTS) == 57
    assert not {n.casefold() for n in updater.PHASE1_OBJECTS} & {
        n.casefold() for n in INSTALLATION_OBJECTS
    }
