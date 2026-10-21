from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import logging
from typing import Any

from mge.dal import mge_event_dal

logger = logging.getLogger(__name__)

_ALLOWED_VARIANTS = {"infantry", "cavalry", "archer", "leadership"}
_BLOCK_OPEN_SWITCH_STATUSES = {"published", "completed"}
_CONTROLLED_EVENT_MODES = {"controlled"}
_OPEN_EVENT_MODES = {"open"}


@dataclass(slots=True)
class MgeSyncResult:
    scanned: int = 0
    created: int = 0
    existing: int = 0
    skipped: int = 0
    errors: int = 0


@dataclass(slots=True)
class SwitchToOpenResult:
    success: bool
    message: str
    deleted_signup_count: int = 0
    changed: bool = True


@dataclass(slots=True)
class SwitchToFixedResult:
    success: bool
    message: str
    updated_row_count: int = 0
    changed: bool = True


def _ensure_utc(dt: Any) -> datetime | None:
    if not isinstance(dt, datetime):
        return None
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def _normalized_variant(raw: Any) -> str | None:
    value = str(raw or "").strip().lower()
    return value if value in _ALLOWED_VARIANTS else None


def _is_mge_event_type(raw: Any) -> bool:
    value = str(raw or "").strip().lower()
    return "mge" in value or "mightiest governor" in value


def _build_variant_lookup() -> dict[str, dict[str, Any]]:
    rows = mge_event_dal.fetch_active_variants()
    lookup: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = str(row.get("VariantName") or "").strip().lower()
        if key:
            lookup[key] = row
    return lookup


def sync_mge_events_from_calendar(
    now_utc: datetime | None = None,
) -> tuple[MgeSyncResult, list[int]]:
    now = now_utc.astimezone(UTC) if now_utc else datetime.now(UTC)
    result = MgeSyncResult()
    event_ids_for_embed: list[int] = []

    # widened window for resilience to scheduler delays/downtime
    window_start = now
    window_end = now + timedelta(days=7)

    candidates = mge_event_dal.fetch_calendar_candidates(window_start, window_end)
    variants = _build_variant_lookup()
    rules_text = mge_event_dal.fetch_fixed_rule_template()

    if not rules_text:
        logger.error("mge_event_sync_aborted reason=fixed_rule_template_missing")
        result.errors += 1
        return result, event_ids_for_embed

    for row in candidates:
        result.scanned += 1
        try:
            if not _is_mge_event_type(row.get("EventType")):
                result.skipped += 1
                continue

            variant_key = _normalized_variant(row.get("Variant"))
            if not variant_key:
                result.skipped += 1
                continue

            variant_row = variants.get(variant_key)
            if not variant_row:
                result.skipped += 1
                continue

            source_instance_id = int(row["InstanceID"])
            source_kind = str(row.get("SourceKind") or "").strip() or None
            source_id = str(row.get("SourceID") or "").strip() or None

            start_utc = _ensure_utc(row.get("StartUTC"))
            end_utc = _ensure_utc(row.get("EndUTC"))
            if start_utc is None or end_utc is None:
                result.skipped += 1
                continue

            signup_close_utc = start_utc - timedelta(hours=1)
            variant_id = int(variant_row["VariantId"])

            # 1) fast path: by current instance id
            existing = mge_event_dal.fetch_mge_event_by_source(source_instance_id)

            # 2) stable-key fallback (handles regenerated InstanceID)
            if existing is None and source_id:
                existing = mge_event_dal.fetch_mge_event_by_stable_key(
                    variant_id=variant_id,
                    start_utc=start_utc,
                    end_utc=end_utc,
                    calendar_source_id=source_id,
                )
                if existing is not None:
                    mge_event_dal.update_event_calendar_source(
                        event_id=int(existing["EventId"]),
                        calendar_event_source_id=source_instance_id,
                        calendar_source_kind=source_kind,
                        calendar_source_id=source_id,
                        now_utc=now,
                    )

            if existing is not None:
                event_id = int(existing["EventId"])
                mge_event_dal.touch_event_updated_utc(event_id=event_id, now_utc=now)
                logger.info(
                    "mge_event_sync_existing source_instance_id=%s event_id=%s",
                    source_instance_id,
                    event_id,
                )
                result.existing += 1
                event_ids_for_embed.append(event_id)
                continue

            event_id = mge_event_dal.insert_mge_event(
                variant_id=variant_id,
                event_name=str(row.get("Title") or f"MGE {variant_row.get('VariantName')}"),
                start_utc=start_utc,
                end_utc=end_utc,
                signup_close_utc=signup_close_utc,
                rules_text=rules_text,
                calendar_event_source_id=source_instance_id,
                calendar_source_kind=source_kind,
                calendar_source_id=source_id,
                now_utc=now,
            )

            if event_id is None:
                result.errors += 1
                logger.warning(
                    "mge_event_sync_insert_failed source_instance_id=%s source_id=%s",
                    source_instance_id,
                    source_id,
                )
                continue

            logger.info(
                "mge_event_sync_created source_instance_id=%s event_id=%s source_id=%s",
                source_instance_id,
                event_id,
                source_id,
            )
            result.created += 1
            event_ids_for_embed.append(event_id)

        except Exception:
            result.errors += 1
            logger.exception(
                "mge_event_sync_item_failed source_instance_id=%s", row.get("InstanceID")
            )

    return result, event_ids_for_embed


