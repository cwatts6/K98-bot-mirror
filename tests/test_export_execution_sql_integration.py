"""S11-only opt-in SQL tests. No defaults, predecessor fixtures or provider calls.

The operator supplies a newly prepared disposable target and restricted SQL users.
All resulting synthetic rows are retained; this module does not drop/restore data.
"""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.export_execution_dal import EvidenceCommitUnknown, ExportExecutionDAL


@pytest.fixture
def sql_packet():
    if os.environ.get("K98_S11_SQL_AUTHORIZED") != "S11_EXACT_EVIDENCE_OPERATIONS_APPROVED":
        pytest.skip("S11 SQL target/operations not authorized; authored tests only")
    path = Path(os.environ["K98_S11_SQL_APPROVAL_FILE"])
    if not path.is_absolute() or not path.is_file():
        pytest.fail("Exact S11 approval file required")
    import hashlib

    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ.get("K98_S11_SQL_APPROVAL_SHA256"):
        pytest.fail("Approval-file identity differs")
    packet = json.loads(raw)
    required = {
        "server",
        "database",
        "connection_string",
        "authority_user",
        "reader_user",
        "backup_evidence",
        "restore_evidence",
    }
    if (
        not required
        <= set(packet)
        <= required | {"closing_probe_scope", "runtime_registration", "enrollment_plan"}
        or not packet["database"].startswith("K98_S11_Disposable_")
        or any(not isinstance(packet[k], str) or not packet[k] for k in required)
    ):
        pytest.fail(
            "Exact new disposable target/principals and backup/actual restore evidence required"
        )
    # No live state is inferred from a filename; operators retain and approve the
    # actual backup/restore evidence before providing this explicit packet.
    return packet


@pytest.fixture
def legacy_permission_sql_packet():
    """Separate, disabled gate: legacy bodies hard-code ROK_TRACKER.

    Never rename the ordinary S11 evidence fixture to imitate this target. G4
    provisions a separate disposable SQL instance, original procedure bodies,
    exact signatures and a restricted login before approving these operations.
    """
    if (
        os.environ.get("K98_S11_LEGACY_SQL_AUTHORIZED")
        != "S11_EXACT_LEGACY_PERMISSION_TESTS_APPROVED"
    ):
        pytest.skip("Legacy permission/transaction SQL fixture not authorized; authored only")
    import hashlib

    path = Path(os.environ["K98_S11_LEGACY_SQL_APPROVAL_FILE"])
    if not path.is_absolute() or not path.is_file():
        pytest.fail("Exact legacy SQL approval file required")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != os.environ.get("K98_S11_LEGACY_SQL_APPROVAL_SHA256"):
        pytest.fail("Legacy SQL approval-file identity differs")
    packet = json.loads(raw)
    if (
        set(packet)
        != {
            "purpose",
            "server",
            "database",
            "connection_string",
            "legacy_contract",
            "backup_evidence",
            "restore_evidence",
            "operations",
        }
        or packet["purpose"] != "S11_LEGACY_DISPOSABLE_PERMISSION_TEST"
        or packet["database"] != "ROK_TRACKER"
        or not isinstance(packet["server"], str)
        or "K98_S11_Disposable_" not in packet["server"]
        or packet["operations"]
        != [
            "readiness",
            "denied_child_execute",
            "denied_evidence_update",
            "configuration_fallback_rollback",
        ]
        or any(
            not isinstance(packet[k], str) or not packet[k]
            for k in ("connection_string", "backup_evidence", "restore_evidence")
        )
    ):
        pytest.fail(
            "Exact isolated instance, operation list and actual backup/restore evidence required"
        )
    from services.export_runtime_composition import validate_legacy_installation_contract

    validate_legacy_installation_contract(packet["legacy_contract"])
    assert packet["legacy_contract"]["server"] == packet["server"]
    assert packet["legacy_contract"]["database"] == packet["database"]
    return packet


@pytest.fixture
def legacy_permission_sql_connection(legacy_permission_sql_packet):
    """Use the real restricted login; never impersonate an elevated test connection."""
    import pyodbc

    from services.export_execution_dal import legacy_installation_snapshot
    from services.export_runtime_composition import verify_legacy_installation_contract

    packet = legacy_permission_sql_packet
    connection = pyodbc.connect(packet["connection_string"], autocommit=True, timeout=10)
    try:
        cursor = connection.cursor()
        try:
            observed = legacy_installation_snapshot(cursor, packet["legacy_contract"]["source"])
            verify_legacy_installation_contract(observed, packet["legacy_contract"])
        finally:
            cursor.close()
        yield connection
    finally:
        if not connection.autocommit:
            connection.rollback()
        connection.close()


