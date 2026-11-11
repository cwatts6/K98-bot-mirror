"""Explicit D4 contract selection, source custody and historical compatibility."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
from test_p02_phase1_release import application_contract, legacy_contract

from services.export_d4_contract import ACTIVATION_SCOPE_SHA256, MIGRATION_ID, d4_contract
from services.export_execution_dal import (
    application_activation_scope,
    legacy_permission_queries,
)
from services.export_runtime_composition import validate_application_installation_contract
from services.export_sql_direct_permissions import validate_contract

ROOT = Path(__file__).resolve().parents[1]


def successor(factory):
    approved = factory()
    approved["d4_installation"] = MIGRATION_ID
    if factory is application_contract:
        approved["sources"] = json.loads(
            (ROOT / "deploy/p02_d4_application_sources.json").read_bytes()
        )
        approved["scope_hash"] = ACTIVATION_SCOPE_SHA256
    else:
        approved["source"] = json.loads((ROOT / "deploy/p02_d4_legacy_source.json").read_bytes())
    return approved


@pytest.mark.parametrize(
    "factory,validator",
    [
        (application_contract, validate_application_installation_contract),
        (legacy_contract, validate_contract),
    ],
)
def test_both_generations_are_explicit_and_missing_or_foreign_lineage_refuses(factory, validator):
    original = factory()
    validator(original)
    assert not d4_contract(original)
    approved = successor(factory)
    validator(approved)
    assert d4_contract(approved)
    for damage in ("missing_d4", "missing_phase1", "foreign_d4", "old_source", "extra_field"):
        bad = deepcopy(approved)
        if damage == "missing_d4":
            del bad["d4_installation"]
        elif damage == "missing_phase1":
            del bad["phase1_installation"]
        elif damage == "foreign_d4":
            bad["d4_installation"] = "unreviewed"
        elif damage == "old_source":
            field = "sources" if factory is application_contract else "source"
            bad[field] = original[field]
        else:
            bad["fallback"] = True
        with pytest.raises(ValueError):
            validator(bad)


def test_exact_d4_receipt_extends_historical_reader_without_replacing_phase1():
    old = legacy_permission_queries(legacy_contract()["source"])["migration"]
    new = legacy_permission_queries(successor(legacy_contract)["source"])["migration"]
    assert new[1] == (*old[1], MIGRATION_ID)
    assert new[0].count("?") == 8 and old[0].count("?") == 7
    assert new[0].endswith("ORDER BY MigrationId")


def test_expanded_closure_audits_existing_rights_without_new_grants():
    old = legacy_contract()["source"]
    new = successor(legacy_contract)["source"]
    assert new["grants"] == old["grants"]
    assert new["permission_model"] == old["permission_model"] == "direct_application_v1"
    assert new["signatures"] == old["signatures"]
    assert set(new["roots"]) - set(old["roots"]) == {"dbo.usp_MarkLogBackupTriggerProcessed"}
    from services.export_sql_direct_permissions import application_grant_rows

    assert any(
        row["TargetName"] == "dbo.usp_MarkLogBackupTriggerProcessed"
        and row["PermissionName"] == "EXECUTE"
        for row in application_grant_rows()
    )
    assert len(new["modules"]) == 64
    assert {m["name"] for m in old["modules"]} <= {m["name"] for m in new["modules"]}
    for name in ("dbo.UPDATE_ALL", "dbo.UPDATE_RALLY_DATA", "dbo.TEST"):
        row = next(m for m in new["modules"] if m["name"] == name)
        assert not row.get("compatible_definition_sha256")
        assert name not in new["roots"]
    # New claims/children stay outside the direct application EXECUTE roots.
    assert not any("Maintenance" in name for name in new["roots"])


def test_new_tables_and_children_extend_source_scope_without_dropping_old_objects():
    old = application_contract()["sources"]
    new = successor(application_contract)["sources"]
    assert len(old) == 574 and len(new) == 591
    assert {r["name"] for r in old} <= {r["name"] for r in new}
    before = set(application_activation_scope(phase1=True))
    after = set(application_activation_scope(phase1=True, d4=True))
    assert before < after and len(after - before) == 17
    assert after <= {r["name"] for r in new}
    with pytest.raises(ValueError, match="Phase 1"):
        application_activation_scope(d4=True)


def test_d4_scope_cannot_fall_back_to_old_or_mutated_resource(monkeypatch):
    from services import export_execution_dal as dal

    old = (ROOT / "deploy/p02_phase1_activation_scope.json").read_bytes()
    monkeypatch.setattr(dal, "read_contract_resource", lambda name: old)
    with pytest.raises(ValueError, match="dependency scope differs"):
        dal.application_activation_scope(phase1=True, d4=True)


def test_fixed_verifier_archive_includes_d4_reader_and_scope():
    from scripts.verify_k98_update_pair import CONTRACT_ARCHIVE_MEMBERS

    assert "services/export_d4_contract.py" in CONTRACT_ARCHIVE_MEMBERS
    assert "deploy/p02_d4_activation_scope.json" in CONTRACT_ARCHIVE_MEMBERS
    assert "services/export_phase1_contract.py" in CONTRACT_ARCHIVE_MEMBERS
    assert "deploy/p02_phase1_activation_scope.json" in CONTRACT_ARCHIVE_MEMBERS
