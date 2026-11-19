"""One bounded verification of an already running release; no apply or retry.

Executed only from a separately sealed administrative packet. The original
source, startup policy, release files and receipts remain immutable.
"""

import argparse
from contextlib import ExitStack
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import runpy
import sys
import time
from typing import Any
from uuid import UUID


class VerificationBudgetExceeded(RuntimeError):
    pass


def sql_error_facts(error):
    """No driver prose, statement text, parameters or credentials in receipts."""
    facts = {"error_type": type(error).__name__[:80]}
    args = getattr(error, "args", ())
    if args and isinstance(args[0], str) and re.fullmatch(r"[A-Z0-9]{5}", args[0]):
        facts["sqlstate"] = args[0]
    if len(args) > 1 and isinstance(args[1], str):
        codes = re.findall(r"\((-?\d{1,10})\)", args[1][:4096])
        if codes:
            facts["native_code"] = int(codes[-1])
    module = sys.modules.get("services.application_maintenance_dal")
    if isinstance(error, getattr(module, "SchemaObservationRefused", ())):
        facts["schema_lock_result"] = error.result
    return facts


class ObservationConnections:
    """Own new, single-attempt connections and refuse uncertain cleanup.

    The same total budget spans all three contract observations and sessions.
    Existing runtime connections and their settings are never borrowed.
    """

    def __init__(self, connect, *, clock=time.monotonic):
        self.connect = connect
        self.clock = clock
        self.deadline = clock() + 45
        self.statements = 0
        self.connections = []
        self.phase = "connection_setup"
        self.observations = []
        self.first_failure = None

    def observation_phase(self, phase):
        if phase not in {"export", "legacy", "application", "sessions", "retained_work"}:
            raise ValueError("Unknown observation phase")
        self.phase = phase

    def record_failure(self, error, operation, statement=None):
        facts = dict(phase=self.phase, operation=operation, **sql_error_facts(error))
        if statement is not None:
            facts.update(ordinal=statement["ordinal"], sql_sha256=statement["sql_sha256"])
        if self.first_failure is None:
            self.first_failure = facts
        return facts

    def evidence(self):
        return dict(
            first_failure=self.first_failure,
            statements=self.observations,
            connections=[
                dict(closed=c.closed, close_failed=c.close_failed) for c in self.connections
            ],
            timing_scope="Client call wall time; not SQL Server CPU or a benchmark",
        )

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is not None:
            self.record_failure(error, "contract_or_session_comparison")
        try:
            self.close()
            if error is None:
                self.check(dispatch=False)
        except BaseException as cleanup:
            facts = self.record_failure(cleanup, "observation_close")
            cleanup.sql_observation = dict(self.evidence(), final_failure=facts)
            raise
        if error is not None:
            error.sql_observation = self.evidence()

    def check(self, *, dispatch=True):
        if self.clock() >= self.deadline or (dispatch and self.statements >= 256):
            raise VerificationBudgetExceeded("Verification observation budget exhausted; no retry")

    def __call__(self):
        self.check()
        owner = Connection(self, self.connect())
        self.connections.append(owner)
        owner.raw.timeout = 3
        owner.autocommit = True
        cursor = owner.cursor()
        try:
            cursor.execute("SET LOCK_TIMEOUT 0")
        finally:
            cursor.close()
        return owner

    def close(self):
        from core.sql_connection_custody import SqlCleanupUnknown, connection_retained

        unknown = False
        for owner in self.connections:
            if connection_retained(owner) or owner.close_failed:
                unknown = True
                continue
            try:
                owner.close()
            except BaseException:
                unknown = True
        if unknown:
            raise SqlCleanupUnknown("Verification SQL cleanup unconfirmed; no retry or acceptance")


