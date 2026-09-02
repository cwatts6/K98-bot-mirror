from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
import logging
import re
from typing import Any

from ark.dal.ark_dal import (
    ArkMatchCreateRequest,
    create_match,
    fetch_ark_calendar_candidates,
    get_alliance,
    get_config,
    get_match_by_alliance_weekend,
)
from ark.datetime_utils import compute_signup_close
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)

_TITLE_PATTERN = re.compile(
    r"^ark\s+(?P<alliance>\S+)\s+(?P<day>saturday|sunday)\s+(?P<time>\d{2}:\d{2})$",
    re.IGNORECASE,
)
_DAY_TO_SHORT = {"saturday": "Sat", "sunday": "Sun"}
_DEFAULT_LOOKAHEAD_DAYS = 21
_QUERY_BACKLOOK_DAYS = 1


@dataclass(frozen=True, slots=True)
class ArkCalendarParseResult:
    alliance: str
    match_day_display: str
    match_day_short: str
    match_time_utc: time


@dataclass(slots=True)
class ArkAutoCreateResult:
    scanned: int = 0
    created: int = 0
    existing: int = 0
    skipped_cancelled_match: int = 0
    invalid_title: int = 0
    errors: int = 0


def parse_ark_calendar_title(title: str) -> ArkCalendarParseResult | None:
    """Parse an Ark EventInstances title into alliance/day/time values."""
    normalized = " ".join((title or "").strip().split())
    match = _TITLE_PATTERN.match(normalized)
    if not match:
        return None

    day_value = str(match.group("day")).strip().lower()
    match_day_short = _DAY_TO_SHORT.get(day_value)
    if not match_day_short:
        return None

    try:
        match_time_utc = datetime.strptime(str(match.group("time")), "%H:%M").time()
    except ValueError:
        return None

    return ArkCalendarParseResult(
        alliance=str(match.group("alliance")).strip(),
        match_day_display=day_value.title(),
        match_day_short=match_day_short,
        match_time_utc=match_time_utc,
    )


def derive_ark_weekend_date(end_utc: Any) -> date | None:
    """Derive the stored Ark weekend date from EventInstances.EndUTC."""
    if not isinstance(end_utc, datetime):
        return None
    end_dt = ensure_aware_utc(end_utc)
    return end_dt.date()


