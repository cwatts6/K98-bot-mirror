from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import io
import json
import logging
from typing import Any
from urllib.parse import quote

import requests

from constants import DATABASE, SERVER
from file_utils import emit_telemetry_event, get_conn_with_retries

logger = logging.getLogger(__name__)

_REQUIRED_RECURRING = {
    "active",
    "rule_id",
    "title",
    "type",
    "recurrence_type",
    "first_start_utc",
    "duration_days",
}
_REQUIRED_ONEOFF = {"active", "event_id", "title", "type", "start_utc", "end_utc"}
_REQUIRED_OVERRIDES = {"active", "override_id", "target_kind", "target_id", "action"}

_ALLOWED_TABLE_KEYS: dict[str, tuple[str, set[str]]] = {
    "EventRecurringRules": (
        "RuleID",
        {
            "RuleID",
            "IsActive",
            "Emoji",
            "Title",
            "EventType",
            "Variant",
            "RecurrenceType",
            "IntervalDays",
            "FirstStartUTC",
            "DurationDays",
            "RepeatUntilUTC",
            "MaxOccurrences",
            "AllDay",
            "Importance",
            "Description",
            "LinkURL",
            "ChannelID",
            "SignupURL",
            "Tags",
            "SortOrder",
            "NotesInternal",
            "SourceRowHash",
        },
    ),
    "EventOneOffEvents": (
        "EventID",
        {
            "EventID",
            "IsActive",
            "Emoji",
            "Title",
            "EventType",
            "Variant",
            "StartUTC",
            "EndUTC",
            "AllDay",
            "Importance",
            "Description",
            "LinkURL",
            "ChannelID",
            "SignupURL",
            "Tags",
            "SortOrder",
            "NotesInternal",
            "SourceRowHash",
        },
    ),
    "EventOverrides": (
        "OverrideID",
        {
            "OverrideID",
            "IsActive",
            "TargetKind",
            "TargetID",
            "TargetOccurrenceStartUTC",
            "ActionType",
            "NewStartUTC",
            "NewEndUTC",
            "NewTitle",
            "NewVariant",
            "NewEmoji",
            "NewImportance",
            "NewDescription",
            "NewLinkURL",
            "NewChannelID",
            "NewSignupURL",
            "NewTags",
            "NotesInternal",
            "SourceRowHash",
        },
    ),
}


@dataclass
class SyncResult:
    ok: bool
    status: str
    rows_read_recurring: int = 0
    rows_read_oneoff: int = 0
    rows_read_overrides: int = 0
    rows_upserted_recurring: int = 0
    rows_upserted_oneoff: int = 0
    rows_upserted_overrides: int = 0
    instances_generated: int = 0
    error_message: str | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_bool(v: Any) -> bool:
    s = str(v or "").strip().lower()
    return s in {"1", "true", "t", "yes", "y"}


def _parse_int(v: Any) -> int | None:
    s = str(v or "").strip()
    if not s:
        return None
    return int(float(s))


def _parse_dt(v: Any) -> datetime | None:
    s = str(v or "").strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    if " " in s and "T" not in s:
        s = s.replace(" ", "T")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)
    return dt.replace(microsecond=0)


def _clean(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s != "" else None


def _normalize_tags(v: Any) -> str | None:
    raw = _clean(v)
    if not raw:
        return None
    seen: set[str] = set()
    out: list[str] = []
    for p in raw.split(","):
        t = p.strip()
        if not t:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return ",".join(out) if out else None


def _hash_row(row: dict[str, Any]) -> bytes:
    payload = json.dumps(row, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).digest()


def _ensure_columns(rows: list[dict[str, Any]], required: set[str], tab: str) -> None:
    if not rows:
        return
    headers = {k.strip().lower() for k in rows[0].keys()}
    missing = sorted(required - headers)
    if missing:
        raise ValueError(f"{tab}: missing required columns: {missing}")


def _normalize_header_key(key: str) -> str:
    return key.replace("\ufeff", "").strip().lower()


def _normalize_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    return {_normalize_header_key(str(k)): v for k, v in row.items()}


def fetch_sheet_csv(sheet_id: str, tab: str, *, timeout: float = 20.0) -> list[dict[str, str]]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{quote(sheet_id)}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(tab)}"
    )
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    text = r.text or ""
    reader = csv.DictReader(io.StringIO(text))
    return [_normalize_row_keys(dict(row)) for row in reader]