def test_s11_legacy_restricted_login_cannot_execute_child_or_mutate_evidence(
    legacy_permission_sql_connection,
):
    import pyodbc

    connection = legacy_permission_sql_connection
    cursor = connection.cursor()
    try:
        # Fixed, zero-row evidence statement; an unexpected grant cannot alter data.
        # Child has no matching index columns on this evidence table even if the
        # EXECUTE denial is broken. No file/bulk/provider procedure is invoked.
        for statement in (
            "UPDATE dbo.ExportExecutionStream SET Version=Version WHERE 1=0",
            "EXEC dbo.sp_Create_Excel_For_Kvk_Indexes @FullTableName=N'dbo.ExportExecutionStream',@TableBase=N'S11_PERMISSION_NEGATIVE'",
        ):
            with pytest.raises(pyodbc.Error) as error:
                cursor.execute(statement)
                while cursor.nextset():
                    pass
            assert "229" in str(
                error.value
            ), "Failure must be the permission denial, not an unrelated SQL error"
    finally:
        cursor.close()


@pytest.mark.parametrize("xact_abort", [False, True])
def test_s11_configuration_denied_truncate_fallback_preserves_caller_transaction(
    legacy_permission_sql_connection, xact_abort
):
    """AUTHORED ONLY: original helper, real permission failure and explicit rollback.

    G4 supplies exactly one synthetic staging row (KVK_NO=2147483000, every other
    column NULL) in the isolated instance. No upsert, business root or export runs.
    Both session settings must be observed; a doomed transaction is a failure,
    never evidence to broaden Bot DDL grants or retry the import automatically.
    """
    import pandas as pd

    from sheet_importer import write_df_to_table

    connection = legacy_permission_sql_connection
    cursor = connection.cursor()
    columns = (
        "KVK_NO",
        "LASTKVKEND",
        "MATCHMAKING_SCAN",
        "PRE_PASS_4_SCAN",
        "PASS4END",
        "PASS6END",
        "PASS7END",
        "KVK_END_SCAN",
        "CURRENTKVK3",
        "DRAFTSCAN",
    )
    select = "SELECT " + ",".join("[" + c + "]" for c in columns) + " FROM dbo.ProcConfig_Staging"
    baseline = [(2147483000, *([None] * 9))]
    try:
        cursor.execute(select)
        assert [tuple(row) for row in cursor.fetchall()] == baseline
        cursor.execute("SELECT HAS_PERMS_BY_NAME('dbo.ProcConfig_Staging','OBJECT','ALTER')")
        assert cursor.fetchone()[0] == 0
        cursor.execute("SET XACT_ABORT " + ("ON" if xact_abort else "OFF"))
        connection.autocommit = False
        cursor.execute("BEGIN TRANSACTION")
        result = write_df_to_table(
            cursor,
            connection,
            pd.DataFrame({"KVK_NO": [2147483001]}),
            "dbo.ProcConfig_Staging",
            mode="truncate",
            transactional=True,
        )
        assert result["status"] == "ok", result
        cursor.execute("SELECT @@TRANCOUNT,XACT_STATE()")
        transaction_count, transaction_state = cursor.fetchone()
        assert transaction_count > 0 and transaction_state == 1
        cursor.execute(select)
        assert [tuple(row) for row in cursor.fetchall()] == [(2147483001, *([None] * 9))]
        connection.rollback()
        connection.autocommit = True
        cursor.execute(select)
        assert [tuple(row) for row in cursor.fetchall()] == baseline
    finally:
        if not connection.autocommit:
            connection.rollback()
            connection.autocommit = True
        cursor.close()


