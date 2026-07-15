"""Profile preference Discord components for the /me preferences page."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class _ProfileChoice:
    label: str
    value: str
    description: str = ""


_TIMEZONE_CHOICES: tuple[_ProfileChoice, ...] = (
    _ProfileChoice("UTC", "UTC", "Coordinated Universal Time"),
    _ProfileChoice("United Kingdom", "Europe/London", "Europe/London"),
    _ProfileChoice("Central Europe", "Europe/Berlin", "Germany, Italy, Netherlands, Poland"),
    _ProfileChoice("France / Spain", "Europe/Paris", "Europe/Paris"),
    _ProfileChoice("Eastern Europe", "Europe/Kyiv", "Ukraine and nearby regions"),
    _ProfileChoice("Turkey", "Europe/Istanbul", "Europe/Istanbul"),
    _ProfileChoice("Dubai / Gulf", "Asia/Dubai", "Asia/Dubai"),
    _ProfileChoice("India", "Asia/Kolkata", "Asia/Kolkata"),
    _ProfileChoice("Thailand / Vietnam", "Asia/Bangkok", "Asia/Bangkok"),
    _ProfileChoice("Indonesia West", "Asia/Jakarta", "Asia/Jakarta"),
    _ProfileChoice("Philippines", "Asia/Manila", "Asia/Manila"),
    _ProfileChoice("Singapore / Malaysia", "Asia/Singapore", "Asia/Singapore"),
    _ProfileChoice("China", "Asia/Shanghai", "Asia/Shanghai"),
    _ProfileChoice("Japan", "Asia/Tokyo", "Asia/Tokyo"),
    _ProfileChoice("Australia East", "Australia/Sydney", "Australia/Sydney"),
    _ProfileChoice("New Zealand", "Pacific/Auckland", "Pacific/Auckland"),
    _ProfileChoice("US Eastern", "America/New_York", "America/New_York"),
    _ProfileChoice("US Central", "America/Chicago", "America/Chicago"),
    _ProfileChoice("US Mountain", "America/Denver", "America/Denver"),
    _ProfileChoice("US Pacific", "America/Los_Angeles", "America/Los_Angeles"),
    _ProfileChoice("Brazil", "America/Sao_Paulo", "America/Sao_Paulo"),
    _ProfileChoice("Mexico City", "America/Mexico_City", "America/Mexico_City"),
    _ProfileChoice("South Africa", "Africa/Johannesburg", "Africa/Johannesburg"),
    _ProfileChoice("Egypt", "Africa/Cairo", "Africa/Cairo"),
)

_COUNTRY_CHOICES: tuple[_ProfileChoice, ...] = (
    _ProfileChoice("United Kingdom (GB)", "GB"),
    _ProfileChoice("United States (US)", "US"),
    _ProfileChoice("Germany (DE)", "DE"),
    _ProfileChoice("France (FR)", "FR"),
    _ProfileChoice("Spain (ES)", "ES"),
    _ProfileChoice("Italy (IT)", "IT"),
    _ProfileChoice("Netherlands (NL)", "NL"),
    _ProfileChoice("Poland (PL)", "PL"),
    _ProfileChoice("Ukraine (UA)", "UA"),
    _ProfileChoice("Romania (RO)", "RO"),
    _ProfileChoice("Turkey (TR)", "TR"),
    _ProfileChoice("Brazil (BR)", "BR"),
    _ProfileChoice("Mexico (MX)", "MX"),
    _ProfileChoice("Canada (CA)", "CA"),
    _ProfileChoice("Australia (AU)", "AU"),
    _ProfileChoice("New Zealand (NZ)", "NZ"),
    _ProfileChoice("India (IN)", "IN"),
    _ProfileChoice("Indonesia (ID)", "ID"),
    _ProfileChoice("Philippines (PH)", "PH"),
    _ProfileChoice("Singapore (SG)", "SG"),
    _ProfileChoice("Malaysia (MY)", "MY"),
    _ProfileChoice("Japan (JP)", "JP"),
    _ProfileChoice("South Korea (KR)", "KR"),
    _ProfileChoice("South Africa (ZA)", "ZA"),
)

_LANGUAGE_CHOICES: tuple[_ProfileChoice, ...] = (
    _ProfileChoice("English", "en"),
    _ProfileChoice("English (UK)", "en-GB"),
    _ProfileChoice("English (US)", "en-US"),
    _ProfileChoice("German / Deutsch", "de"),
    _ProfileChoice("French / Francais", "fr"),
    _ProfileChoice("Spanish / Espanol", "es"),
    _ProfileChoice("Portuguese", "pt"),
    _ProfileChoice("Portuguese (Brazil)", "pt-BR"),
    _ProfileChoice("Italian", "it"),
    _ProfileChoice("Dutch", "nl"),
    _ProfileChoice("Polish", "pl"),
    _ProfileChoice("Ukrainian", "uk"),
    _ProfileChoice("Turkish", "tr"),
    _ProfileChoice("Russian", "ru"),
    _ProfileChoice("Arabic", "ar"),
    _ProfileChoice("Hindi", "hi"),
    _ProfileChoice("Indonesian", "id"),
    _ProfileChoice("Malay", "ms"),
    _ProfileChoice("Thai", "th"),
    _ProfileChoice("Vietnamese", "vi"),
    _ProfileChoice("Chinese", "zh"),
    _ProfileChoice("Chinese (Simplified)", "zh-CN"),
    _ProfileChoice("Chinese (Traditional)", "zh-TW"),
    _ProfileChoice("Japanese", "ja"),
    _ProfileChoice("Korean", "ko"),
)

_PROFILE_CHOICES: dict[ProfileField, tuple[_ProfileChoice, ...]] = {
    "timezone": _TIMEZONE_CHOICES,
    "country": _COUNTRY_CHOICES,
    "language": _LANGUAGE_CHOICES,
}


def _current_value(field: ProfileField, profile: UserProfilePreference) -> str | None:
    if field == "timezone":
        return profile.timezone_name
    if field == "country":
        return profile.location_country_code
    return profile.preferred_language_tag


def _current_label(field: ProfileField, value: str) -> str:
    if field == "country":
        return profile_preference_service.country_display_name(value)
    if field == "language":
        return profile_preference_service.language_display_name(value)
    return value


def _choice_options(
    field: ProfileField,
    profile: UserProfilePreference,
) -> list[discord.SelectOption]:
    current = _current_value(field, profile)
    choices = list(_PROFILE_CHOICES[field])
    values = {choice.value for choice in choices}
    if current and current not in values:
        choices.insert(
            0,
            _ProfileChoice(
                label=_current_label(field, current),
                value=current,
                description="Current saved value",
            ),
        )
    return [
        discord.SelectOption(
            label=choice.label,
            value=choice.value,
            description=choice.description or None,
            default=current == choice.value,
        )
        for choice in choices[:25]
    ]


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


class ProfilePreferenceSelect(discord.ui.Select):
    def __init__(
        self,
        *,
        field: ProfileField,
        profile: UserProfilePreference,
        row: int,
    ) -> None:
        self.field = field
        super().__init__(
            placeholder={
                "timezone": "Choose timezone",
                "country": "Choose location country",
                "language": "Choose preferred language",
            }[field],
            min_values=1,
            max_values=1,
            options=_choice_options(field, profile),
            custom_id=f"me:preference:profile:select_{field}",
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if not isinstance(view, ProfilePreferenceManageView):
            await interaction.response.send_message(
                "This profile preference selector is temporarily unavailable.",
                ephemeral=True,
            )
            return
        await view._set_field(interaction, self.field, str(self.values[0]))


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
        self.add_item(ProfilePreferenceSelect(field="timezone", profile=profile, row=0))
        self.add_item(ProfilePreferenceSelect(field="country", profile=profile, row=1))
        self.add_item(ProfilePreferenceSelect(field="language", profile=profile, row=2))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and int(interaction.user.id) == self.author_id:
            return True
        await interaction.response.send_message(
            "This private profile preference menu is not for you.",
            ephemeral=True,
        )
        return False

    async def _replace_manager_message(
        self,
        interaction: discord.Interaction,
        *,
        message: str,
        profile: UserProfilePreference,
    ) -> None:
        refreshed_view = ProfilePreferenceManageView(
            author_id=self.author_id,
            display_name=self.display_name,
            profile=profile,
            host_message=self.host_message,
            summary_loader=self.summary_loader,
        )
        try:
            await interaction.edit_original_response(
                content=message,
                view=refreshed_view,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("profile_preference_manager_replace_failed", exc_info=True)
            await interaction.followup.send(
                message,
                view=refreshed_view,
                ephemeral=True,
            )

    async def _set_field(
        self,
        interaction: discord.Interaction,
        field: ProfileField,
        value: str,
    ) -> None:
        await _defer_private(interaction)
        result = await profile_preference_service.set_profile_preference(
            self.author_id,
            field,
            value,
        )
        if not result.ok or result.profile is None:
            await self._replace_manager_message(
                interaction,
                message=result.message,
                profile=self.profile,
            )
            return
        self.profile = result.profile
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        await self._replace_manager_message(
            interaction,
            message=result.message,
            profile=result.profile,
        )

    async def _clear_field(self, interaction: discord.Interaction, field: ProfileField) -> None:
        await _defer_private(interaction)
        result = await profile_preference_service.clear_profile_preference(
            self.author_id,
            field,
        )
        if not result.ok or result.profile is None:
            await self._replace_manager_message(
                interaction,
                message=result.message,
                profile=self.profile,
            )
            return
        self.profile = result.profile
        await _refresh_host_page(
            host_message=self.host_message,
            interaction=interaction,
            author_id=self.author_id,
            display_name=self.display_name,
            summary_loader=self.summary_loader,
        )
        await self._replace_manager_message(
            interaction,
            message=result.message,
            profile=result.profile,
        )

    @discord.ui.button(
        label="Clear Timezone",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_timezone",
        row=3,
    )
    async def clear_timezone_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "timezone")

    @discord.ui.button(
        label="Clear Country",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_country",
        row=3,
    )
    async def clear_country_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "country")

    @discord.ui.button(
        label="Clear Language",
        style=discord.ButtonStyle.secondary,
        custom_id="me:preference:profile:clear_language",
        row=3,
    )
    async def clear_language_button(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        await self._clear_field(interaction, "language")
