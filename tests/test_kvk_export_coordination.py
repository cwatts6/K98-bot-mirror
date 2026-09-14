"""Offline temporal regressions. SQL concurrency lives in the opt-in SQL suite."""

import asyncio
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
import hashlib
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services import export_coordination_dal as mod
from services.export_coordination_dal import Claim, ExportCoordinationDAL, JobSpec, validate_parts
from services.export_coordination_service import ExportCoordinator, ExportWorker
from services.export_request_budget import RequestBudget, retry_delay
from services.export_snapshot_store import ExportSnapshotStore


def spec(**changes):
    args = dict(
        account="account-a",
        consumer="new_source",
        input_hash=b"a" * 32,
        destinations=("file-a", "file-b"),
        actor="operator",
        reason="complete result",
        kvk_no=16,
        intent_id=str(uuid4()),
        epoch=1,
    )
    args.update(changes)
    return JobSpec(**args)


@pytest.mark.parametrize(
    "changes",
    [
        {"account": "bad account"},
        {"consumer": "other"},
        {"input_hash": b"short"},
        {"destinations": ("file-b", "file-a")},
        {"destinations": ("file-a", "file-a")},
        {"destinations": ("https://bad",)},
        {"destinations": ()},
        {"actor": " "},
        {"reason": ""},
        {"kvk_no": True},
        {"epoch": 0},
        {"intent_id": None},
        {"spool_key": "../bad"},
        {"provenance": "[]"},
        {"provenance": '{"x":"' + "x" * 32768 + '"}'},
    ],
)
def test_job_rejects_invalid_or_mutable_identity(changes):
    with pytest.raises(ValueError):
        spec(**changes)


def test_daily_spool_and_null_replay_shape():
    daily = spec(
        consumer="scan_data",
        kvk_no=None,
        epoch=None,
        intent_id=None,
        spool_key="opaque",
        spool_bytes=1,
        storage_owner="worker-a",
    )
    assert daily.resource_keys == ("account:account-a", "destination:file-a", "destination:file-b")
    assert daily.repair_id is None
    with pytest.raises(ValueError):
        replace(daily, spool_bytes=None)
    with pytest.raises(ValueError):
        replace(daily, kvk_no=16)


def test_spool_roundtrip_corruption_affinity_and_no_overwrite(tmp_path):
    store = ExportSnapshotStore(tmp_path, "worker-a")
    first = store.put(b"immutable A")
    second = store.put(b"immutable B")
    assert first.key != second.key and store.read(first) == b"immutable A"
    assert first.sha256 == hashlib.sha256(b"immutable A").hexdigest()
    with pytest.raises(ValueError, match="another storage owner"):
        ExportSnapshotStore(tmp_path, "worker-b").read(first)
    (tmp_path / first.key).write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        store.read(first)
    assert store.read(second) == b"immutable B"


@pytest.mark.parametrize("key", ["../x", "x/y", "C:\\escape", "", ".", "a" * 129])
def test_spool_rejects_path_input(tmp_path, key):
    store = ExportSnapshotStore(tmp_path, "worker")
    with pytest.raises(ValueError):
        store._path(key)


def test_spool_root_and_size_bounds(tmp_path):
    with pytest.raises(ValueError):
        ExportSnapshotStore("relative", "worker")
    with pytest.raises(ValueError):
        ExportSnapshotStore(tmp_path / "absent", "worker")
    store = ExportSnapshotStore(tmp_path, "worker", max_bytes=4)
    with pytest.raises(ValueError):
        store.put(b"12345")
    (tmp_path / ".git").mkdir()
    with pytest.raises(ValueError):
        ExportSnapshotStore(tmp_path, "worker")


class Cursor:
    """Scripted database responses; validates parameter arity without imitating SQL."""

    def __init__(self, *, singles=(), batches=()):
        self.singles, self.batches = iter(singles), iter(batches)
        self.calls = []

    def execute(self, query, *args):
        assert query.count("?") == len(args), (query, len(args))
        self.calls.append((query, args))


