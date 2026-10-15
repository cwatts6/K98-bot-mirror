"""Compile literal migration postimages in temporary procedures only."""

import hashlib
import json
import os
from pathlib import Path
import re

import pytest

from tests import test_export_target_containment_sql as fixture_module

contained_job = fixture_module.contained_job
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)


def test_migration_postimages_match_engine_definitions_and_pinned_sources(contained_job):
    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"])
    text = (root / "migrations/20261015_008_export_target_containment.sql").read_text()
    bodies = re.findall(
        r"SET @Apply=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;", text, re.S
    )
    assert len(bodies) == 5
    manifest = json.loads(
        (
            Path(__file__).resolve().parents[1] / "deploy/export_application_schema_source.json"
        ).read_text()
    )
    sql = contained_job.sql
    for index, escaped in enumerate(bodies):
        body = escaped.replace("''", "'")
        name = re.search(r"PROCEDURE (\S+)", body)[1]
        temporary = "#K98TargetImage" + str(index)
        rewritten = fixture_module.local_sql(body.replace(name, temporary, 1))
        # Proof/session helpers have dependencies not exercised in this test;
        # this compiles bodies but never executes them or installs permanent DDL.
        sql.execute(rewritten)
        actual = sql.execute(
            "SELECT definition FROM tempdb.sys.sql_modules WHERE object_id=OBJECT_ID(?)",
            "tempdb.." + temporary,
        ).fetchval()
        actual = actual.replace(temporary, name, 1).replace("\r\n", "\n")
        for identifier in sorted(
            (*fixture_module.TABLES, *fixture_module.PROCEDURES), key=len, reverse=True
        ):
            actual = actual.replace("#" + identifier.split(".")[1], identifier)
        actual = re.sub(
            r"^(?:CREATE OR ALTER|CREATE  |ALTER) PROCEDURE", "CREATE PROCEDURE", actual
        )
        expected = body.replace("CREATE OR ALTER PROCEDURE", "CREATE PROCEDURE", 1)
        assert actual == expected
        assert "0x" + hashlib.sha256(actual.encode("utf-16-le")).hexdigest() in text
        source = (root / ("sql_schema/" + name + ".StoredProcedure.sql")).read_text(
            encoding="utf-8-sig"
        )
        assert (
            source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
            == expected.strip()
        )
        assert (
            next(v["sha256"] for v in manifest if v["name"] == name)
            == hashlib.sha256(source.encode()).hexdigest()
        )
    # The migration's compiled trusted post-constraint must equal the actual
    # authoritative table constraint, not merely contain the new state text.
    start = text.index("CREATE TABLE #K98TargetStateBefore")
    end = text.index("DECLARE @Before", start)
    sql.execute(text[start:end])
    expected = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#ExportExecutionStream') AND name LIKE 'CK_ExportExecutionStream_State%'"
    ).fetchval()
    actual = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#K98TargetStateAfter')"
    ).fetchval()
    assert actual == expected
