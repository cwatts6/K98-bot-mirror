from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
from types import SimpleNamespace

import pytest

from inventory.models import InventoryReportVisibility
from player_self_service.preference_service import PreferenceMutationResult
from player_self_service.preferences_summary import (
    InventoryVisibilitySummary,
    PreferencesSummaryPayload,
    PreferenceValueSummary,
    RegionalProfileSummary,
    TimeReferenceSummary,
)
from player_self_service.profile_preference_service import (
    UserProfilePreference,
    UserProfilePreferenceMutationResult,
    UserProfilePreferenceRead,
)
from ui.views import player_self_service_preference_views as preference_views


class _Response:
    def __init__(self) -> None:
        self.sent = []
        self.edited = []
        self.deferred = []
        self._done = False

    def is_done(self):
        return self._done

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)
        self._done = True

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True


class _FailingDeferResponse(_Response):
    def __init__(self, failures: tuple[BaseException, ...]) -> None:
        super().__init__()
        self.failures = list(failures)

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        raise self.failures.pop(0)


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.response = _Response()
        self.followup = _Followup()
        self.message = SimpleNamespace(id=123)
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return self.message


def _payload(*, public: bool = False) -> PreferencesSummaryPayload:
    return PreferencesSummaryPayload(
        discord_user_id=42,
        display_name="Tester",
        kingdom_id=1198,
        generated_at_utc=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
        inventory_visibility=InventoryVisibilitySummary(
            is_public=public,
            state_label="PUBLIC" if public else "PRIVATE",
            consequence_text=(
                "Detailed Inventory reports may be posted in the channel."
                if public
                else "Detailed Inventory reports are shown only to you."
            ),
            is_explicit=True,
        ),
        regional_profile=RegionalProfileSummary(
            timezone=PreferenceValueSummary(True, True, "United Kingdom", "Europe/London"),
            location=PreferenceValueSummary(True, True, "United Kingdom (GB)", "GB"),
            preferred_language=PreferenceValueSummary(True, True, "English (en-GB)", "en-GB"),
        ),
        time_reference=TimeReferenceSummary(
            mode="LOCAL",
            heading="LOCAL TIME REFERENCE",
            display_time="13:00",
            timezone_label="United Kingdom",
            utc_offset_label="UTC+1",
            supporting_line="United Kingdom • UTC+1",
            regional_context=None,
        ),
        profile_details_set=3,
        profile_details_total=3,
        profile_supporting_text="3 of 3 profile details set",
        settings_insight="Regional profile complete.",
    )


async def _loader(_user_id: int, *, display_name: str):
    assert display_name == "Tester"
    return _payload()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failures",
    [
        (RuntimeError("primary defer failed"),),
        (TypeError("ephemeral unsupported"), RuntimeError("fallback defer failed")),
    ],
)
async def test_private_defer_logs_and_suppresses_api_failures(failures, caplog) -> None:
    interaction = _Interaction()
    interaction.response = _FailingDeferResponse(failures)

    with caplog.at_level(logging.DEBUG, logger=preference_views.logger.name):
        await preference_views._defer_private(interaction)

    assert "player_self_service_preference_defer_failed" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failures",
    [
        (asyncio.CancelledError(),),
        (TypeError("ephemeral unsupported"), asyncio.CancelledError()),
    ],
)
async def test_private_defer_propagates_cancellation(failures) -> None:
    interaction = _Interaction()
    interaction.response = _FailingDeferResponse(failures)

    with pytest.raises(asyncio.CancelledError):
        await preference_views._defer_private(interaction)


def _common(
    journey: preference_views.PreferencesJourneyState,
    generation: int,
) -> dict[str, object]:
    return {
        "author_id": 42,
        "display_name": "Tester",
        "preferences_loader": _loader,
        "avatar_bytes": None,
        "dashboard_governor_id": 999,
        "journey": journey,
        "generation": generation,
        "timeout": 180,
    }


@pytest.mark.asyncio
async def test_manage_settings_replaces_parent_and_clears_attachment() -> None:
    journey = preference_views.PreferencesJourneyState()
    source_generation = journey.advance()
    interaction = _Interaction()

    await preference_views.show_preferences_manage_settings(
        interaction,
        author_id=42,
        display_name="Tester",
        payload=_payload(),
        preferences_loader=_loader,
        avatar_bytes=None,
        dashboard_governor_id=999,
        journey=journey,
        source_generation=source_generation,
    )

    edit = interaction.response.edited[-1]
    assert edit["attachments"] == []
    assert edit["embed"] is None
    assert isinstance(edit["view"], preference_views.ManageSettingsView)
    labels = {getattr(item, "label", None) for item in edit["view"].children}
    assert labels == {"Regional profile", "Privacy & sharing", "Back to Preferences"}


