"""Player report/cache SQL resources; explicit commits stay with the producer."""

from contextlib import contextmanager
from types import SimpleNamespace

from core.sql_connection_custody import (
    SqlCleanupUnknown,
    preserve_failure,
    require_sql_admission,
    retain_connection,
)
from core.sql_operation_policy import player_statement_seconds


@contextmanager
def player_connection(*, operation):
    from file_utils import get_conn_with_retries

    require_sql_admission()
    connection = get_conn_with_retries(meta={"operation": operation})
    failure = None
    cleanup_error = None
    try:
        require_sql_admission()
        yield connection
    except BaseException as error:
        failure = error
    finally:
        for phase, action in (("rollback", connection.rollback), ("close", connection.close)):
            try:
                action()
            except BaseException as error:
                failure = preserve_failure(failure, error, "player_" + phase)
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            retain_connection(
                connection, effect="unknown", first_failure=failure, cleanup_error=cleanup_error
            )
    if cleanup_error is not None and isinstance(failure, Exception):
        raise SqlCleanupUnknown("Player SQL cleanup remains unconfirmed.") from failure
    if failure is not None:
        raise failure


@contextmanager
def player_report_cursor(connection, *, requested):
    require_sql_admission()
    previous = connection.timeout
    seconds = player_statement_seconds(requested, previous)
    cursor = None
    failure = None
    cleanup_error = None
    restored = False
    try:
        connection.timeout = seconds
        cursor = connection.cursor()
        connection.timeout = previous
        restored = True
        yield cursor, seconds
    except BaseException as error:
        failure = error
    finally:
        for phase, action in (
            (
                "timeout_restore",
                None if restored else lambda: setattr(connection, "timeout", previous),
            ),
            ("cursor_close", cursor.close if cursor is not None else None),
        ):
            if action is None:
                continue
            try:
                action()
            except BaseException as error:
                failure = preserve_failure(failure, error, "player_" + phase)
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            retain_connection(
                SimpleNamespace(connection=connection, cursor=cursor),
                effect="unknown",
                first_failure=failure,
                cleanup_error=cleanup_error,
            )
    if cleanup_error is not None and isinstance(failure, Exception):
        from kvk.dal.new_source_import_dal import UncertainCommit

        if not isinstance(failure, UncertainCommit):
            raise SqlCleanupUnknown(
                "Player report cursor cleanup remains unconfirmed."
            ) from failure
    if failure is not None:
        raise failure
