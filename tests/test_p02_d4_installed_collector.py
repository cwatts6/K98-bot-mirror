"""Exercise native output custody without connecting the collector to any database."""

from contextlib import closing
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from scripts.p02_d4_inventory import ROOTS

SOURCE = Path(__file__).resolve().parents[1] / "scripts/collect_p02_d4_installed.ps1"


def test_installed_and_offline_root_inventory_match():
    source = SOURCE.read_text(encoding="utf-8")
    assert "version=2; kind='p02_d4_installed_metadata'" in source
    roots = source.split("$roots = @'", 1)[1].split("'@", 1)[0]
    assert set(re.findall(r"\(N'([^']+)'\)", roots)) == set(ROOTS)


@pytest.fixture
def powershell():
    executable = shutil.which("powershell.exe")
    if executable is None:
        pytest.skip("Windows PowerShell 5.1 required for native collector checks")
    return executable


def run_script(powershell, path, output):
    return subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(path),
            "-OutputFile",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )


def test_wrong_machine_refuses_before_creating_output(powershell, tmp_path):
    if os.environ.get("COMPUTERNAME", "").casefold() == "mini_amd":
        pytest.skip("Never invoke this test on the installed target")
    output = tmp_path / "receipt.json"
    result = run_script(powershell, SOURCE, output)
    assert result.returncode != 0
    assert "requires MINI_AMD" in result.stderr
    assert not output.exists()


def test_native_private_output_acl_and_no_overwrite(powershell, tmp_path):
    # Execute only the output-creation prefix. The SQL connection and all query
    # execution are absent. The genuine machine guard is separately tested above.
    source = SOURCE.read_text(encoding="utf-8")
    prefix = source.split("$timer =", 1)[0]
    prefix = "\n".join(
        line for line in prefix.splitlines() if not line.startswith("if ($env:COMPUTERNAME")
    )
    script = tmp_path / "output_fixture.ps1"
    script.write_text(
        prefix + "\n$output.Dispose()\n"
        "$a=[IO.File]::GetAccessControl($outputPath)\n"
        "if(-not $a.AreAccessRulesProtected){throw 'inherited_acl'}\n"
        "if(@($a.Access).Count -ne 2){throw 'unexpected_acl'}\n",
        encoding="utf-8",
    )
    output = tmp_path / "receipt.json"
    first = run_script(powershell, script, output)
    assert first.returncode == 0, first.stderr
    output.write_text("preserve exact prior receipt", encoding="utf-8")
    second = run_script(powershell, script, output)
    assert second.returncode != 0
    assert output.read_text(encoding="utf-8") == "preserve exact prior receipt"


def catalog_queries(powershell, tmp_path):
    """Evaluate only the three fixed data assignments, never the collector body."""
    extractor = tmp_path / "queries.ps1"
    extractor.write_text(
        "param([string]$Source)\n$ErrorActionPreference='Stop'\n"
        "$tokens=$null;$errors=$null\n"
        "$ast=[System.Management.Automation.Language.Parser]::ParseFile("
        "$Source,[ref]$tokens,[ref]$errors)\n"
        "if($errors.Count){throw 'parse_failed'}\n"
        "foreach($name in @('$roots','$queries','$jobs')){\n"
        " $s=@($ast.EndBlock.Statements | Where-Object {"
        " $_ -is [System.Management.Automation.Language.AssignmentStatementAst]"
        " -and $_.Left.Extent.Text -ceq $name })\n"
        " if($s.Count -ne 1){throw 'assignment_count'}\n"
        " . ([scriptblock]::Create($s[0].Extent.Text))\n}\n"
        "@($queries)+@(@{name='jobs';sql=$jobs}) | ConvertTo-Json -Depth 6\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(extractor),
            "-Source",
            str(SOURCE),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_fixed_queries_extract_without_running_collector(powershell, tmp_path):
    queries = catalog_queries(powershell, tmp_path)
    assert len(queries) == 13
    assert len({q["name"] for q in queries}) == 13
    for query in queries:
        assert "TOP(513)" in query["sql"]
        # SQL text consists of fixed metadata reads. No application execution.
        assert not re.search(
            r"\b(EXEC(?:UTE)?|INSERT|UPDATE|DELETE|ALTER|DROP|CREATE|MERGE|BACKUP)\b",
            query["sql"],
            re.I,
        )


def test_activity_is_metadata_only_and_jobs_include_id_only_bindings(powershell, tmp_path):
    queries = {q["name"]: q["sql"] for q in catalog_queries(powershell, tmp_path)}
    assert "o.create_date,o.modify_date" in queries["objects"]
    assert "p.cached_time,p.last_execution_time" in queries["procedure_activity"]
    assert "p.database_id=DB_ID()" in queries["procedure_activity"]
    assert "sys.database_query_store_options" in queries["query_store_options"]
    assert "retained_statement_executions" in queries["query_store_activity"]
    assert "j.job_id) AS job_id" in queries["jobs"]
    assert "WHERE st.database_name" not in queries["jobs"]
    assert "st.command AS" not in queries["jobs"]


def test_native_catalog_queries(powershell, tmp_path, snapshot_database):
    import pyodbc

    queries = catalog_queries(powershell, tmp_path)
    with closing(
        pyodbc.connect(snapshot_database.connection_string, autocommit=True, timeout=5)
    ) as con:
        con.timeout = 3
        con.execute("CREATE SEQUENCE dbo.KS4_UNO_SEQ AS bigint START WITH 42 INCREMENT BY 2")
        con.execute("CREATE PROCEDURE dbo.UPDATE_ALL AS SELECT 1")
        # Exercise only this inert disposable fixture, never an installed procedure.
        con.execute("EXEC dbo.UPDATE_ALL").fetchall()
        con.execute("CREATE ROLE d4_reader")
        con.execute("GRANT EXECUTE ON dbo.UPDATE_ALL TO d4_reader")
        for query in queries:
            if query["name"] == "jobs":
                continue
            cursor = con.execute(query["sql"])
            names = [c[0] for c in cursor.description]
            rows = [dict(zip(names, row, strict=True)) for row in cursor.fetchall()]
            if query["name"] == "sequence":
                assert rows[0]["start_value"] == "42"
                assert rows[0]["increment_value"] == "2"
            if query["name"] == "objects":
                item = next(r for r in rows if r["requested_name"] == "UPDATE_ALL")
                assert "SELECT 1" in item["definition"]
                assert item["create_date"] is not None
            if query["name"] == "procedure_activity":
                item = next(r for r in rows if r["module_name"] == "UPDATE_ALL")
                assert item["execution_count"] >= 1
                assert item["last_execution_time"] >= item["cached_time"]
            if query["name"] == "query_store_options":
                assert len(rows) == 1 and rows[0]["actual_state_desc"]
            if query["name"] == "grants":
                assert any(
                    r["grantee"] == "d4_reader" and r["permission_name"] == "EXECUTE" for r in rows
                )
    # Read-only compilation/execution against this guarded local instance's msdb.
    # Never call the returned jobs or inspect their command bodies.
    local_msdb = snapshot_database.connection_string.replace(snapshot_database.name, "msdb")
    with closing(pyodbc.connect(local_msdb, autocommit=True, timeout=5)) as con:
        con.timeout = 3
        con.execute(next(q["sql"] for q in queries if q["name"] == "jobs")).fetchall()