@pytest.mark.asyncio
async def test_repeated_manage_click_is_rejected_as_superseded() -> None:
    journey = preference_views.PreferencesJourneyState()
    source_generation = journey.advance()
    first = _Interaction()
    await preference_views.show_preferences_manage_settings(
        first,
        author_id=42,
        display_name="Tester",
        payload=_payload(),
        avatar_bytes=None,
        dashboard_governor_id=None,
        journey=journey,
        source_generation=source_generation,
    )
    second = _Interaction()

    await preference_views.show_preferences_manage_settings(
        second,
        author_id=42,
        display_name="Tester",
        payload=_payload(),
        avatar_bytes=None,
        dashboard_governor_id=None,
        journey=journey,
        source_generation=source_generation,
    )

    assert second.response.edited == []
    assert "superseded" in second.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_child_rejects_foreign_and_superseded_interactions() -> None:
    journey = preference_views.PreferencesJourneyState()
    generation = journey.advance()
    view = preference_views.ManageSettingsView(
        payload=_payload(),
        **_common(journey, generation),
    )

    foreign = _Interaction(user_id=99)
    assert await view.interaction_check(foreign) is False
    assert foreign.response.sent[-1][1]["ephemeral"] is True

    journey.advance()
    stale = _Interaction()
    assert await view.interaction_check(stale) is False
    assert "superseded" in stale.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_regional_profile_uses_field_selector_and_contextual_clear(monkeypatch) -> None:
    profile = UserProfilePreference(
        timezone_name="Pacific/Honolulu",
        location_country_code="GB",
        preferred_language_tag="es-MX",
    )

    async def read(_user_id: int):
        return UserProfilePreferenceRead(ok=True, profile=profile)

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "read_user_profile_preference",
        read,
    )
    journey = preference_views.PreferencesJourneyState()
    generation = journey.advance()
    manage = preference_views.ManageSettingsView(
        payload=_payload(),
        **_common(journey, generation),
    )
    interaction = _Interaction()

    await manage.regional_button.callback(interaction)

    regional = interaction.original_edits[-1]["view"]
    assert isinstance(regional, preference_views.RegionalProfileView)
    selector = next(item for item in regional.children if hasattr(item, "options"))
    assert [option.value for option in selector.options] == ["timezone", "country", "language"]

    field = preference_views.ProfileFieldView(
        field="language",
        profile=profile,
        page=0,
        **_common(journey, journey.advance()),
    )
    value_select = next(item for item in field.children if hasattr(item, "options"))
    assert len(value_select.options) == 25
    assert field.total_pages == 2
    assert any(getattr(item, "label", None) == "Clear / Not set" for item in field.children)


@pytest.mark.asyncio
async def test_field_save_refreshes_same_field_with_authoritative_row(monkeypatch) -> None:
    calls = []
    saved_profile = UserProfilePreference(timezone_name="Asia/Kolkata")

    async def save(user_id: int, field: str, value: str):
        calls.append((user_id, field, value))
        return UserProfilePreferenceMutationResult(
            ok=True,
            message="Timezone saved as India.",
            profile=saved_profile,
        )

    async def read(_user_id: int):
        return UserProfilePreferenceRead(ok=True, profile=saved_profile)

    monkeypatch.setattr(preference_views.profile_preference_service, "set_profile_preference", save)
    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "read_user_profile_preference",
        read,
    )
    journey = preference_views.PreferencesJourneyState()
    view = preference_views.ProfileFieldView(
        field="timezone",
        profile=UserProfilePreference(),
        page=0,
        **_common(journey, journey.advance()),
    )
    interaction = _Interaction()

    await view.save_value(interaction, "Asia/Kolkata")

    assert calls == [(42, "timezone", "Asia/Kolkata")]
    replacement = interaction.original_edits[-1]["view"]
    assert isinstance(replacement, preference_views.ProfileFieldView)
    assert replacement.profile == saved_profile
    assert "Timezone saved as India" in interaction.original_edits[-1]["content"]


