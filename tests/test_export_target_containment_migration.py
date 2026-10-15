"""Compile literal migration postimages in temporary procedures only."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

import pytest

from tests import test_export_target_containment_sql as fixture_module

contained_job = fixture_module.contained_job
pytestmark = pytest.mark.skipif(
    os.getenv("K98_TARGET_CONTAINMENT_SQL") != "1", reason="Explicit temporary SQL opt-in"
)
PREDECESSOR = "79987f7bd5e40aaecc66a36bcbd8ecdc93522667"


def test_replacement_document_bounds_match_reviewed_preimages_and_restrict_other_work(
    contained_job,
):
    import pyodbc

    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"])
    migration = (root / "migrations/20261015_009_guided_export_replacement.sql").read_text()
    blocks = re.findall(
        r"CREATE TABLE #K98BoundBefore.*?DROP TABLE #K98BoundAfter;", migration, re.S
    )
    assert len(blocks) == 3
    sql = contained_job.sql
    for index, (block, table, name, columns, value, allowed, denied) in enumerate(
        zip(
            blocks,
            ("dbo.ExportPreparation", "dbo.ExportExecutionStream", "dbo.RecoveryIncident"),
            (
                "CK_ExportPreparation_Request",
                "CK_ExportExecutionStream_Scope",
                "CK_RecoveryIncident_Evidence",
            ),
            (
                "RequestJson nvarchar(max),ConsumerKind varchar(32)",
                "ScopeJson nvarchar(max),Purpose varchar(16)",
                "EvidenceJson nvarchar(max),SourceKind varchar(64)",
            ),
            (
                dict(version=4, purpose="output_enrollment", padding="x" * 40000),
                dict(padding="x" * 40000),
                dict(padding="x" * 20000),
            ),
            ("config", "enrollment", "export_job"),
            ("scan_data", "probe", "stats_import"),
            strict=True,
        )
    ):
        sql.execute(block[: block.index("IF NOT EXISTS")])
        for old, temporary in ((True, "#K98BoundBefore"), (False, "#K98BoundAfter")):
            path = f"sql_schema/{table}.Table.sql"
            source = (
                subprocess.check_output(
                    ["git", "show", "4867666888b0cc8031c4494b4d92124dfa8ed2c0:" + path], cwd=root
                ).decode("utf-8-sig")
                if old
                else (root / path).read_text(encoding="utf-8-sig")
            )
            line = next(line for line in source.splitlines() if f"CONSTRAINT {name} CHECK " in line)
            check = line.split(" CHECK ", 1)[1].rstrip().removesuffix(",")
            independent = f"#K98IndependentBound{index}{int(old)}"
            sql.execute(f"CREATE TABLE {independent} ({columns}, CHECK {check})")
            definition = lambda table: sql.execute(
                "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID(?)",
                "tempdb.." + table,
            ).fetchval()
            assert definition(temporary) == definition(independent)
        raw = json.dumps(value)
        sql.execute("INSERT #K98BoundAfter VALUES (?,?)", raw, allowed)
        with pytest.raises(pyodbc.Error):
            sql.execute("INSERT #K98BoundAfter VALUES (?,?)", raw, denied)
        if index == 0:
            with pytest.raises(pyodbc.Error):
                sql.execute(
                    "INSERT #K98BoundAfter VALUES (?,?)",
                    json.dumps(dict(value, version=3)),
                    allowed,
                )
        sql.execute("DROP TABLE #K98BoundBefore;DROP TABLE #K98BoundAfter")


@pytest.mark.parametrize("replacement", [False, True])
def test_migration_postimages_match_engine_definitions_and_pinned_sources(
    contained_job, replacement
):
    root = Path(os.environ["K98_TARGET_CONTAINMENT_SQL_SOURCE"])
    migration = (
        "20261015_009_guided_export_replacement"
        if replacement
        else "20261015_008_export_target_containment"
    )
    predecessor_commit = "4867666888b0cc8031c4494b4d92124dfa8ed2c0" if replacement else PREDECESSOR

    def reviewed_source(name, kind):
        path = f"sql_schema/{name}.{kind}.sql"
        if replacement:
            return (root / path).read_text(encoding="utf-8-sig")
        return (
            subprocess.check_output(
                ["git", "show", "4867666888b0cc8031c4494b4d92124dfa8ed2c0:" + path], cwd=root
            )
            .decode("utf-8-sig")
            .replace("\r\n", "\n")
        )

    text = (root / f"migrations/{migration}.sql").read_text()
    bodies = re.findall(
        r"SET @Apply=N'((?:''|[^'])*)';\nEXEC sys.sp_executesql @Apply;", text, re.S
    )
    assert len(bodies) == (8 if replacement else 5)
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
        source = reviewed_source(name, "StoredProcedure")
        assert (
            source[source.index("CREATE PROCEDURE") :].strip().removesuffix("GO").strip()
            == expected.strip()
        )
        assert (
            next(v["sha256"] for v in manifest if v["name"] == name)
            == hashlib.sha256(
                (root / f"sql_schema/{name}.StoredProcedure.sql")
                .read_text(encoding="utf-8-sig")
                .encode()
            ).hexdigest()
        )
        if index < 4:
            predecessor = (
                subprocess.check_output(
                    ["git", "show", f"{predecessor_commit}:sql_schema/{name}.StoredProcedure.sql"],
                    cwd=root,
                )
                .decode("utf-8-sig")
                .replace("\r\n", "\n")
            )
            predecessor = (
                predecessor[predecessor.index("CREATE PROCEDURE") :]
                .strip()
                .removesuffix("GO")
                .rstrip()
                + "\n"
            )
            assert "0x" + hashlib.sha256(predecessor.encode("utf-16-le")).hexdigest() in text
    # The migration's compiled trusted post-constraint must equal the actual
    # authoritative table constraint, not merely contain the new state text.
    start = text.index("CREATE TABLE #K98TargetStateBefore")
    end = text.index("DECLARE @Before", start)
    sql.execute(text[start:end])
    checked_source = reviewed_source("dbo.ExportExecutionStream", "Table")
    check = re.search(r"CONSTRAINT CK_ExportExecutionStream_State CHECK (.*),\n", checked_source)[1]
    table = text[text.index("CREATE TABLE #K98TargetStateAfter") : end]
    table = table[: table.index("CHECK ")] + "CHECK " + check + ");"
    sql.execute(table.replace("#K98TargetStateAfter", "#K98IndependentlyReviewedState"))
    expected = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#K98IndependentlyReviewedState')"
    ).fetchval()
    actual = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#K98TargetStateAfter')"
    ).fetchval()
    assert actual == expected
    # Compile the immutable predecessor independently. Comparing only the
    # postimage missed a generator bug that inserted it into both checks.
    previous = (
        subprocess.check_output(
            [
                "git",
                "show",
                f"{predecessor_commit}:migrations/"
                + (
                    "20261015_008_export_target_containment.sql"
                    if replacement
                    else "20261015_007_read_dispatch_containment.sql"
                ),
            ],
            cwd=root,
        )
        .decode("utf-8-sig")
        .replace("\r\n", "\n")
    )
    previous = previous.replace("#K98TargetStateAfter", "#K98ReadStateAfter")
    start = previous.index("CREATE TABLE #K98ReadStateAfter")
    end = previous.index("DECLARE @Before", start)
    sql.execute(previous[start:end])
    before = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#K98TargetStateBefore')"
    ).fetchval()
    predecessor = sql.execute(
        "SELECT definition FROM tempdb.sys.check_constraints WHERE parent_object_id=OBJECT_ID('tempdb..#K98ReadStateAfter')"
    ).fetchval()
    assert before == predecessor
    assert before != actual