@contextmanager
def transaction_cursor(cursor):
    yield cursor


def scripted(monkeypatch, cursor):
    monkeypatch.setattr(mod, "transaction", lambda _: transaction_cursor(cursor))
    monkeypatch.setattr(mod, "one", lambda _: next(cursor.singles))
    monkeypatch.setattr(mod, "rows", lambda _: next(cursor.batches))
    return ExportCoordinationDAL(Mock())


def test_durable_budget_uses_server_time_and_next_allowed(monkeypatch):
    now = datetime(2026, 9, 14)
    cursor = Cursor(singles=[{"NowUTC": now}, None])
    dal = scripted(monkeypatch, cursor)
    reserved = dal.reserve_request("acct")
    assert reserved == {"ReservedUTC": now, "WaitSeconds": 0}
    assert cursor.calls[-1][1] == ("acct", now + timedelta(milliseconds=2100))


def test_budget_reserves_after_shared_cooldown_with_cas(monkeypatch):
    now = datetime(2026, 9, 14)
    cooldown = now + timedelta(seconds=30)
    cursor = Cursor(
        singles=[
            {"NowUTC": now},
            dict(
                NextAllowedUTC=now + timedelta(seconds=2),
                CooldownUntilUTC=cooldown,
                IntervalMilliseconds=2100,
                Version=7,
            ),
            {"Version": 8},
        ]
    )
    dal = scripted(monkeypatch, cursor)
    assert dal.reserve_request("acct")["WaitSeconds"] == 30
    assert cursor.calls[-1][1] == (cooldown + timedelta(milliseconds=2100), "acct", 7)


def test_cooldown_extension_rebooks_old_reservations_without_burst(monkeypatch):
    now = datetime(2026, 9, 14)
    next_slot = now + timedelta(seconds=40)
    cursor = Cursor(
        singles=[
            dict(
                NowUTC=now,
                CooldownUntilUTC=now + timedelta(seconds=30),
                NextAllowedUTC=next_slot,
                IntervalMilliseconds=2100,
                Version=4,
            ),
            {"Version": 5},
        ]
    )
    dal = scripted(monkeypatch, cursor)
    result = dal.refresh_reservation("acct", now - timedelta(seconds=1))
    assert result == {"ReservedUTC": next_slot, "WaitSeconds": 40}
    assert cursor.calls[-1][1] == (next_slot + timedelta(milliseconds=2100), "acct", 4)


def test_budget_waits_after_repository_return_and_observes_extension():
    events = []
    dal = Mock()
    dal.reserve_request.side_effect = lambda _: events.append("committed") or dict(
        ReservedUTC=1, WaitSeconds=2
    )
    dal.refresh_reservation.side_effect = [
        dict(ReservedUTC=4, WaitSeconds=3),
        dict(ReservedUTC=4, WaitSeconds=0),
    ]
    RequestBudget(dal, "acct", sleep=lambda seconds: events.append(("sleep", seconds)))()
    assert events == ["committed", ("sleep", 2), ("sleep", 3)]
    assert dal.refresh_reservation.call_args.args == ("acct", 4)


@pytest.mark.parametrize(
    "value,expected", [("3", 3), ("999999", 3600), ("-3", 1), ("nan", 1), ("bad", 1), (None, 1)]
)
def test_retry_after_is_bounded(value, expected):
    assert retry_delay(value) == expected


def test_stopped_budget_makes_no_reservation():
    stop = Event()
    stop.set()
    dal = Mock()
    with pytest.raises(InterruptedError):
        RequestBudget(dal, "acct", stop=stop)()
    dal.reserve_request.assert_not_called()


def part(**changes):
    result = dict(
        file_id="file-a", role="generation", manifest_hash="a" * 64, grids=1, rows=2, cells=4
    )
    result.update(changes)
    return result


