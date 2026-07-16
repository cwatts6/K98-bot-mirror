"""Accounts-owned Update VIP journey for linked governors."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging
from math import ceil

import discord

from inventory import profile_service, reporting_service
from inventory.models import InventoryGovernorProfile, RegisteredGovernor
from inventory.vip_levels import VIP_LABELS, InventoryVipLevel, normalize_vip_level
from player_self_service import account_service
from player_self_service.service import PlayerSelfServiceSummary, build_player_self_service_summary

logger = logging.getLogger(__name__)

SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]
GovernorLoader = Callable[[int], Awaitable[list[RegisteredGovernor]]]
ProfileLoader = Callable[[int], Awaitable[InventoryGovernorProfile]]
_PAGE_SIZE = 25
_VIP_LEVELS = (
    InventoryVipLevel.UNKNOWN,
    InventoryVipLevel.VIP_14_OR_LESS,
    InventoryVipLevel.VIP_15,
    InventoryVipLevel.VIP_16,
    InventoryVipLevel.VIP_17,
    InventoryVipLevel.VIP_18,
    InventoryVipLevel.VIP_19,
    InventoryVipLevel.SVIP,
)


class _VipJourneyState:
    def __init__(self) -> None:
        self.generation = 0
        self.expired = False
        self.lock = asyncio.Lock()

    def advance(self) -> int:
        self.generation += 1
        self.expired = False
        return self.generation

    def current(self, generation: int) -> bool:
        return not self.expired and int(generation) == self.generation


async def _defer_private(interaction: discord.Interaction) -> None:
    try:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
    except TypeError:
        try:
            if not interaction.response.is_done():
                await interaction.response.defer()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("player_self_service_account_vip_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("player_self_service_account_vip_defer_failed", exc_info=True)


class _AccountVipView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        governors: tuple[RegisteredGovernor, ...],
        host_message: object | None,
        summary_loader: SummaryLoader,
        profile_loader: ProfileLoader,
        state: _VipJourneyState,
        generation: int,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout, disable_on_timeout=False)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.governors = governors
        self.governors_by_id = {int(item.governor_id): item for item in governors}
        self.host_message = host_message
        self.summary_loader = summary_loader
        self.profile_loader = profile_loader
        self.state = state
        self.generation = int(generation)
        self._message_ref: object | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user or int(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This private VIP editor is not for you.", ephemeral=True
            )
            return False
        if not self.state.current(self.generation):
            await interaction.response.send_message(
                "This VIP editor was superseded. Use the current private window.",
                ephemeral=True,
            )
            return False
        return True

    def _common(self) -> dict[str, object]:
        return {
            "author_id": self.author_id,
            "display_name": self.display_name,
            "governors": self.governors,
            "host_message": self.host_message,
            "summary_loader": self.summary_loader,
            "profile_loader": self.profile_loader,
            "state": self.state,
            "generation": self.state.advance(),
            "timeout": self.timeout or 120,
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
            await interaction.response.edit_message(content=content, embed=None, view=view)
        else:
            await interaction.edit_original_response(content=content, embed=None, view=view)
        if isinstance(view, _AccountVipView):
            view._message_ref = getattr(interaction, "message", None)

    async def _return_to_account_tasks(
        self,
        interaction: discord.Interaction,
        *,
        message: str,
    ) -> None:
        state = await account_service.build_account_centre_state(self.author_id)
        from ui.views.player_self_service_account_views import AccountManageView

        view = AccountManageView(
            author_id=self.author_id,
            display_name=self.display_name,
            state=state,
            host_message=self.host_message,
            summary_loader=self.summary_loader,
            timeout=self.timeout or 120,
        )
        self.stop()
        if not interaction.response.is_done():
            await interaction.response.edit_message(content=message, embed=None, view=view)
        else:
            await interaction.edit_original_response(content=message, embed=None, view=view)

    async def on_timeout(self) -> None:
        if self.state.current(self.generation):
            self.state.expired = True
        for child in self.children:
            child.disabled = True
        try:
            message = self._message_ref or getattr(self, "message", None)
            if message is not None and hasattr(message, "edit"):
                await message.edit(
                    content="This private VIP editor has expired. Reopen Manage Accounts.",
                    view=self,
                )
        except Exception:
            logger.debug("account_vip_timeout_edit_failed", exc_info=True)
        await super().on_timeout()


class _GovernorSelect(discord.ui.Select):
    def __init__(self, *, governors: tuple[RegisteredGovernor, ...], page: int) -> None:
        total_pages = max(1, ceil(len(governors) / _PAGE_SIZE))
        page = min(max(0, page), total_pages - 1)
        start = page * _PAGE_SIZE
        options = [
            discord.SelectOption(
                label=(item.governor_name or str(item.governor_id))[:100],
                value=str(item.governor_id),
                description=f"{item.account_type} • Governor ID {item.governor_id}"[:100],
            )
            for item in governors[start : start + _PAGE_SIZE]
        ]
        super().__init__(
            placeholder=(
                f"Choose linked governor ({page + 1}/{total_pages})"
                if total_pages > 1
                else "Choose linked governor"
            ),
            options=options,
            min_values=1,
            max_values=1,
            custom_id="me:account:vip:governor",
            row=0,
        )
        self.allowed_ids = {int(option.value) for option in options}

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccountVipGovernorView):
            await interaction.response.send_message(
                "This governor selector is unavailable.", ephemeral=True
            )
            return
        governor_id = int(self.values[0])
        if governor_id not in self.allowed_ids or governor_id not in view.governors_by_id:
            await interaction.response.send_message(
                "That governor is not available on this page.", ephemeral=True
            )
            return
        await view.select_governor(interaction, governor_id)


class AccountVipGovernorView(_AccountVipView):
    def __init__(self, *, page: int = 0, **kwargs) -> None:
        self.page = max(0, int(page))
        super().__init__(**kwargs)
        self.total_pages = max(1, ceil(len(self.governors) / _PAGE_SIZE))
        self.page = min(self.page, self.total_pages - 1)
        self.add_item(_GovernorSelect(governors=self.governors, page=self.page))
        self.previous_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= self.total_pages - 1

    async def select_governor(self, interaction: discord.Interaction, governor_id: int) -> None:
        if int(governor_id) not in self.governors_by_id:
            await interaction.response.send_message(
                "That governor is no longer available in this VIP editor.",
                ephemeral=True,
            )
            return
        await _defer_private(interaction)
        try:
            profile = await self.profile_loader(int(governor_id))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "account_vip_profile_load_failed user_id=%s governor_id=%s",
                self.author_id,
                governor_id,
            )
            await interaction.followup.send(
                "VIP details are temporarily unavailable. Choose the governor again in a moment.",
                ephemeral=True,
            )
            return
        governor = self.governors_by_id[int(governor_id)]
        view = AccountVipEditView(governor=governor, profile=profile, **self._common())
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Previous",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:vip:previous",
        row=1,
    )
    async def previous_button(self, _button, interaction: discord.Interaction) -> None:
        view = AccountVipGovernorView(page=self.page - 1, **self._common())
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Next",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:vip:next",
        row=1,
    )
    async def next_button(self, _button, interaction: discord.Interaction) -> None:
        view = AccountVipGovernorView(page=self.page + 1, **self._common())
        await self._replace(interaction, content=view.content, view=view)

    @discord.ui.button(
        label="Back to Account tasks",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:vip:cancel_governor",
        row=2,
    )
    async def cancel_button(self, _button, interaction: discord.Interaction) -> None:
        await self._return_to_account_tasks(interaction, message="Choose an account task.")

    @property
    def content(self) -> str:
        return (
            "**Update VIP**\nChoose the linked governor whose VIP level you want to update.\n"
            f"Page {self.page + 1} of {self.total_pages}."
        )


class _VipLevelSelect(discord.ui.Select):
    def __init__(self, initial: InventoryVipLevel | None) -> None:
        super().__init__(
            placeholder="Select VIP level",
            options=[
                discord.SelectOption(
                    label=VIP_LABELS[level],
                    value=level.value,
                    default=initial == level,
                )
                for level in _VIP_LEVELS
            ],
            min_values=1,
            max_values=1,
            custom_id="me:account:vip:level",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, AccountVipEditView):
            await interaction.response.send_message(
                "This VIP selector is unavailable.", ephemeral=True
            )
            return
        try:
            selected = InventoryVipLevel(self.values[0])
        except ValueError:
            await interaction.response.send_message(
                "That VIP level is not supported.", ephemeral=True
            )
            return
        view.selected_level = selected
        for option in self.options:
            option.default = option.value == selected.value
        await interaction.response.edit_message(content=view.content, view=view)


class AccountVipEditView(_AccountVipView):
    def __init__(
        self,
        *,
        governor: RegisteredGovernor,
        profile: InventoryGovernorProfile,
        **kwargs,
    ) -> None:
        self.governor = governor
        self.profile = profile
        self.selected_level = (
            normalize_vip_level(profile.vip_level_code) if profile.vip_level_code else None
        )
        self.completed = False
        super().__init__(**kwargs)
        self.add_item(_VipLevelSelect(self.selected_level))

    @property
    def content(self) -> str:
        current = self.profile.vip_level_label
        selected = (
            VIP_LABELS[self.selected_level] if self.selected_level is not None else "Choose a level"
        )
        return (
            f"**Update VIP**\n{self.governor.governor_name} (`{self.governor.governor_id}`)"
            f" • {self.governor.account_type}\nCurrent: **{current}**\nSelected: **{selected}**"
        )

    @discord.ui.button(
        label="Save VIP",
        style=discord.ButtonStyle.success,
        custom_id="me:account:vip:save",
        row=1,
    )
    async def save_button(self, _button, interaction: discord.Interaction) -> None:
        if self.selected_level is None:
            await interaction.response.send_message("Choose a VIP level first.", ephemeral=True)
            return
        await _defer_private(interaction)
        if self.completed or self.state.lock.locked():
            await interaction.followup.send(
                "This VIP save is already being processed.", ephemeral=True
            )
            return
        async with self.state.lock:
            if not self.state.current(self.generation):
                await interaction.followup.send("This VIP editor was superseded.", ephemeral=True)
                return
            self.completed = True
            try:
                saved = await profile_service.update_inventory_vip(
                    discord_user_id=self.author_id,
                    governor_id=int(self.governor.governor_id),
                    vip_level_code=self.selected_level.value,
                    discord_user=getattr(interaction, "user", None),
                )
            except PermissionError as exc:
                self.completed = False
                await interaction.followup.send(str(exc), ephemeral=True)
                return
            except asyncio.CancelledError:
                self.completed = False
                raise
            except Exception:
                self.completed = False
                logger.exception(
                    "account_vip_save_failed user_id=%s governor_id=%s",
                    self.author_id,
                    self.governor.governor_id,
                )
                await interaction.followup.send(
                    "VIP could not be saved. Your previous setting is unchanged.", ephemeral=True
                )
                return

        from ui.views.player_self_service_account_views import _refresh_host_page
        from ui.views.player_self_service_views import PAGE_ACCOUNTS

        refreshed = await _refresh_host_page(
            host_message=self.host_message,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
            page=PAGE_ACCOUNTS,
            user=getattr(interaction, "user", None),
        )
        await self._return_to_account_tasks(
            interaction,
            message=(
                f"VIP saved for {self.governor.governor_name} "
                f"(`{self.governor.governor_id}`): **{saved.vip_level_label}**.\n\n"
                + (
                    "The Accounts card has been refreshed."
                    if refreshed
                    else "Reopen Account Summary to see the saved VIP value."
                )
                + " Choose another account task if needed."
            ),
        )

    @discord.ui.button(
        label="Back",
        style=discord.ButtonStyle.secondary,
        custom_id="me:account:vip:back",
        row=1,
    )
    async def back_button(self, _button, interaction: discord.Interaction) -> None:
        if len(self.governors) == 1:
            await self._return_to_account_tasks(interaction, message="VIP update cancelled.")
            return
        view = AccountVipGovernorView(page=0, **self._common())
        await self._replace(interaction, content=view.content, view=view)


async def show_account_vip_update(
    interaction: discord.Interaction,
    *,
    author_id: int,
    display_name: str,
    host_message: object | None,
    summary_loader: SummaryLoader = build_player_self_service_summary,
    governor_loader: GovernorLoader = reporting_service.get_registered_governors_for_user,
    profile_loader: ProfileLoader = profile_service.fetch_inventory_profile,
    timeout: float = 120,
) -> None:
    try:
        governors = tuple(await governor_loader(int(author_id)))
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("account_vip_governor_load_failed user_id=%s", author_id)
        await interaction.edit_original_response(
            content="Linked governors are temporarily unavailable. Reopen Manage Accounts and try again.",
            embed=None,
            view=None,
        )
        return
    if not governors:
        state = await account_service.build_account_centre_state(int(author_id))
        from ui.views.player_self_service_account_views import AccountManageView

        view = AccountManageView(
            author_id=author_id,
            display_name=display_name,
            state=state,
            host_message=host_message,
            summary_loader=summary_loader,
            timeout=timeout,
        )
        await interaction.edit_original_response(
            content=(
                "No linked governors are available for VIP editing. "
                "Use Register account first, then reopen Update VIP."
            ),
            embed=None,
            view=view,
        )
        return

    state = _VipJourneyState()
    generation = state.advance()
    common = {
        "author_id": int(author_id),
        "display_name": display_name,
        "governors": governors,
        "host_message": host_message,
        "summary_loader": summary_loader,
        "profile_loader": profile_loader,
        "state": state,
        "generation": generation,
        "timeout": timeout,
    }
    if len(governors) == 1:
        governor = governors[0]
        try:
            profile = await profile_loader(int(governor.governor_id))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "account_vip_profile_load_failed user_id=%s governor_id=%s",
                author_id,
                governor.governor_id,
            )
            await interaction.edit_original_response(
                content="VIP details are temporarily unavailable. Reopen Manage Accounts and try again.",
                embed=None,
                view=None,
            )
            return
        view: _AccountVipView = AccountVipEditView(
            governor=governor,
            profile=profile,
            **common,
        )
    else:
        view = AccountVipGovernorView(page=0, **common)
    await interaction.edit_original_response(content=view.content, embed=None, view=view)
    view._message_ref = getattr(interaction, "message", None)
