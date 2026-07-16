"""Discord views and embeds for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from io import BytesIO
import logging
from typing import Any

import discord

from core.interaction_safety import safe_defer
from player_self_service import (
    account_service,
    accounts_renderer,
    accounts_service,
    dashboard_card,
    page_cards,
    preferences_renderer,
    reminder_service,
    reminders_renderer,
    reminders_summary,
)
from player_self_service.account_service import AccountCentreState
from player_self_service.accounts_models import AccountsPortfolioPayload
from player_self_service.preferences_summary import (
    PreferencesSummaryPayload,
    build_preferences_summary,
)
from player_self_service.reminder_service import ReminderCentreState
from player_self_service.reminders_summary import RemindersSummaryPayload
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)
from ui.views import player_self_service_export_views as export_views
from ui.views.player_self_service_account_views import AccountManageView
from ui.views.player_self_service_preference_views import (
    PreferencesJourneyState,
    show_preferences_manage_settings,
)
from ui.views.player_self_service_reminder_views import (
    ReminderSetupView,
)

logger = logging.getLogger(__name__)

PlayerSelfServicePage = str
SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]
AccountsLoader = Callable[[int], Awaitable[AccountsPortfolioPayload]]
PreferencesLoader = Callable[..., Awaitable[PreferencesSummaryPayload]]
_AVATAR_READ_TIMEOUT_SECONDS = 5.0

PAGE_DASHBOARD = "dashboard"
PAGE_ACCOUNTS = "accounts"
PAGE_REMINDERS = "reminders"
PAGE_PREFERENCES = "preferences"
PAGE_EXPORTS = "exports"


def _display_name(user: object) -> str:
    return (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or "player"
    )


async def _read_avatar_bytes(user: object | None, *, expected_user_id: int) -> bytes | None:
    try:
        if user is None or int(getattr(user, "id", -1)) != int(expected_user_id):
            return None
    except (TypeError, ValueError):
        return None
    avatar = getattr(user, "display_avatar", None) or getattr(user, "avatar", None)
    if avatar is None:
        return None
    try:
        if hasattr(avatar, "with_size"):
            avatar = avatar.with_size(256)
        if hasattr(avatar, "read"):
            return await asyncio.wait_for(avatar.read(), timeout=_AVATAR_READ_TIMEOUT_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug(
            "player_self_service_avatar_read_failed user_id=%s",
            getattr(user, "id", None),
            exc_info=True,
        )
    return None


def _field_value(lines: list[str]) -> str:
    return "\n".join(lines)[:1024]


def build_dashboard_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    embed = discord.Embed(
        title="K98 Personal Command Centre",
        description=f"Private setup dashboard for {display_name}",
        color=discord.Color.blurple(),
    )
    accounts = summary.accounts
    reminders = summary.reminders
    exports = summary.exports

    embed.add_field(
        name="Accounts",
        value=_field_value(
            [
                f"Main: {accounts.main_state}",
                f"Linked: {accounts.linked_label}",
                f"Next action: {accounts.next_action}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Reminders",
        value=_field_value(
            [
                f"KVK reminders: {reminders.state}",
                f"Calendar reminders: {reminders.calendar.state}",
                f"KVK times: {reminders.time_summary}",
                f"Calendar lead times: {reminders.calendar.time_summary}",
                f"Next action: {reminders.combined_next_action}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Exports",
        value=_field_value(
            [
                f"Stats: {exports.stats_export}",
                f"Next action: {exports.action_summary}",
            ]
        ),
        inline=False,
    )
    embed.set_footer(text="Private player self-service.")
    return embed


def build_dashboard_card_embed(filename: str) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.blurple())
    embed.set_image(url=f"attachment://{filename}")
    return embed


def build_card_embed(filename: str) -> discord.Embed:
    return build_dashboard_card_embed(filename)


def build_accounts_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    accounts = summary.accounts
    embed = discord.Embed(
        title="Account Centre",
        description=f"Private account status for {display_name}",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Current Status",
        value=_field_value(
            [
                f"Main: {accounts.main_label}",
                f"Linked accounts: {accounts.linked_count}",
                f"State: {accounts.state}",
            ]
        ),
        inline=False,
    )
    names = ", ".join(accounts.account_names[:5]) if accounts.account_names else "none shown"
    embed.add_field(
        name="Available Actions",
        value=_field_value(
            [
                f"Account names: {names}",
                "Use Manage to look up IDs, add governors to open slots, replace, or remove accounts.",
            ]
        ),
        inline=False,
    )
    return embed


def build_accounts_portfolio_fallback(
    payload: AccountsPortfolioPayload,
    *,
    display_name: str,
) -> discord.Embed:
    """Concise same-payload fallback; deliberately excludes private coordinates."""
    embed = discord.Embed(
        title="Account Centre",
        description=f"Private account portfolio for {display_name}",
        color={
            "READY": discord.Color.green(),
            "REVIEW": discord.Color.gold(),
            "SETUP": discord.Color.blue(),
        }[payload.state],
    )
    main = payload.main_row
    embed.add_field(
        name=f"{payload.state} • {accounts_renderer.format_governor_count(payload.linked_count)}",
        value=_field_value(
            [
                f"Main: {main.display_name if main else 'not set'}",
                f"Power: {payload.power.value if payload.power.value is not None else '—'} "
                f"({payload.power.reporting_count}/{payload.power.expected_count})",
                f"T4+T5 kills: "
                f"{payload.t4_t5_kills.value if payload.t4_t5_kills.value is not None else '—'} "
                f"({payload.t4_t5_kills.reporting_count}/{payload.t4_t5_kills.expected_count})",
                f"RSS total: "
                f"{payload.rss_total.value if payload.rss_total.value is not None else '—'} "
                f"({payload.rss_total.reporting_count}/{payload.rss_total.expected_count})",
            ]
        ),
        inline=False,
    )
    embed.add_field(name="Portfolio Insight", value=payload.insight[:1024], inline=False)
    embed.set_footer(text=f"Refreshed {payload.refreshed_at_utc:%d %b %Y %H:%M UTC}")
    return embed


def _reminders_payload(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> RemindersSummaryPayload:
    payload = summary.reminders_summary
    if payload is None:
        legacy = summary.reminders
        kvk_config = None
        if legacy.state.strip().lower() != "off":
            kvk_config = {
                "subscriptions": ["all"],
                "reminder_times": [
                    token
                    for token in ("24h", "12h", "4h", "1h", "now")
                    if token in legacy.time_summary.lower()
                ],
            }
        calendar_enabled = legacy.calendar.state.strip().lower() == "on"
        calendar_prefs = {
            "enabled": calendar_enabled,
            "by_event_type": ({"all": ["24h"]} if calendar_enabled else {}),
        }
        payload = reminders_summary.build_reminders_summary_payload(
            viewer_discord_id=summary.discord_user_id,
            display_name=display_name,
            kvk_config=kvk_config,
            calendar_prefs=calendar_prefs,
            calendar_catalog=reminders_summary.CalendarEventCatalog(
                available=False,
                event_types=(),
            ),
            generated_at_utc=datetime.now(UTC),
        )
    return reminders_summary.with_display_name(payload, display_name)


def build_reminders_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    payload = _reminders_payload(summary, display_name=display_name)
    embed = discord.Embed(
        title="Reminder Centre",
        description=accounts_renderer.format_discord_heading(
            payload.display_name,
            kingdom_id=payload.kingdom_id,
        ),
        color={
            "ACTIVE": discord.Color.green(),
            "REVIEW": discord.Color.gold(),
            "OFF": discord.Color.dark_grey(),
        }[payload.configuration_state.value],
    )
    embed.add_field(
        name=payload.configuration_state.value,
        value=payload.state_supporting_text,
        inline=False,
    )
    embed.add_field(
        name=payload.hero.headline,
        value=_field_value([payload.hero.primary_line, payload.hero.secondary_line]),
        inline=False,
    )
    embed.add_field(
        name="KVK REMINDERS",
        value=_field_value(
            [
                payload.kvk.state_count_line,
                payload.kvk.event_summary,
                payload.kvk.time_summary,
                payload.kvk.coverage_label,
            ]
        ),
        inline=True,
    )
    embed.add_field(
        name="CALENDAR REMINDERS",
        value=_field_value(
            [
                payload.calendar.state_count_line,
                payload.calendar.event_summary,
                payload.calendar.time_summary,
                payload.calendar.coverage_label,
            ]
        ),
        inline=True,
    )
    embed.add_field(
        name="REMINDER INSIGHT",
        value=payload.insight,
        inline=False,
    )
    embed.add_field(
        name="Manage reminders",
        value="Choose KVK and calendar events and when each alert is sent.",
        inline=False,
    )
    embed.set_footer(
        text=(
            "Scheduled times shown in UTC • "
            f"Refreshed {payload.generated_at_utc:%d %b %Y %H:%M UTC}"
        )
    )
    return embed


def build_preferences_embed(
    payload: PreferencesSummaryPayload,
) -> discord.Embed:
    profile = payload.regional_profile
    embed = discord.Embed(
        title="Personal Settings",
        description=f"Private settings for {payload.display_name}",
        color=discord.Color.teal(),
    )
    embed.add_field(
        name=(
            f"{'LOCAL' if payload.time_reference.mode == 'LOCAL' else 'UTC'} "
            f"• {payload.profile_supporting_text}"
        ),
        value=_field_value(
            [
                f"{payload.time_reference.heading}: {payload.time_reference.display_time}",
                payload.time_reference.supporting_line,
                f"Timezone: {profile.timezone.friendly_label}",
                f"Location: {profile.location.friendly_label}",
                f"Preferred language: {profile.preferred_language.friendly_label}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Settings insight",
        value=payload.settings_insight,
        inline=False,
    )
    embed.add_field(
        name="Manage settings",
        value="Update your saved timezone, location, and preferred language.",
        inline=False,
    )
    embed.set_footer(text=f"Refreshed {payload.generated_at_utc:%d %B %Y %H:%M UTC}")
    return embed


def build_exports_embed(
    summary: PlayerSelfServiceSummary,
    *,
    display_name: str,
) -> discord.Embed:
    exports = summary.exports
    embed = discord.Embed(
        title="Exports",
        description=f"Private exports for {display_name}",
        color=discord.Color.dark_teal(),
    )
    embed.add_field(
        name="Status",
        value=_field_value(
            [
                f"Stats: {exports.stats_export}",
                f"Delivery: {exports.privacy_note}",
            ]
        ),
        inline=False,
    )
    embed.add_field(
        name="Actions",
        value=_field_value(
            ["Export Stats"]
            if exports.action_state.strip().lower() == "actionable"
            else [exports.action_summary]
        ),
        inline=False,
    )
    return embed


def build_page_embed(
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary | None,
    *,
    display_name: str,
    accounts_payload: AccountsPortfolioPayload | None = None,
    preferences_payload: PreferencesSummaryPayload | None = None,
) -> discord.Embed:
    if page == PAGE_ACCOUNTS:
        if accounts_payload is not None:
            return build_accounts_portfolio_fallback(accounts_payload, display_name=display_name)
        if summary is None:
            raise ValueError("Accounts fallback requires an authorised portfolio payload")
        return build_accounts_embed(summary, display_name=display_name)
    if page == PAGE_PREFERENCES:
        if preferences_payload is None:
            raise ValueError("Preferences fallback requires an authorised payload")
        return build_preferences_embed(preferences_payload)
    if summary is None:
        raise ValueError(f"{page} requires a player self-service summary")
    if page == PAGE_REMINDERS:
        return build_reminders_embed(summary, display_name=display_name)
    if page == PAGE_EXPORTS:
        return build_exports_embed(summary, display_name=display_name)
    return build_dashboard_embed(summary, display_name=display_name)


def _close_files(files: list[discord.File] | None) -> None:
    for file in files or []:
        try:
            file.close()
        except Exception:
            logger.debug("player_self_service_file_close_failed", exc_info=True)
        stream = getattr(file, "fp", None)
        try:
            if stream is not None and not getattr(stream, "closed", False):
                stream.close()
        except Exception:
            logger.debug("player_self_service_stream_close_failed", exc_info=True)


def _payload_user_id(
    summary: PlayerSelfServiceSummary | None,
    accounts_payload: AccountsPortfolioPayload | None,
    preferences_payload: PreferencesSummaryPayload | None = None,
) -> int | None:
    if accounts_payload is not None:
        return accounts_payload.discord_user_id
    if summary is not None:
        return summary.discord_user_id
    if preferences_payload is not None:
        return preferences_payload.discord_user_id
    return None


async def _build_page_response(
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary | None,
    *,
    display_name: str,
    accounts_payload: AccountsPortfolioPayload | None = None,
    preferences_payload: PreferencesSummaryPayload | None = None,
    avatar_bytes: bytes | None = None,
) -> tuple[discord.Embed | None, list[discord.File]]:
    fallback_embed = build_page_embed(
        page,
        summary,
        display_name=display_name,
        accounts_payload=accounts_payload,
        preferences_payload=preferences_payload,
    )
    try:
        if page == PAGE_ACCOUNTS:
            if accounts_payload is None:
                raise ValueError("Accounts render requires an authorised portfolio payload")
            rendered = await asyncio.to_thread(
                accounts_renderer.render_accounts_card,
                accounts_payload,
                display_name=display_name,
                avatar_bytes=avatar_bytes,
            )
        elif page == PAGE_DASHBOARD:
            if summary is None:
                raise ValueError("Dashboard render requires a summary")
            rendered = await asyncio.to_thread(
                dashboard_card.render_dashboard_card,
                summary,
                display_name=display_name,
            )
        elif page == PAGE_REMINDERS:
            if summary is None:
                raise ValueError("Reminders render requires a summary")
            rendered = await asyncio.to_thread(
                reminders_renderer.render_reminders_card,
                _reminders_payload(summary, display_name=display_name),
                avatar_bytes=avatar_bytes,
            )
        elif page == PAGE_PREFERENCES:
            if preferences_payload is None:
                raise ValueError("Preferences render requires an authorised payload")
            rendered = await asyncio.to_thread(
                preferences_renderer.render_preferences_card,
                preferences_payload,
                avatar_bytes=avatar_bytes,
            )
        else:
            if summary is None:
                raise ValueError(f"{page} render requires a summary")
            rendered = await asyncio.to_thread(
                page_cards.render_page_card,
                page,
                summary,
                display_name=display_name,
            )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "player_self_service_card_render_failed user_id=%s page=%s",
            _payload_user_id(summary, accounts_payload, preferences_payload),
            page,
        )
        return fallback_embed, []

    image_source = (
        BytesIO(rendered.image_bytes)
        if isinstance(rendered.image_bytes, (bytes, bytearray))
        else rendered.image_bytes
    )
    try:
        file = discord.File(image_source, filename=rendered.filename)
    except asyncio.CancelledError:
        try:
            image_source.close()
        finally:
            raise
    except Exception:
        try:
            image_source.close()
        except Exception:
            logger.debug("player_self_service_stream_close_failed", exc_info=True)
        logger.exception(
            "player_self_service_file_create_failed user_id=%s page=%s",
            _payload_user_id(summary, accounts_payload, preferences_payload),
            page,
        )
        return fallback_embed, []
    embed = (
        None
        if page in {PAGE_ACCOUNTS, PAGE_REMINDERS, PAGE_PREFERENCES}
        else (
            build_dashboard_card_embed(rendered.filename)
            if page == PAGE_DASHBOARD
            else build_card_embed(rendered.filename)
        )
    )
    return embed, [file]


def _edit_kwargs(
    *,
    embed: discord.Embed | None,
    view: discord.ui.View,
    files: list[discord.File],
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "content": None,
        "embed": embed,
        "view": view,
        "attachments": [],
    }
    if files:
        kwargs["files"] = files
    return kwargs


async def _edit_original_with_image_fallback(
    target: Any,
    *,
    page: PlayerSelfServicePage,
    summary: PlayerSelfServiceSummary | None,
    accounts_payload: AccountsPortfolioPayload | None = None,
    preferences_payload: PreferencesSummaryPayload | None = None,
    display_name: str,
    view: discord.ui.View,
    embed: discord.Embed | None,
    files: list[discord.File],
) -> object:
    try:
        return await target.edit_original_response(
            **_edit_kwargs(embed=embed, view=view, files=files)
        )
    except discord.NotFound:
        raise
    except asyncio.CancelledError:
        raise
    except Exception:
        if not files:
            raise
        logger.exception(
            "player_self_service_card_send_failed user_id=%s page=%s",
            _payload_user_id(summary, accounts_payload, preferences_payload),
            page,
        )
        fallback_embed = build_page_embed(
            page,
            summary,
            display_name=display_name,
            accounts_payload=accounts_payload,
            preferences_payload=preferences_payload,
        )
        return await target.edit_original_response(
            content=None,
            embed=fallback_embed,
            view=view,
            attachments=[],
        )


class PlayerSelfServiceView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        page: PlayerSelfServicePage = PAGE_DASHBOARD,
        summary: PlayerSelfServiceSummary | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        accounts_payload: AccountsPortfolioPayload | None = None,
        accounts_loader: AccountsLoader = accounts_service.build_accounts_portfolio,
        preferences_payload: PreferencesSummaryPayload | None = None,
        preferences_loader: PreferencesLoader = build_preferences_summary,
        preferences_journey: PreferencesJourneyState | None = None,
        preferences_generation: int | None = None,
        avatar_bytes: bytes | None = None,
        dashboard_governor_id: int | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout, disable_on_timeout=False)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.page = page
        self.summary = summary
        self.summary_loader = summary_loader
        self.accounts_payload = accounts_payload
        self.accounts_loader = accounts_loader
        self.preferences_payload = preferences_payload
        self.preferences_loader = preferences_loader
        self.preferences_journey = preferences_journey or PreferencesJourneyState()
        self.preferences_generation = (
            self.preferences_journey.advance()
            if page == PAGE_PREFERENCES and preferences_generation is None
            else preferences_generation
        )
        self.avatar_bytes = avatar_bytes
        self.dashboard_governor_id = dashboard_governor_id
        self._message_ref: discord.Message | None = None
        self._timeout_editor: Callable[..., Awaitable[Any]] | None = None
        self._expired = False
        self._transition_generation = 0
        self._apply_page_state()

    def set_message_ref(self, message: discord.Message | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self._message = message
            except Exception:
                logger.debug("player_self_service_internal_message_ref_failed", exc_info=True)

    def set_timeout_target(self, target: Any) -> None:
        editor = getattr(target, "edit_original_response", None)
        if callable(editor):
            self._timeout_editor = editor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired:
            await interaction.response.send_message(
                "This private menu has expired. Run `/me dashboard` again.",
                ephemeral=True,
            )
            return False
        if (
            self.page == PAGE_PREFERENCES
            and self.preferences_generation is not None
            and not self.preferences_journey.is_current(self.preferences_generation)
        ):
            await interaction.response.send_message(
                "This Preferences window was superseded. Use the current private window.",
                ephemeral=True,
            )
            return False
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message("This private menu is not for you.", ephemeral=True)
        return False

    def _apply_page_state(self) -> None:
        if self.page != PAGE_ACCOUNTS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:account:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_REMINDERS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:reminder:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_PREFERENCES:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:preference:"
                ):
                    self.remove_item(child)
        if self.page != PAGE_EXPORTS:
            for child in list(self.children):
                if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                    "me:export:"
                ):
                    self.remove_item(child)
        if self.page == PAGE_EXPORTS:
            self._apply_export_button_state()
        self._apply_visible_action_rows()
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if str(child.custom_id or "").startswith("me:export:"):
                    continue
                child.disabled = child.custom_id == f"me:{self.page}"
        if self.page == PAGE_ACCOUNTS:
            self._apply_accounts_button_state()

    def _apply_accounts_button_state(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "me:account:summary":
                child.disabled = not bool(
                    self.accounts_payload and self.accounts_payload.has_linked_governors
                )

    def _apply_visible_action_rows(self) -> None:
        action_prefixes = (
            "me:account:",
            "me:reminder:",
            "me:preference:",
            "me:export:",
        )
        for child in self.children:
            if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                action_prefixes
            ):
                child.row = 2

    def _apply_export_button_state(self) -> None:
        action_state = ""
        if self.summary is not None:
            action_state = self.summary.exports.action_state.strip().lower()
        disabled = action_state != "actionable"
        for child in self.children:
            if isinstance(child, discord.ui.Button) and str(child.custom_id or "").startswith(
                "me:export:"
            ):
                child.disabled = disabled

    async def _show_page(
        self,
        interaction: discord.Interaction,
        page: PlayerSelfServicePage,
        *,
        can_edit: Callable[[], bool] | None = None,
    ) -> bool:
        self._transition_generation += 1
        transition_generation = self._transition_generation
        external_can_edit = can_edit

        def transition_is_current() -> bool:
            return self._transition_generation == transition_generation and (
                external_can_edit is None or external_can_edit()
            )

        can_edit = transition_is_current
        if page == PAGE_DASHBOARD:
            from ui.views.player_self_service_governor_dashboard_views import (
                show_governor_dashboard_for_interaction,
            )

            await show_governor_dashboard_for_interaction(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                governor_id=self.dashboard_governor_id,
                summary_loader=self.summary_loader,
                timeout=self.timeout or 180,
            )
            return True
        try:
            if getattr(interaction, "message", None) is not None:
                await interaction.response.defer()
            else:
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                await interaction.response.defer()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug(
                    "player_self_service_navigation_defer_failed user_id=%s page=%s",
                    self.author_id,
                    page,
                    exc_info=True,
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug(
                "player_self_service_navigation_defer_failed user_id=%s page=%s",
                self.author_id,
                page,
                exc_info=True,
            )

        summary: PlayerSelfServiceSummary | None = None
        accounts_payload: AccountsPortfolioPayload | None = None
        preferences_payload: PreferencesSummaryPayload | None = None
        avatar_bytes = self.avatar_bytes
        try:
            if page == PAGE_ACCOUNTS:
                accounts_payload = await self.accounts_loader(self.author_id)
            elif page == PAGE_PREFERENCES:
                preferences_payload = await self.preferences_loader(
                    self.author_id,
                    display_name=self.display_name,
                )
            else:
                summary = await self.summary_loader(self.author_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "player_self_service_view_summary_failed user_id=%s page=%s",
                self.author_id,
                page,
            )
            try:
                await interaction.followup.send(
                    "Personal status is temporarily unavailable. Please try again in a moment.",
                    ephemeral=True,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("player_self_service_view_error_followup_failed", exc_info=True)
            return False

        if can_edit is not None and not can_edit():
            logger.info(
                "player_self_service_stale_navigation_suppressed user_id=%s page=%s",
                self.author_id,
                page,
            )
            return False

        if page in {PAGE_ACCOUNTS, PAGE_REMINDERS, PAGE_PREFERENCES} and avatar_bytes is None:
            avatar_bytes = await _read_avatar_bytes(
                getattr(interaction, "user", None), expected_user_id=self.author_id
            )

        view = PlayerSelfServiceView(
            author_id=self.author_id,
            display_name=self.display_name,
            page=page,
            summary=summary,
            summary_loader=self.summary_loader,
            accounts_payload=accounts_payload,
            accounts_loader=self.accounts_loader,
            preferences_payload=preferences_payload,
            preferences_loader=self.preferences_loader,
            preferences_journey=self.preferences_journey,
            avatar_bytes=avatar_bytes,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )
        embed, files = await _build_page_response(
            page,
            summary,
            display_name=self.display_name,
            accounts_payload=accounts_payload,
            preferences_payload=preferences_payload,
            avatar_bytes=avatar_bytes,
        )
        if can_edit is not None and not can_edit():
            _close_files(files)
            logger.info(
                "player_self_service_stale_navigation_render_suppressed user_id=%s page=%s",
                self.author_id,
                page,
            )
            return False
        try:
            edited = await _edit_original_with_image_fallback(
                interaction,
                page=page,
                summary=summary,
                accounts_payload=accounts_payload,
                preferences_payload=preferences_payload,
                display_name=self.display_name,
                view=view,
                embed=embed,
                files=files,
            )
            view.set_message_ref(getattr(interaction, "message", None) or edited)
            view.set_timeout_target(interaction)
            return True
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_edit_message_failed", exc_info=True)
            if can_edit is not None and not can_edit():
                return False
            sent = await interaction.followup.send(
                embed=build_page_embed(
                    page,
                    summary,
                    display_name=self.display_name,
                    accounts_payload=accounts_payload,
                    preferences_payload=preferences_payload,
                ),
                view=view,
                ephemeral=True,
            )
            view.set_message_ref(sent)
            return True
        finally:
            _close_files(files)

    @discord.ui.button(
        label="Accounts",
        style=discord.ButtonStyle.primary,
        custom_id="me:accounts",
        row=0,
    )
    async def accounts_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_ACCOUNTS)

    @discord.ui.button(
        label="Reminders",
        style=discord.ButtonStyle.primary,
        custom_id="me:reminders",
        row=0,
    )
    async def reminders_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_REMINDERS)

    @discord.ui.button(
        label="Preferences",
        style=discord.ButtonStyle.primary,
        custom_id="me:preferences",
        row=0,
    )
    async def preferences_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_PREFERENCES)

    @discord.ui.button(
        label="Dashboard",
        style=discord.ButtonStyle.secondary,
        custom_id="me:dashboard",
        row=1,
    )
    async def dashboard_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_DASHBOARD)

    @discord.ui.button(
        label="Exports",
        style=discord.ButtonStyle.secondary,
        custom_id="me:exports",
        row=1,
    )
    async def dashboard_exports_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._show_page(interaction, PAGE_EXPORTS)

    @discord.ui.button(
        label="Export Stats",
        style=discord.ButtonStyle.success,
        custom_id="me:export:stats",
        row=2,
    )
    async def export_stats_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await export_views.send_stats_export_options(
            interaction,
            display_name=self.display_name,
        )

    async def _load_account_state(
        self, interaction: discord.Interaction
    ) -> AccountCentreState | None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                logger.debug("player_self_service_account_action_defer_failed", exc_info=True)
        except Exception:
            logger.debug("player_self_service_account_action_defer_failed", exc_info=True)

        try:
            state = await account_service.build_account_centre_state(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_account_state_failed user_id=%s page=%s",
                self.author_id,
                self.page,
            )
            await interaction.followup.send(
                "Account data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None

        if not state.ok:
            await interaction.followup.send(
                "Account data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None
        return state

    @discord.ui.button(
        label="Manage Accounts",
        style=discord.ButtonStyle.success,
        custom_id="me:account:manage",
        row=3,
    )
    async def account_manage_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_account_state(interaction)
        if state is None:
            return
        await interaction.followup.send(
            "Choose what you want to manage.",
            view=AccountManageView(
                author_id=self.author_id,
                display_name=self.display_name,
                state=state,
                host_message=getattr(interaction, "message", None),
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Account Summary",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:summary",
        row=3,
    )
    async def account_summary_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        from ui.views.player_self_service_account_summary_views import (
            show_account_summary_for_interaction,
        )

        await show_account_summary_for_interaction(
            interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            accounts_loader=self.accounts_loader,
            avatar_bytes=self.avatar_bytes,
            summary_loader=self.summary_loader,
            dashboard_governor_id=self.dashboard_governor_id,
            timeout=self.timeout or 180,
        )

    async def _load_reminder_state(
        self, interaction: discord.Interaction
    ) -> ReminderCentreState | None:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except TypeError:
            try:
                if not interaction.response.is_done():
                    await interaction.response.defer()
            except Exception:
                logger.debug("player_self_service_reminder_action_defer_failed", exc_info=True)
        except Exception:
            logger.debug("player_self_service_reminder_action_defer_failed", exc_info=True)

        try:
            state = await reminder_service.build_reminder_centre_state(self.author_id)
        except Exception:
            logger.exception(
                "player_self_service_reminder_state_failed user_id=%s page=%s",
                self.author_id,
                self.page,
            )
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None

        if not state.ok:
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return None
        return state

    @discord.ui.button(
        label="Manage",
        style=discord.ButtonStyle.success,
        custom_id="me:reminder:manage",
        row=3,
    )
    async def reminder_manage_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        state = await self._load_reminder_state(interaction)
        if state is None:
            return
        if not state.can_manage:
            await interaction.followup.send(
                "Reminder data is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
            return
        setup_view = ReminderSetupView(
            author_id=self.author_id,
            username=str(getattr(interaction, "user", "") or self.display_name),
            state=state,
            display_name=self.display_name,
            host_message=getattr(interaction, "message", None),
            summary_loader=self.summary_loader,
            avatar_bytes=self.avatar_bytes,
        )
        sent = await interaction.followup.send(
            "Choose KVK event types and times, or switch to calendar reminder management.",
            view=setup_view,
            ephemeral=True,
        )
        setup_view.set_message_ref(sent)

    @discord.ui.button(
        label="Manage settings",
        style=discord.ButtonStyle.success,
        custom_id="me:preference:manage",
        row=4,
    )
    async def preference_manage_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        if self.preferences_payload is None:
            await interaction.response.send_message(
                "Preferences are temporarily unavailable. Run `/me preferences` again.",
                ephemeral=True,
            )
            return
        await show_preferences_manage_settings(
            interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            payload=self.preferences_payload,
            preferences_loader=self.preferences_loader,
            avatar_bytes=self.avatar_bytes,
            dashboard_governor_id=self.dashboard_governor_id,
            journey=self.preferences_journey,
            source_generation=self.preferences_generation,
            timeout=self.timeout or 180,
        )

    async def on_timeout(self) -> None:
        self._expired = True
        if self.page == PAGE_PREFERENCES and self.preferences_generation is not None:
            self.preferences_journey.expire(self.preferences_generation)
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        timeout_content = (
            "This private reminder report has expired. Run `/me reminders` again."
            if self.page == PAGE_REMINDERS
            else (
                "This private Preferences page has expired. Run `/me preferences` again."
                if self.page == PAGE_PREFERENCES
                else "This private /me menu has expired. Run `/me dashboard` again."
            )
        )
        edited = False
        try:
            if self._timeout_editor is not None:
                await self._timeout_editor(content=timeout_content, view=self)
                edited = True
        except Exception:
            logger.debug("player_self_service_timeout_original_edit_failed", exc_info=True)
        try:
            if not edited and message:
                await message.edit(
                    content=timeout_content,
                    view=self,
                )
        except Exception:
            logger.debug("player_self_service_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


async def show_player_self_service_page_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    page: PlayerSelfServicePage,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    accounts_loader: AccountsLoader = accounts_service.build_accounts_portfolio,
    preferences_loader: PreferencesLoader = build_preferences_summary,
    avatar_bytes: bytes | None = None,
    dashboard_governor_id: int | None = None,
    timeout: float = 180,
    can_edit: Callable[[], bool] | None = None,
) -> bool:
    """Open an existing Discord-user-level ``/me`` page in the current message."""
    router = PlayerSelfServiceView(
        author_id=author_id,
        display_name=display_name,
        page=page,
        summary_loader=summary_loader,
        accounts_loader=accounts_loader,
        preferences_loader=preferences_loader,
        avatar_bytes=avatar_bytes,
        dashboard_governor_id=dashboard_governor_id,
        timeout=timeout,
    )
    return await router._show_page(interaction, page, can_edit=can_edit)


async def send_player_self_service_page(
    ctx: discord.ApplicationContext,
    *,
    page: PlayerSelfServicePage = PAGE_DASHBOARD,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    preferences_loader: PreferencesLoader = build_preferences_summary,
) -> None:
    await safe_defer(ctx, ephemeral=True)
    display_name = _display_name(getattr(ctx, "user", None))
    summary: PlayerSelfServiceSummary | None = None
    accounts_payload: AccountsPortfolioPayload | None = None
    preferences_payload: PreferencesSummaryPayload | None = None
    avatar_bytes: bytes | None = None
    try:
        if page == PAGE_ACCOUNTS:
            accounts_payload = await accounts_service.build_accounts_portfolio(int(ctx.user.id))
        elif page == PAGE_PREFERENCES:
            preferences_payload = await preferences_loader(
                int(ctx.user.id),
                display_name=display_name,
            )
        else:
            summary = await summary_loader(int(ctx.user.id))
        if page in {PAGE_ACCOUNTS, PAGE_REMINDERS, PAGE_PREFERENCES}:
            avatar_bytes = await _read_avatar_bytes(ctx.user, expected_user_id=int(ctx.user.id))
    except Exception:
        logger.exception(
            "player_self_service_initial_summary_failed user_id=%s page=%s",
            getattr(getattr(ctx, "user", None), "id", None),
            page,
        )
        try:
            await ctx.interaction.edit_original_response(
                content="Personal status is temporarily unavailable. Please try again in a moment.",
                embed=None,
                view=None,
            )
        except Exception:
            logger.debug("player_self_service_initial_error_edit_failed", exc_info=True)
            await ctx.followup.send(
                "Personal status is temporarily unavailable. Please try again in a moment.",
                ephemeral=True,
            )
        return

    view = PlayerSelfServiceView(
        author_id=int(ctx.user.id),
        display_name=display_name,
        page=page,
        summary=summary,
        summary_loader=summary_loader,
        accounts_payload=accounts_payload,
        preferences_payload=preferences_payload,
        preferences_loader=preferences_loader,
        avatar_bytes=avatar_bytes,
    )
    embed, files = await _build_page_response(
        page,
        summary,
        display_name=display_name,
        accounts_payload=accounts_payload,
        preferences_payload=preferences_payload,
        avatar_bytes=avatar_bytes,
    )
    try:
        message = await _edit_original_with_image_fallback(
            ctx.interaction,
            page=page,
            summary=summary,
            accounts_payload=accounts_payload,
            preferences_payload=preferences_payload,
            display_name=display_name,
            view=view,
            embed=embed,
            files=files,
        )
        view.set_message_ref(message)
        view.set_timeout_target(ctx.interaction)
    finally:
        _close_files(files)