@pytest.fixture
def closing_probe_scope(sql_packet):
    """Operator provisions a NEW synthetic closing operation; this fixture only reads it.

    The reviewed approval file may add closing_probe_scope with the exact typed
    IPC scope. No retained production/S6/S8 operation is an eligible fixture.
    """
    from scripts.run_export_authority import AuthorityBroker

    if "closing_probe_scope" not in sql_packet or "runtime_registration" not in sql_packet:
        pytest.skip("No exact synthetic closing-operation scope in the approved SQL packet")
    scope = sql_packet["closing_probe_scope"]
    assert (scope["OwnerKind"], scope["Purpose"], scope["OwnerID"], scope["Fence"]) == (
        "operation",
        "probe",
        None,
        0,
    )
    admitted = []
    from services.export_runtime_composition import RuntimeRegistration

    broker = AuthorityBroker(
        SimpleNamespace(open_stream=lambda **kw: admitted.append(kw["scope"]) or kw["stream_id"]),
        RuntimeRegistration(sql_packet["runtime_registration"]),
    )
    broker.dispatch(dict(version=1, action="open", stream_id=str(uuid4()), scope=scope))
    return admitted[0]


def test_s11_closing_probe_exact_admission_and_mutation_rejection(
    sql_connections, sql_packet, closing_probe_scope
):
    """AUTHORED ONLY: transaction proof; synthetic evidence never claims provider success."""
    dal = ExportExecutionDAL(lambda: sql_connections(sql_packet["authority_user"]))
    session_id = str(uuid4())
    dal.transition(
        "session",
        SessionID=session_id,
        Action="open",
        ExpectedVersion=0,
        HostIdentity="s11-closing-probe-fixture",
        BootID=str(uuid4()),
        ExecutableHash=b"e" * 32,
        ManifestHash=b"m" * 32,
    )
    scope = closing_probe_scope
    # Each rejection must leave no stream row. Nothing rewrites an operation or claim.
    invalid = [
        {"Purpose": "mutation"},
        {"OwnerID": str(uuid4()), "Fence": 1},
        {"Fence": 1},
        {"ClaimVersion": scope["ClaimVersion"] + 1},
        {"Epoch": scope["Epoch"] + 1},
        {"RegistrationHash": b"x" * 32},
        {
            "ScopeJson": json.dumps(
                {"resources": [{"key": "account:" + scope["AccountKey"], "version": 1}]}
            )
        },
    ]
    for change in invalid:
        stream_id = str(uuid4())
        with pytest.raises(EvidenceCommitUnknown):
            dal.transition(
                "stream",
                SessionID=session_id,
                StreamID=stream_id,
                Action="open",
                ExpectedVersion=0,
                ChildIdentity=str(uuid4()),
                **(scope | change),
            )
        assert dal.read_stream(stream_id) is None
    stream_id, child_id = str(uuid4()), str(uuid4())
    opened = dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        Action="open",
        ExpectedVersion=0,
        ChildIdentity=child_id,
        **scope,
    )
    assert opened["OwnerID"] is None and opened["Fence"] == 0
    second_id = str(uuid4())
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition(
            "stream",
            SessionID=session_id,
            StreamID=second_id,
            Action="open",
            ExpectedVersion=0,
            ChildIdentity=str(uuid4()),
            **scope,
        )
    assert dal.read_stream(second_id) is None
    target = next(
        r["key"].removeprefix("destination:")
        for r in json.loads(scope["ScopeJson"])["resources"]
        if r["key"].startswith("destination:")
    )
    request_id = str(uuid4())
    base = dict(
        SessionID=session_id,
        StreamID=stream_id,
        AccountKey=scope["AccountKey"],
        RequestID=request_id,
        EvidenceHash=b"e" * 32,
        EvidenceReference=str(uuid4()),
    )
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition(
            "event",
            **base,
            EventID=str(uuid4()),
            ExpectedVersion=1,
            State="prepared",
            Operation="drive.files.update",
            RequestKind="mutation",
            TargetID=target,
            PayloadHash=b"p" * 32,
            PayloadReference=str(uuid4()),
        )
    assert dal.read_request(request_id) == (None, [])
    # NULL must not disable SQL's version comparison. Each rejected prepare
    # preserves both request absence and the complete admitted stream row.
    for wrong_version in (None, 0, -1, opened["Version"] + 1):
        with pytest.raises(EvidenceCommitUnknown):
            dal.transition(
                "event",
                **base,
                EventID=str(uuid4()),
                ExpectedVersion=wrong_version,
                State="prepared",
                Operation="drive.files.get",
                RequestKind="read",
                TargetID=target,
                PayloadHash=b"p" * 32,
                PayloadReference=str(uuid4()),
            )
        assert dal.read_request(request_id) == (None, [])
        assert dal.read_stream(stream_id) == opened
    prepared = dal.transition(
        "event",
        **base,
        EventID=str(uuid4()),
        ExpectedVersion=1,
        State="prepared",
        Operation="drive.files.get",
        RequestKind="read",
        TargetID=target,
        PayloadHash=b"p" * 32,
        PayloadReference=str(uuid4()),
    )
    retained_request = dal.read_request(request_id)
    for wrong_version in (None, 0, opened["Version"], prepared["Version"] + 1):
        with pytest.raises(EvidenceCommitUnknown):
            dal.transition(
                "event",
                **base,
                EventID=str(uuid4()),
                ExpectedVersion=wrong_version,
                State="not_sent",
            )
        assert dal.read_request(request_id) == retained_request
        assert dal.read_stream(stream_id) == prepared
    terminal = dal.transition(
        "event", **base, EventID=str(uuid4()), ExpectedVersion=prepared["Version"], State="not_sent"
    )
    frozen = dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        AccountKey=scope["AccountKey"],
        Action="freeze",
        ExpectedVersion=terminal["Version"],
    )
    count, event_digest = dal.stream_digest(stream_id)
    # These are disposable synthetic SQL values, not genuine Windows closure evidence.
    dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        AccountKey=scope["AccountKey"],
        Action="close",
        ExpectedVersion=frozen["Version"],
        ChildIdentity=child_id,
        ClosureHash=b"c" * 32,
        ClosureReference=str(uuid4()),
        EventDigest=event_digest,
        LastSequence=count,
    )
    dal.transition("session", SessionID=session_id, Action="close", ExpectedVersion=1)


