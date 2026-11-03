"""The shared application contract must honor recovery migration DENYs."""

import os
from pathlib import Path
import subprocess

import pytest

from services.export_execution_dal import EVIDENCE_TABLES, installation_permissions


@pytest.mark.parametrize("profile", ["authority", "reader", "application"])
@pytest.mark.parametrize("direct", [False, True])
def test_rollover_procedure_has_execute_without_alter(profile, direct):
    rights = installation_permissions(profile, direct=direct)
    name = "dbo.usp_ExportRolloverContainTargets"
    assert rights[name, None, "EXECUTE"] == int(profile != "reader")
    for permission in ("ALTER", "CONTROL", "TAKE OWNERSHIP"):
        assert rights[name, None, permission] == 0


def test_direct_legacy_permissions_and_evidence_denials_remain_exact():
    rights = installation_permissions("application", direct=True)
    assert rights["dbo.usp_ExportJobContainTargets", None, "ALTER"] == 1
    assert rights["dbo.ExportPreparation", None, "ALTER"] == 1
    assert all(rights[name, None, "ALTER"] == 0 for name in EVIDENCE_TABLES)


def test_rollover_permission_expectation_matches_immutable_sql_migration():
    root = Path(os.getenv("K98_CONFIG_RECOVERY_SQL_SOURCE", "C:/K98-bot-SQL-Server"))
    if not (root / ".git").exists():
        pytest.skip("Authoritative SQL repository unavailable")
    sql = subprocess.check_output(
        [
            "git",
            "-c",
            "safe.directory=" + root.as_posix(),
            "show",
            "21de1988819fc734252b9efc68c2ea047d0b11d3:migrations/20261016_001_rollover_replacement.sql",
        ],
        cwd=root,
    ).decode("utf-8-sig")
    for role in ("ExportExecutionAuthority", "ExportExecutionReader"):
        assert (
            f"DENY ALTER,TAKE OWNERSHIP ON OBJECT::dbo.usp_ExportRolloverContainTargets TO {role};"
            in sql
        )
    assert (
        "GRANT EXECUTE ON OBJECT::dbo.usp_ExportRolloverContainTargets TO ExportExecutionAuthority;"
        in sql
    )
    assert (
        "DENY EXECUTE ON OBJECT::dbo.usp_ExportRolloverContainTargets TO ExportExecutionReader;"
        in sql
    )
