"""Only the explicitly pinned observer bodies gain transport normalization."""

from copy import deepcopy
import hashlib
import json

import pytest

from services import application_observation_fingerprint as candidate
from services.catalogue_observation_dal import canonical_module
from services.export_schema_fingerprint import (
    IDENTITY_FIELDS,
    METADATA_FIELDS,
    SchemaFingerprintError,
    canonical_application_metadata,
)


@pytest.fixture
def sample(monkeypatch):
    metadata = {name: [] for name in METADATA_FIELDS}
    identity = {name: [] for name in IDENTITY_FIELDS}
    bodies = {name: f"CREATE PROCEDURE {name} AS SELECT 1;\n" for name in candidate.PROCEDURES}
    monkeypatch.setattr(
        candidate,
        "reviewed_procedure_hashes",
        lambda: {
            name: hashlib.sha256(canonical_module(body).encode("utf-16-le")).hexdigest()
            for name, body in bodies.items()
        },
    )
    for name in [*sorted(candidate.PROCEDURES), "dbo.Unrelated"]:
        metadata["objects"].append(
            dict(
                ObjectName=name,
                ObjectType="P",
                ModuleDefinition=bodies.get(name, "CREATE PROCEDURE dbo.Unrelated AS SELECT 1;\n"),
                AnsiNulls=True,
                QuotedIdentifier=True,
                ExecuteAsPrincipal=None,
                MemoryOptimized=None,
                TemporalType=None,
            )
        )
    protocol = {}
    for name, parent in candidate.TRIGGERS.items():
        body = f"CREATE TRIGGER dbo.{name} ON {parent} AFTER UPDATE AS SELECT 1;\n"
        protocol[name] = body
        metadata["triggers"].append(
            dict(
                ObjectName=parent,
                TriggerName=name,
                ModuleDefinition=body,
                Disabled=False,
                InsteadOf=False,
                NotForReplication=False,
                AnsiNulls=True,
                QuotedIdentifier=True,
                ExecuteAsPrincipal=None,
            )
        )
    name = "tr_P02CatalogueObservation"
    protocol[name] = (
        f"CREATE TRIGGER {name} ON DATABASE FOR DDL_DATABASE_LEVEL_EVENTS AS SELECT 1;\n"
    )
    metadata["database_triggers"].append(
        dict(
            TriggerName=name,
            ModuleDefinition=protocol[name],
            Disabled=False,
            ExecuteAsPrincipal=None,
        )
    )
    monkeypatch.setattr(candidate, "reviewed_protocol_modules", lambda: protocol)
    return metadata, identity


def test_explicit_successor_normalizes_only_pinned_headers_and_lf(sample):
    metadata, identity = sample
    before = deepcopy(metadata)
    expected = candidate.canonical_observer_metadata(metadata, identity)
    assert metadata == before
    for category in ("objects", "triggers", "database_triggers"):
        for row in metadata[category]:
            if row.get("ObjectName") != "dbo.Unrelated":
                row["ModuleDefinition"] = "\n\t" + row["ModuleDefinition"].replace(
                    "CREATE", "CREATE OR ALTER", 1
                ).replace("\n", "\r\n")
    assert candidate.canonical_observer_metadata(metadata, identity) == expected
    assert canonical_application_metadata(metadata, identity) != canonical_application_metadata(
        before, identity
    )
    assert expected["format"] == candidate.FORMAT


@pytest.mark.parametrize("damage", ["body", "trailing_space", "missing", "parent"])
def test_body_or_closure_drift_is_never_transport_compatibility(sample, damage):
    metadata, identity = sample
    if damage == "missing":
        metadata["database_triggers"].clear()
    elif damage == "parent":
        metadata["triggers"][0]["ObjectName"] = "dbo.Other"
    else:
        row = metadata["objects"][0]
        row["ModuleDefinition"] += " SELECT 2;" if damage == "body" else " "
    with pytest.raises(SchemaFingerprintError):
        candidate.canonical_observer_metadata(metadata, identity)


@pytest.mark.parametrize("damage", ["disabled", "unrelated_body", "set_option"])
def test_every_other_metadata_field_remains_part_of_fingerprint(sample, damage):
    metadata, identity = sample
    before = candidate.canonical_observer_metadata(metadata, identity)
    if damage == "disabled":
        metadata["triggers"][0]["Disabled"] = True
    elif damage == "set_option":
        metadata["objects"][0]["AnsiNulls"] = False
    else:
        row = next(r for r in metadata["objects"] if r["ObjectName"] == "dbo.Unrelated")
        row["ModuleDefinition"] = row["ModuleDefinition"].replace("CREATE", "ALTER", 1)
    assert candidate.canonical_observer_metadata(metadata, identity) != before


def test_real_source_pin_refuses_amended_resource(monkeypatch):
    assert set(candidate.reviewed_procedure_hashes()) == candidate.PROCEDURES
    raw = json.loads(candidate.read_contract_resource("p02_observer_legacy_source.json"))
    raw["modules"][0]["definition_sha256"] = "0" * 64
    monkeypatch.setattr(candidate, "read_contract_resource", lambda _: json.dumps(raw).encode())
    with pytest.raises(SchemaFingerprintError, match="reviewed observer procedure"):
        candidate.reviewed_procedure_hashes()
