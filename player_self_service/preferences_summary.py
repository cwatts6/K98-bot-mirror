"""Typed, read-only summary construction for the premium Preferences card."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from player_self_service import profile_preference_service
from player_self_service.profile_preference_service import UserProfilePreference

TimeReferenceMode = Literal["LOCAL", "UTC_FALLBACK"]


@dataclass(frozen=True, slots=True)
class PreferenceValueSummary:
    is_set: bool
    is_available: bool
    friendly_label: str
    stored_value: str | None = None
    player_code: str | None = None


@dataclass(frozen=True, slots=True)
class RegionalProfileSummary:
    timezone: PreferenceValueSummary
    location: PreferenceValueSummary
    preferred_language: PreferenceValueSummary


@dataclass(frozen=True, slots=True)
class TimeReferenceSummary:
    mode: TimeReferenceMode
    heading: Literal["LOCAL TIME REFERENCE", "UTC REFERENCE"]
    display_time: str
    timezone_label: str | None
    utc_offset_label: str | None
    supporting_line: str
    regional_context: str | None


@dataclass(frozen=True, slots=True)
class PreferencesSummaryPayload:
    discord_user_id: int
    display_name: str
    kingdom_id: int
    generated_at_utc: datetime
    regional_profile: RegionalProfileSummary
    time_reference: TimeReferenceSummary
    profile_details_set: int
    profile_details_total: int
    profile_supporting_text: str
    settings_insight: str
    warnings: tuple[str, ...] = ()


ProfileLoader = Callable[[int], Awaitable[profile_preference_service.UserProfilePreferenceRead]]
UtcClock = Callable[[], datetime]


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Preferences generated_at must be timezone-aware")
    return value.astimezone(UTC)


def format_utc_offset(offset: timedelta | None) -> str:
    if offset is None:
        return "UTC"
    seconds = int(offset.total_seconds())
    if seconds == 0:
        return "UTC"
    sign = "+" if seconds > 0 else "-"
    minutes = abs(seconds) // 60
    hours, remainder = divmod(minutes, 60)
    return f"UTC{sign}{hours}" if remainder == 0 else f"UTC{sign}{hours}:{remainder:02d}"


def _preference_value(
    field: profile_preference_service.ProfileField, value: str | None
) -> PreferenceValueSummary:
    is_set, is_available, friendly_label, code = profile_preference_service.profile_value_display(
        field, value
    )
    return PreferenceValueSummary(
        is_set=is_set,
        is_available=is_available,
        friendly_label=friendly_label,
        stored_value=value,
        player_code=code,
    )


def _regional_profile(profile: UserProfilePreference) -> RegionalProfileSummary:
    return RegionalProfileSummary(
        timezone=_preference_value("timezone", profile.timezone_name),
        location=_preference_value("country", profile.location_country_code),
        preferred_language=_preference_value("language", profile.preferred_language_tag),
    )


def _regional_context(profile: RegionalProfileSummary) -> str | None:
    items: list[str] = []
    if profile.location.is_set and profile.location.is_available:
        items.append(profile.location.friendly_label)
    if profile.preferred_language.is_set and profile.preferred_language.is_available:
        items.append(profile.preferred_language.friendly_label)
    return " • ".join(items) or None


def _time_reference(
    generated_at: datetime,
    profile: RegionalProfileSummary,
) -> TimeReferenceSummary:
    context = _regional_context(profile)
    if profile.timezone.is_set and profile.timezone.is_available and profile.timezone.player_code:
        local = generated_at.astimezone(ZoneInfo(profile.timezone.player_code))
        offset = format_utc_offset(local.utcoffset())
        return TimeReferenceSummary(
            mode="LOCAL",
            heading="LOCAL TIME REFERENCE",
            display_time=local.strftime("%H:%M"),
            timezone_label=profile.timezone.friendly_label,
            utc_offset_label=offset,
            supporting_line=f"{profile.timezone.friendly_label} • {offset}",
            regional_context=context,
        )
    return TimeReferenceSummary(
        mode="UTC_FALLBACK",
        heading="UTC REFERENCE",
        display_time=generated_at.strftime("%H:%M"),
        timezone_label=None,
        utc_offset_label="UTC",
        supporting_line="Set a timezone to show your local-time reference.",
        regional_context=context,
    )


def _settings_insight(profile: RegionalProfileSummary) -> str:
    values = (profile.timezone, profile.location, profile.preferred_language)
    if any(value.is_set and not value.is_available for value in values):
        return "One or more saved profile details are unavailable and need review."
    if not profile.timezone.is_set or not profile.timezone.is_available:
        return "Set a timezone to add a local-time reference to Personal Settings."
    if any(not value.is_set for value in (profile.location, profile.preferred_language)):
        return "Your local-time reference is ready; optional regional details are not all set."
    return "All three regional profile details are available."


async def build_preferences_summary(
    discord_user_id: int,
    *,
    display_name: str,
    profile_loader: ProfileLoader = profile_preference_service.read_user_profile_preference,
    utc_clock: UtcClock = lambda: datetime.now(UTC),
) -> PreferencesSummaryPayload:
    generated_at = _aware_utc(utc_clock())
    profile_result = await profile_loader(int(discord_user_id))

    warnings: list[str] = []
    if profile_result.ok:
        profile = _regional_profile(profile_result.profile)
    else:
        unavailable = PreferenceValueSummary(
            is_set=True,
            is_available=False,
            friendly_label="Profile details temporarily unavailable",
        )
        profile = RegionalProfileSummary(unavailable, unavailable, unavailable)
        warnings.append("Regional profile details are temporarily unavailable.")

    values = (profile.timezone, profile.location, profile.preferred_language)
    coverage = sum(value.is_set and value.is_available for value in values)
    time_reference = _time_reference(generated_at, profile)
    return PreferencesSummaryPayload(
        discord_user_id=int(discord_user_id),
        display_name=str(display_name or "player"),
        kingdom_id=1198,
        generated_at_utc=generated_at,
        regional_profile=profile,
        time_reference=time_reference,
        profile_details_set=int(coverage),
        profile_details_total=3,
        profile_supporting_text=f"{coverage} of 3 profile details set",
        settings_insight=_settings_insight(profile),
        warnings=tuple(warnings),
    )
