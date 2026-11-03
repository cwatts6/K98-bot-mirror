"""Portable contract adoption has a separate exact installed authority."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater


@pytest.fixture
def previous(monkeypatch):
    contract = {
        "version": 2,
        "server": "fixture",
        "database": "fixture",
        "principal": "restricted",
        "metadata_hash": "raw-before",
        "permissions_hash": "permissions",
        "scope_hash": "scope",
        "sources": [{"path": "source", "sha256": "source-hash"}],
        "review_id": "old-review",
    }
    monkeypatch.setattr(updater, "MGE_APPLICATION_BEFORE", updater.sha256(updater.encode(contract)))
    return {
        "bot-template.json": {
            "application_sql_contract": contract,
            "sql_contract": {"unchanged": "installation"},
            "legacy_sql_contract": {"unchanged": "legacy"},
        }
    }


def test_exact_portable_transition_preserves_every_other_expectation(previous):
    original = deepcopy(previous)
    pairs = updater.mge_portable_application_contract_transition(
        previous, updater.MGE_PORTABLE_APPLICATION_RELEASE
    )["contracts"]
    before, after = pairs["application_sql_contract"].values()
    assert {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)} == {
        "version",
        "fingerprint_format",
        "metadata_hash",
        "review_id",
    }
    assert after["version"] == 3
    assert after["fingerprint_format"] == "application_schema_v2"
    assert after["metadata_hash"] == updater.MGE_PORTABLE_APPLICATION_AFTER_METADATA
    assert after["review_id"] == updater.MGE_PORTABLE_APPLICATION_REVIEW
    for key in ("sql_contract", "legacy_sql_contract"):
        assert pairs[key]["before"] == pairs[key]["after"] == original["bot-template.json"][key]
        pairs[key]["after"]["unchanged"] = "mutation"
    after["sources"][0]["path"] = "mutation"
    assert previous == original


@pytest.mark.parametrize(
    "field",
    [
        "version",
        "fingerprint_format",
        "server",
        "database",
        "principal",
        "metadata_hash",
        "permissions_hash",
        "scope_hash",
        "sources",
        "review_id",
        "extra",
    ],
)
def test_any_predecessor_drift_is_refused(previous, field):
    previous["bot-template.json"]["application_sql_contract"][field] = "drift"
    with pytest.raises(ValueError, match="predecessor application contract"):
        updater.mge_portable_application_contract_transition(
            previous, updater.MGE_PORTABLE_APPLICATION_RELEASE
        )


@pytest.mark.parametrize(
    "version,format_value", [(3, None), (True, None), (2.0, None), (2, "application_schema_v2")]
)
def test_format_is_explicit_even_with_matching_test_digest(
    previous, monkeypatch, version, format_value
):
    contract = previous["bot-template.json"]["application_sql_contract"]
    contract["version"] = version
    if format_value is not None:
        contract["fingerprint_format"] = format_value
    monkeypatch.setattr(updater, "MGE_APPLICATION_BEFORE", updater.sha256(updater.encode(contract)))
    with pytest.raises(ValueError, match="predecessor application contract"):
        updater.mge_portable_application_contract_transition(
            previous, updater.MGE_PORTABLE_APPLICATION_RELEASE
        )


@pytest.mark.parametrize(
    "field",
    [
        "version",
        "profile",
        "bot_predecessors",
        "sql_commit",
        "migrations",
        "application_contract_transition",
        "extra",
    ],
)
def test_other_release_cannot_borrow_portable_authority(previous, field):
    description = deepcopy(updater.MGE_PORTABLE_APPLICATION_RELEASE)
    description[field] = "drift"
    with pytest.raises(ValueError, match="exact reviewed release"):
        updater.mge_portable_application_contract_transition(previous, description)
    with pytest.raises(ValueError):
        updater.validate_combined_description(json.dumps(description).encode())


def test_legacy_and_portable_descriptors_are_independent(previous):
    raw = updater.MGE_APPLICATION_RELEASE
    portable = updater.MGE_PORTABLE_APPLICATION_RELEASE
    assert raw["version"] == 1 and "application_contract_transition" not in raw
    for description in (raw, portable):
        assert (
            updater.validate_combined_description(json.dumps(description).encode()) == description
        )
    with pytest.raises(ValueError, match="exact reviewed release"):
        updater.mge_application_contract_transition(previous, portable)
    with pytest.raises(ValueError, match="exact reviewed release"):
        updater.mge_portable_application_contract_transition(previous, raw)
    with pytest.raises(ValueError, match="does not support installed Bot predecessor"):
        updater.combined_description(json.dumps(portable).encode(), "a" * 40)


@pytest.mark.parametrize("version", [True, False, 2.0, "2", 0, 3])
def test_descriptor_version_is_exact(version):
    d = deepcopy(updater.MGE_PORTABLE_APPLICATION_RELEASE)
    d["version"] = version
    with pytest.raises(ValueError):
        updater.validate_combined_description(json.dumps(d).encode())


def test_committed_descriptor_selects_portable_transition():
    root = Path(__file__).resolve().parents[1]
    assert (
        json.loads((root / updater.RELEASE_DESCRIPTION).read_bytes())
        == updater.MGE_PORTABLE_APPLICATION_RELEASE
    )


def test_legacy_descriptor_cannot_smuggle_a_format_choice():
    d = deepcopy(updater.MGE_APPLICATION_RELEASE)
    d["application_contract_transition"] = "mge_application_schema_v2"
    with pytest.raises(ValueError, match="Exact combined release fields"):
        updater.validate_combined_description(json.dumps(d).encode())
