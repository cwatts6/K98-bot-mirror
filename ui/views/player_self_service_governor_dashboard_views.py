"""Private Discord journey for the governor-first ``/me dashboard``."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from io import BytesIO
import logging
from math import ceil
import time
from typing import Any

import discord

from player_self_service.governor_dashboard_models import (
    GovernorDashboardContext,
    GovernorDashboardOption,
    GovernorDashboardPayload,
    GovernorDashboardResolution,
)
from player_self_service.governor_dashboard_renderer import render_governor_dashboard
from player_self_service.governor_dashboard_service import (
    GovernorDashboardAccessDenied,
    build_governor_dashboard_payload,
    resolve_dashboard_context,
)
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)
from utils import fmt_short

logger = logging.getLogger(__name__)

ContextResolver = Callable[..., Awaitable[GovernorDashboardResolution]]
PayloadLoader = Callable[[GovernorDashboardContext], Awaitable[GovernorDashboardPayload]]
SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]

_SELECT_PAGE_SIZE = 25
_VIEW_TIMEOUT_SECONDS = 180.0
_MISSING = "N/A"
_DASHBOARD_TITLE_PREFIX = "Governor Dashboard — "
_DISCORD_EMBED_TITLE_LIMIT = 256
_AVATAR_READ_TIMEOUT_SECONDS = 3.0


def _safe_text(value: Any, *, missing: str = _MISSING) -> str:
    text = str(value).strip() if value is not None else ""
    return text or missing


def _format_number(value: int | float | None) -> str:
    if value is None:
        return _MISSING
    if isinstance(value, bool):
        return _MISSING
    if isinstance(value, int):
        return f"{value:,}"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _MISSING
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _format_short_number(value: int | float | None) -> str:
    if value is None or isinstance(value, bool):
        return _MISSING
    try:
        rendered = fmt_short(value)
    except (TypeError, ValueError):
        return _MISSING
    if rendered.endswith("k"):
        rendered = f"{rendered[:-1]}K"
    if len(rendered) >= 3 and rendered[-1] in "KMB" and rendered[-3:-1] == ".0":
        rendered = f"{rendered[:-3]}{rendered[-1]}"
    return rendered


def _format_freshness(value: Any) -> str:
    if value is None:
        return "No recent scan available"
    if isinstance(value, datetime):
        timestamp = value
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        epoch = int(timestamp.timestamp())
        return f"<t:{epoch}:f> (<t:{epoch}:R>)"
    return _safe_text(value, missing="No recent scan available")


def _format_vip(value: Any) -> str:
    label = str(value or "").strip()
    if not label:
        return "VIP: Not set"
    return label if label.casefold().startswith("vip") else f"VIP: {label}"


def _format_location(x: int | None, y: int | None) -> str:
    if x is None or y is None:
        return _MISSING
    return f"{x}:{y}"


def _option_label(option: GovernorDashboardOption) -> str:
    label = " ".join(str(option.governor_name or "").split()) or option.governor_id_str
    return label[:100]


def _governor_dashboard_title(name: Any, *, fallback: str) -> str:
    safe_name = " ".join(str(name or "").split()) or fallback
    safe_name = safe_name.replace("@", "@\u200b")
    safe_name = safe_name.replace("<", "‹").replace(">", "›")
    available = _DISCORD_EMBED_TITLE_LIMIT - len(_DASHBOARD_TITLE_PREFIX)
    return f"{_DASHBOARD_TITLE_PREFIX}{safe_name[:available]}"


def _is_authorized_self_context(context: GovernorDashboardContext, author_id: int) -> bool:
    return bool(
        context.viewer_mode == "self"
        and context.viewer_discord_id == int(author_id)
        and context.is_linked_to_viewer
        and context.access_allowed
        and context.selected_governor_id is not None
    )


def build_governor_dashboard_embed(payload: GovernorDashboardPayload) -> discord.Embed:
    """Render the replaceable Phase 3 fallback shell from the Phase 2 payload."""
    identity = payload.identity
    self_view = payload.self_view
    metrics = payload.latest_metrics
    history = payload.historical_highlights
    honours = payload.activity_honours
    profile = payload.profile_status

    embed = discord.Embed(
        title=_governor_dashboard_title(
            identity.governor_name,
            fallback=f"Governor {identity.governor_id}",
        ),
        description="Your private KD98 governor overview.",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Governor Identity",
        value="\n".join(
            (
                f"Governor ID: `{identity.governor_id}`",
                f"Account type: {_safe_text(getattr(self_view, 'account_type', None))}",
                _format_vip(getattr(self_view, "vip_level_label", None)),
            )
        ),
        inline=False,
    )
    embed.add_field(
        name="Profile",
        value="\n".join(
            (
                f"Alliance: {_safe_text(identity.alliance)}",
                f"Civilisation: {_safe_text(identity.civilisation)}",
                f"Location: {_format_location(identity.location_x, identity.location_y)}",
                f"Conduct Score: {_format_number(profile.conduct_score)}",
            )
        ),
        inline=False,
    )
    embed.add_field(
        name="Power & Battle",
        value="\n".join(
            (
                f"Power: {_format_short_number(metrics.power)}",
                f"Kill Points: {_format_short_number(metrics.kill_points)}",
                f"Highest Acclaim: {_format_short_number(history.highest_acclaim)}",
                f"Dead: {_format_short_number(metrics.dead)}",
                f"Helps: {_format_short_number(metrics.helps)}",
                f"Healed: {_format_short_number(metrics.healed)}",
            )
        ),
        inline=False,
    )
    embed.add_field(
        name="Ark & Honours",
        value="\n".join(
            (
                f"Ark joined: {_format_number(honours.ark_joined)}",
                f"Ark won: {_format_number(honours.ark_won)}",
                f"Ark win ratio: {_safe_text(honours.ark_win_ratio_label)}",
                f"Times Named Autarch: {_format_number(history.times_named_autarch)}",
                "Times Autarch Participated: "
                f"{_format_number(history.times_autarch_participated)}",
            )
        ),
        inline=False,
    )
    freshness = _format_freshness(payload.freshness.updated_at_utc)
    embed.add_field(name="Freshness", value=freshness, inline=False)
    embed.set_footer(text="Private self-view • Data shown for your linked governor.")
    return embed


def build_governor_dashboard_card_embed(filename: str) -> discord.Embed:
    embed = discord.Embed(color=discord.Color.from_rgb(74, 54, 117))
    embed.set_image(url=f"attachment://{filename}")
    return embed


async def _read_avatar_bytes(user: Any, *, expected_user_id: int) -> bytes | None:
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
            "governor_dashboard_avatar_read_failed user_id=%s",
            getattr(user, "id", None),
            exc_info=True,
        )
    return None


def _close_files(files: list[discord.File] | None) -> None:
    for file in files or []:
        try:
            file.close()
        except Exception:
            logger.debug("governor_dashboard_file_close_failed", exc_info=True)
        stream = getattr(file, "fp", None)
        try:
            if stream is not None and not getattr(stream, "closed", False):
                stream.close()
        except Exception:
            logger.debug("governor_dashboard_stream_close_failed", exc_info=True)


def build_governor_selector_embed(
    options: tuple[GovernorDashboardOption, ...],
    *,
    page: int = 0,
) -> discord.Embed:
    total_pages = max(1, ceil(len(options) / _SELECT_PAGE_SIZE))
    embed = discord.Embed(
        title="Choose a Governor",
        description=(
            "Select one of your linked governors. Access is checked again before dashboard "
            "data is loaded."
        ),
        color=discord.Color.blurple(),
    )
    default_option = next((option for option in options if option.is_default), None)
    if default_option is not None:
        embed.add_field(
            name="Default account",
            value=f"{_option_label(default_option)} (`{default_option.governor_id_str}`)",
            inline=False,
        )
    embed.set_footer(text=f"Private selector • Page {page + 1} of {total_pages}")
    return embed


def build_governor_setup_embed() -> discord.Embed:
    return discord.Embed(
        title="Set up your Governor Dashboard",
        description=(
            "No linked governors were found. Open **Accounts** to link a governor, then return "
            "to `/me dashboard`."
        ),
        color=discord.Color.gold(),
    )


def build_governor_unavailable_embed() -> discord.Embed:
    return discord.Embed(
        title="Governor Dashboard Temporarily Unavailable",
        description=(
            "The account registry could not be checked. Your registrations have not been treated "
            "as missing; please try again shortly."
        ),
        color=discord.Color.orange(),
    )


def build_governor_denied_embed() -> discord.Embed:
    return discord.Embed(
        title="Governor Access Denied",
        description=(
            "That governor is not currently linked to your Discord account. Open **Accounts** to "
            "review your registrations."
        ),
        color=discord.Color.red(),
    )


def build_governor_payload_error_embed(context: GovernorDashboardContext) -> discord.Embed:
    governor_id = context.selected_governor_id
    embed = discord.Embed(
        title=_governor_dashboard_title(
            context.selected_governor_name,
            fallback=f"Governor {governor_id}" if governor_id is not None else "Governor",
        ),
        description=(
            "The governor is linked, but dashboard data is temporarily unavailable. No values "
            "have been guessed."
        ),
        color=discord.Color.orange(),
    )
    embed.add_field(
        name="Governor Identity",
        value=f"Governor ID: `{governor_id}`\nAccount type: {_safe_text(context.account_type_for_self_view)}",
        inline=False,
    )
    embed.add_field(name="Metrics", value="Dashboard metrics: N/A", inline=False)
    embed.add_field(name="Freshness", value="No recent scan available", inline=False)
    return embed


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if interaction.response.is_done():
            return
        if getattr(interaction, "message", None) is not None:
            await interaction.response.defer()
        else:
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        if not interaction.response.is_done():
            await interaction.response.defer()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("governor_dashboard_interaction_defer_failed", exc_info=True)


async def _send_private_error(interaction: discord.Interaction, content: str) -> None:
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True)
        else:
            await interaction.response.send_message(content, ephemeral=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("governor_dashboard_private_error_send_failed", exc_info=True)


class _GovernorSelect(discord.ui.Select):
    def __init__(
        self,
        parent: GovernorDashboardView,
        options: tuple[GovernorDashboardOption, ...],
    ) -> None:
        choices = [
            discord.SelectOption(
                label=_option_label(option),
                value=option.governor_id_str,
                description=option.account_type[:100],
                emoji="⭐" if option.is_default else None,
            )
            for option in options
        ]
        super().__init__(
            placeholder="Select a linked governor",
            min_values=1,
            max_values=1,
            options=choices,
            custom_id="me:dashboard:governor",
            row=0,
        )
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        await self.parent_view.select_governor(interaction, self.values[0])


class _DashboardButton(discord.ui.Button):
    def __init__(
        self,
        *,
        label: str,
        custom_id: str,
        style: discord.ButtonStyle,
        row: int,
        action: Callable[[discord.Interaction], Awaitable[None]],
    ) -> None:
        super().__init__(label=label, custom_id=custom_id, style=style, row=row)
        self._action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._action(interaction)


class GovernorDashboardView(discord.ui.View):
    """Author-gated, non-persistent view for dashboard selection and navigation."""

    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        resolution: GovernorDashboardResolution,
        context_resolver: ContextResolver = resolve_dashboard_context,
        payload_loader: PayloadLoader = build_governor_dashboard_payload,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        selector_page: int = 0,
        timeout: float = _VIEW_TIMEOUT_SECONDS,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=True)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.resolution = resolution
        self.context_resolver = context_resolver
        self.payload_loader = payload_loader
        self.summary_loader = summary_loader
        self.selector_page = max(0, int(selector_page))
        self._message_ref: discord.Message | None = None
        self._timeout_editor: Callable[..., Awaitable[Any]] | None = None
        self._expired = False
        self._busy = False
        self._timed_out = False
        self._active_transition_id: int | None = None
        self._build_controls()

    def _lock_for_transition(self) -> None:
        """Reject new events while preserving the real timeout during awaited work."""
        self._expired = True

    async def _claim_transition(self, interaction: discord.Interaction) -> bool:
        transition_id = id(interaction)
        if self._timed_out:
            await _send_private_error(
                interaction,
                "This private dashboard has expired. Run `/me dashboard` again.",
            )
            return False
        if self._active_transition_id == transition_id:
            return True
        if self._busy or self._active_transition_id is not None or self._expired:
            await _send_private_error(
                interaction,
                "This dashboard action is stale or another action is already being processed.",
            )
            return False
        self._busy = True
        self._active_transition_id = transition_id
        return True

    def _transition_is_current(self, interaction: discord.Interaction) -> bool:
        return bool(not self._timed_out and self._active_transition_id == id(interaction))

    def _transition_timeout_remaining(self) -> float:
        expiry = getattr(self, "_timeout_expiry", None)
        if expiry is None:
            return float(self.timeout or _VIEW_TIMEOUT_SECONDS)
        return max(0.001, float(expiry) - time.monotonic())

    def set_message_ref(self, message: discord.Message | None) -> None:
        self._message_ref = message
        if message is not None and hasattr(message, "flags") and hasattr(message, "channel"):
            try:
                self._message = message
            except Exception:
                logger.debug("governor_dashboard_internal_message_ref_failed", exc_info=True)

    def set_timeout_target(self, target: Any) -> None:
        editor = getattr(target, "edit_original_response", None)
        if callable(editor):
            self._timeout_editor = editor

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self._expired:
            await _send_private_error(
                interaction,
                "This private dashboard has expired. Run `/me dashboard` again.",
            )
            return False
        if not interaction.user or int(interaction.user.id) != self.author_id:
            await _send_private_error(interaction, "This private dashboard is not for you.")
            return False
        if self._busy or self._active_transition_id is not None:
            await _send_private_error(
                interaction,
                "Another dashboard action is already being processed.",
            )
            return False
        self._busy = True
        self._active_transition_id = id(interaction)
        return True

    def _build_controls(self) -> None:
        selecting = self.resolution.state == "requires_selection"
        if selecting and self.resolution.options:
            total_pages = max(1, ceil(len(self.resolution.options) / _SELECT_PAGE_SIZE))
            self.selector_page = min(self.selector_page, total_pages - 1)
            start = self.selector_page * _SELECT_PAGE_SIZE
            page_options = self.resolution.options[start : start + _SELECT_PAGE_SIZE]
            self.add_item(_GovernorSelect(self, page_options))
            if total_pages > 1:
                self.add_item(
                    _DashboardButton(
                        label="Previous",
                        custom_id="me:dashboard:selector:previous",
                        style=discord.ButtonStyle.secondary,
                        row=1,
                        action=self.previous_selector_page,
                    )
                )
                self.add_item(
                    _DashboardButton(
                        label="Next",
                        custom_id="me:dashboard:selector:next",
                        style=discord.ButtonStyle.secondary,
                        row=1,
                        action=self.next_selector_page,
                    )
                )

        selected_with_multiple = (
            self.resolution.state == "selected" and len(self.resolution.options) > 1
        )
        if selected_with_multiple:
            self.add_item(
                _DashboardButton(
                    label="Change Governor",
                    custom_id="me:dashboard:change",
                    style=discord.ButtonStyle.success,
                    row=0,
                    action=self.change_governor,
                )
            )

        navigation_row = 2 if selecting else 1
        secondary_row = 3 if selecting else 2
        from ui.views.player_self_service_views import (
            PAGE_ACCOUNTS,
            PAGE_EXPORTS,
            PAGE_INVENTORY,
            PAGE_PREFERENCES,
            PAGE_REMINDERS,
        )

        navigation = (
            ("Accounts", PAGE_ACCOUNTS, navigation_row),
            ("Reminders", PAGE_REMINDERS, navigation_row),
            ("Preferences", PAGE_PREFERENCES, navigation_row),
            ("Inventory", PAGE_INVENTORY, secondary_row),
            ("Exports", PAGE_EXPORTS, secondary_row),
        )
        for label, page, row in navigation:
            style = (
                discord.ButtonStyle.success
                if label == "Accounts" and self.resolution.state == "requires_setup"
                else discord.ButtonStyle.secondary
            )
            self.add_item(
                _DashboardButton(
                    label=label,
                    custom_id=f"me:dashboard:navigate:{page}",
                    style=style,
                    row=row,
                    action=lambda interaction, target=page: self.open_page(interaction, target),
                )
            )

    async def open_page(self, interaction: discord.Interaction, page: str) -> None:
        from ui.views.player_self_service_views import show_player_self_service_page_for_interaction

        if not await self._claim_transition(interaction):
            return
        self._lock_for_transition()
        try:
            rendered = await asyncio.wait_for(
                show_player_self_service_page_for_interaction(
                    interaction,
                    author_id=self.author_id,
                    display_name=self.display_name,
                    page=page,
                    summary_loader=self.summary_loader,
                    dashboard_governor_id=(
                        self.resolution.context.selected_governor_id
                        if self.resolution.context is not None
                        else None
                    ),
                    can_edit=lambda: self._transition_is_current(interaction),
                ),
                timeout=self._transition_timeout_remaining(),
            )
        except TimeoutError:
            logger.info(
                "governor_dashboard_navigation_timed_out user_id=%s page=%s",
                self.author_id,
                page,
            )
            return
        if rendered and self._transition_is_current(interaction):
            self.stop()

    async def select_governor(
        self,
        interaction: discord.Interaction,
        governor_id: str,
    ) -> None:
        if not await self._claim_transition(interaction):
            return
        self._lock_for_transition()
        await _defer_private(interaction)
        safe_governor_id = str(governor_id).replace("\r", "").replace("\n", "")[:32]
        try:
            resolution = await self.context_resolver(
                self.author_id,
                governor_id,
                viewer_mode="self",
            )
            rendered = await _render_resolution(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                resolution=resolution,
                context_resolver=self.context_resolver,
                payload_loader=self.payload_loader,
                summary_loader=self.summary_loader,
                timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
                can_edit=lambda: self._transition_is_current(interaction),
                timeout_remaining=self._transition_timeout_remaining,
            )
            if rendered:
                self.stop()
            logger.info(
                "governor_dashboard_selection user_id=%s governor_id=%s state=%s",
                self.author_id,
                safe_governor_id,
                resolution.state,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "governor_dashboard_selection_failed user_id=%s governor_id=%s",
                self.author_id,
                safe_governor_id,
            )
            await _send_private_error(
                interaction,
                "The dashboard could not process that selection. Please try again.",
            )
        finally:
            if not self._expired:
                self._busy = False
                self._active_transition_id = None

    async def change_governor(self, interaction: discord.Interaction) -> None:
        if not await self._claim_transition(interaction):
            return
        self._lock_for_transition()
        await _defer_private(interaction)
        try:
            resolution = await self.context_resolver(self.author_id, viewer_mode="self")
            rendered = await _render_resolution(
                interaction,
                author_id=self.author_id,
                display_name=self.display_name,
                resolution=resolution,
                context_resolver=self.context_resolver,
                payload_loader=self.payload_loader,
                summary_loader=self.summary_loader,
                timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
                can_edit=lambda: self._transition_is_current(interaction),
                timeout_remaining=self._transition_timeout_remaining,
            )
            if rendered:
                self.stop()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("governor_dashboard_change_failed user_id=%s", self.author_id)
            await _send_private_error(
                interaction,
                "Linked governors could not be refreshed. Please try again.",
            )
        finally:
            if not self._expired:
                self._busy = False
                self._active_transition_id = None

    async def _show_selector_page(
        self,
        interaction: discord.Interaction,
        page: int,
    ) -> None:
        if not await self._claim_transition(interaction):
            return
        self._lock_for_transition()
        total_pages = max(1, ceil(len(self.resolution.options) / _SELECT_PAGE_SIZE))
        next_page = min(max(0, page), total_pages - 1)
        view = GovernorDashboardView(
            author_id=self.author_id,
            display_name=self.display_name,
            resolution=self.resolution,
            context_resolver=self.context_resolver,
            payload_loader=self.payload_loader,
            summary_loader=self.summary_loader,
            selector_page=next_page,
            timeout=self.timeout or _VIEW_TIMEOUT_SECONDS,
        )
        embed = build_governor_selector_embed(self.resolution.options, page=next_page)
        try:
            if not self._transition_is_current(interaction):
                return
            edited = await asyncio.wait_for(
                interaction.response.edit_message(
                    content=None,
                    embed=embed,
                    view=view,
                    attachments=[],
                ),
                timeout=self._transition_timeout_remaining(),
            )
            if not self._transition_is_current(interaction):
                return
            view.set_message_ref(getattr(interaction, "message", None) or edited)
            view.set_timeout_target(interaction)
            self.stop()
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            logger.info("governor_dashboard_selector_page_timed_out user_id=%s", self.author_id)
        except Exception:
            logger.debug("governor_dashboard_selector_page_edit_failed", exc_info=True)
            if not self._transition_is_current(interaction):
                return
            try:
                sent = await asyncio.wait_for(
                    interaction.followup.send(embed=embed, view=view, ephemeral=True),
                    timeout=self._transition_timeout_remaining(),
                )
            except TimeoutError:
                logger.info(
                    "governor_dashboard_selector_fallback_timed_out user_id=%s",
                    self.author_id,
                )
                return
            if not self._transition_is_current(interaction):
                return
            view.set_message_ref(sent)
            self.stop()

    async def previous_selector_page(self, interaction: discord.Interaction) -> None:
        await self._show_selector_page(interaction, self.selector_page - 1)

    async def next_selector_page(self, interaction: discord.Interaction) -> None:
        await self._show_selector_page(interaction, self.selector_page + 1)

    async def on_timeout(self) -> None:
        self._timed_out = True
        self._active_transition_id = None
        self._expired = True
        for child in self.children:
            child.disabled = True
        message = self._message_ref or getattr(self, "message", None)
        timeout_content = "This private governor dashboard has expired. Run `/me dashboard` again."
        edited = False
        try:
            if self._timeout_editor is not None:
                await self._timeout_editor(
                    content=timeout_content, embed=None, view=self, attachments=[]
                )
                edited = True
        except Exception:
            logger.debug("governor_dashboard_timeout_original_edit_failed", exc_info=True)
        try:
            if not edited and message:
                await message.edit(
                    content=timeout_content,
                    embed=None,
                    view=self,
                    attachments=[],
                )
        except Exception:
            logger.debug("governor_dashboard_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


async def _edit_dashboard_response(
    target: Any,
    *,
    embed: discord.Embed,
    view: GovernorDashboardView,
    files: list[discord.File] | None = None,
    fallback_embed: discord.Embed | None = None,
    can_edit: Callable[[], bool] | None = None,
    timeout_remaining: Callable[[], float] | None = None,
) -> bool:
    files = files or []
    fallback_embed = fallback_embed or embed
    if can_edit is not None and not can_edit():
        _close_files(files)
        return False
    try:
        kwargs: dict[str, Any] = {
            "content": None,
            "embed": embed,
            "view": view,
            "attachments": [],
        }
        if files:
            kwargs["files"] = files
        edit_call = target.edit_original_response(**kwargs)
        edited = (
            await asyncio.wait_for(edit_call, timeout=timeout_remaining())
            if timeout_remaining is not None
            else await edit_call
        )
        if can_edit is not None and not can_edit():
            return False
        view.set_message_ref(getattr(target, "message", None) or edited)
        view.set_timeout_target(target)
        return True
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        logger.info("governor_dashboard_terminal_edit_timed_out")
        return False
    except Exception:
        logger.debug("governor_dashboard_edit_failed_falling_back", exc_info=True)
        if can_edit is not None and not can_edit():
            return False
        if files:
            try:
                fallback_call = target.edit_original_response(
                    content=None,
                    embed=fallback_embed,
                    view=view,
                    attachments=[],
                )
                edited = (
                    await asyncio.wait_for(fallback_call, timeout=timeout_remaining())
                    if timeout_remaining is not None
                    else await fallback_call
                )
                if can_edit is not None and not can_edit():
                    return False
                view.set_message_ref(getattr(target, "message", None) or edited)
                view.set_timeout_target(target)
                return True
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("governor_dashboard_embed_retry_failed", exc_info=True)
        try:
            followup_call = target.followup.send(embed=fallback_embed, view=view, ephemeral=True)
            sent = (
                await asyncio.wait_for(followup_call, timeout=timeout_remaining())
                if timeout_remaining is not None
                else await followup_call
            )
        except TimeoutError:
            logger.info("governor_dashboard_terminal_fallback_timed_out")
            return False
        if can_edit is not None and not can_edit():
            return False
        view.set_message_ref(sent)
        return True
    finally:
        _close_files(files)


async def _render_resolution(
    target: Any,
    *,
    author_id: int,
    display_name: str,
    resolution: GovernorDashboardResolution,
    context_resolver: ContextResolver,
    payload_loader: PayloadLoader,
    summary_loader: SummaryLoader,
    timeout: float,
    can_edit: Callable[[], bool] | None = None,
    timeout_remaining: Callable[[], float] | None = None,
) -> bool:
    embed: discord.Embed
    fallback_embed: discord.Embed | None = None
    files: list[discord.File] = []
    if resolution.state == "selected":
        context = resolution.context
        if context is None or not _is_authorized_self_context(context, author_id):
            logger.warning(
                "governor_dashboard_selected_without_access user_id=%s",
                author_id,
            )
            embed = build_governor_denied_embed()
        else:
            try:
                payload = await payload_loader(context)
                if (
                    payload.context.viewer_discord_id != int(author_id)
                    or payload.context.viewer_mode != "self"
                    or payload.identity.governor_id != context.selected_governor_id
                ):
                    logger.warning(
                        "governor_dashboard_payload_context_mismatch user_id=%s governor_id=%s",
                        author_id,
                        context.selected_governor_id,
                    )
                    embed = build_governor_denied_embed()
                else:
                    fallback_embed = build_governor_dashboard_embed(payload)
                    try:
                        avatar_bytes = await _read_avatar_bytes(
                            getattr(target, "user", None), expected_user_id=author_id
                        )
                        rendered_card = await asyncio.to_thread(
                            render_governor_dashboard,
                            payload,
                            avatar_bytes=avatar_bytes,
                        )
                        file = discord.File(
                            BytesIO(rendered_card.image_bytes),
                            filename=rendered_card.filename,
                        )
                        files = [file]
                        embed = build_governor_dashboard_card_embed(rendered_card.filename)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception(
                            "governor_dashboard_card_render_failed user_id=%s governor_id=%s",
                            author_id,
                            context.selected_governor_id,
                        )
                        embed = fallback_embed
            except GovernorDashboardAccessDenied:
                logger.warning(
                    "governor_dashboard_payload_access_denied user_id=%s governor_id=%s",
                    author_id,
                    context.selected_governor_id,
                )
                embed = build_governor_denied_embed()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "governor_dashboard_payload_failed user_id=%s governor_id=%s",
                    author_id,
                    context.selected_governor_id,
                )
                embed = build_governor_payload_error_embed(context)
    elif resolution.state == "requires_selection":
        embed = build_governor_selector_embed(resolution.options)
    elif resolution.state == "requires_setup":
        embed = build_governor_setup_embed()
    elif resolution.state == "unavailable":
        embed = build_governor_unavailable_embed()
    else:
        logger.warning(
            "governor_dashboard_resolution_denied user_id=%s reason=%s",
            author_id,
            resolution.reason,
        )
        embed = build_governor_denied_embed()

    view = GovernorDashboardView(
        author_id=author_id,
        display_name=display_name,
        resolution=resolution,
        context_resolver=context_resolver,
        payload_loader=payload_loader,
        summary_loader=summary_loader,
        timeout=timeout,
    )
    rendered = await _edit_dashboard_response(
        target,
        embed=embed,
        view=view,
        files=files,
        fallback_embed=fallback_embed,
        can_edit=can_edit,
        timeout_remaining=timeout_remaining,
    )
    if not rendered:
        logger.info("governor_dashboard_stale_transition_edit_suppressed user_id=%s", author_id)
    return rendered


async def show_governor_dashboard_for_interaction(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    governor_id: int | str | None = None,
    context_resolver: ContextResolver = resolve_dashboard_context,
    payload_loader: PayloadLoader = build_governor_dashboard_payload,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    timeout: float = _VIEW_TIMEOUT_SECONDS,
) -> None:
    """Replace an existing private ``/me`` message with the governor journey."""
    await _defer_private(interaction)
    try:
        if governor_id is None:
            resolution = await context_resolver(int(author_id), viewer_mode="self")
        else:
            resolution = await context_resolver(
                int(author_id),
                governor_id,
                viewer_mode="self",
            )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("governor_dashboard_resolution_failed user_id=%s", author_id)
        resolution = GovernorDashboardResolution(
            state="unavailable",
            options=(),
            reason="account source unavailable",
        )
    await _render_resolution(
        interaction,
        author_id=int(author_id),
        display_name=display_name,
        resolution=resolution,
        context_resolver=context_resolver,
        payload_loader=payload_loader,
        summary_loader=summary_loader,
        timeout=timeout,
    )


async def send_governor_dashboard(
    ctx: discord.ApplicationContext,
    *,
    context_resolver: ContextResolver = resolve_dashboard_context,
    payload_loader: PayloadLoader = build_governor_dashboard_payload,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    timeout: float = _VIEW_TIMEOUT_SECONDS,
) -> None:
    """Open the private governor-first journey from ``/me dashboard``."""
    user = getattr(ctx, "user", None)
    display_name = (
        str(getattr(user, "display_name", "") or "").strip()
        or str(getattr(user, "name", "") or "").strip()
        or "player"
    )
    await show_governor_dashboard_for_interaction(
        ctx.interaction,
        author_id=int(user.id),
        display_name=display_name,
        context_resolver=context_resolver,
        payload_loader=payload_loader,
        summary_loader=summary_loader,
        timeout=timeout,
    )
