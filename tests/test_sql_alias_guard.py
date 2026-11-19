"""Independent syntax checks and automatic discovery, never a SQL connection."""

from pathlib import Path
import subprocess

import pytest

from scripts.validate_sql_aliases import alias_errors, source_errors, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1 AS RowCount",
        "SELECT 1 aS /* outer /* inner */ end */ bAcKuP",
        "SELECT 1 AS -- comment\nRowCount",
        "SELECT 1 AS /* apostrophe ' */ RowCount",
        "UPDATE dbo.T SET RowCount=?",
        "INSERT dbo.T (ID, RowCount) VALUES(?,?)",
    ],
)
def test_reserved_identifiers_are_rejected_independent_of_old_sites(query):
    assert alias_errors(query)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT 1 AS [RowCount], 2 AS [backup]",
        'SELECT 1 AS "RowCount"',
        "SELECT 'AS RowCount' AS [Text]",
        "SELECT @@ROWCOUNT AS [N]",
        "SET ROWCOUNT 1; SELECT 1; SET ROWCOUNT 0;",
        "SELECT @RowCount AS [N]",
        "SELECT 1 /* AS RowCount */ AS [N]",
    ],
)
def test_sql_language_constructs_strings_comments_and_delimiters_remain_valid(query):
    assert not alias_errors(query)


@pytest.mark.parametrize(
    "name,text",
    [
        ("new.py", 'sql = "SELECT 1 AS " + "RowCount"'),
        ("new.py", 'sql = f"SELECT {value} AS RowCount"'),
        ("new.ps1", "$sql = @'\nSELECT 1 AS RowCount\n'@"),
        ("new.sql", "SELECT 1 AS backup"),
    ],
)
def test_new_source_files_and_python_string_forms_are_checked(name, text):
    assert source_errors(name, text)


def test_repository_discovery_includes_untracked_new_queries(tmp_path):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    (tmp_path / "new_query.py").write_text('QUERY = "SELECT 1 AS RowCount"')
    assert any("new_query.py" in error for error in validate(tmp_path))


def test_whole_current_repository_reserved_identifier_guard():
    assert validate(ROOT) == []
