"""Driver diagnostics preserve transaction behavior without exposing private data."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging
from unittest.mock import Mock

import pyodbc
import pytest

from kvk.dal.new_source_admin_dal import _BorrowedConnection
from kvk.dal.new_source_import_dal import UncertainCommit, transaction
from kvk.dal.source_sql_diagnostics import diagnosed_source_operation, failure_reference


@pytest.mark.parametrize("point", ["execute", "fetchone", "fetchall", "commit"])
def test_safe_diagnostic_and_transaction_semantics(caplog, point):
    caplog.set_level(logging.WARNING)
    sql = "SELECT private_column FROM private_table WHERE secret=?"
    error = pyodbc.ProgrammingError(
        "42000", "[driver] Private workbook value PASSWORD=secret (229) (SQLExecDirectW)"
    )
    cursor = Mock()
    connection = Mock(autocommit=False)
    connection.cursor.return_value = cursor
    if point == "execute":
        cursor.execute.side_effect = [None, error]
    elif point == "commit":
        connection.commit.side_effect = error
    else:
        getattr(cursor, point).side_effect = error

    @diagnosed_source_operation
    def operation():
        with transaction(lambda: connection) as cur:
            cur.execute(sql, "private parameter")
            if point in ("fetchone", "fetchall"):
                getattr(cur, point)()

    expected = UncertainCommit if point == "commit" else pyodbc.ProgrammingError
    with pytest.raises(expected) as caught:
        operation()
    if point != "commit":
        assert caught.value is error
    assert failure_reference(caught.value) in caplog.text
    assert f"stage={point}" in caplog.text
    assert "sqlstate=42000 native=229" in caplog.text
    if point != "commit":
        assert hashlib.sha256(sql.encode()).hexdigest()[:16] in caplog.text
    for private in ("private_column", "private_table", "secret", "PASSWORD", "workbook"):
        assert private not in caplog.text
    assert connection.rollback.call_count == (point != "commit")
    assert connection.commit.call_count == (point == "commit")
    connection.close.assert_called_once()


def test_borrowed_cursor_has_one_diagnostic_and_outer_rollback(caplog):
    conn = Mock(autocommit=False)
    cursor = conn.cursor.return_value
    error = pyodbc.ProgrammingError("42S22", "Private column (207) (SQLExecDirectW)")
    cursor.execute.side_effect = [None, None, error]

    @diagnosed_source_operation
    def inner(cur):
        with transaction(lambda: _BorrowedConnection(cur)) as borrowed:
            borrowed.execute("INSERT synthetic VALUES (?)", "private")

    @diagnosed_source_operation
    def outer():
        with transaction(lambda: conn) as cur:
            inner(cur)

    with pytest.raises(pyodbc.ProgrammingError) as caught:
        outer()
    assert caught.value is error
    assert caplog.text.count("Source SQL failure") == 1
    conn.rollback.assert_called_once()
    conn.commit.assert_not_called()
    conn.close.assert_called_once()


def test_cleanup_failure_does_not_erase_initial_sql_diagnostic(caplog):
    conn = Mock(autocommit=False)
    conn.cursor.return_value.execute.side_effect = [None, pyodbc.Error("42000", "secret")]
    conn.rollback.side_effect = RuntimeError("private rollback failure")

    @diagnosed_source_operation
    def operation():
        with transaction(lambda: conn) as cur:
            cur.execute("INSERT synthetic VALUES (?)", "secret")

    with pytest.raises(RuntimeError) as caught:
        operation()
    assert failure_reference(caught.value) in caplog.text
    assert "stage=execute" in caplog.text
    assert "sqlstate=42000 native=unknown" in caplog.text
    assert "secret" not in caplog.text and "private" not in caplog.text


def test_no_diagnostics_for_domain_rejection_or_success(caplog):
    conn = Mock(autocommit=False)

    @diagnosed_source_operation
    def operation(reject):
        with transaction(lambda: conn):
            if reject:
                raise ValueError("controlled conflict")
        return 7

    assert operation(False) == 7
    with pytest.raises(ValueError) as caught:
        operation(True)
    assert failure_reference(caught.value) is None
    assert "Source SQL failure" not in caplog.text


def test_each_concurrent_operation_has_its_own_reference():
    @diagnosed_source_operation
    def operation():
        conn = Mock(autocommit=False)
        conn.cursor.return_value.execute.side_effect = pyodbc.Error("HY000", "private")
        with transaction(lambda: conn):
            pass

    def invoke(_):
        try:
            operation()
        except pyodbc.Error as exc:
            return failure_reference(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        refs = list(pool.map(invoke, range(4)))
    assert None not in refs and len(set(refs)) == 4


@pytest.mark.parametrize("reference", ["secret", "@everyone", "a" * 33, None])
def test_untrusted_reference_is_never_displayed(reference):
    exc = RuntimeError("private")
    exc.source_sql_correlation = reference
    assert failure_reference(exc) is None


@pytest.mark.asyncio
async def test_discord_gets_only_correlation_and_safe_recovery_guidance(caplog):
    from tests.test_kvk_source_import_view import interaction
    from ui.views.kvk_source_import_view import report_failure

    exc = pyodbc.ProgrammingError("42000", "secret workbook contents")
    exc.source_sql_correlation = "a" * 32
    inter = interaction()
    await report_failure(inter, exc)
    text = inter.response.send_message.call_args.args[0]
    assert "a" * 32 in text
    assert "Do not repeat the confirmation blindly" in text
    assert "secret" not in text + caplog.text
    assert inter.response.send_message.call_args.kwargs["ephemeral"]