class Connection:
    def __init__(self, budget, raw):
        self.budget, self.raw = budget, raw
        self.closed = self.close_failed = False
        self.cursors = []

    @property
    def autocommit(self):
        return self.raw.autocommit

    @autocommit.setter
    def autocommit(self, value):
        if value is not True:
            raise ValueError("Verification connections must remain autocommit")
        self.raw.autocommit = value

    def cursor(self):
        result = Cursor(self, self.raw.cursor())
        self.cursors.append(result)
        return result

    def close(self):
        if self.closed:
            return
        if self.close_failed:
            raise RuntimeError("Prior connection close unconfirmed")
        # Mark before dispatch: a lost acknowledgement never triggers another close.
        self.close_failed = True
        if (original := sys.exception()) is not None:
            self.budget.record_failure(original, "before_connection_close")
        try:
            for cursor in self.cursors:
                cursor.close()
        finally:
            try:
                self.raw.close()
            except BaseException as error:
                self.budget.record_failure(error, "connection_close")
                raise
        self.closed = True
        self.close_failed = False


class Cursor:
    def __init__(self, connection, raw):
        self.connection, self.raw = connection, raw
        self.closed = self.close_failed = False
        self.statement: dict[str, Any] | None = None
        self.acquire_pending = False
        self.schema_owned = False
        self.release_attempted = False

    def execute(self, *args):
        from services.application_maintenance_contract import RESOURCE
        from services.application_maintenance_dal import SCHEMA_ACQUIRE_SQL

        budget = self.connection.budget
        try:
            budget.check()
        except BaseException as error:
            budget.record_failure(error, "dispatch_budget")
            raise
        budget.statements += 1
        self.acquire_pending = args == (SCHEMA_ACQUIRE_SQL, RESOURCE)
        self.statement = dict(
            ordinal=len(budget.observations) + 1,
            phase=budget.phase,
            sql_sha256=hashlib.sha256(args[0].encode()).hexdigest(),
            execute_seconds=0.0,
            fetch_seconds=0.0,
            fetch_calls=0,
            cleanup=False,
        )
        budget.observations.append(self.statement)
        self._call("execute", self.raw.execute, *args)
        return self

    def _call(self, operation, method, *args) -> Any:
        budget = self.connection.budget
        statement = self.statement
        if statement is None:
            raise ValueError("SQL observation requires an executed statement")
        started = budget.clock()
        try:
            return method(*args)
        except BaseException as error:
            statement["failure"] = budget.record_failure(error, operation, statement)
            raise
        finally:
            key = "execute_seconds" if operation == "execute" else "fetch_seconds"
            statement[key] += round(budget.clock() - started, 6)
            if operation != "execute":
                statement["fetch_calls"] += 1

    def _fetch(self, operation, *args) -> Any:
        # Learn the acquisition acknowledgement even if its bounded call crossed
        # the deadline. The guard must know whether it owns cleanup.
        if not self.acquire_pending:
            try:
                self.connection.budget.check(dispatch=False)
            except BaseException as error:
                self.connection.budget.record_failure(error, "fetch_budget", self.statement)
                raise
        result = self._call(operation, getattr(self.raw, operation), *args)
        if self.acquire_pending and operation == "fetchone":
            self.acquire_pending = False
            self.schema_owned = (
                result is not None and type(result[0]) is int and result[0] in {0, 1}
            )
            return result
        try:
            self.connection.budget.check(dispatch=False)
        except BaseException as error:
            self.connection.budget.record_failure(error, "fetch_budget", self.statement)
            raise
        return result

    def fetchone(self):
        return self._fetch("fetchone")

    def fetchmany(self, *args):
        return self._fetch("fetchmany", *args)

    def fetchall(self):
        return self._fetch("fetchall")

    def nextset(self):
        return self._fetch("nextset")

    def release_schema_observation(self, resource, *, first_failure=None):
        """One fixed cleanup after acknowledged ownership, with the same 3s driver cap.

        This cannot admit arbitrary SQL or a new observation after budget expiry.
        A lost acknowledgement consumes the attempt and retains uncertainty.
        """
        from services.application_maintenance_contract import RESOURCE
        from services.application_maintenance_dal import SCHEMA_RELEASE_SQL

        if resource != RESOURCE or not self.schema_owned or self.release_attempted:
            raise ValueError("Unowned or repeated schema cleanup refused")
        self.release_attempted = True
        budget = self.connection.budget
        if first_failure is not None:
            budget.record_failure(first_failure, "before_schema_release")
        self.statement = dict(
            ordinal=len(budget.observations) + 1,
            phase=budget.phase,
            sql_sha256=hashlib.sha256(SCHEMA_RELEASE_SQL.encode()).hexdigest(),
            execute_seconds=0.0,
            fetch_seconds=0.0,
            fetch_calls=0,
            cleanup=True,
        )
        budget.observations.append(self.statement)
        self._call("execute", self.raw.execute, SCHEMA_RELEASE_SQL, RESOURCE, RESOURCE)
        result = self._call("fetchone", self.raw.fetchone)
        if result is not None and result[0] == 0 and result[1] == "NoLock":
            self.schema_owned = False
        return result

    def __getattr__(self, name):
        if name != "description":
            raise AttributeError(name)
        return getattr(self.raw, name)

    def close(self):
        if self.closed:
            return
        if self.close_failed:
            raise RuntimeError("Prior cursor close unconfirmed")
        self.close_failed = True
        if (original := sys.exception()) is not None:
            self.connection.budget.record_failure(original, "before_cursor_close")
        try:
            self.raw.close()
        except BaseException as error:
            self.connection.budget.record_failure(error, "cursor_close")
            raise
        self.closed, self.close_failed = True, False


