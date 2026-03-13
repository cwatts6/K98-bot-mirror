from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
from typing import Any

from file_utils import get_conn_with_retries

logger = logging.getLogger(__name__)

# current:
_VALID_TARGET_KINDS = {"rule", "oneoff", "instance"}

# add:
_TARGET_KIND_TO_SOURCE_KIND = {
    "rule": "recurring",
    "oneoff": "oneoff",
    "instance": "instance",
    "recurring": "recurring",  # defensive for future data
}


@dataclass
class GenerationResult:
    ok: bool
    status: str
    instances_generated: int = 0
    instances_written: int = 0
    cancelled_count: int = 0
    modified_count: int = 0
    error_message: str | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _dt(v: Any) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.astimezone(UTC) if v.tzinfo else v.replace(tzinfo=UTC)
    return None


def load_recurring_rules(conn) -> list[dict[str, Any]]:
    sql = """
    SELECT RuleID, IsActive, Emoji, Title, EventType, Variant, RecurrenceType,
           IntervalDays, FirstStartUTC, DurationDays, RepeatUntilUTC, MaxOccurrences,
           AllDay, Importance, Description, LinkURL, ChannelID, SignupURL, Tags, SortOrder
    FROM dbo.EventRecurringRules
    WHERE IsActive = 1
    """
    cur = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def load_oneoff_events(conn) -> list[dict[str, Any]]:
    sql = """
    SELECT EventID, IsActive, Emoji, Title, EventType, Variant, StartUTC, EndUTC,
           AllDay, Importance, Description, LinkURL, ChannelID, SignupURL, Tags, SortOrder
    FROM dbo.EventOneOffEvents
    WHERE IsActive = 1
    """
    cur = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def load_overrides(conn) -> list[dict[str, Any]]:
    sql = """
    SELECT OverrideID, IsActive, TargetKind, TargetID, TargetOccurrenceStartUTC, ActionType,
           NewStartUTC, NewEndUTC, NewTitle, NewVariant, NewEmoji, NewImportance,
           NewDescription, NewLinkURL, NewChannelID, NewSignupURL, NewTags
    FROM dbo.EventOverrides
    WHERE IsActive = 1
    ORDER BY OverrideID ASC
    """
    cur = conn.cursor()
    cur.execute(sql)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]

    for r in rows:
        tk = str(r.get("TargetKind") or "").lower().strip()
        if tk not in _VALID_TARGET_KINDS:
            raise ValueError(
                f"overrides[{r.get('OverrideID')}]: target_kind must be rule|oneoff|instance"
            )
        r["TargetKind"] = tk

        action = str(r.get("ActionType") or "").lower().strip()
        if action not in {"cancel", "modify"}:
            raise ValueError(f"overrides[{r.get('OverrideID')}]: action must be cancel|modify")
        r["ActionType"] = action
    return rows


