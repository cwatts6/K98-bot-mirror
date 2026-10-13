"""Atomic, scoped, immutable import-history capture for a pinned export intent.

Callers supply an already authorised guild/season. No default connection or audience.
Reader projection integration is deliberately separate from this persistence contract.
"""

from dataclasses import replace
import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.source_update_dal import read_export_intent
from kvk.models.new_source_history import (
    HISTORY_VERSION,
    HistorySnapshot,
    encode_fact,
    hash_row,
    history_fact,
    page_size,
)
from kvk.models.source_integration import identity
from kvk.schemas.new_source_schema import INT_MAX, SOURCE_KEY


def _scope(intent_id, kvk_no, guild_id):
    intent_id = identity(intent_id)
    if type(kvk_no) is not int or not 1 <= kvk_no <= INT_MAX:
        raise ValueError("Invalid history season.")
    if (
        not isinstance(guild_id, str)
        or not guild_id.isascii()
        or not guild_id.isdigit()
        or not 1 <= len(guild_id) <= 32
    ):
        raise ValueError("Explicit authorised guild identity is required.")
    return intent_id, guild_id, HISTORY_VERSION


def _header(cursor, key, kvk_no, vector_hash):
    cursor.execute(
        "SELECT * FROM KVK.SourceExportHistory WITH (HOLDLOCK) "
        "WHERE IntentID=? AND GuildID=? AND HistoryVersion=?",
        *key,
    )
    row = one(cursor)
    if row is None:
        return None
    if (row["SourceKey"], row["KVK_NO"], bytes(row["VectorHash"])) != (
        SOURCE_KEY,
        kvk_no,
        vector_hash,
    ):
        raise SourceConflict("Export history scope or vector differs.")
    return HistorySnapshot(
        key[0],
        SOURCE_KEY,
        kvk_no,
        key[1],
        vector_hash,
        row["CapturedUTC"],
        row["AttemptCount"],
        bytes(row["ContentHash"]),
    )


def capture_history(*, connect, intent_id, kvk_no, guild_id, batch_size=250):
    """First capture wins; an uncertain commit is recovered by repeating this identity."""
    key = _scope(intent_id, kvk_no, guild_id)
    page_size(batch_size)
    with transaction(connect) as cursor:
        intent, _ = read_export_intent(cursor, key[0])
        if (intent["SourceKey"], intent["KVK_NO"]) != (SOURCE_KEY, kvk_no):
            raise SourceConflict("Export intent is outside the authorised history scope.")
        vector_hash = bytes(intent["VectorHash"])
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?, "
            "@LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=10000; "
            "IF @r<0 THROW 51400,'Export history lock unavailable',1;",
            f"kvk-history:{key[0]}:{key[1]}:{HISTORY_VERSION}",
        )
        existing = _header(cursor, key, kvk_no, vector_hash)
        if existing is not None:
            _verify(cursor, existing, batch_size)
            return existing
        # One serializable source read freezes mutable statuses too. Do not filter by
        # selected revisions, successful status, or a ReceivedUTC cutoff.
        # Create outside the parameterised prepared batch so the ODBC temporary table
        # survives that batch's scope and is available to subsequent paging statements.
        cursor.execute(
            "CREATE TABLE #ReportHistoryAttempts (AttemptID uniqueidentifier NOT NULL,"
            "ReceivedUTC datetime2(0) NOT NULL,OriginalFilename nvarchar(512) NULL,"
            "Status varchar(32) NOT NULL,ObservationRevisionID uniqueidentifier NULL,"
            "AggregateRevisionID uniqueidentifier NULL); "
            "CREATE UNIQUE CLUSTERED INDEX IX_ReportHistoryAttempts "
            "ON #ReportHistoryAttempts (ReceivedUTC,AttemptID);"
        )
        cursor.execute(
            "INSERT #ReportHistoryAttempts SELECT AttemptID,ReceivedUTC,OriginalFilename,"
            "Status,ObservationRevisionID,AggregateRevisionID FROM KVK.SourceImportAttempt "
            "WITH (HOLDLOCK) WHERE SourceKey=? AND KVK_NO=? AND GuildID=?",
            SOURCE_KEY,
            kvk_no,
            guild_id,
        )
        cursor.execute("SELECT SYSUTCDATETIME() AS CapturedUTC")
        captured = one(cursor)["CapturedUTC"].replace(microsecond=0)
        snapshot = HistorySnapshot(
            key[0], SOURCE_KEY, kvk_no, guild_id, vector_hash, captured, 0, b""
        )
        hasher = snapshot.hasher()
        cursor.execute(
            "INSERT KVK.SourceExportHistory (IntentID,GuildID,HistoryVersion,SourceKey,KVK_NO,"
            "VectorHash,CapturedUTC,AttemptCount,ContentHash) VALUES (?,?,?,?,?,?,?,0,?)",
            *key,
            SOURCE_KEY,
            kvk_no,
            vector_hash,
            captured,
            hasher.digest(),
        )
        ordinal = 0
        for batch in _attempt_pages(cursor, kvk_no, batch_size):
            for row in batch:
                payload = encode_fact(history_fact(row))
                ordinal += 1
                row_hash = hash_row(hasher, payload)
                cursor.execute(
                    "INSERT KVK.SourceExportHistoryRow (IntentID,GuildID,HistoryVersion,"
                    "Ordinal,AttemptID,PayloadJson,RowHash) VALUES (?,?,?,?,?,?,?)",
                    *key,
                    ordinal,
                    row["AttemptID"],
                    payload,
                    row_hash,
                )
        cursor.execute(
            "UPDATE KVK.SourceExportHistory SET AttemptCount=?,ContentHash=? "
            "WHERE IntentID=? AND GuildID=? AND HistoryVersion=?",
            ordinal,
            hasher.digest(),
            *key,
        )
        return replace(snapshot, row_count=ordinal, content_hash=hasher.digest())