@pytest.mark.asyncio
async def test_field_clear_stores_not_set_and_refreshes(monkeypatch) -> None:
    calls = []
    cleared = UserProfilePreference(timezone_name="UTC")

    async def clear(user_id: int, field: str):
        calls.append((user_id, field))
        return UserProfilePreferenceMutationResult(
            ok=True,
            message="Location removed.",
            profile=cleared,
        )

    async def read(_user_id: int):
        return UserProfilePreferenceRead(ok=True, profile=cleared)

    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "clear_profile_preference",
        clear,
    )
    monkeypatch.setattr(
        preference_views.profile_preference_service,
        "read_user_profile_preference",
        read,
    )
    journey = preference_views.PreferencesJourneyState()
    view = preference_views.ProfileFieldView(
        field="country",
        profile=UserProfilePreference(location_country_code="GB"),
        page=0,
        **_common(journey, journey.advance()),
    )
    interaction = _Interaction()

    await view.clear_button.callback(interaction)

    assert calls == [(42, "country")]
    assert "Location removed" in interaction.original_edits[-1]["content"]


@pytest.mark.asyncio
async def test_privacy_action_is_state_aware_and_cancel_does_not_mutate(monkeypatch) -> None:
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("cancel must not mutate")

    monkeypatch.setattr(
        preference_views.preference_service,
        "confirm_inventory_visibility_change",
        forbidden,
    )
    journey = preference_views.PreferencesJourneyState()
    private_view = preference_views.PrivacySharingView(
        payload=_payload(public=False),
        **_common(journey, journey.advance()),
    )
    assert private_view.change_button.label == "Make Public"
    open_confirmation = _Interaction()
    await private_view.change_button.callback(open_confirmation)
    confirmation = open_confirmation.response.edited[-1]["view"]
    assert isinstance(confirmation, preference_views.VisibilityConfirmationView)
    assert "does not make /me resources" in open_confirmation.response.edited[-1]["content"]

    cancel = _Interaction()
    await confirmation.cancel_button.callback(cancel)
    assert "cancelled" in cancel.response.edited[-1]["content"]
    assert isinstance(cancel.response.edited[-1]["view"], preference_views.PrivacySharingView)

    public_view = preference_views.PrivacySharingView(
        payload=_payload(public=True),
        **_common(journey, journey.advance()),
    )
    assert public_view.change_button.label == "Make Private"


@pytest.mark.asyncio
async def test_visibility_confirmation_revalidates_and_refreshes_stale_state(monkeypatch) -> None:
    calls = []

    async def confirm(user_id: int, *, expected_visibility, target_visibility):
        calls.append((user_id, expected_visibility, target_visibility))
        return PreferenceMutationResult(
            ok=False,
            stale=True,
            message="Inventory visibility changed after this confirmation opened.",
        )

    monkeypatch.setattr(
        preference_views.preference_service,
        "confirm_inventory_visibility_change",
        confirm,
    )
    journey = preference_views.PreferencesJourneyState()
    view = preference_views.VisibilityConfirmationView(
        payload=_payload(),
        expected=InventoryReportVisibility.ONLY_ME,
        target=InventoryReportVisibility.PUBLIC,
        **_common(journey, journey.advance()),
    )
    interaction = _Interaction()

    await view.confirm_button.callback(interaction)

    assert calls == [(42, InventoryReportVisibility.ONLY_ME, InventoryReportVisibility.PUBLIC)]
    assert "changed after" in interaction.original_edits[-1]["content"]
    assert isinstance(interaction.original_edits[-1]["view"], preference_views.PrivacySharingView)


@pytest.mark.asyncio
async def test_child_timeout_disables_controls_and_rejects_late_interaction() -> None:
    journey = preference_views.PreferencesJourneyState()
    generation = journey.advance()
    view = preference_views.ManageSettingsView(
        payload=_payload(),
        **_common(journey, generation),
    )

    await view.on_timeout()

    assert all(item.disabled for item in view.children)
    assert journey.expired is True
    interaction = _Interaction()
    assert await view.interaction_check(interaction) is False


@pytest.mark.asyncio
async def test_visibility_confirmation_cancellation_releases_completed_state(monkeypatch) -> None:
    async def cancel(*_args, **_kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(
        preference_views.preference_service,
        "confirm_inventory_visibility_change",
        cancel,
    )
    journey = preference_views.PreferencesJourneyState()
    view = preference_views.VisibilityConfirmationView(
        payload=_payload(),
        expected=InventoryReportVisibility.ONLY_ME,
        target=InventoryReportVisibility.PUBLIC,
        **_common(journey, journey.advance()),
    )

    with pytest.raises(asyncio.CancelledError):
        await view.confirm_button.callback(_Interaction())

    assert view.completed is False
    assert journey.mutation_lock.locked() is False