@pytest.mark.parametrize(
    "parts",
    [
        [],
        [part(), part()],
        [part(file_id="unregistered")],
        [part(role="unknown")],
        [part(manifest_hash="bad")],
        [part(cells=1)],
        [part(grids=True)],
    ],
)
def test_manifest_requires_exact_registered_distinct_bounded_parts(parts):
    with pytest.raises(ValueError):
        validate_parts(parts, ["file-a"])


def test_stale_resource_owner_blocks_even_with_matching_job(monkeypatch):
    claim = Claim("job", "acct", "owner", 5, 2, (("account:acct", 9),))
    cursor = Cursor(
        singles=[dict(ActiveJobID="job", OwnerID="old", Fence=5, Version=9, BlockedReason=None)]
    )
    dal = scripted(monkeypatch, cursor)
    with pytest.raises(SourceConflict, match="Resource"):
        dal.authorize(claim)
    assert not any("UPDATE" in q for q, _ in cursor.calls)


@pytest.mark.parametrize("state", ["confirmed", "failed", "uncertain", "cancelled"])
def test_job_state_cannot_release_owned_resource(monkeypatch, state):
    claim = Claim("job", "acct", "owner", 5, 2, (("account:acct", 9),))
    cursor = Cursor(
        singles=[
            dict(ActiveJobID="job", OwnerID="owner", Fence=5, Version=9, BlockedReason=None),
            dict(
                JobID=str(uuid4()),
                SupersededByJobID=None,
                RepairID=None,
                AccountKey="acct",
                OwnerID="owner",
                Fence=5,
                Version=2,
                State=state,
            ),
        ]
    )
    dal = scripted(monkeypatch, cursor)
    with pytest.raises(SourceConflict, match="Job"):
        dal.fail(claim)
    assert not any("UPDATE" in q for q, _ in cursor.calls)


def test_coordinator_discovery_paginates_without_losing_retained_intents():
    dal = Mock()
    dal.pending_intents.side_effect = [[dict(KVK_NO=16, CommitSequence=32)], []]
    coordinator = ExportCoordinator(dal, adapters={})
    coordinator.discover()
    assert coordinator.after == (16, 32)
    coordinator.discover()
    assert coordinator.after == (0, 0)


def test_worker_checks_spool_before_adapter_and_preserves_failed_evidence():
    claim = Mock()
    dal, adapter, store = Mock(), Mock(), Mock()
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct"]
    dal.claim_next.return_value = claim
    dal.authorize.return_value = dict(
        ConsumerKind="scan_data",
        SpoolKey="missing",
        SpoolBytes=1,
        InputHash=b"a" * 32,
        StorageOwner="owner",
    )
    store.read.side_effect = ValueError("corrupt")
    ExportCoordinator(dal, adapters={"scan_data": adapter}, storage=store).run_batch(Event())
    adapter.assert_not_called()
    dal.fail.assert_called_once_with(claim)


@pytest.mark.asyncio
async def test_cancellation_waits_for_running_thread_and_retains_no_replacement():
    entered, release, finished = Event(), Event(), Event()
    calls = []

    def batch(stop, limit):
        calls.append(limit)
        entered.set()
        assert release.wait(3)
        assert stop.is_set()
        finished.set()

    worker = ExportWorker(lambda: SimpleNamespace(run_batch=batch))
    task = asyncio.create_task(worker.run())
    assert await asyncio.to_thread(entered.wait, 3)
    task.cancel()
    await asyncio.sleep(0.01)
    task.cancel()
    await asyncio.sleep(0.01)
    assert not task.done()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert finished.is_set() and calls == [8]


