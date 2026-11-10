"""The explicit maintenance worker owns one connection through physical cleanup."""

from types import SimpleNamespace
from uuid import UUID, uuid4

from core.sql_connection_custody import (
    preserve_failure,
    require_sql_admission,
    retain_connection,
)

KINDS = frozenset(
    {"import", "configuration", "player_report", "kvk_output", "final_stats", "post_import"}
)
FIELDS = (
    "Kind",
    "DueGeneration",
    "CompletedGeneration",
    "ClaimedGeneration",
    "ClaimID",
    "State",
    "FirstErrorNumber",
    "LastErrorNumber",
)


def run_maintenance(connect, *, timeout_seconds=300, request_id=None):
    """Consume the entire response; unknown cleanup closes process admission.

    A returned pending/failed/unknown receipt is maintenance evidence only.
    Transport failure does not authorize repeating this request or its import.
    """
    request = str(UUID(str(request_id))) if request_id is not None else str(uuid4())
    require_sql_admission()
    connection = connect()
    cursor = None
    failure = None
    cleanup_error = None
    receipts = []
    try:
        require_sql_admission()
        connection.autocommit = True
        connection.timeout = timeout_seconds
        cursor = connection.cursor()
        cursor.execute("EXEC dbo.usp_update_stats @RequestID=?", request)
        while True:
            if cursor.description:
                columns = tuple(column[0] for column in cursor.description)
                if columns == FIELDS:
                    # The SQL contract contains six fixed rows at most. Never
                    # silently accept duplicate receipts or a truncated response.
                    rows = cursor.fetchmany(7)
                    receipts.extend(dict(zip(columns, row, strict=True)) for row in rows)
                    if len(receipts) > 6:
                        raise ValueError("Maintenance receipt exceeded its finite contract.")
                else:
                    # sp_updatestats can emit diagnostic result sets. Drain them
                    # without retaining arbitrary SQL/provider text in evidence.
                    while cursor.fetchmany(128):
                        pass
            if not cursor.nextset():
                break
        validate_receipts(receipts)
    except BaseException as error:
        failure = error
    finally:
        for phase, action in (
            ("cursor_close", cursor.close if cursor is not None else None),
            ("close", connection.close),
        ):
            if action is None:
                continue
            try:
                action()
            except BaseException as error:
                failure = preserve_failure(failure, error, phase)
                cleanup_error = cleanup_error or error
        if cleanup_error is not None:
            retain_connection(
                SimpleNamespace(connection=connection, cursor=cursor),
                effect="unknown",
                first_failure=failure,
                cleanup_error=cleanup_error,
            )
    if failure is not None:
        raise failure
    return {"request_id": request, "maintenance": receipts}


def validate_receipts(receipts):
    seen = set()
    for row in receipts:
        kind, state = row["Kind"], row["State"]
        if kind not in KINDS or kind in seen:
            raise ValueError("Unexpected maintenance receipt kind.")
        seen.add(kind)
        if state not in {"pending", "running", "complete", "failed", "unknown"}:
            raise ValueError("Unexpected maintenance state.")
        due, done = row["DueGeneration"], row["CompletedGeneration"]
        if not isinstance(due, int) or not isinstance(done, int) or not 0 <= done <= due:
            raise ValueError("Invalid maintenance generation.")
        if state == "complete" and done != due:
            raise ValueError("Incomplete maintenance was labelled complete.")
        if row["ClaimID"] is not None:
            row["ClaimID"] = str(UUID(str(row["ClaimID"])))
    if "post_import" not in seen:
        raise ValueError("The post-import maintenance receipt is missing.")