def verify_sessions(rows, config, journal):
    """The newly observed ID is evidence; its identity comes from the pinned manifest."""
    old = config["old_session"]
    if len(rows) != 2 or len({str(r["SessionID"]).lower() for r in rows}) != 2:
        raise ValueError("Exactly the closed predecessor and one open successor required")
    previous = [r for r in rows if str(r["SessionID"]).lower() == old["SessionID"].lower()]
    current = [r for r in rows if r["State"] == "open"]
    if len(previous) != 1 or len(current) != 1:
        raise ValueError("Predecessor closure or successor session differs")
    before, after = previous[0], current[0]
    for row, manifest in (
        (before, config["old_journal"]["Record"]["publication"]["manifests"]["authority"]),
        (after, journal["publication"]["manifests"]["authority"]),
    ):
        if (
            row["AuthorityPrincipal"] != "S11_ExportApplication"
            or row["HostIdentity"].lower() != "mini_amd"
            or row["ManifestHash"].lower() != manifest
        ):
            raise ValueError("SQL authority identity differs from protected publication")
    if (
        before["State"] != "closed"
        or before["Version"] != old["Version"] + 1
        or after["Version"] != 1
        or after["ClosedUTC"] is not None
        or before["ClosedUTC"] is None
        or not before["CreatedUTC"] <= before["ClosedUTC"] <= after["CreatedUTC"]
    ):
        raise ValueError("SQL successor lifecycle differs")
    return str(after["SessionID"]).lower()


def retained_row(row):
    # These columns are uniqueidentifier in the authoritative SQL definitions.
    # SqlClient evidence uses lower-case GUID strings; pyodbc may return UUIDs
    # or upper-case strings. No text/hash/state normalization is permitted.
    identifiers = {
        "PreparationID",
        "JobID",
        "OwnerID",
        "ActivePreparationID",
        "ActiveJobID",
        "ActiveOutputOperationID",
        "StreamID",
        "SessionID",
        "OutputOperationID",
        "NestedToken",
    }
    return {
        k: str(UUID(str(v))) if k in identifiers and v is not None else v for k, v in row.items()
    }


def bounded_rows(cursor):
    columns = [c[0] for c in cursor.description]
    values = cursor.fetchmany(129)
    if len(values) > 128:
        raise ValueError("Retained work inventory exceeds bound")
    return [retained_row(dict(zip(columns, row, strict=True))) for row in values]


