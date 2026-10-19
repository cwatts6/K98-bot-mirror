"""The coordinated release must admit exactly the atomic configuration producer."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

from kvk.dal.new_source_import_dal import digest
from services import export_sql_direct_permissions as direct
from services.export_execution_dal import legacy_definition_hash, validate_legacy_permission_source

SQL_HEAD = "21de1988819fc734252b9efc68c2ea047d0b11d3"
SQL_BASE = "b3480656e3454fbe713905460177f8d038c2bd5f"


def test_manifest_admits_atomic_configuration_and_excludes_old_definition():
    source = json.loads(Path("deploy/export_stats_import_outcome_source.json").read_bytes())
    validate_legacy_permission_source(source)
    module = next(m for m in source["modules"] if m["name"] == "dbo.sp_TARGETS_MASTER")
    admitted = {module["definition_sha256"], *module["compatible_definition_sha256"]}
    assert "59f759eec2f7dd042e6f75ab235583d6addd0f9268ff290d8a517f4ca0ff85ff" in admitted
    assert not admitted & {
        "d20e2dc29c7d6455a17ebfcb59e78210e1c10aa20145974293ac5f417822ec20",
        "f298271b8e7a57e5cce55bca88cd2aa21a1243ebce0a5c0a9559fce1fd600a3e",
    }
    assert digest(source).hex() == direct.DIRECT_SOURCE_HASH


def test_reviewed_sql_migration_and_source_have_the_same_pinned_body():
    root = Path(os.environ.get("K98_CONFIG_RECOVERY_SQL_SOURCE", "C:/K98-bot-SQL-Server"))
    if not root.is_dir():
        pytest.skip("Separate authoritative SQL repository is required")

    def read(revision, path):
        return subprocess.check_output(
            ["git", "-C", str(root), "show", revision + ":" + path], timeout=15
        )

    source = json.loads(Path("deploy/export_stats_import_outcome_source.json").read_bytes())
    module = next(m for m in source["modules"] if m["name"] == "dbo.sp_TARGETS_MASTER")
    raw = read(SQL_HEAD, module["path"])
    assert hashlib.sha256(raw).hexdigest() == module["source_sha256"]
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    body = text[text.index("ALTER PROCEDURE [dbo].[sp_TARGETS_MASTER]") :].strip()
    assert legacy_definition_hash(body) == module["definition_sha256"]
    migration = (
        read(SQL_HEAD, "migrations/20261016_002_atomic_configuration_publication.sql")
        .decode("utf-8-sig")
        .replace("\r\n", "\n")
    )
    match = re.search(
        r"DECLARE @Apply nvarchar\(max\)=N'((?:[^']|'')*)';\nEXEC sys.sp_executesql @Apply;",
        migration,
    )
    assert match is not None
    assert match[1].replace("''", "'").strip() == body
    historical = read(SQL_BASE, module["path"]).decode("utf-8-sig").replace("\r\n", "\n")
    old_body = historical[historical.index("ALTER PROCEDURE [dbo].[sp_TARGETS_MASTER]") :]
    assert legacy_definition_hash(old_body) not in {
        module["definition_sha256"],
        *module["compatible_definition_sha256"],
    }
