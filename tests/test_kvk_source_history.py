"""Real DAL with a transactional cursor model; SQL-engine proof is a separate suite."""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from kvk.dal import new_source_history_dal as dal
from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit
from kvk.models.new_source_history import (
    HISTORY_VERSION,
    encode_fact,
    history_fact,
    safe_basename,
)
from kvk.schemas.new_source_schema import SOURCE_KEY

INTENT = str(UUID(int=1))
REVISION = str(UUID(int=2))
NOW = datetime(2026, 10, 13, 11, 2, 3)
VECTOR = b"v" * 32


def attempt(n=1, **changes):
    return (
        dict(
            AttemptID=str(UUID(int=n + 100)),
            SourceKey=SOURCE_KEY,
            KVK_NO=16,
            GuildID="123",
            ReceivedUTC=NOW,
            OriginalFilename=r"C:\private\scan.xlsx",
            Status="accepted",
            ObservationRevisionID=REVISION,
            AggregateRevisionID=None,
            LogicalScanID=12,
            DataTimeUTC=NOW - timedelta(days=1),
            RevisionNo=1,
            PlayerRecords=42,
            KingdomRecords=None,
            CampRecords=None,
            **{},
        )
        | changes
    )


class Cursor:
    def __init__(self):
        self.attempts = []
        self.headers = {}
        self.stored = {}
        self.executed = []
        self.copied = []
        self.on_copy = None
        self.fail_ordinal = None
        self.uncertain = False

    def result(self, values):
        names = tuple(values[0]) if values else ()
        self.description = [(name,) for name in names]
        self.values = [tuple(row[n] for n in names) for row in values]

    def fetchone(self):
        return self.values.pop(0) if self.values else None

    def fetchall(self):
        result, self.values = self.values, []
        return result

    def execute(self, sql, *args):
        self.executed.append((sql, args))
        self.result([])
        if "sp_getapplock" in sql:
            return self
        if sql.startswith("CREATE TABLE #ReportHistoryAttempts"):
            return self
        if sql.startswith("SELECT * FROM KVK.SourceExportHistory "):
            self.result([self.headers[args]] if args in self.headers else [])
        elif "INSERT #ReportHistoryAttempts" in sql:
            source, season, guild = args
            self.copied = deepcopy(
                [
                    r
                    for r in self.attempts
                    if (r["SourceKey"], r["KVK_NO"], r["GuildID"]) == (source, season, guild)
                ]
            )
            if self.on_copy:
                self.on_copy()
        elif "SYSUTCDATETIME() AS CapturedUTC" in sql:
            self.result([{"CapturedUTC": NOW}])
        elif sql.startswith("INSERT KVK.SourceExportHistory ("):
            intent, guild, version, source, season, vector, captured, digest = args
            self.headers[args[:3]] = dict(
                IntentID=intent,
                GuildID=guild,
                HistoryVersion=version,
                SourceKey=source,
                KVK_NO=season,
                VectorHash=vector,
                CapturedUTC=captured,
                AttemptCount=0,
                ContentHash=digest,
            )
            self.stored[args[:3]] = []
        elif "FROM #ReportHistoryAttempts a" in sql:
            size, source, season, other_source, other_season, *continuation = args
            last, _, last_id = continuation if continuation else (None, None, None)
            assert (source, season) == (other_source, other_season) == (SOURCE_KEY, 16)
            ordered = sorted(self.copied, key=lambda r: (r["ReceivedUTC"], r["AttemptID"]))
            self.result(
                [
                    r
                    for r in ordered
                    if last is None or (r["ReceivedUTC"], r["AttemptID"]) > (last, last_id)
                ][:size]
            )
        elif sql.startswith("INSERT KVK.SourceExportHistoryRow"):
            _, _, _, ordinal, attempt_id, payload, digest = args
            if ordinal == self.fail_ordinal:
                raise OSError("injected capture failure")
            self.stored[args[:3]].append(
                dict(Ordinal=ordinal, AttemptID=attempt_id, PayloadJson=payload, RowHash=digest)
            )
        elif sql.startswith("UPDATE KVK.SourceExportHistory"):
            count, digest, *key = args
            self.headers[tuple(key)].update(AttemptCount=count, ContentHash=digest)
        elif sql.startswith("SELECT COUNT_BIG(*) AS n"):
            self.result([{"n": len(self.stored[args])}])
        elif "FROM KVK.SourceExportHistoryRow " in sql:
            size, *key, ordinal = args
            self.result([r for r in self.stored[tuple(key)] if r["Ordinal"] > ordinal][:size])
        else:
            raise AssertionError(sql)
        return self