def verify_retained_work(cursor, config, session_id):
    """Mirror the ordinary successor gate without reconciliation or provider work."""
    preparations = [retained_row(r) for r in config["expected_preparation"]]
    resources = [retained_row(r) for r in config["expected_resources"]]
    if len(preparations) > 128 or len(resources) > 128:
        raise ValueError("Retained work expectation exceeds bound")
    cursor.execute(
        "SELECT TOP (129) PreparationID,AccountKey,ConsumerKind,State,OwnerID,Fence,Version,JobID,"
        "CONVERT(varchar(64),HASHBYTES('SHA2_256',CONVERT(varbinary(max),GenerationJson)),2) AS GenerationHash,"
        "SpoolKey,SpoolBytes,CONVERT(varchar(64),SpoolHash,2) AS SpoolHash FROM dbo.ExportPreparation "
        "WHERE AccountKey=? AND State IN ('captured','materialized','uncertain') ORDER BY PreparationID",
        config["account"],
    )
    current = bounded_rows(cursor)
    for expected in preparations:
        if [r for r in current if r["PreparationID"] == expected["PreparationID"]] != [expected]:
            raise ValueError("Retained preparation changed; no reconciliation authorized")
    for preparation_id in sorted({r["ActivePreparationID"] for r in resources}):
        cursor.execute(
            "SELECT ResourceKey,ActiveJobID,ActivePreparationID,ActiveOutputOperationID,OwnerID,Fence,BlockedReason,Version "
            "FROM dbo.ExportResource WHERE ActivePreparationID=? ORDER BY ResourceKey",
            preparation_id,
        )
        current = bounded_rows(cursor)
        for expected in (r for r in resources if r["ActivePreparationID"] == preparation_id):
            if [r for r in current if r["ResourceKey"] == expected["ResourceKey"]] != [expected]:
                raise ValueError("Retained resource changed; no reconciliation authorized")
    cursor.execute(
        "SELECT TOP (129) s.StreamID,s.SessionID,s.State,s.Purpose,s.ActiveAccountKey,s.JobID,s.PreparationID,"
        "s.OutputOperationID,s.NestedToken,s.Epoch,s.CreatedUTC,s.ClosedUTC,s.ClosureReference,s.ClosureHash,"
        "s.EventDigest,e.State AS SessionState,e.HostIdentity,e.ClosedUTC AS SessionClosedUTC "
        "FROM dbo.ExportExecutionStream s LEFT JOIN dbo.ExportExecutionSession e ON e.SessionID=s.SessionID "
        "WHERE s.AccountKey=? AND s.State<>'closed' ORDER BY s.StreamID",
        config["account"],
    )
    for row in bounded_rows(cursor):
        if row["State"] in {"target_contained", "read_contained"}:
            created, closed, session_closed = (
                row["CreatedUTC"],
                row["ClosedUTC"],
                row["SessionClosedUTC"],
            )
            shape = (
                row["State"] == "target_contained" and row["Purpose"] in {"mutation", "probe"}
            ) or (
                row["State"] == "read_contained"
                and row["Purpose"] in {"probe", "enrollment"}
                and row["PreparationID"] is not None
                and all(
                    row[k] is None for k in ("JobID", "OutputOperationID", "NestedToken", "Epoch")
                )
            )
            if (
                not shape
                or row["ActiveAccountKey"] is not None
                or row["SessionState"] != "closed"
                or row["HostIdentity"].lower() != config["host"].lower()
                or created is None
                or closed is None
                or session_closed is None
                or not created <= closed <= session_closed
                or row["ClosureReference"] is None
                or any(
                    not isinstance(row[k], bytes) or len(row[k]) != 32
                    for k in ("ClosureHash", "EventDigest")
                )
            ):
                raise ValueError("Retained contained stream closure is incomplete")
        elif str(row["SessionID"]).lower() != session_id:
            raise ValueError("Stream belongs to an unexpected session")