def switch_event_to_open(*, event_id: int, actor_discord_id: int) -> SwitchToOpenResult:
    ctx = mge_event_dal.fetch_event_switch_context(event_id)
    if not ctx:
        return SwitchToOpenResult(False, "Event not found.", changed=False)

    status = str(ctx.get("Status") or "").strip().lower()
    if status in _BLOCK_OPEN_SWITCH_STATUSES:
        return SwitchToOpenResult(
            False, "Switch to open is blocked for published/completed events.", changed=False
        )

    event_mode = str(ctx.get("EventMode") or "").strip().lower()
    if event_mode in _OPEN_EVENT_MODES:
        return SwitchToOpenResult(
            True,
            "Event is already in open mode.",
            deleted_signup_count=0,
            changed=False,
        )

    open_rules = mge_event_dal.fetch_open_rule_template()
    if not open_rules:
        return SwitchToOpenResult(False, "Open rules template is missing.", changed=False)

    try:
        deleted_count = mge_event_dal.apply_open_mode_switch_atomic(
            event_id=event_id,
            actor_discord_id=actor_discord_id,
            old_rule_mode=(str(ctx.get("RuleMode")) if ctx.get("RuleMode") is not None else None),
            old_rules_text=(
                str(ctx.get("RulesText")) if ctx.get("RulesText") is not None else None
            ),
            new_rules_text=open_rules,
        )
    except Exception:
        logger.exception(
            "mge_switch_to_open_failed event_id=%s actor_discord_id=%s",
            event_id,
            actor_discord_id,
        )
        return SwitchToOpenResult(
            success=False,
            message="Failed to switch event to open mode. Please try again later.",
            deleted_signup_count=0,
            changed=False,
        )

    logger.info(
        "mge_switch_to_open_success event_id=%s actor_discord_id=%s deleted_signup_count=%s",
        event_id,
        actor_discord_id,
        deleted_count,
    )
    return SwitchToOpenResult(
        success=True,
        message="Event switched to open mode.",
        deleted_signup_count=deleted_count,
        changed=True,
    )


def switch_event_to_fixed(*, event_id: int, actor_discord_id: int) -> SwitchToFixedResult:
    ctx = mge_event_dal.fetch_event_switch_context(event_id)
    if not ctx:
        return SwitchToFixedResult(False, "Event not found.", changed=False)

    status = str(ctx.get("Status") or "").strip().lower()
    if status in _BLOCK_OPEN_SWITCH_STATUSES:
        return SwitchToFixedResult(
            False, "Switch back to fixed is blocked for published/completed events.", changed=False
        )

    event_mode = str(ctx.get("EventMode") or "").strip().lower()
    if event_mode in _CONTROLLED_EVENT_MODES:
        return SwitchToFixedResult(
            True,
            "Event is already in fixed mode.",
            updated_row_count=0,
            changed=False,
        )

    fixed_rules = mge_event_dal.fetch_fixed_rule_template()
    if not fixed_rules:
        return SwitchToFixedResult(False, "Fixed rules template is missing.", changed=False)

    try:
        updated_count = mge_event_dal.apply_fixed_mode_switch_atomic(
            event_id=event_id,
            actor_discord_id=actor_discord_id,
            old_rule_mode=(str(ctx.get("RuleMode")) if ctx.get("RuleMode") is not None else None),
            old_rules_text=(
                str(ctx.get("RulesText")) if ctx.get("RulesText") is not None else None
            ),
            new_rules_text=fixed_rules,
        )
    except Exception:
        logger.exception(
            "mge_switch_to_fixed_failed event_id=%s actor_discord_id=%s",
            event_id,
            actor_discord_id,
        )
        return SwitchToFixedResult(
            success=False,
            message="Failed to switch event back to fixed mode. Please try again later.",
            updated_row_count=0,
            changed=False,
        )

    logger.info(
        "mge_switch_to_fixed_success event_id=%s actor_discord_id=%s updated_row_count=%s",
        event_id,
        actor_discord_id,
        updated_count,
    )
    return SwitchToFixedResult(
        success=True,
        message="Event switched back to fixed mode.",
        updated_row_count=updated_count,
        changed=True,
    )