@pytest.fixture
def database(monkeypatch):
    cursor = Cursor()

    @contextmanager
    def transaction(connect):
        before = deepcopy((cursor.headers, cursor.stored))
        try:
            yield cursor
        except BaseException:
            cursor.headers, cursor.stored = before
            raise
        if cursor.uncertain:
            cursor.uncertain = False
            raise UncertainCommit("lost commit acknowledgement")

    monkeypatch.setattr(dal, "transaction", transaction)
    monkeypatch.setattr(
        dal,
        "read_export_intent",
        lambda cursor, intent_id: (
            dict(IntentID=intent_id, SourceKey=SOURCE_KEY, KVK_NO=16, VectorHash=VECTOR),
            [],
        ),
    )
    return cursor


def capture(**kwargs):
    return dal.capture_history(
        connect=lambda: None, intent_id=INTENT, kvk_no=16, guild_id="123", **kwargs
    )


def read(snapshot, **kwargs):
    return list(dal.iter_history(connect=lambda: None, snapshot=snapshot, **kwargs))


@pytest.mark.parametrize("count,size", [(0, 1), (1, 1), (11, 2), (1001, 250)])
def test_complete_stable_pagination_and_restart(database, count, size):
    database.attempts = [attempt(n) for n in reversed(range(count))]
    snapshot = capture(batch_size=size)
    facts = read(snapshot, batch_size=size)
    assert len(facts) == snapshot.row_count == count
    assert len({f["attempt_id"] for f in facts}) == count
    assert facts == [
        history_fact(r) for r in sorted(database.attempts, key=lambda r: r["AttemptID"])
    ]
    database.attempts.append(attempt(9999))
    assert capture(batch_size=500) == snapshot
    assert read(snapshot, batch_size=500) == facts
    assert sum("INSERT #ReportHistoryAttempts" in sql for sql, _ in database.executed) == 1


def test_mutable_status_and_concurrent_import_are_frozen(database):
    database.attempts = [attempt(1, Status="received", ObservationRevisionID=None), attempt(2)]

    def mutate():
        database.attempts[0].update(Status="accepted", ObservationRevisionID=REVISION)
        database.attempts.append(attempt(3))

    database.on_copy = mutate
    snapshot = capture(batch_size=1)
    assert [r["import_status"] for r in read(snapshot)] == ["Pending", "Accepted"]
    assert capture() == snapshot


def test_all_attempt_outcomes_corrections_duplicates_and_unused_are_retained(database):
    states = ["received", "validated", "rejected", "accepted", "duplicate", "conflict"]
    database.attempts = [
        attempt(
            n,
            Status=status,
            ObservationRevisionID=REVISION if status in ("accepted", "duplicate") else None,
        )
        for n, status in enumerate(states)
    ]
    database.attempts.append(attempt(8, ObservationRevisionID=str(UUID(int=44)), RevisionNo=2))
    facts = read(capture(batch_size=2))
    assert len(facts) == 7
    assert facts[3]["observation_revision_id"] == facts[4]["observation_revision_id"] == REVISION
    assert facts[-1]["revision_number"] == 2


def test_no_cross_season_source_or_guild_exposure(database):
    database.attempts = [
        attempt(1),
        attempt(2, KVK_NO=17),
        attempt(3, GuildID="999"),
        attempt(4, SourceKey="legacy_full_data"),
    ]
    assert [r["attempt_id"] for r in read(capture())] == [attempt(1)["AttemptID"]]
    with pytest.raises(SourceConflict):
        dal.capture_history(connect=lambda: None, intent_id=INTENT, kvk_no=17, guild_id="123")


@pytest.mark.parametrize(
    "field,value", [("KVK_NO", 17), ("SourceKey", "other"), ("VectorHash", b"x" * 32)]
)
def test_existing_snapshot_wrong_scope_fails_closed(database, field, value):
    capture()
    database.headers[(INTENT, "123", HISTORY_VERSION)][field] = value
    with pytest.raises(SourceConflict):
        capture()


def test_capture_rollback_and_uncertain_commit_replay(database):
    database.attempts = [attempt(1), attempt(2)]
    database.fail_ordinal = 2
    with pytest.raises(OSError):
        capture(batch_size=1)
    assert database.headers == database.stored == {}
    database.fail_ordinal = None
    database.uncertain = True
    with pytest.raises(UncertainCommit):
        capture()
    database.attempts.clear()
    assert len(read(capture())) == 2


