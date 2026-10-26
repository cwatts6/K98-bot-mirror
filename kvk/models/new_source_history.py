"""Versioned, report-safe import facts; no private admission diagnostics."""

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import ntpath
import unicodedata

HISTORY_VERSION = "source_export_history_v1"
MAX_PAGE_SIZE = 500
MAX_ROW_BYTES = 16384


def page_size(value):
    if type(value) is not int or not 1 <= value <= MAX_PAGE_SIZE:
        raise ValueError("History page size must be between 1 and 500.")
    return value


def safe_basename(value):
    """Windows and POSIX paths can arrive on either host; never return directories."""
    if not isinstance(value, str):
        return None
    name = ntpath.basename(value.replace("/", "\\"))
    # Remove alternate streams and control/format characters, including bidi overrides.
    name = name.split(":", 1)[0]
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C")).strip()
    return name[:255] if name and name not in (".", "..") else None


def history_fact(row):
    """Allowlist only. Unknown metadata is absent, never parsed from filenames."""
    status = row["Status"]
    outcomes = {
        "received": "Pending",
        "validated": "Validated",
        "accepted": "Accepted",
        "duplicate": "Duplicate",
        "rejected": "Rejected",
        "conflict": "Conflict",
    }
    if status not in outcomes:
        raise ValueError("Unknown import status.")
    player = row.get("ObservationRevisionID")
    aggregate = row.get("AggregateRevisionID")
    if (status in ("accepted", "duplicate") and not (bool(player) ^ bool(aggregate))) or (
        status not in ("accepted", "duplicate")
        and (player or aggregate)
        and not (
            status == "validated"
            and row.get("RetainedAcceptance") is True
            and bool(player) ^ bool(aggregate)
        )
    ):
        raise ValueError("Import outcome and revision identity differ.")
    filename = safe_basename(row.get("OriginalFilename"))
    notes = []
    if filename is None:
        notes.append("Source filename unavailable.")
    if not player and not aggregate:
        notes.append("No accepted revision; data time and record count unavailable.")
    if status == "duplicate":
        notes.append("Same accepted revision; does not add another contribution.")
    if row.get("RetainedAcceptance"):
        notes.append("Earlier accepted input retained during a pending or cancelled follow-up.")
    if (player and row.get("PlayerRecords") is None) or (
        aggregate and (row.get("KingdomRecords") is None or row.get("CampRecords") is None)
    ):
        notes.append("Verified record count unavailable.")
    return {
        "attempt_id": row["AttemptID"],
        "source_file": filename,
        "imported_utc": _time(row["ReceivedUTC"]),
        "import_status": outcomes[status],
        "observation_revision_id": player,
        "aggregate_revision_id": aggregate,
        "scan": row.get("LogicalScanID") if player else None,
        "data_included": "Players" if player else "Kingdoms and camps" if aggregate else None,
        "data_time_utc": _time(row.get("DataTimeUTC")) if player or aggregate else None,
        "player_records": row.get("PlayerRecords") if player else None,
        "kingdom_records": row.get("KingdomRecords") if aggregate else None,
        "camp_records": row.get("CampRecords") if aggregate else None,
        "revision_number": row.get("RevisionNo") if player or aggregate else None,
        "notes": notes,
    }


def _time(value):
    if value is None:
        return None
    if not isinstance(value, datetime) or value.utcoffset() not in (None, timedelta(0)):
        raise ValueError("Import history requires UTC timestamps.")
    return value.replace(tzinfo=None).isoformat(timespec="seconds") + "Z"


def encode_fact(fact):
    value = json.dumps(fact, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    if len(value.encode("utf-16-le")) > MAX_ROW_BYTES:
        raise ValueError("Import history row exceeds its durable bound.")
    return value


@dataclass(frozen=True)
class HistorySnapshot:
    intent_id: str
    source_key: str
    kvk_no: int
    guild_id: str
    vector_hash: bytes
    captured_utc: datetime
    row_count: int
    content_hash: bytes
    version: str = HISTORY_VERSION

    def hasher(self):
        """Length-delimited canonical rows follow this scope-bound hash seed."""
        seed = [
            self.version,
            self.intent_id,
            self.source_key,
            self.kvk_no,
            self.guild_id,
            self.vector_hash.hex(),
            _time(self.captured_utc),
        ]
        return hashlib.sha256(json.dumps(seed, separators=(",", ":")).encode("utf-8"))


def hash_row(hasher, payload):
    encoded = payload.encode("utf-8")
    hasher.update(len(encoded).to_bytes(8, "big"))
    hasher.update(encoded)
    return hashlib.sha256(encoded).digest()