@pytest.fixture
def sql_connections(sql_packet):
    import pyodbc

    def connect(principal):
        connection = pyodbc.connect(sql_packet["connection_string"], autocommit=True, timeout=5)
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
            assert tuple(cursor.fetchone()) == (sql_packet["server"], sql_packet["database"])
            cursor.execute("DECLARE @u sysname=?; EXECUTE AS USER=@u;", principal)
            cursor.close()
            return connection
        except BaseException:
            connection.close()
            raise

    return connect


def test_s11_session_stale_version_rejected_and_positive_control(sql_connections, sql_packet):
    dal = ExportExecutionDAL(lambda: sql_connections(sql_packet["authority_user"]))
    session = str(uuid4())
    opened = dal.transition(
        "session",
        SessionID=session,
        Action="open",
        ExpectedVersion=0,
        HostIdentity="s11-synthetic",
        BootID=str(uuid4()),
        ExecutableHash=b"e" * 32,
        ManifestHash=b"m" * 32,
    )
    assert opened["Version"] == 1
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition("session", SessionID=session, Action="close", ExpectedVersion=2)
    closed = dal.transition("session", SessionID=session, Action="close", ExpectedVersion=1)
    assert closed["State"] == "closed" and closed["Version"] == 2


def test_s11_session_creation_race_has_one_winner(sql_connections, sql_packet):
    session = str(uuid4())
    args = dict(
        SessionID=session,
        Action="open",
        ExpectedVersion=0,
        HostIdentity="s11-synthetic-race",
        BootID=str(uuid4()),
        ExecutableHash=b"e" * 32,
        ManifestHash=b"m" * 32,
    )

    def compete(_):
        try:
            return ExportExecutionDAL(
                lambda: sql_connections(sql_packet["authority_user"])
            ).transition("session", **args)
        except EvidenceCommitUnknown:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(compete, range(2)))
    assert sum(row is not None for row in results) == 1


@pytest.mark.parametrize("role_key", ["authority_user", "reader_user"])
def test_s11_effective_rights_deny_direct_evidence_dml(sql_connections, sql_packet, role_key):
    connection = sql_connections(sql_packet[role_key])
    try:
        cursor = connection.cursor()
        for table in (
            "ExportExecutionSession",
            "ExportExecutionStream",
            "ExportProviderRequest",
            "ExportProviderRequestEvent",
            "ExportReconciliationProof",
            "ExportManagedFileOrigin",
        ):
            for permission in (
                "INSERT",
                "UPDATE",
                "DELETE",
                "ALTER",
                "CONTROL",
                "TAKE OWNERSHIP",
            ):
                cursor.execute(
                    "SELECT HAS_PERMS_BY_NAME(?, 'OBJECT', ?)", "dbo." + table, permission
                )
                assert cursor.fetchone()[0] == 0
        if role_key == "reader_user":
            cursor.execute(
                "SELECT HAS_PERMS_BY_NAME('dbo.usp_ExportReconciliationProofIssue','OBJECT','EXECUTE')"
            )
            assert cursor.fetchone()[0] == 0
            cursor.execute(
                "SELECT HAS_PERMS_BY_NAME('dbo.usp_ExportOutputEnrollmentTransition','OBJECT','EXECUTE')"
            )
            assert cursor.fetchone()[0] == 0
        cursor.close()
    finally:
        connection.close()