def parse_recurring_rules(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_columns(rows, _REQUIRED_RECURRING, "recurring_rules")
    out: list[dict[str, Any]] = []
    for row in rows:
        norm = {
            "RuleID": _clean(row.get("rule_id")),
            "IsActive": _parse_bool(row.get("active")),
            "Emoji": _clean(row.get("emoji")),
            "Title": _clean(row.get("title")),
            "EventType": _clean(row.get("type")),
            "Variant": _clean(row.get("variant")),
            "RecurrenceType": _clean(row.get("recurrence_type")),
            "IntervalDays": _parse_int(row.get("interval_days")),
            "FirstStartUTC": _parse_dt(row.get("first_start_utc")),
            "DurationDays": _parse_int(row.get("duration_days")),
            "RepeatUntilUTC": _parse_dt(row.get("repeat_until_utc")),
            "MaxOccurrences": _parse_int(row.get("max_occurrences")),
            "AllDay": _parse_bool(row.get("all_day")),
            "Importance": _clean(row.get("importance")),
            "Description": _clean(row.get("description")),
            "LinkURL": _clean(row.get("link_url")),
            "ChannelID": _clean(row.get("channel_id")),
            "SignupURL": _clean(row.get("signup_url")),
            "Tags": _normalize_tags(row.get("tags")),
            "SortOrder": _parse_int(row.get("sort_order")),
            "NotesInternal": _clean(row.get("notes_internal")),
        }
        if not norm["RuleID"] or not norm["Title"] or not norm["EventType"]:
            raise ValueError("recurring_rules: rule_id/title/type required")
        if norm["FirstStartUTC"] is None:
            raise ValueError(f"recurring_rules[{norm['RuleID']}]: first_start_utc required")
        if norm["DurationDays"] is None:
            raise ValueError(f"recurring_rules[{norm['RuleID']}]: duration_days required")
        hash_input = {
            k: v for k, v in norm.items() if k not in {"SourceRowHash", "CreatedUTC", "ModifiedUTC"}
        }
        norm["SourceRowHash"] = _hash_row(hash_input)
        out.append(norm)
    return out


def parse_oneoff_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_columns(rows, _REQUIRED_ONEOFF, "oneoff_events")
    out: list[dict[str, Any]] = []
    for row in rows:
        norm = {
            "EventID": _clean(row.get("event_id")),
            "IsActive": _parse_bool(row.get("active")),
            "Emoji": _clean(row.get("emoji")),
            "Title": _clean(row.get("title")),
            "EventType": _clean(row.get("type")),
            "Variant": _clean(row.get("variant")),
            "StartUTC": _parse_dt(row.get("start_utc")),
            "EndUTC": _parse_dt(row.get("end_utc")),
            "AllDay": _parse_bool(row.get("all_day")),
            "Importance": _clean(row.get("importance")),
            "Description": _clean(row.get("description")),
            "LinkURL": _clean(row.get("link_url")),
            "ChannelID": _clean(row.get("channel_id")),
            "SignupURL": _clean(row.get("signup_url")),
            "Tags": _normalize_tags(row.get("tags")),
            "SortOrder": _parse_int(row.get("sort_order")),
            "NotesInternal": _clean(row.get("notes_internal")),
        }
        if not norm["EventID"] or not norm["Title"] or not norm["EventType"]:
            raise ValueError("oneoff_events: event_id/title/type required")
        if norm["StartUTC"] is None or norm["EndUTC"] is None:
            raise ValueError(f"oneoff_events[{norm['EventID']}]: start_utc/end_utc required")
        if norm["EndUTC"] <= norm["StartUTC"]:
            raise ValueError(f"oneoff_events[{norm['EventID']}]: end_utc must be > start_utc")
        hash_input = {
            k: v for k, v in norm.items() if k not in {"SourceRowHash", "CreatedUTC", "ModifiedUTC"}
        }
        norm["SourceRowHash"] = _hash_row(hash_input)
        out.append(norm)
    return out


def parse_overrides(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_columns(rows, _REQUIRED_OVERRIDES, "overrides")
    out: list[dict[str, Any]] = []
    for row in rows:
        action = (_clean(row.get("action")) or "").lower()
        target_kind = (_clean(row.get("target_kind")) or "").lower()

        norm = {
            "OverrideID": _clean(row.get("override_id")),
            "IsActive": _parse_bool(row.get("active")),
            "TargetKind": target_kind,
            "TargetID": _clean(row.get("target_id")),
            "TargetOccurrenceStartUTC": _parse_dt(row.get("target_occurrence_start_utc")),
            "ActionType": action,
            "NewStartUTC": _parse_dt(row.get("new_start_utc")),
            "NewEndUTC": _parse_dt(row.get("new_end_utc")),
            "NewTitle": _clean(row.get("new_title")),
            "NewVariant": _clean(row.get("new_variant")),
            "NewEmoji": _clean(row.get("new_emoji")),
            "NewImportance": _clean(row.get("new_importance")),
            "NewDescription": _clean(row.get("new_description")),
            "NewLinkURL": _clean(row.get("new_link_url")),
            "NewChannelID": _clean(row.get("new_channel_id")),
            "NewSignupURL": _clean(row.get("new_signup_url")),
            "NewTags": _normalize_tags(row.get("new_tags")),
            "NotesInternal": _clean(row.get("notes_internal")),
        }
        if not norm["OverrideID"] or not norm["TargetKind"] or not norm["TargetID"]:
            raise ValueError("overrides: override_id/target_kind/target_id required")
        if target_kind not in {"rule", "oneoff", "instance"}:
            raise ValueError(
                f"overrides[{norm['OverrideID']}]: target_kind must be rule|oneoff|instance"
            )
        if action not in {"cancel", "modify"}:
            raise ValueError(f"overrides[{norm['OverrideID']}]: action must be cancel|modify")
        if norm["NewEndUTC"] and norm["NewStartUTC"] and norm["NewEndUTC"] <= norm["NewStartUTC"]:
            raise ValueError(
                f"overrides[{norm['OverrideID']}]: new_end_utc must be > new_start_utc"
            )
        hash_input = {
            k: v for k, v in norm.items() if k not in {"SourceRowHash", "CreatedUTC", "ModifiedUTC"}
        }
        norm["SourceRowHash"] = _hash_row(hash_input)
        out.append(norm)
    return out


def _validate_upsert_identifiers(table_name: str, key_column: str, cols: list[str]) -> None:
    entry = _ALLOWED_TABLE_KEYS.get(table_name)
    if not entry:
        raise ValueError(f"Unsupported table_name: {table_name}")

    expected_key, allowed_cols = entry
    if key_column != expected_key:
        raise ValueError(
            f"Unsupported key_column '{key_column}' for table '{table_name}', expected '{expected_key}'"
        )

    unexpected = sorted(set(cols) - allowed_cols)
    if unexpected:
        raise ValueError(f"Unexpected columns for {table_name}: {unexpected}")


def upsert_sql_rows(
    *,
    table_name: str,
    key_column: str,
    rows: list[dict[str, Any]],
    conn=None,
) -> int:
    if not rows:
        return 0

    cols = [c for c in rows[0].keys()]
    _validate_upsert_identifiers(table_name, key_column, cols)

    non_key = [c for c in cols if c != key_column]
    placeholders = ", ".join(["?"] * len(cols))
    insert_sql = f"""
        INSERT INTO dbo.{table_name} ({", ".join(cols)})
        VALUES ({placeholders})
    """
    select_sql = f"SELECT SourceRowHash FROM dbo.{table_name} WHERE {key_column} = ?"
    update_cols = [c for c in non_key if c not in {"CreatedUTC"}]
    update_sql = f"""
        UPDATE dbo.{table_name}
        SET {", ".join([f"{c} = ?" for c in update_cols])},
            ModifiedUTC = SYSUTCDATETIME()
        WHERE {key_column} = ?
    """

    changed = 0

    def _run(cur) -> int:
        local_changed = 0
        for row in rows:
            key_val = row[key_column]
            cur.execute(select_sql, key_val)
            found = cur.fetchone()
            if not found:
                cur.execute(insert_sql, [row[c] for c in cols])
                local_changed += 1
                continue

            old_hash = found[0]
            new_hash = row.get("SourceRowHash")
            if old_hash == new_hash:
                continue

            params = [row[c] for c in update_cols] + [key_val]
            cur.execute(update_sql, params)
            local_changed += 1
        return local_changed

    if conn is not None:
        cur = conn.cursor()
        changed = _run(cur)
        return changed

    with get_conn_with_retries(meta={"operation": f"calendar_upsert_{table_name}"}) as new_conn:
        cur = new_conn.cursor()
        changed = _run(cur)
        new_conn.commit()
    return changed


def _insert_sync_log_start(source_name: str) -> int:
    sql = """
        INSERT INTO dbo.EventSyncLog (SyncStartedUTC, SourceName, Status)
        OUTPUT INSERTED.SyncID
        VALUES (SYSUTCDATETIME(), ?, ?)
    """
    with get_conn_with_retries(meta={"operation": "calendar_synclog_start"}) as conn:
        cur = conn.cursor()
        cur.execute(sql, source_name, "running")
        row = cur.fetchone()
        conn.commit()
        return int(row[0])


def _finish_sync_log(sync_id: int, result: SyncResult) -> None:
    sql = """
        UPDATE dbo.EventSyncLog
        SET
            SyncCompletedUTC = SYSUTCDATETIME(),
            Status = ?,
            RowsReadRecurring = ?,
            RowsReadOneOff = ?,
            RowsReadOverrides = ?,
            RowsUpsertedRecurring = ?,
            RowsUpsertedOneOff = ?,
            RowsUpsertedOverrides = ?,
            InstancesGenerated = ?,
            ErrorMessage = ?
        WHERE SyncID = ?
    """
    with get_conn_with_retries(meta={"operation": "calendar_synclog_finish"}) as conn:
        cur = conn.cursor()
        cur.execute(
            sql,
            result.status,
            result.rows_read_recurring,
            result.rows_read_oneoff,
            result.rows_read_overrides,
            result.rows_upserted_recurring,
            result.rows_upserted_oneoff,
            result.rows_upserted_overrides,
            result.instances_generated,
            result.error_message,
            sync_id,
        )
        conn.commit()


def sync_sheets_to_sql(sheet_id: str) -> SyncResult:
    sync_id = _insert_sync_log_start("google_sheets")
    try:
        recurring_raw = fetch_sheet_csv(sheet_id, "recurring_rules")
        oneoff_raw = fetch_sheet_csv(sheet_id, "oneoff_events")
        overrides_raw = fetch_sheet_csv(sheet_id, "overrides")

        recurring = parse_recurring_rules(recurring_raw)
        oneoff = parse_oneoff_events(oneoff_raw)
        overrides = parse_overrides(overrides_raw)

        with get_conn_with_retries(meta={"operation": "calendar_sync_upserts_txn"}) as conn:
            up_r = upsert_sql_rows(
                table_name="EventRecurringRules",
                key_column="RuleID",
                rows=recurring,
                conn=conn,
            )
            up_o = upsert_sql_rows(
                table_name="EventOneOffEvents",
                key_column="EventID",
                rows=oneoff,
                conn=conn,
            )
            up_v = upsert_sql_rows(
                table_name="EventOverrides",
                key_column="OverrideID",
                rows=overrides,
                conn=conn,
            )
            conn.commit()

        result = SyncResult(
            ok=True,
            status="success",
            rows_read_recurring=len(recurring_raw),
            rows_read_oneoff=len(oneoff_raw),
            rows_read_overrides=len(overrides_raw),
            rows_upserted_recurring=up_r,
            rows_upserted_oneoff=up_o,
            rows_upserted_overrides=up_v,
            instances_generated=0,
            error_message=None,
        )
        _finish_sync_log(sync_id, result)
        emit_telemetry_event(
            {
                "event": "calendar_sync",
                "status": "success",
                "server": SERVER,
                "database": DATABASE,
                "rows": {
                    "recurring": len(recurring_raw),
                    "oneoff": len(oneoff_raw),
                    "overrides": len(overrides_raw),
                },
                "upserted": {
                    "recurring": up_r,
                    "oneoff": up_o,
                    "overrides": up_v,
                },
            }
        )
        return result

    except Exception as e:
        logger.exception("[CALENDAR] sync_sheets_to_sql failed")
        result = SyncResult(
            ok=False,
            status="failed_fetch_or_validate",
            error_message=f"{type(e).__name__}: {e}",
        )
        try:
            _finish_sync_log(sync_id, result)
        except Exception:
            logger.exception("[CALENDAR] failed to write EventSyncLog failure row")
        emit_telemetry_event(
            {
                "event": "calendar_sync",
                "status": "failed",
                "error_type": type(e).__name__,
                "error": str(e),
            }
        )
        return result