async def sync_ark_matches_from_calendar(
    *,
    client,
    now_utc: datetime | None = None,
    lookahead_days: int = _DEFAULT_LOOKAHEAD_DAYS,
    config: dict[str, Any] | None = None,
) -> ArkAutoCreateResult:
    """Create missing Ark matches from EventInstances."""
    now = ensure_aware_utc(now_utc or datetime.now(UTC))
    result = ArkAutoCreateResult()
    config = config or await get_config()
    if not config:
        logger.warning("ark_auto_create_missing_config")
        result.errors += 1
        return result

    window_start = ensure_aware_utc(now - timedelta(days=_QUERY_BACKLOOK_DAYS))
    window_end = ensure_aware_utc(now + timedelta(days=max(1, int(lookahead_days))))
    logger.info(
        "ark_auto_create_scan_start window_start=%s window_end=%s",
        window_start.isoformat(),
        window_end.isoformat(),
    )

    candidates = await fetch_ark_calendar_candidates(
        window_start=window_start, window_end=window_end
    )
    logger.info("ark_auto_create_candidates_found count=%s", len(candidates))

    for row in candidates:
        result.scanned += 1
        instance_id = row.get("InstanceID")
        try:
            parsed = parse_ark_calendar_title(str(row.get("Title") or ""))
            if parsed is None:
                result.invalid_title += 1
                logger.warning(
                    "ark_auto_create_invalid_title instance_id=%s title=%r",
                    instance_id,
                    row.get("Title"),
                )
                continue

            ark_weekend_date = derive_ark_weekend_date(row.get("EndUTC"))
            if ark_weekend_date is None:
                result.errors += 1
                logger.warning(
                    "ark_auto_create_missing_endutc instance_id=%s title=%r",
                    instance_id,
                    row.get("Title"),
                )
                continue

            logger.info(
                "ark_auto_create_parsed instance_id=%s alliance=%s match_day=%s match_time_utc=%s ark_weekend_date=%s",
                instance_id,
                parsed.alliance,
                parsed.match_day_short,
                parsed.match_time_utc.isoformat(timespec="minutes"),
                ark_weekend_date.isoformat(),
            )

            alliance_row = await get_alliance(parsed.alliance)
            if not alliance_row:
                result.errors += 1
                logger.warning(
                    "ark_auto_create_alliance_not_found instance_id=%s alliance=%s",
                    instance_id,
                    parsed.alliance,
                )
                continue

            reg_channel_id = alliance_row.get("RegistrationChannelId")
            conf_channel_id = alliance_row.get("ConfirmationChannelId")
            if not reg_channel_id or not conf_channel_id:
                result.errors += 1
                logger.warning(
                    "ark_auto_create_missing_channels instance_id=%s alliance=%s reg_channel_id=%s conf_channel_id=%s",
                    instance_id,
                    parsed.alliance,
                    reg_channel_id,
                    conf_channel_id,
                )
                continue

            existing_match = await get_match_by_alliance_weekend(parsed.alliance, ark_weekend_date)
            if existing_match:
                status = str(existing_match.get("Status") or "").strip().lower()
                if status == "cancelled":
                    result.skipped_cancelled_match += 1
                    logger.info(
                        "ark_auto_create_skip_cancelled_match instance_id=%s match_id=%s alliance=%s ark_weekend_date=%s",
                        instance_id,
                        existing_match.get("MatchId"),
                        parsed.alliance,
                        ark_weekend_date.isoformat(),
                    )
                else:
                    result.existing += 1
                    logger.info(
                        "ark_auto_create_existing instance_id=%s match_id=%s alliance=%s ark_weekend_date=%s status=%s",
                        instance_id,
                        existing_match.get("MatchId"),
                        parsed.alliance,
                        ark_weekend_date.isoformat(),
                        existing_match.get("Status"),
                    )
                continue

            signup_close = compute_signup_close(
                ark_weekend_date,
                str(config["SignupCloseDay"]),
                config["SignupCloseTimeUtc"],
            )
            registration_starts_at_utc = row.get("StartUTC")
            if not isinstance(registration_starts_at_utc, datetime):
                result.errors += 1
                logger.warning(
                    "ark_auto_create_missing_startutc instance_id=%s alliance=%s ark_weekend_date=%s",
                    instance_id,
                    parsed.alliance,
                    ark_weekend_date.isoformat(),
                )
                continue

            match_id = await create_match(
                ArkMatchCreateRequest(
                    alliance=parsed.alliance,
                    ark_weekend_date=ark_weekend_date,
                    match_day=parsed.match_day_short,
                    match_time_utc=parsed.match_time_utc,
                    registration_starts_at_utc=ensure_aware_utc(registration_starts_at_utc),
                    signup_close_utc=signup_close,
                    notes=None,
                    actor_discord_id=0,
                    calendar_instance_id=int(instance_id) if instance_id is not None else None,
                    created_source="calendar_auto",
                )
            )
            if not match_id:
                result.errors += 1
                logger.warning(
                    "ark_auto_create_insert_failed instance_id=%s alliance=%s ark_weekend_date=%s",
                    instance_id,
                    parsed.alliance,
                    ark_weekend_date.isoformat(),
                )
                continue

            result.created += 1
            logger.info(
                "ark_auto_create_created instance_id=%s match_id=%s alliance=%s ark_weekend_date=%s registration_starts_at_utc=%s created_source=%s",
                instance_id,
                match_id,
                parsed.alliance,
                ark_weekend_date.isoformat(),
                ensure_aware_utc(registration_starts_at_utc).isoformat(),
                "calendar_auto",
            )
        except Exception:
            result.errors += 1
            logger.exception("ark_auto_create_item_failed instance_id=%s", instance_id)

    logger.info(
        "ark_auto_create_scan_complete scanned=%s created=%s existing=%s skipped_cancelled_match=%s invalid_title=%s errors=%s",
        result.scanned,
        result.created,
        result.existing,
        result.skipped_cancelled_match,
        result.invalid_title,
        result.errors,
    )
    return result