def test_attempt_persists_parts_before_any_provider_io(monkeypatch):
    claim = Claim(str(uuid4()), "acct", str(uuid4()), 2, 2, (("destination:file-a", 1),))
    cursor = Cursor(singles=[None])
    dal = scripted(monkeypatch, cursor)

    @contextmanager
    def owned(_):
        yield cursor, dict(ConsumerKind="scan_data", PoolEpoch=None)

    monkeypatch.setattr(dal, "_owned", owned)
    attempt_id = dal.begin_attempt(claim, {"export_key": "x"}, [part()])
    assert attempt_id
    inserts = [q for q, _ in cursor.calls if q.startswith("INSERT")]
    assert len(inserts) == 2 and "ExportAttemptPart" in inserts[1]


def test_incomplete_attempt_parts_cannot_be_confirmed(monkeypatch):
    document = {"generation": {"export_key": "x"}, "parts": [part()]}
    cursor = Cursor(
        singles=[
            dict(
                ManifestJson=mod.bounded_json(document), ManifestHash=digest(document), PartCount=1
            )
        ],
        batches=[[]],
    )
    dal = scripted(monkeypatch, cursor)
    with pytest.raises(SourceConflict, match="cardinality"):
        dal._attempt(cursor, Claim("job", "acct", "owner", 1, 1, ()), "attempt")


def test_cas_zero_rows_is_not_success(monkeypatch):
    cursor = Cursor(singles=[None])
    scripted(monkeypatch, cursor)
    with pytest.raises(SourceConflict):
        mod._cas(
            cursor, "UPDATE safe SET Version=Version+1 OUTPUT inserted.Version WHERE Version=?", 7
        )


def test_running_a_is_untouched_while_b_coalesces_to_c_with_original_ticket(monkeypatch):
    from kvk.dal import season_source_dal, source_update_dal

    monkeypatch.setattr(season_source_dal, "require_source", lambda *_: None)

    request = spec()
    pending_id, running_id, final_id = str(uuid4()), str(uuid4()), str(uuid4())
    resource = dict(ResourceKind="destination", ActiveJobID=running_id)
    pending = dict(JobID=pending_id, IntentID=str(uuid4()), Version=2, EnqueueSequence=7)
    final = dict(JobID=final_id, SupersededByJobID=None, RepairID=None)
    cursor = Cursor(
        singles=[
            None,
            dict(ResourceKind="account", ActiveJobID=running_id),
            resource,
            resource,
            {"Ticket": 15},
            {"CommitSequence": 2},
            {"Version": 3},
            final,
        ],
        batches=[[], [], [pending]],
    )
    dal = scripted(monkeypatch, cursor)
    sync = Mock()
    monkeypatch.setattr(dal, "_sync_intent", sync)
    monkeypatch.setattr(
        source_update_dal,
        "read_export_intent",
        lambda *_: (
            dict(
                KVK_NO=16, VectorHash=b"a" * 32, IntentState="waiting_destination", CommitSequence=3
            ),
            [],
        ),
    )
    dal.enqueue(request)
    assert [call.args[1] for call in sync.call_args_list] == [
        pending["IntentID"],
        request.intent_id,
    ]
    updates = [(q, values) for q, values in cursor.calls if q.startswith("UPDATE dbo.ExportJob")]
    assert len(updates) == 1 and updates[0][1][1:] == (pending_id, 2)
    assert "OwnerID IS NULL AND Fence=0" in updates[0][0]
    insertion = next(values for q, values in cursor.calls if q.startswith("INSERT dbo.ExportJob ("))
    assert insertion[13] == 7
    assert all(running_id not in values for q, values in cursor.calls if q.startswith("UPDATE"))


