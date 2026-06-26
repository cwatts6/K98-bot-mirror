"""Profile preference Discord components for the /me preferences page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
import logging

import discord

from player_self_service import profile_preference_service
from player_self_service.profile_preference_service import (
    ProfileField,
    UserProfilePreference,
)
from player_self_service.service import (
    PlayerSelfServiceSummary,
    build_player_self_service_summary,
)

logger = logging.getLogger(__name__)

SummaryLoader = Callable[[int], Awaitable[PlayerSelfServiceSummary]]


def _profile_message(profile: UserProfilePreference) -> str:
    return "\n".join(profile.summary_lines)


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
            logger.debug("profile_preference_defer_failed", exc_info=True)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("profile_preference_defer_failed", exc_info=True)


async def _refresh_host_page(
    *,
    host_message: object | None,
    interaction: discord.Interaction | None = None,
    author_id: int,
    display_name: str,
    summary_loader: SummaryLoader,
) -> None:
    if host_message is None:
        return
    try:
        summary = await summary_loader(int(author_id))
        from ui.views.player_self_service_views import (
            PAGE_PREFERENCES,
            PlayerSelfServiceView,
            _build_page_response,
            _edit_original_with_image_fallback,
        )

        view = PlayerSelfServiceView(
            author_id=int(author_id),
            display_name=display_name,
            page=PAGE_PREFERENCES,
            summary=summary,
            summary_loader=summary_loader,
        )
        embed, files = await _build_page_response(
            PAGE_PREFERENCES,
            summary,
            display_name=display_name,
        )

        class _MessageTarget:
            async def edit_original_response(self, **kwargs):
                if interaction is not None and hasattr(interaction.followup, "edit_message"):
                    return await interaction.followup.edit_message(host_message.id, **kwargs)
                if hasattr(host_message, "edit"):
                    return await host_message.edit(**kwargs)
                return None

        edited = await _edit_original_with_image_fallback(
            _MessageTarget(),
            page=PAGE_PREFERENCES,
            summary=summary,
            display_name=display_name,
            view=view,
            embed=embed,
            files=files,
        )
        view.set_message_ref(edited or host_message)
    except discord.NotFound:
        logger.debug("profile_preference_host_refresh_message_missing user_id=%s", author_id)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("profile_preference_host_refresh_failed", exc_info=True)


class ProfilePreferenceInputModal(discord.ui.Modal):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        field: ProfileField,
        current_profile: UserProfilePreference,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
    ) -> None:
        self.author_id = int(author_id)
        self.display_name = display_name
        self.field = field
        self.host_message = host_message
        self.summary_loader = summary_loader
        title = {
            "timezone": "Set Timezone",
            "country": "Set Location Country",
            "language": "Set Preferred Language",
        }[field]
        super().__init__(title=title)
        self.value_input = discord.ui.InputText(
            label={
                "timezone": "IANA timezone",
                "country": "Country name or code",
                "language": "Language name or tag",
            }[field],
            placeholder={
                "timezone": "Europe/London",
                "country": "United Kingdom or GB",
                "language": "English or en-GB",
            }[field],
            value={
                "timezone": current_profile.timezone_name or "",
                "country": current_profile.location_country_code or "",
                "language": current_profile.preferred_language_tag or "",
            }[field],
            required=True,
            max_length=100,
        )
        self.add_item(self.value_input)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.user or int(interaction.user.id) != self.author_id:
            await interaction.response.send_message(
                "This profile preference action is not for you.",
                ephemeral=True,
            )
            return
        await _defer_private(interaction)
        result = await profile_preference_service.set_profile_preference(
            self.author_id,
            self.field,
            str(self.value_input.value),
        )
        if not result.ok or result.profile is None:
            await interaction.followup.send(result.message, ephemeral=True)
            return
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        await interaction.followup.send(
            result.message,
            view=ProfilePreferenceManageView(
                author_id=self.author_id,
                display_name=self.display_name,
                profile=result.profile,
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )


class ProfilePreferenceManageView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        display_name: str,
        profile: UserProfilePreference,
        host_message: object | None = None,
        summary_loader: SummaryLoader = build_player_self_service_summary,
        timeout: float = 120,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = int(author_id)
        self.display_name = display_name
        self.profile = profile
        self.host_message = host_message
        self.summary_loader = summary_loader

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private profile preference menu is not for you.",
            ephemeral=True,
        )
        return False

    async def _open_modal(self, interaction: discord.Interaction, field: ProfileField) -> None:
        await interaction.response.send_modal(
            ProfilePreferenceInputModal(
                author_id=self.author_id,
                display_name=self.display_name,
                field=field,
                current_profile=self.profile,
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            )
        )

    async def _clear_field(self, interaction: discord.Interaction, field: ProfileField) -> None:
        await _defer_private(interaction)
        result = await profile_preference_service.clear_profile_preference(
            self.author_id,
            field,
        )
        if not result.ok or result.profile is None:
            await interaction.followup.send(result.message, ephemeral=True)
            return
        self.profile = result.profile
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        await interaction.followup.send(
            result.message,
            view=ProfilePreferenceManageView(
                author_id=self.author_id,
                display_name=self.display_name,
                profile=result.profile,
                host_message=self.host_message,
                summary_loader=self.summary_loader,
            ),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Set Timezone",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:profile:set_timezone",
        row=0,
    )
    async def set_timezone_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._open_modal(interaction, "timezone")

    @discord.ui.button(
        label="Clear Timezone",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_timezone",
        row=0,
    )
    async def clear_timezone_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "timezone")

    @discord.ui.button(
        label="Set Country",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:profile:set_country",
        row=1,
    )
    async def set_country_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._open_modal(interaction, "country")

    @discord.ui.button(
        label="Clear Country",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_country",
        row=1,
    )
    async def clear_country_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "country")

    @discord.ui.button(
        label="Set Language",
        style=discord.ButtonStyle.primary,
        custom_id="me:preference:profile:set_language",
        row=2,
    )
    async def set_language_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._open_modal(interaction, "language")

    @discord.ui.button(
        label="Clear Language",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_language",
        row=2,
    )
    async def clear_language_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "language")
