"""Admission scope is source-pinned, not selected by a caller or runtime catalog."""

from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import export_execution_dal as dal
from services.export_runtime_composition import (
    application_contract_scope,
    application_snapshot_for_contract,
    verify_application_installation_contract,
)
from tests.test_export_runtime_composition import application_installation_fixture


def test_committed_scope_keeps_all_coordination_and_kvk_roots():
    root = Path(__file__).resolve().parents[1]
    sources = json.loads((root / "deploy/export_application_schema_source.json").read_bytes())
    scope = json.loads((root / "deploy/s11_activation_scope.json").read_bytes())
    assert digest(scope).hex() == dal.APPLICATION_ACTIVATION_SCOPE_HASH
    names = set(dal.application_activation_scope())
    assert set(dal.INSTALLATION_OBJECTS) <= names
    assert {s["name"] for s in sources if s["name"].startswith("KVK.")} <= names
    assert set(scope["roots"]) <= names
    assert all(set(refs) <= names for refs in scope["references"].values())
    assert "dbo.sp_TARGETS_MASTER" in names and "dbo.sp_Prep_TargetTable" in names
    assert "dbo.Repair_PreKvk_20260828_BadImport_Scan" not in names
    assert "dbo.SurveyQuestions" not in names


def scoped_fixture(monkeypatch):
    observed, approved = application_installation_fixture(monkeypatch)
    approved["sources"].append(
        dict(name="dbo.archive", type="U", path="archive.sql", sha256="b" * 64)
    )
    monkeypatch.setattr(dal, "APPLICATION_SCHEMA_SOURCE_HASH", digest(approved["sources"]).hex())
    monkeypatch.setattr(dal, "application_activation_scope", lambda: ["dbo.fixture"])
    approved.update(version=2, scope_hash=dal.APPLICATION_ACTIVATION_SCOPE_HASH)
    return observed, approved


def test_scoped_contract_excludes_archive_without_losing_shape_or_permission_gates(monkeypatch):
    observed, approved = scoped_fixture(monkeypatch)
    assert application_contract_scope(approved) == ["dbo.fixture"]
    assert verify_application_installation_contract(observed, approved) == digest(observed).hex()
    for category in ("columns", "dependencies", "foreign_keys", "database_triggers", "synonyms"):
        damaged = deepcopy(observed)
        damaged["metadata"][category].append(
            {"drift": True, "ModuleDefinition": "CREATE TRIGGER fixture"}
        )
        with pytest.raises(SourceConflict):
            verify_application_installation_contract(damaged, approved)
    damaged = deepcopy(observed)
    damaged["column_permissions"][0]["Allowed"] = 0
    with pytest.raises(SourceConflict):
        verify_application_installation_contract(damaged, approved)


def test_scoped_contract_rejects_caller_scope_and_omitted_sources(monkeypatch):
    _, approved = scoped_fixture(monkeypatch)
    with pytest.raises(SourceConflict):
        application_contract_scope(approved | {"scope_hash": "0" * 64})
    with pytest.raises(SourceConflict):
        application_contract_scope(approved | {"objects": []})
    monkeypatch.setattr(dal, "application_activation_scope", lambda: ["dbo.missing"])
    with pytest.raises(SourceConflict):
        application_contract_scope(approved)


def test_all_admission_reads_receive_the_pinned_scope(monkeypatch):
    observed, approved = scoped_fixture(monkeypatch)
    read = Mock(return_value=observed)
    monkeypatch.setattr(dal, "application_installation_snapshot", read)
    cursor = object()
    assert application_snapshot_for_contract(cursor, approved) is observed
    read.assert_called_once_with(cursor, scope=["dbo.fixture"])


def test_scope_builder_keeps_unqualified_recursive_references_and_rejects_changed_bytes(
    monkeypatch,
):
    import hashlib

    from scripts import prepare_s11_activation_scope as builder

    bodies = {
        "procedure.sql": b"CREATE PROCEDURE dbo.entry AS SELECT * FROM [intermediate]",
        "intermediate.sql": b"CREATE TABLE dbo.intermediate (id int REFERENCES [dbo].[leaf](id))",
        "leaf.sql": b"CREATE TABLE dbo.leaf (id int)",
        "archive.sql": b"CREATE TABLE dbo.archive (id int)",
    }
    sources = [
        dict(
            name="dbo." + name,
            path=path,
            type=kind,
            sha256=hashlib.sha256(bodies[path]).hexdigest(),
        )
        for name, path, kind in (
            ("entry", "procedure.sql", "P"),
            ("intermediate", "intermediate.sql", "U"),
            ("leaf", "leaf.sql", "U"),
            ("archive", "archive.sql", "U"),
        )
    ]
    monkeypatch.setattr(builder, "INSTALLATION_OBJECTS", set())
    monkeypatch.setattr(
        builder.subprocess,
        "check_output",
        lambda command, **_: bodies[command[-1].split(":", 1)[1]],
    )
    scope = builder.prepare(Path("fixture"), "revision", sources, {"grants": []})
    assert scope["objects"] == ["dbo.entry", "dbo.intermediate", "dbo.leaf"]
    assert scope["references"]["dbo.entry"] == ["dbo.intermediate"]
    bodies["leaf.sql"] += b" changed"
    with pytest.raises(ValueError, match="Source pin mismatch"):
        builder.prepare(Path("fixture"), "revision", sources, {"grants": []})


@pytest.mark.parametrize("scope", [None, ["dbo.fixture", "dbo.fixture_type"]])
def test_metadata_sql_uses_expressions_for_collated_order_and_parameterized_scope(
    monkeypatch, scope
):
    cursor = Mock()
    monkeypatch.setattr(dal, "one", lambda _: {"ViewDefinition": 1})
    monkeypatch.setattr(dal, "rows", lambda _: [])
    dal.application_installation_snapshot(cursor, scope=scope)
    calls = cursor.execute.call_args_list
    for call in calls:
        query = call.args[0]
        assert "ORDER BY ObjectName COLLATE" not in query
        assert "ORDER BY TypeName COLLATE" not in query
        assert "dbo.fixture" not in query
        if "OPENJSON(?)" in query:
            assert json.loads(call.args[1]) == scope
    if scope is not None:
        assert (
            sum("OPENJSON(?)" in call.args[0] for call in calls)
            == len(dal.INSTALLATION_METADATA) + 4
        )