def test_failed_attempt_keeps_claims_and_quarantines_parts(monkeypatch):
    claim = Claim("job", "acct", "owner", 2, 3, (("account:acct", 1), ("destination:file-a", 1)))
    cursor = Cursor(
        singles=[{"Version": 2}, {"Version": 2}, {"Version": 4}, {"Version": 2}, {"Version": 2}],
        batches=[[{"AttemptID": "attempt"}]],
    )
    dal = scripted(monkeypatch, cursor)

    @contextmanager
    def owned(_):
        yield cursor, {"Version": 3}

    monkeypatch.setattr(dal, "_owned", owned)
    monkeypatch.setattr(dal, "_attempt", lambda *_: ({"Version": 1}, [{"Version": 1, "PartNo": 1}]))
    dal.fail(claim)
    queries = [q for q, _ in cursor.calls]
    assert any("Phase='uncertain'" in q for q in queries)
    assert any("QuarantineState='quarantined'" in q for q in queries)
    assert sum("BlockedReason='Outcome requires reconciliation'" in q for q in queries) == 2
    assert not any("ActiveJobID=NULL" in q for q in queries)


def test_safe_retry_is_audited_without_replacing_identity_or_ticket(monkeypatch):
    job_id = str(uuid4())
    job = dict(
        JobID=job_id,
        SupersededByJobID=None,
        RepairID=None,
        AccountKey="acct",
        Version=4,
        PoolEpoch=None,
        State="failed",
        ConsumerKind="scan_data",
        ProvenanceJson="{}",
        OwnerID=str(uuid4()),
        Fence=3,
    )
    cursor = Cursor(singles=[job, None, {"NowUTC": "2026-09-14T12:00:00"}, {"Version": 5}])
    dal = scripted(monkeypatch, cursor)
    dal.request_safe_retry(
        job_id,
        "acct",
        expected_version=4,
        expected_epoch=None,
        actor="operator",
        reason="GET failed before mutation",
    )
    query, args = cursor.calls[-1]
    assert "EnqueueSequence=" not in query and "OwnerID=" not in query and "InputHash=" not in query
    evidence = mod.json.loads(args[0])
    assert evidence["safe_retry_history"][0]["owner"] == job["OwnerID"]
    assert evidence["safe_retry"]["requested"] is True


def test_attempted_failure_cannot_use_safe_retry(monkeypatch):
    job_id = str(uuid4())
    cursor = Cursor(
        singles=[
            dict(
                JobID=job_id,
                SupersededByJobID=None,
                RepairID=None,
                AccountKey="acct",
                Version=4,
                PoolEpoch=None,
                State="failed",
            ),
            {"AttemptID": str(uuid4())},
        ]
    )
    dal = scripted(monkeypatch, cursor)
    with pytest.raises(SourceConflict, match="Attempted work"):
        dal.request_safe_retry(
            job_id,
            "acct",
            expected_version=4,
            expected_epoch=None,
            actor="operator",
            reason="retry",
        )
    assert not any(q.startswith("UPDATE") for q, _ in cursor.calls)


def test_shutdown_prevents_discovery_and_account_rotation_prevents_starvation():
    dal = Mock()
    service = ExportCoordinator(dal, adapters={})
    stop = Event()
    stop.set()
    service.run_batch(stop)
    dal.pending_intents.assert_not_called()
    stop.clear()
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct-a", "acct-b"]
    dal.claim_next.return_value = None
    dal.claim_next.side_effect = [SourceConflict("busy"), None]
    service.run_batch(stop)
    assert [c.args[0] for c in dal.claim_next.call_args_list] == ["acct-a", "acct-b"]


def test_nonfinite_evidence_is_rejected():
    with pytest.raises(ValueError):
        spec(provenance='{"x":NaN}')


def test_delayed_request_completion_preserves_full_spacing(monkeypatch):
    slot = datetime(2026, 9, 14)
    finished = slot + timedelta(seconds=1.9)
    cursor = Cursor(
        singles=[
            dict(
                NowUTC=finished,
                NextAllowedUTC=slot + timedelta(seconds=2.1),
                CooldownUntilUTC=None,
                IntervalMilliseconds=2100,
                Version=7,
            ),
            {"Version": 8},
        ]
    )
    dal = scripted(monkeypatch, cursor)
    dal.complete_request("acct")
    until = finished + timedelta(seconds=2.1)
    assert cursor.calls[-1][1] == (until, until, "acct", 7)


