from __future__ import annotations

from datetime import UTC, datetime

import pytest

from inventory.models import InventoryReportVisibility
from inventory.reporting_service import InventoryVisibilityPreferenceRead
from player_self_service.preferences_summary import (
    PRIVATE_CONSEQUENCE,
    PUBLIC_CONSEQUENCE,
    PreferencesSummaryUnavailable,
    build_preferences_summary,
)
from player_self_service.profile_preference_service import (
    UserProfilePreference,
    UserProfilePreferenceRead,
)


def _profile_loader(profile: UserProfilePreference, *, ok: bool = True):
    async def load(_user_id: int) -> UserProfilePreferenceRead:
        return UserProfilePreferenceRead(ok=ok, profile=profile, error=None if ok else "down")

    return load


def _visibility_loader(visibility: InventoryReportVisibility | None, *, ok: bool = True):
    async def load(_user_id: int) -> InventoryVisibilityPreferenceRead:
        return InventoryVisibilityPreferenceRead(
            ok=ok,
            visibility=visibility,
            error=None if ok else "down",
        )

    return load


async def _build(
    profile: UserProfilePreference,
    *,
    visibility: InventoryReportVisibility | None = InventoryReportVisibility.ONLY_ME,
    now: datetime = datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
):
    return await build_preferences_summary(
        42,
        display_name="Tester",
        profile_loader=_profile_loader(profile),
        visibility_loader=_visibility_loader(visibility),
        utc_clock=lambda: now,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile", "coverage", "insight_fragment"),
    [
        (UserProfilePreference(), 0, "Set a timezone"),
        (UserProfilePreference(timezone_name="UTC"), 1, "optional regional details"),
        (
            UserProfilePreference(
                timezone_name="Europe/London",
                location_country_code="GB",
                preferred_language_tag="en-GB",
            ),
            3,
            "regional profile is complete",
        ),
    ],
)
async def test_profile_coverage_for_unset_partial_and_complete_profiles(
    profile: UserProfilePreference,
    coverage: int,
    insight_fragment: str,
) -> None:
    payload = await _build(profile)

    assert payload.profile_details_set == coverage
    assert payload.profile_details_total == 3
    assert payload.profile_supporting_text == f"{coverage} of 3 profile details set"
    assert insight_fragment in payload.settings_insight


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("timezone_name", "now", "time", "offset"),
    [
        ("UTC", datetime(2026, 1, 15, 12, 0, tzinfo=UTC), "12:00", "UTC"),
        ("Europe/London", datetime(2026, 1, 15, 12, 0, tzinfo=UTC), "12:00", "UTC"),
        ("Europe/London", datetime(2026, 7, 15, 12, 0, tzinfo=UTC), "13:00", "UTC+1"),
        ("America/New_York", datetime(2026, 1, 15, 12, 0, tzinfo=UTC), "07:00", "UTC-5"),
        ("Asia/Kolkata", datetime(2026, 1, 15, 12, 0, tzinfo=UTC), "17:30", "UTC+5:30"),
        ("Asia/Kathmandu", datetime(2026, 1, 15, 12, 0, tzinfo=UTC), "17:45", "UTC+5:45"),
    ],
)
async def test_local_time_uses_iana_dst_and_fractional_offsets(
    timezone_name: str,
    now: datetime,
    time: str,
    offset: str,
) -> None:
    payload = await _build(UserProfilePreference(timezone_name=timezone_name), now=now)

    assert payload.time_reference.mode == "LOCAL"
    assert payload.time_reference.display_time == time
    assert payload.time_reference.utc_offset_label == offset
    assert offset in payload.time_reference.supporting_line
    assert payload.generated_at_utc is now


@pytest.mark.asyncio
async def test_local_date_can_differ_from_utc_without_a_second_clock_read() -> None:
    calls = 0
    now = datetime(2026, 1, 1, 11, 30, tzinfo=UTC)

    def clock() -> datetime:
        nonlocal calls
        calls += 1
        return now

    payload = await build_preferences_summary(
        42,
        display_name="Tester",
        profile_loader=_profile_loader(UserProfilePreference(timezone_name="Pacific/Auckland")),
        visibility_loader=_visibility_loader(InventoryReportVisibility.ONLY_ME),
        utc_clock=clock,
    )

    assert calls == 1
    assert payload.generated_at_utc == now
    assert payload.time_reference.display_time == "00:30"


@pytest.mark.asyncio
async def test_missing_and_unavailable_timezone_use_honest_utc_fallback() -> None:
    missing = await _build(UserProfilePreference(location_country_code="GB"))
    unavailable = await _build(UserProfilePreference(timezone_name="Not/A_Zone"))

    assert missing.time_reference.mode == "UTC_FALLBACK"
    assert missing.time_reference.heading == "UTC REFERENCE"
    assert missing.time_reference.display_time == "12:00"
    assert unavailable.regional_profile.timezone.is_set is True
    assert unavailable.regional_profile.timezone.is_available is False
    assert unavailable.regional_profile.timezone.friendly_label == "Saved timezone unavailable"
    assert "Not/A_Zone" not in unavailable.regional_profile.timezone.friendly_label
    assert unavailable.profile_details_set == 0
    assert "need review" in unavailable.settings_insight


@pytest.mark.asyncio
async def test_unknown_country_and_language_are_unavailable_and_not_exposed() -> None:
    payload = await _build(
        UserProfilePreference(
            timezone_name="UTC",
            location_country_code="ZZ",
            preferred_language_tag="xx-SECRET",
        )
    )

    assert payload.profile_details_set == 1
    assert payload.regional_profile.location.friendly_label == "Saved location unavailable"
    assert (
        payload.regional_profile.preferred_language.friendly_label == "Saved language unavailable"
    )
    assert "ZZ" not in payload.regional_profile.location.friendly_label
    assert "SECRET" not in payload.regional_profile.preferred_language.friendly_label
    assert "need review" in payload.settings_insight


@pytest.mark.asyncio
async def test_settings_insight_priority_places_public_before_optional_unset() -> None:
    payload = await _build(
        UserProfilePreference(timezone_name="UTC"),
        visibility=InventoryReportVisibility.PUBLIC,
    )

    assert payload.inventory_visibility.state_label == "PUBLIC"
    assert payload.inventory_visibility.consequence_text == PUBLIC_CONSEQUENCE
    assert "sharing is public" in payload.settings_insight
    assert "optional" not in payload.settings_insight


@pytest.mark.asyncio
async def test_private_default_is_explicitly_marked_without_changing_consequence() -> None:
    payload = await _build(UserProfilePreference(), visibility=None)

    assert payload.inventory_visibility.state_label == "PRIVATE"
    assert payload.inventory_visibility.is_explicit is False
    assert payload.inventory_visibility.consequence_text == PRIVATE_CONSEQUENCE
    assert payload.warnings


@pytest.mark.asyncio
async def test_location_does_not_infer_or_override_timezone() -> None:
    payload = await _build(
        UserProfilePreference(timezone_name="Asia/Tokyo", location_country_code="GB")
    )

    assert payload.time_reference.display_time == "21:00"
    assert payload.regional_profile.location.friendly_label == "United Kingdom (GB)"
    assert "match" not in payload.settings_insight.casefold()


@pytest.mark.asyncio
async def test_visibility_failure_blocks_card_instead_of_guessing_private() -> None:
    with pytest.raises(PreferencesSummaryUnavailable):
        await build_preferences_summary(
            42,
            display_name="Tester",
            profile_loader=_profile_loader(UserProfilePreference()),
            visibility_loader=_visibility_loader(None, ok=False),
        )