def test_s11_enrollment_refuses_replay_stale_owner_and_unproven_binding(
    sql_connections, sql_packet
):
    """AUTHORED ONLY. Retains synthetic preparation/account ownership and empty stream."""
    from services.export_enrollment_service import EnrollmentPlan, enrollment_scope

    if "enrollment_plan" not in sql_packet:
        pytest.skip("No exact synthetic enrollment operations in the approved SQL packet")
    plan = EnrollmentPlan(sql_packet["enrollment_plan"])
    assert plan.value()["account"].startswith("s11-enrollment-fixture-")
    dal = ExportExecutionDAL(lambda: sql_connections(sql_packet["authority_user"]))
    session_id, prep_id, owner_id = str(uuid4()), str(uuid4()), str(uuid4())
    dal.transition(
        "session",
        SessionID=session_id,
        Action="open",
        ExpectedVersion=0,
        HostIdentity="s11-enrollment-fixture",
        BootID=str(uuid4()),
        ExecutableHash=b"e" * 32,
        ManifestHash=bytes.fromhex(plan.value()["manifest_sha256"]),
    )
    common = dict(
        SessionID=session_id,
        PreparationID=prep_id,
        AccountKey=plan.value()["account"],
        OwnerID=owner_id,
    )
    begin = dict(
        Action="begin",
        ExpectedVersion=0,
        PlanJson=plan.sql_json,
        Actor="s11-fixture",
        Reason="Exact authorized synthetic SQL checks",
    )
    claim = dal.transition("enrollment", **common, **begin)
    # Admission owns resources even before its first provider stream exists.
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition("session", SessionID=session_id, Action="close", ExpectedVersion=1)
    assert dal.read_session(session_id)["State"] == "open"
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition("enrollment", **common, **begin)
    for damage in ({"ExpectedVersion": claim["Version"] + 1}, {"OwnerID": str(uuid4())}, {}):
        with pytest.raises(EvidenceCommitUnknown):
            dal.transition(
                "enrollment",
                **(
                    common
                    | dict(
                        Action="bind",
                        ExpectedVersion=claim["Version"],
                        Fence=claim["Fence"],
                        ResourcesJson=claim["ResourcesJson"],
                        Ordinal=0,
                        FileID="s11-unproven-file",
                        CreationStreamID=str(uuid4()),
                        CreationRequestID=str(uuid4()),
                        ResponseEventID=str(uuid4()),
                        OriginHash=b"o" * 32,
                        OriginReference=str(uuid4()),
                    )
                    | damage
                ),
            )
    scope = enrollment_scope(plan, claim)
    stream_id, child_id = str(uuid4()), str(uuid4())
    row = dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        Action="open",
        ExpectedVersion=0,
        ChildIdentity=child_id,
        **scope,
    )
    row = dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        AccountKey=plan.value()["account"],
        Action="freeze",
        ExpectedVersion=row["Version"],
    )
    dal.transition(
        "stream",
        SessionID=session_id,
        StreamID=stream_id,
        AccountKey=plan.value()["account"],
        Action="close",
        ExpectedVersion=row["Version"],
        ChildIdentity=child_id,
        ClosureHash=b"c" * 32,
        ClosureReference=str(uuid4()),
        EventDigest=b"d" * 32,
        LastSequence=0,
    )
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition(
            "stream",
            SessionID=session_id,
            StreamID=str(uuid4()),
            Action="open",
            ExpectedVersion=0,
            ChildIdentity=str(uuid4()),
            **scope,
        )
    assert dal.read_origins(plan.value()["account"], ["s11-unproven-file"]) == []
    # A closed phase does not mean its enclosing enrollment is complete.
    with pytest.raises(EvidenceCommitUnknown):
        dal.transition("session", SessionID=session_id, Action="close", ExpectedVersion=1)
    session = dal.read_session(session_id)
    assert session["State"] == "open" and session["Version"] == 1
    # No provider success, origin eligibility, release, cleanup or pool activation.
