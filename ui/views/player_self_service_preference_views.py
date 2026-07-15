"""In-place Personal Settings components for the premium Preferences page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from math import ceil

import discord

from inventory.models import InventoryReportVisibility
from player_self_service import preference_service, profile_preference_service
from player_self_service.preferences_summary import (
    PreferencesSummaryPayload,
    build_preferences_summary,
)
from player_self_service.profile_preference_service import (
    ProfileField,
    ProfilePreferenceChoice,
    UserProfilePreference,
)

logger = logging.getLogger(__name__)

PreferencesLoader = Callable[..., Awaitable[PreferencesSummaryPayload]]
_PAGE_SIZE = 25


class PreferencesJourneyState:
    """Narrow per-message generation and mutation state for Preferences."""

    def __init__(self) -> None:
        self.generation = 0
        self.expired = False
        self.mutation_lock = asyncio.Lock()

    def advance(self) -> int:
        self.generation += 1
        self.expired = False
        return self.generation

    def is_current(self, generation: int) -> bool:
        return not self.expired and int(generation) == self.generation

    def expire(self, generation: int) -> None:
        if int(generation) == self.generation:
            self.expired = True


async def _send_private(interaction: discord.Interaction, content: str) -> None:
    if not interaction.response.is_done():
        await interaction.response.send_message(content, ephemeral=True)
    else:
        await interaction.followup.send(content, ephemeral=True)


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        if not interaction.response.is_done():
            await interaction.response.defer()


def _profile_content(profile: UserProfilePreference) -> str:
    values = (
        profile_preference_service.profile_value_display("timezone", profile.timezone_name),
        profile_preference_service.profile_value_display("country", profile.location_country_code),
        profile_preference_service.profile_value_display(
            "language", profile.preferred_language_tag
        ),
    )
    return "\n".join(
        (
            "**Regional profile**",
            f"Timezone: {values[0][2]}",
            f"Location: {values[1][2]}",
            f"Preferred language: {values[2][2]}",
            "\nChoose the field to update. Saved values are applied immediately.",
        )
    )


def _manage_content(payload: PreferencesSummaryPayload) -> str:
    profile = payload.regional_profile
    return "\n".join(
        (
            "**Manage settings**",
            f"Timezone: {profile.timezone.friendly_label}",
            f"Location: {profile.location.friendly_label}",
            f"Preferred language: {profile.preferred_language.friendly_label}",
            "",
            f"Inventory visibility: **{payload.inventory_visibility.state_label}**",
            payload.inventory_visibility.consequence_text,
        )
    )


class _PreferencesChildView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        preferences_loader: PreferencesLoader,
        avatar_bytes: bytes | None,
        dashboard_governor_id: int | None,
        journey: PreferencesJourneyState,
        generation: int,
        timeout: float,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=False)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.preferences_loader = preferences_loader
        self.avatar_bytes = avatar_bytes
        self.dashboard_governor_id = dashboard_governor_id
        self.journey = journey
        self.generation = int(generation)
        self._message_ref: object | None = None

    def set_message_ref(self, message: object | None) -> None:
        self._message_ref = message

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user or int(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This private Preferences window is not for you.", ephemeral=True
            )
            return False
        if not self.journey.is_current(self.generation):
            await interaction.response.send_message(
                "This Preferences window was superseded. Use the current private window.",
                ephemeral=True,
            )
            return False
        return True

    def _next_common(self) -> dict[str, object]:
        return {
            "author_id": self.author_id,
            "display_name": self.display_name,
            "preferences_loader": self.preferences_loader,
            "avatar_bytes": self.avatar_bytes,
            "dashboard_governor_id": self.dashboard_governor_id,
            "journey": self.journey,
            "generation": self.journey.advance(),
            "timeout": self.timeout or 180,
        }

    async def _replace(
        self,
        interaction: discord.Interaction,
        *,
        content: str,
        view: discord.ui.View,
    ) -> None:
        self.stop()
        if not interaction.response.is_done():
            await interaction.response.edit_message(
                content=content,
                embed=None,
                attachments=[],
                view=view,
            )
        else:
            await interaction.edit_original_response(
                content=content,
                embed=None,
                attachments=[],
                view=view,
            )
        if isinstance(view, _PreferencesChildView):
            view.set_message_ref(getattr(interaction, "message", None))

    async def _load_payload(self) -> PreferencesSummaryPayload:
        return await self.preferences_loader(
            self.author_id,
            display_name=self.display_name,
        )

    async def _back_to_preferences(self, interaction: discord.Interaction) -> None:
        await _defer_private(interaction)
        payload = await self._load_payload()
        from ui.views.player_self_service_views import (
            PAGE_PREFERENCES,
            PlayerSelfServiceView,
            _build_page_response,
            _close_files,
            _edit_original_with_image_fallback,
        )

        generation = self.journey.advance()
        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=PAGE_PREFERENCES,
            preferences_payload=payload,
            preferences_loader=self.preferences_loader,
            preferences_journey=self.journey,
            preferences_generation=generation,
            avatar_bytes=self.avatar_bytes,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(
            PAGE_PREFERENCES,
            None,
            display_name=self.display_name,
            preferences_payload=payload,
            avatar_bytes=self.avatar_bytes,
        )
        try:
            edited = await _edit_original_with_image_fallback(
                interaction,
                page=PAGE_PREFERENCES,
                summary=None,
                preferences_payload=payload,
                display_name=self.display_name,
                view=view,
                embed=embed,
                files=files,
            )
            view.set_message_ref(getattr(interaction, "message", None) or edited)
            view.set_timeout_target(interaction)
            self.stop()
        finally:
            _close_files(files)

    async def on_timeout(self) -> None:
        self.journey.expire(self.generation)
        for child in self.children:
            child.disabled = True
        try:
            message = self._message_ref or getattr(self, "message", None)
            if message is not None and hasattr(message, "edit"):
                await message.edit(
                    content="This private settings window has expired. Run `/me preferences` again.",
                    view=self,
                )
        except Exception:
            logger.debug("preferences_child_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


class ManageSettingsView(_PreferencesChildView):
    def __init__(self, *, payload: PreferencesSummaryPayload, **kwargs) -> None:
        self.payload = payload
        super().__init__(**kwargs)

    @discord.ui.button(
        label="Regional profile",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:manage:regional",
        row=0,
    )
    async def regional_button(self, _button, interaction: discord.Interaction) -> None:
        await _defer_private(interaction)
        result = await profile_preference_service.read_user_profile_preference(self.author_id)
        if not result.ok:
            await interaction.followup.send(
                "Regional profile details are temporarily unavailable.", ephemeral=True
            )
            return
        view = RegionalProfileView(profile=result.profile, **self._next_common())
        await self._replace(interaction, content=_profile_content(result.profile), view=view)

    @discord.ui.button(
        label="Privacy & sharing",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:manage:privacy",
        row=0,
    )
    async def privacy_button(self, _button, interaction: discord.Interaction) -> None:
        view = PrivacySharingView(payload=self.payload, **self._next_common())
        await self._replace(
            interaction,
            content=view.content,
            view=view,
        )

    @discord.ui.button(
        label="Back to Preferences",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:manage:back",
        row=1,
    )
    async def back_button(self, _button, interaction: discord.Interaction) -> None:
        await self._back_to_preferences(interaction)


class _ProfileFieldSelect(discord.ui.Select):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose regional profile field",
            options=[
                discord.SelectOption(label="Timezone", value="timezone"),
                discord.SelectOption(label="Location", value="country"),
                discord.SelectOption(label="Preferred language", value="language"),
            ],
            min_values=1,
            max_values=1,
            custom_id="me:preference:regional:field",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, RegionalProfileView):
            await _send_private(interaction, "This regional profile selector is unavailable.")
            return
        await view.open_field(interaction, self.values[0])


class RegionalProfileView(_PreferencesChildView):
    def __init__(self, *, profile: UserProfilePreference, **kwargs) -> None:
        self.profile = profile
        super().__init__(**kwargs)
        self.add_item(_ProfileFieldSelect())

    async def open_field(self, interaction: discord.Interaction, field_value: str) -> None:
        if field_value not in {"timezone", "country", "language"}:
            await _send_private(interaction, "That profile field was not recognised.")
            return
        field = field_value
        view = ProfileFieldView(field=field, profile=self.profile, page=0, **self._next_common())
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Back to Manage settings",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:back_manage",
        row=1,
    )
    async def back_manage_button(self, _button, interaction: discord.Interaction) -> None:
        payload = await self._load_payload()
        view = ManageSettingsView(payload=payload, **self._next_common())
        await self._replace(interaction, content=_manage_content(payload), view=view)

    @discord.ui.button(
        label="Back to Preferences",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:back_parent",
        row=1,
    )
    async def back_parent_button(self, _button, interaction: discord.Interaction) -> None:
        await self._back_to_preferences(interaction)


def _profile_value(field: ProfileField, profile: UserProfilePreference) -> str | None:
    if field == "timezone":
        return profile.timezone_name
    if field == "country":
        return profile.location_country_code
    return profile.preferred_language_tag


def _field_label(field: ProfileField) -> str:
    return {"timezone": "Timezone", "country": "Location", "language": "Preferred language"}[field]


def _field_choices(
    field: ProfileField,
    profile: UserProfilePreference,
) -> tuple[ProfilePreferenceChoice, ...]:
    choices = list(profile_preference_service.PROFILE_CHOICES[field])
    current = _profile_value(field, profile)
    set_value, available, friendly, normalized = profile_preference_service.profile_value_display(
        field, current
    )
    values = {choice.value for choice in choices}
    if set_value and available and normalized and normalized not in values:
        choices.insert(0, ProfilePreferenceChoice(friendly, normalized, "Current saved value"))
    return tuple(choices)


class _ProfileValueSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        field: ProfileField,
        profile: UserProfilePreference,
        page: int,
    ) -> None:
        choices = _field_choices(field, profile)
        total_pages = max(1, ceil(len(choices) / _PAGE_SIZE))
        page = min(max(0, page), total_pages - 1)
        start = page * _PAGE_SIZE
        page_choices = choices[start : start + _PAGE_SIZE]
        current = _profile_value(field, profile)
        options = [
            discord.SelectOption(
                label=choice.label[:100],
                value=choice.value,
                description=choice.description[:100] or None,
                default=current == choice.value,
            )
            for choice in page_choices
        ]
        super().__init__(
            placeholder=(
                f"Choose {_field_label(field).lower()} ({page + 1}/{total_pages})"
                if total_pages > 1
                else f"Choose {_field_label(field).lower()}"
            ),
            options=options,
            min_values=1,
            max_values=1,
            custom_id=f"me:preference:regional:{field}:value",
            row=0,
        )
        self.allowed_values = {choice.value for choice in page_choices}

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, ProfileFieldView):
            await _send_private(interaction, "This profile selector is unavailable.")
            return
        value = str(self.values[0])
        if value not in self.allowed_values:
            await _send_private(interaction, "That profile value is not available on this page.")
            return
        await view.save_value(interaction, value)


class ProfileFieldView(_PreferencesChildView):
    def __init__(
        self,
        *,
        field: ProfileField,
        profile: UserProfilePreference,
        page: int,
        **kwargs,
    ) -> None:
        self.field = field
        self.profile = profile
        choices = _field_choices(field, profile)
        self.total_pages = max(1, ceil(len(choices) / _PAGE_SIZE))
        self.page = min(max(0, int(page)), self.total_pages - 1)
        super().__init__(**kwargs)
        self.add_item(_ProfileValueSelect(field=field, profile=profile, page=self.page))
        self.previous_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    @property
    def content(self) -> str:
        current = profile_preference_service.profile_value_display(
            self.field, _profile_value(self.field, self.profile)
        )[2]
        return (
            f"**Update {_field_label(self.field)}**\nCurrent: {current}\n\n"
            "Choose a value or use Clear to store Not set."
        )

    async def _refresh(
        self,
        interaction: discord.Interaction,
        *,
        message: str,
        profile: UserProfilePreference | None = None,
    ) -> None:
        if profile is None:
            current = await profile_preference_service.read_user_profile_preference(self.author_id)
            profile = current.profile if current.ok else self.profile
        view = ProfileFieldView(
            field=self.field,
            profile=profile,
            page=self.page,
            **self._next_common(),
        )
        await self._replace(interaction, content=f"{message}\n\n{view.content}", view=view)

    async def save_value(self, interaction: discord.Interaction, value: str) -> None:
        await _defer_private(interaction)
        if self.journey.mutation_lock.locked():
            await interaction.followup.send(
                "Another settings change is already being saved.", ephemeral=True
            )
            return
        async with self.journey.mutation_lock:
            if not self.journey.is_current(self.generation):
                await interaction.followup.send(
                    "This settings window was superseded.", ephemeral=True
                )
                return
            result = await profile_preference_service.set_profile_preference(
                self.author_id, self.field, value
            )
        await self._refresh(
            interaction,
            message=result.message,
            profile=result.profile if result.ok else None,
        )

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:previous",
        row=1,
    )
    async def previous_button(self, _button, interaction: discord.Interaction) -> None:
        view = ProfileFieldView(
            field=self.field,
            profile=self.profile,
            page=self.page - 1,
            **self._next_common(),
        )
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:next",
        row=1,
    )
    async def next_button(self, _button, interaction: discord.Interaction) -> None:
        view = ProfileFieldView(
            field=self.field,
            profile=self.profile,
            page=self.page + 1,
            **self._next_common(),
        )
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Clear / Not set",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:clear",
        row=2,
    )
    async def clear_button(self, _button, interaction: discord.Interaction) -> None:
        await _defer_private(interaction)
        if self.journey.mutation_lock.locked():
            await interaction.followup.send(
                "Another settings change is already being saved.", ephemeral=True
            )
            return
        async with self.journey.mutation_lock:
            if not self.journey.is_current(self.generation):
                await interaction.followup.send(
                    "This settings window was superseded.", ephemeral=True
                )
                return
            result = await profile_preference_service.clear_profile_preference(
                self.author_id, self.field
            )
        await self._refresh(
            interaction,
            message=result.message,
            profile=result.profile if result.ok else None,
        )

    @discord.ui.button(
        label="Back to Regional profile",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:field_back",
        row=3,
    )
    async def back_regional_button(self, _button, interaction: discord.Interaction) -> None:
        view = RegionalProfileView(profile=self.profile, **self._next_common())
        await self._replace(interaction, content=_profile_content(self.profile), view=view)

    @discord.ui.button(
        label="Back to Preferences",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:regional:field_parent",
        row=4,
    )
    async def back_parent_button(self, _button, interaction: discord.Interaction) -> None:
        await self._back_to_preferences(interaction)


class PrivacySharingView(_PreferencesChildView):
    def __init__(self, *, payload: PreferencesSummaryPayload, **kwargs) -> None:
        self.payload = payload
        super().__init__(**kwargs)
        self.change_button.label = (
            "Make Private" if payload.inventory_visibility.is_public else "Make Public"
        )

    @property
    def content(self) -> str:
        visibility = self.payload.inventory_visibility
        return (
            f"**Privacy & sharing**\nInventory visibility: **{visibility.state_label}**\n"
            f"{visibility.consequence_text}\n\nReview the consequence before changing this setting."
        )

    @discord.ui.button(
        label="Change visibility",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:privacy:change",
        row=0,
    )
    async def change_button(self, _button, interaction: discord.Interaction) -> None:
        expected = (
            InventoryReportVisibility.PUBLIC
            if self.payload.inventory_visibility.is_public
            else InventoryReportVisibility.ONLY_ME
        )
        target = (
            InventoryReportVisibility.ONLY_ME
            if expected == InventoryReportVisibility.PUBLIC
            else InventoryReportVisibility.PUBLIC
        )
        view = VisibilityConfirmationView(
            payload=self.payload,
            expected=expected,
            target=target,
            **self._next_common(),
        )
        target_label = "PRIVATE" if target == InventoryReportVisibility.ONLY_ME else "PUBLIC"
        consequence = (
            self.payload.inventory_visibility.consequence_text
            if target == expected
            else (
                "Detailed Inventory reports opened through /me inventory or /myinventory are shown only to you."
                if target == InventoryReportVisibility.ONLY_ME
                else "Detailed Inventory reports opened through /me inventory or /myinventory may be posted in the channel."
            )
        )
        await self._replace(
            interaction,
            content=(
                f"**Confirm Inventory visibility: {target_label}**\n{consequence}\n\n"
                "This does not make /me resources, /me materials, /me speedups, summaries, or exports public."
            ),
            view=view,
        )

    @discord.ui.button(
        label="Back to Manage settings",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:privacy:back_manage",
        row=1,
    )
    async def back_manage_button(self, _button, interaction: discord.Interaction) -> None:
        payload = await self._load_payload()
        view = ManageSettingsView(payload=payload, **self._next_common())
        await self._replace(interaction, content=_manage_content(payload), view=view)

    @discord.ui.button(
        label="Back to Preferences",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:privacy:back_parent",
        row=1,
    )
    async def back_parent_button(self, _button, interaction: discord.Interaction) -> None:
        await self._back_to_preferences(interaction)


class VisibilityConfirmationView(_PreferencesChildView):
    def __init__(
        self,
        *,
        payload: PreferencesSummaryPayload,
        expected: InventoryReportVisibility,
        target: InventoryReportVisibility,
        **kwargs,
    ) -> None:
        self.payload = payload
        self.expected = expected
        self.target = target
        self.completed = False
        super().__init__(**kwargs)

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:privacy:confirm",
        row=0,
    )
    async def confirm_button(self, _button, interaction: discord.Interaction) -> None:
        await _defer_private(interaction)
        if self.completed or self.journey.mutation_lock.locked():
            await interaction.followup.send(
                "This visibility confirmation is already being processed.", ephemeral=True
            )
            return
        async with self.journey.mutation_lock:
            if not self.journey.is_current(self.generation):
                await interaction.followup.send(
                    "This visibility confirmation was superseded.", ephemeral=True
                )
                return
            self.completed = True
            try:
                result = await preference_service.confirm_inventory_visibility_change(
                    self.author_id,
                    expected_visibility=self.expected,
                    target_visibility=self.target,
                )
            except asyncio.CancelledError:
                self.completed = False
                raise
        if result.ok:
            await self._back_to_preferences(interaction)
            return
        payload = await self._load_payload()
        view = PrivacySharingView(payload=payload, **self._next_common())
        await self._replace(interaction, content=f"{result.message}\n\n{view.content}", view=view)

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:privacy:cancel",
        row=0,
    )
    async def cancel_button(self, _button, interaction: discord.Interaction) -> None:
        view = PrivacySharingView(payload=self.payload, **self._next_common())
        await self._replace(
            interaction,
            content=f"Inventory visibility change cancelled.\n\n{view.content}",
            view=view,
        )


async def show_preferences_manage_settings(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    payload: PreferencesSummaryPayload,
    preferences_loader: PreferencesLoader = build_preferences_summary,
    avatar_bytes: bytes | None,
    dashboard_governor_id: int | None,
    journey: PreferencesJourneyState,
    source_generation: int | None,
    timeout: float = 180,
) -> None:
    if source_generation is None or not journey.is_current(source_generation):
        await _send_private(
            interaction,
            "This Preferences window was superseded. Use the current private window.",
        )
        return
    generation = journey.advance()
    view = ManageSettingsView(
        payload=payload,
        author_id=author_id,
        display_name=display_name,
        preferences_loader=preferences_loader,
        avatar_bytes=avatar_bytes,
        dashboard_governor_id=dashboard_governor_id,
        journey=journey,
        generation=generation,
        timeout=timeout,
    )
    await interaction.response.edit_message(
        content=_manage_content(payload),
        embed=None,
        attachments=[],
        view=view,
    )
    view.set_message_ref(getattr(interaction, "message", None))