def _attempt_pages(cursor, kvk_no, batch_size):
    last_time = last_id = None
    while True:
        # NULL cursor parameters trigger ODBC metadata discovery that cannot resolve
        # this session's temporary table. The first page needs no cursor predicate.
        continuation = (
            "WHERE (a.ReceivedUTC>? OR (a.ReceivedUTC=? AND a.AttemptID>?)) "
            if last_time is not None
            else ""
        )
        parameters = (last_time, last_time, last_id) if last_time is not None else ()
        # Independent scalar counts cannot multiply player/kingdom/camp records.
        # Revision IDs are immutable; each join is explicitly source/season scoped.
        cursor.execute(
            "SELECT TOP (?) a.*,s.LogicalScanID,"
            "COALESCE(o.ScanStartUTC,g.AsOfUTC) AS DataTimeUTC,"
            "COALESCE(r.RevisionNo,g.RevisionNo) AS RevisionNo,"
            "CASE WHEN r.RevisionID IS NOT NULL THEN (SELECT COUNT_BIG(*) FROM "
            "KVK.SourcePlayerSnapshot x WHERE x.RevisionID=r.RevisionID) END AS PlayerRecords,"
            "CASE WHEN g.RevisionID IS NOT NULL THEN (SELECT COUNT_BIG(*) FROM "
            "KVK.SourceKingdomReportRow x WHERE x.RevisionID=g.RevisionID) END AS KingdomRecords,"
            "CASE WHEN g.RevisionID IS NOT NULL THEN (SELECT COUNT_BIG(*) FROM "
            "KVK.SourceCampReportRow x WHERE x.RevisionID=g.RevisionID) END AS CampRecords "
            "FROM #ReportHistoryAttempts a LEFT JOIN KVK.SourceObservationRevision r "
            "ON r.RevisionID=a.ObservationRevisionID AND r.SourceKey=? AND r.KVK_NO=? "
            "LEFT JOIN KVK.SourceObservation o ON o.ObservationID=r.ObservationID "
            "AND o.SourceKey=r.SourceKey AND o.KVK_NO=r.KVK_NO "
            "LEFT JOIN KVK.SourceLogicalScan s ON s.ObservationID=o.ObservationID "
            "AND s.SourceKey=o.SourceKey AND s.KVK_NO=o.KVK_NO "
            "LEFT JOIN KVK.SourceAggregateRevision g ON g.RevisionID=a.AggregateRevisionID "
            "AND g.SourceKey=? AND g.KVK_NO=? "
            + continuation
            + "ORDER BY a.ReceivedUTC,a.AttemptID",
            batch_size,
            SOURCE_KEY,
            kvk_no,
            SOURCE_KEY,
            kvk_no,
            *parameters,
        )
        batch = rows(cursor)
        if not batch:
            return
        yield batch
        last_time, last_id = batch[-1]["ReceivedUTC"], batch[-1]["AttemptID"]


def _stored_pages(cursor, snapshot, batch_size):
    ordinal = 0
    while True:
        cursor.execute(
            "SELECT TOP (?) Ordinal,AttemptID,PayloadJson,RowHash FROM KVK.SourceExportHistoryRow WITH (HOLDLOCK) "
            "WHERE IntentID=? AND GuildID=? AND HistoryVersion=? AND Ordinal>? ORDER BY Ordinal",
            batch_size,
            snapshot.intent_id,
            snapshot.guild_id,
            snapshot.version,
            ordinal,
        )
        batch = rows(cursor)
        if not batch:
            return
        yield batch
        ordinal = batch[-1]["Ordinal"]


def _verify(cursor, snapshot, batch_size):
    hasher, count = snapshot.hasher(), 0
    for batch in _stored_pages(cursor, snapshot, batch_size):
        for row in batch:
            count += 1
            payload = row["PayloadJson"]
            fact = json.loads(payload)
            if (
                row["Ordinal"] != count
                or fact.get("attempt_id") != row["AttemptID"]
                or encode_fact(fact) != payload
                or hash_row(hasher, payload) != bytes(row["RowHash"])
            ):
                raise SourceConflict("Export history row integrity differs.")
    if count != snapshot.row_count or hasher.digest() != snapshot.content_hash:
        raise SourceConflict("Export history content integrity differs.")


def iter_history(*, connect, snapshot, batch_size=250):
    """Verify the complete persisted snapshot before yielding its first report row."""
    if not isinstance(snapshot, HistorySnapshot) or snapshot.version != HISTORY_VERSION:
        raise ValueError("Supported pinned history snapshot is required.")
    key = _scope(snapshot.intent_id, snapshot.kvk_no, snapshot.guild_id)
    page_size(batch_size)
    with transaction(connect) as cursor:
        actual = _header(cursor, key, snapshot.kvk_no, snapshot.vector_hash)
        if actual != snapshot:
            raise SourceConflict("Pinned export history header differs.")
        # Lock retained rows for this transaction so verification and iteration agree.
        cursor.execute(
            "SELECT COUNT_BIG(*) AS n FROM KVK.SourceExportHistoryRow WITH (HOLDLOCK) "
            "WHERE IntentID=? AND GuildID=? AND HistoryVersion=?",
            *key,
        )
        one(cursor)
        _verify(cursor, snapshot, batch_size)
        for batch in _stored_pages(cursor, snapshot, batch_size):
            for row in batch:
                if hashlib.sha256(row["PayloadJson"].encode("utf-8")).digest() != bytes(
                    row["RowHash"]
                ):
                    raise SourceConflict("Export history row changed during reading.")
                yield json.loads(row["PayloadJson"])