def test_completion_never_shortens_cooldown_or_reserved_queue(monkeypatch):
    now = datetime(2026, 9, 14)
    cooldown, tail = now + timedelta(seconds=30), now + timedelta(seconds=40)
    cursor = Cursor(
        singles=[
            dict(
                NowUTC=now,
                NextAllowedUTC=tail,
                CooldownUntilUTC=cooldown,
                IntervalMilliseconds=3100,
                Version=7,
            ),
            {"Version": 8},
        ]
    )
    dal = scripted(monkeypatch, cursor)
    dal.complete_request("acct")
    assert cursor.calls[-1][1] == (cooldown, tail, "acct", 7)


def test_uncertain_budget_completion_retains_claims_without_mutation(monkeypatch):
    from services.export_request_budget import BudgetCompletionUnknown

    dal = Mock()
    dal.complete_request.side_effect = SourceConflict("commit uncertain")
    with pytest.raises(BudgetCompletionUnknown):
        RequestBudget(dal, "acct").completed()
    dal.pending_intents.return_value = []
    dal.accounts.return_value = ["acct"]
    claim = SimpleNamespace(job_id="job")
    dal.claim_next.return_value = claim
    dal.authorize.return_value = dict(ConsumerKind="scan_data", SpoolKey=None)
    adapter = Mock(side_effect=BudgetCompletionUnknown())
    ExportCoordinator(dal, adapters={"scan_data": adapter}).run_batch(Event())
    dal.fail.assert_called_once_with(claim, retain_claims=True)


def test_budget_uncertainty_blocks_resources_without_attempt(monkeypatch):
    claim = Claim("job", "acct", "owner", 2, 3, (("account:acct", 1),))
    cursor = Cursor(singles=[{"Version": 4}, {"Version": 2}], batches=[[]])
    dal = scripted(monkeypatch, cursor)

    @contextmanager
    def owned(_):
        yield cursor, {"Version": 3}

    monkeypatch.setattr(dal, "_owned", owned)
    dal.fail(claim, retain_claims=True)
    assert not any("ActiveJobID=NULL" in q for q, _ in cursor.calls)
    assert any("BlockedReason='Outcome requires reconciliation'" in q for q, _ in cursor.calls)


@pytest.mark.parametrize(
    "state,jobs,expected",
    [
        ("waiting_destination", [{"State": "ready", "SuccessorIntentID": None}], "materialized"),
        ("materialized", [{"State": "confirmed", "SuccessorIntentID": None}], "confirmed"),
        (
            "materialized",
            [
                {"State": "running", "SuccessorIntentID": None},
                {"State": "confirmed", "SuccessorIntentID": None},
            ],
            None,
        ),
    ],
)
def test_intent_transition_aggregates_registered_jobs_with_state_cas(
    monkeypatch, state, jobs, expected
):
    intent_id = str(uuid4())
    singles = [{"IntentState": state, "SupersededByIntentID": None}]
    if expected:
        singles.append({"IntentID": intent_id})
    cursor = Cursor(singles=singles, batches=[jobs])
    dal = scripted(monkeypatch, cursor)
    dal._sync_intent(cursor, intent_id)
    updates = [(q, a) for q, a in cursor.calls if q.startswith("UPDATE")]
    if expected:
        assert updates[0][1] == (expected, None, intent_id, state, None, None)
        assert "AND IntentState=?" in updates[0][0]
    else:
        assert updates == []


def test_coalesced_intent_retains_exact_successor_and_immutable_vector(monkeypatch):
    old, new = str(uuid4()), str(uuid4())
    cursor = Cursor(
        singles=[{"IntentState": "materialized", "SupersededByIntentID": None}, {"IntentID": old}],
        batches=[[{"State": "coalesced", "SuccessorIntentID": new}]],
    )
    dal = scripted(monkeypatch, cursor)
    dal._sync_intent(cursor, old)
    query, args = cursor.calls[-1]
    assert args == ("coalesced", new, old, "materialized", None, None)
    assert "VectorHash=" not in query and "PublicationID=" not in query