def verify(profile, config, pair, policy=None, *, startup_reader):
    policy = policy or pair["verify_live_source"](config)
    from core.export_deployment_handoff import RecordedTermination, termination_path
    from core.export_process_identity import open_pinned_process
    from core.export_startup_windows import administrative_path, signalled
    from kvk.dal.new_source_admin_dal import configured_connection

    def protected(path, digest=None):
        return json.loads(pair["read"](administrative_path(path, private=True), digest))

    state = Path(administrative_path(policy["state_directory"], private=True))
    if str(state) != config["new_state_directory"]:
        raise ValueError("Successor state directory differs")
    paths = list(state.glob("incarnation-*.json"))
    if len(paths) != 1 or paths[0].name != profile["journal_name"]:
        raise ValueError("Successor incarnation changed; no rebinding")
    journal = protected(paths[0], profile["journal_sha256"])
    if (
        journal["sequence"] != config["old_journal"]["Record"]["sequence"] + 1
        or journal["policy_sha256"] != config["new_policy_sha256"]
    ):
        raise ValueError("Successor sequence or policy differs")
    previous = protected(config["old_journal"]["Path"], config["old_journal"]["SHA256"])
    if previous != config["old_journal"]["Record"]:
        raise ValueError("Predecessor journal differs")
    RecordedTermination(
        previous,
        termination_path(config["old_policy"]["StateDirectory"], previous),
        administrative_path,
    ).verify()
    seed = protected(policy["seed_plan"]["path"], policy["seed_plan"]["sha256"])
    publication_dir = Path(seed["commit_file"]).parent.parent / paths[0].stem[-36:]
    publication = protected(publication_dir / "commit.json")
    if publication != journal["publication"]:
        raise ValueError("Publication differs from protected journal")
    plan = protected(
        publication_dir / "ManualProcessPairPlan-CANDIDATE.json", publication["plan_sha256"]
    )
    if set(publication["manifests"]) != {"authority", "bot"} or set(journal["bindings"]) != {
        "authority",
        "bot",
    }:
        raise ValueError("Exact supervised pair required")
    for role, digest in publication["manifests"].items():
        protected(plan["manifests"][role], digest)
    issuer = protected(publication_dir / "AutomaticIssuer.json")
    if issuer["version"] != 1 or issuer["plan_sha256"] != publication["plan_sha256"]:
        raise ValueError("Issuer publication differs")
    bindings = [*journal["bindings"].values(), issuer["issuer"]]
    if len({b["pid"] for b in bindings}) != 3:
        raise ValueError("Three distinct process identities required")
    start = protected(Path(profile["stage"]) / "start-requested.json", profile["start_sha256"])
    with ExitStack() as stack:
        handles = [
            stack.enter_context(native_handle(open_pinned_process(b["pid"], b))) for b in bindings
        ]
        startup_before = startup_reader["observe"](config, start, profile)
        admission = startup_reader["check_admission"](pair, config, journal, start, startup_before)
        bot = pair["bot_from_policy"](policy)
        if bot["sql_contract"]["profile"] != "application":
            raise ValueError("Dedicated single-attempt application connection required")
        owner = ObservationConnections(lambda: configured_connection(sql_profile="application"))
        with owner:
            contracts = pair["verify_sql_contracts"](config, policy, connection_factory=owner)
            owner.observation_phase("sessions")
            connection = owner()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT SessionID,AuthorityPrincipal,HostIdentity,CONVERT(varchar(64),ManifestHash,2) AS ManifestHash,"
                "State,Version,CreatedUTC,ClosedUTC FROM dbo.ExportExecutionSession "
                "WHERE HostIdentity='MINI_AMD' COLLATE Latin1_General_100_CI_AS "
                "AND (State='open' OR SessionID=?)",
                config["old_session"]["SessionID"],
            )
            columns = [c[0] for c in cursor.description]
            rows = [dict(zip(columns, row, strict=True)) for row in cursor.fetchmany(3)]
            session_id = verify_sessions(rows, config, journal)
            owner.observation_phase("retained_work")
            verify_retained_work(cursor, config, session_id)
        try:
            if (
                any(signalled(h) for h in handles)
                or list(state.glob("incarnation-*.json")) != paths
            ):
                raise ValueError("Native identity or incarnation changed during verification")
            # Bind final files again after the SQL observation, retaining process handles.
            protected(paths[0], profile["journal_sha256"])
            startup_after = startup_reader["observe"](config, start, profile)
            if (
                startup_reader["check_admission"](pair, config, journal, start, startup_after)
                != admission
            ):
                raise startup_reader["StartupHistoryRefused"](
                    "admission_changed", startup_after["evidence"]
                )
        except BaseException as error:
            error.sql_observation = owner.evidence()
            raise
        from services.export_execution_protocol import encode

        return dict(
            stage="RUNNING_RELEASE_VERIFIED",
            release_id=config["release_id"],
            target=config["target"],
            observed_utc=datetime.now(UTC).isoformat(),
            session_id=session_id,
            sequence=journal["sequence"],
            admission=admission,
            startup_evidence_before=startup_before["evidence"],
            startup_evidence_after=startup_after["evidence"],
            sql_observation_sha256=hashlib.sha256(encode(contracts)).hexdigest(),
            original_start="unconfirmed_preserved",
            original_readiness="unstarted_preserved",
            import_export="degraded",
            provider_delivery_verified=False,
            sql_statements=owner.statements,
            sql_observation=owner.evidence(),
            retry=False,
        )


