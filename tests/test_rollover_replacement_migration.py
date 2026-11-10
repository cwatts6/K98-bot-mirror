"""Compile all migration modules on disposable temp procedures and bind exact sources."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

from services.export_execution_dal import _PARAMETERS, _PROCEDURES, CURRENT_INSTALLATION_MIGRATIONS
from tests import test_export_target_containment_sql as fixture_module
from tests.test_rollover_containment_sql import contained_job as contained_job

pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)
PREDECESSOR = "95b4e91b86adbf66f7ab21fc48d195261bf3b4e3"


def module(source):
    return source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").rstrip() + "\n"


def test_migration_compiles_exact_postimages_and_guards_predecessors(contained_job):
    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"])
    text = (root / "migrations/20261016_001_rollover_replacement.sql").read_text(
        encoding="utf-8-sig"
    )
    bodies = re.findall(r"SET @Apply=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;", text)
    assert len(bodies) == 6
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[1] / "deploy/export_application_schema_source.json"
        ).read_text()
    )
    sql = contained_job.sql
    for number, escaped in enumerate(bodies):
        body = escaped.replace("''", "'")
        name = re.search(r"PROCEDURE (\S+)", body)[1]
        temporary = "#RolloverMigration" + str(number)
        sql.execute(fixture_module.local_sql(body.replace(name, temporary, 1)))
        actual = (
            sql.execute(
                "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID(?)",
                "tempdb.." + temporary,
            )
            .fetchval()
            .replace(temporary, name, 1)
            .replace("\r\n", "\n")
        )
        for identifier in sorted(
            (*fixture_module.TABLES, *fixture_module.PROCEDURES), key=len, reverse=True
        ):
            actual = actual.replace("#" + identifier.split(".")[1], identifier)
        actual = re.sub(
            r"^(?:CREATE OR ALTER|CREATE  |ALTER) PROCEDURE", "CREATE PROCEDURE", actual
        )
        relative = "sql_schema/" + name + ".StoredProcedure.sql"
        assert actual == module((root / relative).read_text(encoding="utf-8-sig"))
        assert next(item["sha256"] for item in manifest if item["name"] == name) == (
            hashlib.sha256((root / relative).read_text(encoding="utf-8-sig").encode()).hexdigest()
        )
        assert hashlib.sha256(actual.encode("utf-16-le")).hexdigest() in text
        if number < 5:
            before = (
                subprocess.check_output(["git", "show", PREDECESSOR + ":" + relative], cwd=root)
                .decode("utf-8-sig")
                .replace("\r\n", "\n")
            )
            assert hashlib.sha256(module(before).encode("utf-16-le")).hexdigest() in text
    assert "IF XACT_STATE()<>0 ROLLBACK" in text
    assert "sys.crypt_properties" in text
    assert (
        "DENY EXECUTE ON OBJECT::dbo.usp_ExportRolloverContainTargets TO ExportExecutionReader"
        in text
    )
    assert "20261016_001_rollover_replacement" in CURRENT_INSTALLATION_MIGRATIONS
    assert _PROCEDURES["rollover_containment"] == "dbo.usp_ExportRolloverContainTargets"
    assert "OperationID" in _PARAMETERS["rollover_containment"]
    assert "JobID" not in _PARAMETERS["rollover_containment"]