def test_discovery_filters_materialized_history_but_recovers_missing_registration(monkeypatch):
    from services.export_coordination_service import ExportRegistration

    registration = ExportRegistration(16, "acct", 2, ("file-a",))
    cursor = Cursor(batches=[[]])
    dal = scripted(monkeypatch, cursor)
    assert dal.pending_intents(registrations=(registration,)) == []
    query, args = cursor.calls[-1]
    assert "NOT EXISTS (SELECT 1 FROM dbo.ExportJob" in query
    assert "j.IntentID=i.IntentID" in query and "j.AccountKey=r.AccountKey" in query
    assert (
        "j.PoolEpoch=r.PoolEpoch" in query and "j.DestinationSetHash=r.DestinationSetHash" in query
    )
    assert "i.IntentState NOT IN ('blocked','coalesced')" in query
    assert args == (32, 16, "acct", 2, digest(("file-a",)), 0, 0, 0)


def test_terminal_job_updates_intent_in_the_same_owned_transaction(monkeypatch):
    intent_id = str(uuid4())
    claim = Claim("job", "acct", "owner", 2, 3, (("account:acct", 1),), intent_id)
    cursor = Cursor(singles=[{"Version": 4}, {"Version": 2}])
    dal = scripted(monkeypatch, cursor)
    sync = Mock()
    monkeypatch.setattr(dal, "_sync_intent", sync)
    dal._finish(cursor, claim, {"Version": 3}, "confirmed", release=True)
    sync.assert_called_once_with(cursor, intent_id)


@pytest.mark.parametrize("offset,expected", [(240, 240), (-300, 1), (7200, 3600)])
def test_http_date_uses_sql_utc_despite_host_clock_skew(monkeypatch, offset, expected):
    from datetime import UTC
    from email.utils import format_datetime

    from services import export_request_budget

    sql_now = datetime(2026, 9, 14, 12)
    deadline = (sql_now + timedelta(seconds=offset)).replace(tzinfo=UTC)
    # Neither a fast nor a slow local wall clock participates in parsing.
    monkeypatch.setattr(export_request_budget.time, "time", lambda: 0)
    parsed = retry_delay(format_datetime(deadline, usegmt=True))
    assert parsed == deadline
    cursor = Cursor(
        singles=[{"NowUTC": sql_now}, {"CooldownUntilUTC": None, "Version": 7}, {"Version": 8}]
    )
    dal = scripted(monkeypatch, cursor)
    dal.extend_cooldown("acct", parsed)
    assert cursor.calls[-1][1] == (sql_now + timedelta(seconds=expected), "acct", 7)


def test_retry_after_http_date_reaches_dal_without_local_duration():
    from datetime import UTC

    response = type("Response", (dict,), {"status": 429})(
        {"retry-after": "Mon, 14 Sep 2026 12:04:00 GMT"}
    )
    dal = Mock()
    RequestBudget(dal, "acct").rejected(SimpleNamespace(resp=response))
    dal.extend_cooldown.assert_called_once_with("acct", datetime(2026, 9, 14, 12, 4, tzinfo=UTC))


def test_uncertain_retry_after_checkpoint_cannot_release_read_only_claim():
    from services.export_request_budget import BudgetCompletionUnknown

    response = type("Response", (dict,), {"status": 503})(
        {"retry-after": "Mon, 14 Sep 2026 12:04:00 GMT"}
    )
    dal = Mock()
    dal.extend_cooldown.side_effect = SourceConflict("unconfirmed cooldown")
    with pytest.raises(BudgetCompletionUnknown, match="cooldown"):
        RequestBudget(dal, "acct").rejected(SimpleNamespace(resp=response))