def generate_recurring_instances(
    *, rules: list[dict[str, Any]], horizon_start_utc: datetime, horizon_end_utc: datetime
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in rules:
        interval_days = int(r.get("IntervalDays") or 0)
        if interval_days <= 0:
            continue

        first = _dt(r.get("FirstStartUTC"))
        duration_days = int(r.get("DurationDays") or 0)
        if first is None or duration_days <= 0:
            continue

        repeat_until = _dt(r.get("RepeatUntilUTC"))
        max_occ = int(r.get("MaxOccurrences") or 0) or None

        current = first
        produced = 0
        while current <= horizon_end_utc:
            if repeat_until and current > repeat_until:
                break
            if max_occ is not None and produced >= max_occ:
                break

            end = current + timedelta(days=duration_days)
            if end > horizon_start_utc and current <= horizon_end_utc:
                out.append(
                    {
                        "SourceKind": "recurring",
                        "SourceID": r["RuleID"],
                        "StartUTC": current,
                        "EndUTC": end,
                        "AllDay": bool(r.get("AllDay")),
                        "Emoji": r.get("Emoji"),
                        "Title": r.get("Title"),
                        "EventType": r.get("EventType"),
                        "Variant": r.get("Variant"),
                        "Importance": r.get("Importance"),
                        "Description": r.get("Description"),
                        "LinkURL": r.get("LinkURL"),
                        "ChannelID": r.get("ChannelID"),
                        "SignupURL": r.get("SignupURL"),
                        "Tags": r.get("Tags"),
                        "SortOrder": r.get("SortOrder"),
                        "IsCancelled": False,
                    }
                )
            current = current + timedelta(days=interval_days)
            produced += 1
    return out


def merge_events(
    *, recurring_instances: list[dict[str, Any]], oneoff_events: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged = list(recurring_instances)
    for e in oneoff_events:
        start = _dt(e.get("StartUTC"))
        end = _dt(e.get("EndUTC"))
        if not start or not end or end <= start:
            logger.warning(
                "[CALENDAR][GENERATE] skip_invalid_oneoff event_id=%s reason=invalid_start_end",
                e.get("EventID"),
            )
            continue

        merged.append(
            {
                "SourceKind": "oneoff",
                "SourceID": e["EventID"],
                "StartUTC": start,
                "EndUTC": end,
                "AllDay": bool(e.get("AllDay")),
                "Emoji": e.get("Emoji"),
                "Title": e.get("Title"),
                "EventType": e.get("EventType"),
                "Variant": e.get("Variant"),
                "Importance": e.get("Importance"),
                "Description": e.get("Description"),
                "LinkURL": e.get("LinkURL"),
                "ChannelID": e.get("ChannelID"),
                "SignupURL": e.get("SignupURL"),
                "Tags": e.get("Tags"),
                "SortOrder": e.get("SortOrder"),
                "IsCancelled": False,
            }
        )

    merged.sort(
        key=lambda x: (
            x.get("StartUTC") or datetime.max.replace(tzinfo=UTC),
            str(x.get("EventType") or ""),
            str(x.get("SourceKind") or ""),
            str(x.get("SourceID") or ""),
            str(x.get("Title") or ""),
        )
    )
    return merged


def apply_overrides(
    *, instances: list[dict[str, Any]], overrides: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, int]:
    cancelled = 0
    modified = 0

    for ov in overrides:
        action = ov.get("ActionType")
        tk_raw = str(ov.get("TargetKind") or "").strip().lower()
        tk = _TARGET_KIND_TO_SOURCE_KIND.get(tk_raw, tk_raw)
        target_id = ov.get("TargetID")
        target_start = _dt(ov.get("TargetOccurrenceStartUTC"))

        for inst in instances:
            if inst.get("SourceKind") != tk:
                continue
            if str(inst.get("SourceID")) != str(target_id):
                continue
            if target_start and _dt(inst.get("StartUTC")) != target_start:
                continue

            if action == "cancel":
                if not inst.get("IsCancelled"):
                    inst["IsCancelled"] = True
                    cancelled += 1
            elif action == "modify":
                patch_map = {
                    "NewStartUTC": "StartUTC",
                    "NewEndUTC": "EndUTC",
                    "NewTitle": "Title",
                    "NewVariant": "Variant",
                    "NewEmoji": "Emoji",
                    "NewImportance": "Importance",
                    "NewDescription": "Description",
                    "NewLinkURL": "LinkURL",
                    "NewChannelID": "ChannelID",
                    "NewSignupURL": "SignupURL",
                    "NewTags": "Tags",
                }
                for src, dst in patch_map.items():
                    val = ov.get(src)
                    if val is not None:
                        inst[dst] = val
                if (
                    _dt(inst.get("EndUTC"))
                    and _dt(inst.get("StartUTC"))
                    and _dt(inst["EndUTC"]) <= _dt(inst["StartUTC"])
                ):
                    raise ValueError(
                        f"overrides[{ov.get('OverrideID')}]: resulting end must be > start"
                    )
                modified += 1

    return instances, cancelled, modified


def compute_effective_hash(instance: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in instance.items() if k not in {"EffectiveHash", "GeneratedUTC"}}
    b = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(b).digest()


def write_event_instances(*, conn, instances: list[dict[str, Any]]) -> int:
    cur = conn.cursor()
    cur.execute("DELETE FROM dbo.EventInstances")

    sql = """
    INSERT INTO dbo.EventInstances
    (SourceKind, SourceID, StartUTC, EndUTC, AllDay, Emoji, Title, EventType, Variant,
     Importance, Description, LinkURL, ChannelID, SignupURL, Tags, SortOrder, IsCancelled,
     GeneratedUTC, EffectiveHash)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), ?)
    """
    written = 0
    for i in instances:
        i["EffectiveHash"] = compute_effective_hash(i)
        cur.execute(
            sql,
            i.get("SourceKind"),
            i.get("SourceID"),
            i.get("StartUTC"),
            i.get("EndUTC"),
            bool(i.get("AllDay")),
            i.get("Emoji"),
            i.get("Title"),
            i.get("EventType"),
            i.get("Variant"),
            i.get("Importance"),
            i.get("Description"),
            i.get("LinkURL"),
            i.get("ChannelID"),
            i.get("SignupURL"),
            i.get("Tags"),
            i.get("SortOrder"),
            bool(i.get("IsCancelled")),
            i.get("EffectiveHash"),
        )
        written += 1
    return written


def generate_calendar_instances(*, horizon_days: int = 365) -> GenerationResult:
    now = _utcnow()
    horizon_start = now
    horizon_end = now + timedelta(days=horizon_days)

    try:
        with get_conn_with_retries(meta={"operation": "calendar_generate_instances"}) as conn:
            recurring = load_recurring_rules(conn)
            oneoff = load_oneoff_events(conn)
            overrides = load_overrides(conn)

            recurring_instances = generate_recurring_instances(
                rules=recurring,
                horizon_start_utc=horizon_start,
                horizon_end_utc=horizon_end,
            )
            merged = merge_events(recurring_instances=recurring_instances, oneoff_events=oneoff)
            final_instances, cancelled, modified = apply_overrides(
                instances=merged, overrides=overrides
            )

            written = write_event_instances(conn=conn, instances=final_instances)
            conn.commit()

        return GenerationResult(
            ok=True,
            status="success",
            instances_generated=len(final_instances),
            instances_written=written,
            cancelled_count=cancelled,
            modified_count=modified,
        )
    except Exception as e:
        logger.exception("[CALENDAR] generate_calendar_instances failed")
        return GenerationResult(
            ok=False,
            status="failed_generate",
            error_message=f"{type(e).__name__}: {e}",
        )