@pytest.mark.parametrize(
    "damage",
    ["payload", "row_hash", "ordinal", "missing", "extra", "header_hash", "count", "attempt"],
)
def test_full_integrity_verified_before_first_row(database, damage):
    database.attempts = [attempt(1), attempt(2)]
    snapshot = capture()
    key = INTENT, "123", HISTORY_VERSION
    row = database.stored[key][-1]
    if damage == "payload":
        row["PayloadJson"] = row["PayloadJson"].replace("Accepted", "Rejected")
    elif damage == "row_hash":
        row["RowHash"] = b"x" * 32
    elif damage == "ordinal":
        row["Ordinal"] = 3
    elif damage == "missing":
        database.stored[key].pop()
    elif damage == "extra":
        database.stored[key].append(dict(row, Ordinal=3))
    elif damage == "attempt":
        row["AttemptID"] = INTENT
    elif damage == "count":
        database.headers[key]["AttemptCount"] = 3
    else:
        database.headers[key]["ContentHash"] = b"x" * 32
    with pytest.raises(SourceConflict):
        next(dal.iter_history(connect=lambda: None, snapshot=snapshot, batch_size=1))


@pytest.mark.parametrize(
    "value,expected",
    [
        (r"C:\private\scan.xlsx", "scan.xlsx"),
        ("/private/scan.xlsx", "scan.xlsx"),
        ("../../scan.xlsx", "scan.xlsx"),
        (r"\\server\share\scan.xlsx", "scan.xlsx"),
        ("scan.xlsx:secret", "scan.xlsx"),
        ("\u202escan\x00.xlsx", "scan.xlsx"),
        (None, None),
        ("", None),
        ("..", None),
        (" =SUM(1).xlsx", "=SUM(1).xlsx"),
        ("çŽ©å®¶.xlsx", "çŽ©å®¶.xlsx"),
    ],
)
def test_safe_basename(value, expected):
    assert safe_basename(value) == expected


def test_no_private_diagnostics_and_missing_metadata_are_explicit():
    fact = history_fact(
        attempt(
            1,
            OriginalFilename=None,
            PlayerRecords=None,
            DiagnosticSummary="SECRET /private/file",
            ActorID="private-user",
            ProvenanceJson="private",
        )
    )
    payload = encode_fact(fact)
    assert "private" not in payload and "SECRET" not in payload
    assert fact["player_records"] is None and len(fact["notes"]) == 2
    assert fact["data_time_utc"].endswith("11:02:03Z")


def test_aggregate_counts_remain_independent_and_zero_is_known():
    fact = history_fact(
        attempt(
            1,
            ObservationRevisionID=None,
            AggregateRevisionID=REVISION,
            KingdomRecords=32,
            CampRecords=4,
        )
    )
    assert (fact["player_records"], fact["kingdom_records"], fact["camp_records"]) == (None, 32, 4)
    assert history_fact(attempt(PlayerRecords=0))["player_records"] == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"Status": "unknown"},
        {"AggregateRevisionID": REVISION},
        {"Status": "rejected"},
        {"ObservationRevisionID": None},
        {"ReceivedUTC": NOW.replace(tzinfo=timezone(timedelta(hours=1)))},
    ],
)
def test_invalid_source_fact_rejected(changes):
    with pytest.raises(ValueError):
        history_fact(attempt(**changes))


@pytest.mark.parametrize("size", [0, -1, 501, True, "3"])
def test_page_bounds_before_sql(size):
    with pytest.raises(ValueError):
        capture(batch_size=size)


@pytest.mark.parametrize("guild", ["", "1 OR 1=1", "ï¼‘ï¼’ï¼“", "1 ", "1" * 33, None])
def test_explicit_safe_guild_before_sql(guild):
    with pytest.raises(ValueError):
        dal.capture_history(
            connect=lambda: pytest.fail("No connection"),
            intent_id=INTENT,
            kvk_no=16,
            guild_id=guild,
        )


def test_schema_version_and_payload_bound(database):
    with pytest.raises(ValueError):
        read(replace(capture(), version="unknown"))
    with pytest.raises(ValueError):
        encode_fact({"large": "x" * 10000})


def test_sql_contract_uses_frozen_attempts_parameter_scope_and_no_multiplying_join(database):
    database.attempts = [attempt()]
    capture()
    copy = next(sql for sql, _ in database.executed if "INSERT #ReportHistoryAttempts" in sql)
    query = next(sql for sql, _ in database.executed if "FROM #ReportHistoryAttempts a" in sql)
    assert "WITH (HOLDLOCK)" in copy and "SourceKey=? AND KVK_NO=? AND GuildID=?" in copy
    assert "DiagnosticSummary" not in copy and "ProvenanceJson" not in copy
    assert query.count("SELECT COUNT_BIG(*)") == 3
    assert "ORDER BY a.ReceivedUTC,a.AttemptID" in query
    assert "SelectedRevisionID" not in query