def native_handle(handle):
    from contextlib import contextmanager

    @contextmanager
    def held():
        try:
            yield handle
        finally:
            handle.Close()

    return held()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if not sys.flags.isolated:
        raise ValueError("Isolated interpreter required")
    raw = Path(args.profile).read_bytes()
    if not 0 < len(raw) <= 65536 or hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError("Verification profile differs")
    profile = json.loads(raw)
    if profile.get("version") != 2:
        raise ValueError("Reviewed rotation-aware profile required")
    directory = Path(args.profile).parent
    reader_path = directory / "Read-StartupEvidence.py"
    with reader_path.open("rb") as stream:
        reader_raw = stream.read(1024 * 1024 + 1)
    if (
        len(reader_raw) > 1024 * 1024
        or hashlib.sha256(reader_raw).hexdigest() != profile["members"][reader_path.name]
    ):
        raise ValueError("Sealed startup reader differs")
    startup_reader = runpy.run_path(str(reader_path))
    pair_path = directory / "Verify-NewPair.py"
    pair_raw = pair_path.read_bytes()
    if (
        len(pair_raw) > 1024 * 1024
        or hashlib.sha256(pair_raw).hexdigest() != profile["pair_sha256"]
    ):
        raise ValueError("Sealed native verifier differs")
    pair = runpy.run_path(str(pair_path))
    config = json.loads(
        pair["read"](Path(profile["stage"]) / "ReleaseBindings.json", profile["bindings_sha256"])
    )
    if (
        config["release_id"] != profile["release_id"]
        or config["target"] != profile["target"]
        or config["root"] != r"C:\discord_file_downloader"
    ):
        raise ValueError("Exact installed release required")
    # Bootstrap authenticates installed source before loading any application code.
    policy = pair["verify_live_source"](config)
    pair["activate_contract_archive"](
        directory / "contract_verifier.zip", profile["archive_sha256"], config["root"]
    )
    import pyodbc

    # This isolated verifier owns every connection; close must not return a
    # session to a process-local pool with potentially retained SQL state.
    pyodbc.pooling = False
    try:
        result = verify(profile, config, pair, policy, startup_reader=startup_reader)
    except Exception as error:
        code, record = failure_result(error, startup_reader=startup_reader)
        print(json.dumps(record))
        raise SystemExit(code) from None
    print(json.dumps(result))


def failure_result(error, *, startup_reader=None):
    # Only an exact acknowledged timeout is pending; cancellation/deadlock,
    # unknown cleanup and all contract/identity drift remain hard failures.
    module = sys.modules.get("services.application_maintenance_dal")
    refused = getattr(module, "SchemaObservationRefused", ())
    pending = isinstance(error, refused) and error.result == -1
    record = dict(
        stage="VERIFICATION_PENDING" if pending else "VERIFICATION_REFUSED",
        failure_type=type(error).__name__,
        schema_lock_result=error.result if isinstance(error, refused) else None,
        verified=False,
        retry=False,
    )
    if startup_reader and isinstance(error, startup_reader["StartupHistoryRefused"]):
        record["startup_observation"] = startup_reader["failure_record"](error)
    if hasattr(error, "sql_observation"):
        record["sql_observation"] = error.sql_observation
    return (12 if pending else 1), record


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        code, record = failure_result(error)
        print(json.dumps(record))
        raise SystemExit(code)
