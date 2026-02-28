# ui/views/location_views.py
"""Location-related UI views extracted from command module."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import re

import discord
from discord.errors import HTTPException, NotFound


class OpenFullSizeView(discord.ui.View):
    def __init__(self, url: str, *, label: str = "Open full size"):
        super().__init__(timeout=None)
        self.add_item(
            discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.link,
                url=url,
            )
        )


class ProfileLinksView(discord.ui.View):
    def __init__(self, card_url: str | None = None):
        super().__init__(timeout=None)
        if card_url:
            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.link, label="Open full card", url=card_url
                )
            )


# injected hooks from Commands.py
_on_profile_selected: Callable[[discord.Interaction, int, bool], Awaitable[None]] = (
    lambda *_a, **_k: None
)
_on_request_refresh: Callable[[discord.Interaction], Awaitable[tuple[bool, str]]] = (
    lambda *_a, **_k: (False, "not configured")
)
_on_wait_for_refresh: Callable[[float], Awaitable[bool]] = lambda *_a, **_k: False
_build_refreshed_location_embed: Callable[[int], Awaitable[discord.Embed | None]] = (
    lambda *_a, **_k: None
)
_check_refresh_permission: Callable[[discord.Interaction], bool] = lambda *_a, **_k: False
_is_refresh_running: Callable[[], bool] = lambda: False
_is_refresh_rate_limited: Callable[[], tuple[bool, int]] = lambda: (False, 0)
_mark_refresh_started: Callable[[], None] = lambda: None
_run_refresh_guarded: Callable[[Callable[[], Awaitable[None]]], Awaitable[None]] = (
    lambda coro: coro()
)
_on_refresh_timeout: Callable[[discord.Interaction], Awaitable[None]] = lambda *_a, **_k: None


def configure_location_views(
    *,
    on_profile_selected: Callable[[discord.Interaction, int, bool], Awaitable[None]],
    on_request_refresh: Callable[[discord.Interaction], Awaitable[tuple[bool, str]]],
    on_wait_for_refresh: Callable[[float], Awaitable[bool]],
    build_refreshed_location_embed: Callable[[int], Awaitable[discord.Embed | None]],
    check_refresh_permission: Callable[[discord.Interaction], bool],
    is_refresh_running: Callable[[], bool],
    is_refresh_rate_limited: Callable[[], tuple[bool, int]],
    mark_refresh_started: Callable[[], None],
    run_refresh_guarded: Callable[[Callable[[], Awaitable[None]]], Awaitable[None]],
    on_refresh_timeout: Callable[[discord.Interaction], Awaitable[None]],
) -> None:
    global _on_profile_selected
    global _on_request_refresh
    global _on_wait_for_refresh
    global _build_refreshed_location_embed
    global _check_refresh_permission
    global _is_refresh_running
    global _is_refresh_rate_limited
    global _mark_refresh_started
    global _run_refresh_guarded
    global _on_refresh_timeout

    _on_profile_selected = on_profile_selected
    _on_request_refresh = on_request_refresh
    _on_wait_for_refresh = on_wait_for_refresh
    _build_refreshed_location_embed = build_refreshed_location_embed
    _check_refresh_permission = check_refresh_permission
    _is_refresh_running = is_refresh_running
    _is_refresh_rate_limited = is_refresh_rate_limited
    _mark_refresh_started = mark_refresh_started
    _run_refresh_guarded = run_refresh_guarded
    _on_refresh_timeout = on_refresh_timeout


class _LocationSelect(discord.ui.Select):
    def __init__(
        self, matches: list[tuple[str, int]], *, ephemeral: bool, author_id: int | None = None
    ):
        self._ephemeral = ephemeral
        self._author_id = author_id
        opts: list[discord.SelectOption] = []
        for item in (matches or [])[:25]:
            name_val = ""
            gid_val = ""
            if isinstance(item, dict):
                name_val = str(item.get("GovernorName") or item.get("name") or "")
                gid_val = str(
                    item.get("GovernorID") or item.get("GovernorId") or item.get("id") or ""
                )
            elif isinstance(item, (list, tuple)):
                if len(item) >= 2:
                    name_val = str(item[0] or "")
                    gid_val = str(item[1] or "")
                elif len(item) == 1:
                    name_val = str(item[0] or "")
            else:
                s = str(item)
                name_val = s
                m = re.search(r"(\d{5,})", s)
                gid_val = m.group(1) if m else ""

            if not gid_val:
                gid_val = name_val[:100]

            opts.append(
                discord.SelectOption(
                    label=name_val[:100],
                    description=(str(gid_val)[:100] if gid_val else ""),
                    value=str(gid_val),
                )
            )

        if not opts:
            opts = [discord.SelectOption(label="No matches available", value="")]

        super().__init__(
            placeholder="Multiple matches — pick one", min_values=1, max_values=1, options=opts
        )

    async def callback(self, interaction: discord.Interaction):
        if self._author_id is not None and interaction.user.id != self._author_id:
            await interaction.response.send_message(
                "❌ Only the requester can use this menu.", ephemeral=True
            )
            return

        gid = int(self.values[0]) if str(self.values[0]).isdigit() else None
        if gid is None:
            await interaction.response.send_message(
                "❌ Could not parse the selected Governor ID.", ephemeral=True
            )
            return

        await _on_profile_selected(interaction, gid, self._ephemeral)


class LocationSelectView(discord.ui.View):
    def __init__(
        self,
        matches: list[tuple[str, int]],
        *,
        ephemeral: bool,
        author_id: int | None = None,
        timeout: int = 60,
    ):
        super().__init__(timeout=timeout)
        self.add_item(_LocationSelect(matches, ephemeral=ephemeral, author_id=author_id))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True


class RefreshLocationView(discord.ui.View):
    def __init__(self, *, target_id: int, ephemeral: bool):
        super().__init__(timeout=None)
        self.target_id = target_id
        self.ephemeral = ephemeral
        self.btn = discord.ui.Button(
            label="🔄 Refresh locations",
            style=discord.ButtonStyle.primary,
            custom_id="kvk:refresh_locations",
        )
        self.btn.callback = self._on_refresh
        self.add_item(self.btn)

    async def _on_refresh(self, interaction: discord.Interaction):
        if not _check_refresh_permission(interaction):
            await interaction.response.send_message("❌ Admin/Leadership only.", ephemeral=True)
            return

        if _is_refresh_running():
            await interaction.response.send_message(
                "⏳ A refresh is already running. Please wait for it to finish.", ephemeral=True
            )
            return

        limited, remain = _is_refresh_rate_limited()
        if limited and remain > 0:
            mins, secs = divmod(remain, 60)
            await interaction.response.send_message(
                f"🕒 Location refresh is limited to **once per hour**. Try again in **{mins}m {secs}s**.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        async def _do_refresh():
            _mark_refresh_started()
            ok, err = await _on_request_refresh(interaction)
            if not ok:
                await interaction.followup.send(
                    f"❌ Couldn’t trigger refresh: `{err}`", ephemeral=True
                )
                return

            await interaction.followup.send(
                "📡 Refresh requested. This usually takes ~5–15 minutes. I’ll update this when it’s done.",
                ephemeral=True,
            )

            done = await _on_wait_for_refresh(30 * 60)
            if not done:
                await _on_refresh_timeout(interaction)
                await interaction.followup.send(
                    "⚠️ No update received after 30 minutes. Please try again later.",
                    ephemeral=True,
                )
                return

            embed = await _build_refreshed_location_embed(self.target_id)
            if not embed:
                await interaction.followup.send(
                    f"❌ GovernorID `{self.target_id}` not found after refresh.", ephemeral=True
                )
                return

            try:
                await interaction.message.edit(embed=embed, view=self)
            except (NotFound, HTTPException):
                await interaction.followup.send(embed=embed, ephemeral=self.ephemeral)

        await _run_refresh_guarded(_do_refresh)


__all__ = [
    "LocationSelectView",
    "OpenFullSizeView",
    "ProfileLinksView",
    "RefreshLocationView",
    "_LocationSelect",
    "configure_location_views",
]
