from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
import logging

import discord

from embed_utils import LocalTimeToggleView

logger = logging.getLogger(__name__)


@dataclass
class ArkCreateMatchSelection:
    alliance: str | None = None
    ark_weekend_date: date | None = None
    match_day: str | None = None  # "Saturday" / "Sunday"
    match_time_utc: str | None = None  # "HH:MM"


OnConfirm = Callable[[discord.Interaction, ArkCreateMatchSelection], object]
OnCancel = Callable[[discord.Interaction], object]


class CreateArkMatchView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        alliances: list[str],
        ark_weekend_dates: list[date],
        allowed_days: list[str],
        allowed_times_by_day: dict[str, list[str]],
        on_confirm: OnConfirm,
        on_cancel: OnCancel | None = None,
        timeout: float = 300.0,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.allowed_times_by_day = allowed_times_by_day
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.selection = ArkCreateMatchSelection()
        self.prompt_text = "Select alliance, weekend, day, and time for the Ark match:"

        self.alliance_select = discord.ui.Select(
            placeholder="Select alliance",
            options=[discord.SelectOption(label=a, value=a) for a in alliances],
            min_values=1,
            max_values=1,
        )
        self.alliance_select.callback = self._on_alliance
        self.add_item(self.alliance_select)

        self.weekend_select = discord.ui.Select(
            placeholder="Select Ark weekend (Saturday date)",
            options=[
                discord.SelectOption(
                    label=wd.strftime("%Y-%m-%d"),
                    value=wd.strftime("%Y-%m-%d"),
                )
                for wd in ark_weekend_dates
            ],
            min_values=1,
            max_values=1,
        )
        self.weekend_select.callback = self._on_weekend
        self.add_item(self.weekend_select)

        self.day_select = discord.ui.Select(
            placeholder="Select match day",
            options=[discord.SelectOption(label=d, value=d) for d in allowed_days],
            min_values=1,
            max_values=1,
        )
        self.day_select.callback = self._on_day
        self.add_item(self.day_select)

        self.time_select = discord.ui.Select(
            placeholder="Select match time (UTC)",
            options=[
                discord.SelectOption(
                    label="Select a match day first",
                    value="__placeholder__",
                )
            ],
            min_values=1,
            max_values=1,
            disabled=True,
        )
        self.time_select.callback = self._on_time
        self.add_item(self.time_select)

        self.confirm_btn = discord.ui.Button(
            label="Create Match", style=discord.ButtonStyle.success, disabled=True
        )
        self.confirm_btn.callback = self._on_confirm
        self.add_item(self.confirm_btn)

        self.cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        self.cancel_btn.callback = self._on_cancel
        self.add_item(self.cancel_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This setup flow isn’t for you.", ephemeral=True
            )
            return False
        return True

    def _refresh_confirm_state(self) -> None:
        s = self.selection
        self.confirm_btn.disabled = not all(
            [s.alliance, s.ark_weekend_date, s.match_day, s.match_time_utc]
        )

    def _refresh_time_options(self) -> None:
        day = self.selection.match_day
        times = self.allowed_times_by_day.get(day or "", [])
        current = self.selection.match_time_utc

        if times:
            self.time_select.options = [
                discord.SelectOption(
                    label=f"{t} UTC",
                    value=t,
                    default=(t == current),
                )
                for t in times
            ]
            self.time_select.disabled = False
        else:
            self.time_select.options = [
                discord.SelectOption(
                    label="Select a match day first",
                    value="__placeholder__",
                    default=True,
                )
            ]
            self.time_select.disabled = True

    def _selection_summary(self) -> str:
        s = self.selection
        alliance = s.alliance or "—"
        weekend = s.ark_weekend_date.isoformat() if s.ark_weekend_date else "—"
        day = s.match_day or "—"
        time_val = f"{s.match_time_utc} UTC" if s.match_time_utc else "—"
        return f"{self.prompt_text}\n**Selected:** {alliance} • {weekend} • {day} • {time_val}"

    async def _on_alliance(self, interaction: discord.Interaction):
        self.selection.alliance = self.alliance_select.values[0]
        for opt in self.alliance_select.options:
            opt.default = opt.value == self.selection.alliance
        self._refresh_confirm_state()
        await interaction.response.edit_message(content=self._selection_summary(), view=self)

    async def _on_weekend(self, interaction: discord.Interaction):
        raw = self.weekend_select.values[0]
        self.selection.ark_weekend_date = date.fromisoformat(raw)
        for opt in self.weekend_select.options:
            opt.default = opt.value == raw
        self._refresh_confirm_state()
        await interaction.response.edit_message(content=self._selection_summary(), view=self)

    async def _on_day(self, interaction: discord.Interaction):
        self.selection.match_day = self.day_select.values[0]
        self.selection.match_time_utc = None
        for opt in self.day_select.options:
            opt.default = opt.value == self.selection.match_day
        self._refresh_time_options()
        self._refresh_confirm_state()
        await interaction.response.edit_message(content=self._selection_summary(), view=self)

    async def _on_time(self, interaction: discord.Interaction):
        self.selection.match_time_utc = self.time_select.values[0]
        self._refresh_time_options()
        self._refresh_confirm_state()
        await interaction.response.edit_message(content=self._selection_summary(), view=self)

    async def _on_confirm(self, interaction: discord.Interaction):
        try:
            await self.on_confirm(interaction, self.selection)
        except Exception:
            logger.exception("[ARK] Create match confirm handler failed")
            await interaction.response.send_message(
                "❌ Failed to create the match. Please try again.", ephemeral=True
            )

    async def _on_cancel(self, interaction: discord.Interaction):
        if self.on_cancel:
            await self.on_cancel(interaction)
            return
        await interaction.response.edit_message(content="Cancelled.", view=None)


@dataclass
class ArkAmendMatchSelection:
    match_id: int | None = None
    alliance: str | None = None
    match_day: str | None = None
    match_time_utc: str | None = None
    notes: str | None = None


AmendOnConfirm = Callable[[discord.Interaction, ArkAmendMatchSelection], object]


class ArkNotesModal(discord.ui.Modal):
    def __init__(self, *, author_id: int, current_notes: str | None, on_submit) -> None:
        super().__init__(title="Ark Match Notes")
        self.author_id = author_id
        self._on_submit = on_submit

        self.add_item(
            discord.ui.InputText(
                label="Notes (optional)",
                placeholder="Enter any notes for this match (leave blank to clear).",
                value=current_notes or "",
                style=discord.InputTextStyle.long,
                max_length=2000,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return
        raw = (self.children[0].value or "").strip()
        await self._on_submit(interaction, raw if raw else None)


class AmendArkMatchView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        matches: list[dict],
        alliances: list[str],
        allowed_days: list[str],
        allowed_times_by_day: dict[str, list[str]],
        match_alliance_change_allowed: dict[int, bool],
        notes_templates: list[str] | None,
        on_confirm: AmendOnConfirm,
        on_cancel: OnCancel | None = None,
        timeout: float = 300.0,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.allowed_times_by_day = allowed_times_by_day
        self.match_alliance_change_allowed = match_alliance_change_allowed
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.notes_templates = [n for n in (notes_templates or []) if n]

        self.matches_by_id = {int(m["MatchId"]): m for m in matches}
        self.selection = ArkAmendMatchSelection()

        self.match_select = discord.ui.Select(
            placeholder="Select match to amend",
            options=[self._match_option(m) for m in matches][:25],
            min_values=1,
            max_values=1,
        )
        self.match_select.callback = self._on_match
        self.add_item(self.match_select)

        self.alliance_select = discord.ui.Select(
            placeholder="Select alliance (optional)",
            options=[discord.SelectOption(label=a, value=a) for a in alliances][:25],
            min_values=1,
            max_values=1,
            disabled=True,
        )
        self.alliance_select.callback = self._on_alliance
        self.add_item(self.alliance_select)

        self.day_select = discord.ui.Select(
            placeholder="Select match day",
            options=[discord.SelectOption(label=d, value=d) for d in allowed_days],
            min_values=1,
            max_values=1,
            disabled=True,
        )
        self.day_select.callback = self._on_day
        self.add_item(self.day_select)

        self.time_select = discord.ui.Select(
            placeholder="Select match time (UTC)",
            options=[],
            min_values=1,
            max_values=1,
            disabled=True,
        )
        self.time_select.callback = self._on_time
        self.add_item(self.time_select)

        if self.notes_templates:
            options = [
                discord.SelectOption(label=note[:100], value=note) for note in self.notes_templates
            ]
            options.append(discord.SelectOption(label="Custom…", value="__custom__"))
            self.notes_select = discord.ui.Select(
                placeholder="Select notes template (optional)",
                options=options[:25],
                min_values=1,
                max_values=1,
            )
            self.notes_select.callback = self._on_notes_template
            self.add_item(self.notes_select)

        self.notes_btn = discord.ui.Button(
            label="Edit Notes",
            style=discord.ButtonStyle.secondary,
            disabled=True,
        )
        self.notes_btn.callback = self._on_notes
        self.add_item(self.notes_btn)

        self.confirm_btn = discord.ui.Button(
            label="Apply Changes", style=discord.ButtonStyle.success, disabled=True
        )
        self.confirm_btn.callback = self._on_confirm
        self.add_item(self.confirm_btn)

        self.cancel_btn = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.secondary)
        self.cancel_btn.callback = self._on_cancel
        self.add_item(self.cancel_btn)

    @staticmethod
    def _match_option(match: dict) -> discord.SelectOption:
        alliance = (match.get("Alliance") or "").strip()
        weekend = match.get("ArkWeekendDate")
        day = match.get("MatchDay") or ""
        match_time = match.get("MatchTimeUtc")
        time_str = (
            match_time.strftime("%H:%M") if hasattr(match_time, "strftime") else str(match_time)
        )
        weekend_str = weekend.strftime("%Y-%m-%d") if hasattr(weekend, "strftime") else str(weekend)
        label = f"{alliance} — {weekend_str} {day} {time_str} UTC"
        return discord.SelectOption(label=label[:100], value=str(match["MatchId"]))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This setup flow isn’t for you.", ephemeral=True
            )
            return False
        return True

    def _refresh_confirm_state(self) -> None:
        s = self.selection
        self.confirm_btn.disabled = not all([s.match_id, s.match_day, s.match_time_utc])

    def _refresh_time_options(self) -> None:
        day = self.selection.match_day
        times = self.allowed_times_by_day.get(day or "", [])
        current = self.selection.match_time_utc
        self.time_select.options = [
            discord.SelectOption(
                label=f"{t} UTC",
                value=t,
                default=(t == current),
            )
            for t in times
        ]
        self.time_select.disabled = not bool(times)

    def _refresh_alliance_options(self, current_alliance: str, enabled: bool) -> None:
        self.alliance_select.options = [
            discord.SelectOption(
                label=a,
                value=a,
                default=(a == current_alliance),
            )
            for a in [o.label for o in self.alliance_select.options]  # keep order
        ]
        self.alliance_select.disabled = not enabled

    async def _on_match(self, interaction: discord.Interaction):
        match_id = int(self.match_select.values[0])
        match = self.matches_by_id.get(match_id)
        if not match:
            await interaction.response.send_message("❌ Selected match not found.", ephemeral=True)
            return

        self.selection.match_id = match_id
        self.selection.alliance = (match.get("Alliance") or "").strip()
        self.selection.match_day = (
            "Saturday" if (match.get("MatchDay") or "").startswith("Sat") else "Sunday"
        )
        match_time = match.get("MatchTimeUtc")
        self.selection.match_time_utc = (
            match_time.strftime("%H:%M") if hasattr(match_time, "strftime") else str(match_time)
        )
        self.selection.notes = match.get("Notes")

        allow_change = self.match_alliance_change_allowed.get(match_id, False)
        self.alliance_select.disabled = not allow_change
        if allow_change:
            for opt in self.alliance_select.options:
                opt.default = opt.value == self.selection.alliance

        self.day_select.disabled = False
        self.time_select.disabled = False
        self.notes_btn.disabled = False
        self._refresh_time_options()
        self._refresh_confirm_state()
        await interaction.response.edit_message(view=self)

    async def _on_alliance(self, interaction: discord.Interaction):
        self.selection.alliance = self.alliance_select.values[0]
        self._refresh_confirm_state()
        await interaction.response.edit_message(view=self)

    async def _on_day(self, interaction: discord.Interaction):
        self.selection.match_day = self.day_select.values[0]
        self.selection.match_time_utc = None
        self._refresh_time_options()
        self._refresh_confirm_state()
        await interaction.response.edit_message(view=self)

    async def _on_time(self, interaction: discord.Interaction):
        self.selection.match_time_utc = self.time_select.values[0]
        self._refresh_confirm_state()
        await interaction.response.edit_message(view=self)

    async def _on_notes_template(self, interaction: discord.Interaction):
        val = self.notes_select.values[0]
        if val == "__custom__":
            await self._open_notes_modal(interaction)
            return
        self.selection.notes = val
        await interaction.response.edit_message(view=self)

    async def _on_notes(self, interaction: discord.Interaction):
        await self._open_notes_modal(interaction)

    async def _open_notes_modal(self, interaction: discord.Interaction):
        async def _apply_notes(modal_interaction: discord.Interaction, notes_value: str | None):
            self.selection.notes = notes_value
            await modal_interaction.response.edit_message(view=self)

        await interaction.response.send_modal(
            ArkNotesModal(
                author_id=self.author_id,
                current_notes=self.selection.notes,
                on_submit=_apply_notes,
            )
        )

    async def _on_confirm(self, interaction: discord.Interaction):
        try:
            await self.on_confirm(interaction, self.selection)
        except Exception:
            logger.exception("[ARK] Amend match confirm handler failed")
            await interaction.response.send_message(
                "❌ Failed to amend the match. Please try again.", ephemeral=True
            )

    async def _on_cancel(self, interaction: discord.Interaction):
        if self.on_cancel:
            await self.on_cancel(interaction)
            return
        await interaction.response.edit_message(content="Cancelled.", view=None)


@dataclass
class ArkCancelMatchSelection:
    match_id: int | None = None
    notify_players: bool = False


CancelOnConfirm = Callable[[discord.Interaction, ArkCancelMatchSelection], object]


class CancelArkMatchView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        matches: list[dict],
        on_confirm: CancelOnConfirm,
        on_cancel: OnCancel | None = None,
        notify_toggle_enabled: bool = False,
        timeout: float = 300.0,
    ):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.matches_by_id = {int(m["MatchId"]): m for m in matches}
        self.selection = ArkCancelMatchSelection()
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.notify_toggle_enabled = notify_toggle_enabled

        self.match_select = discord.ui.Select(
            placeholder="Select match to cancel",
            options=[self._match_option(m) for m in matches][:25],
            min_values=1,
            max_values=1,
        )
        self.match_select.callback = self._on_match
        self.add_item(self.match_select)

        self.notify_btn = discord.ui.Button(
            label="Notify players (disabled)",
            style=discord.ButtonStyle.secondary,
            disabled=not self.notify_toggle_enabled,
        )
        self.notify_btn.callback = self._on_notify_toggle
        self.add_item(self.notify_btn)

        self.confirm_btn = discord.ui.Button(
            label="Cancel Match",
            style=discord.ButtonStyle.danger,
            disabled=True,
        )
        self.confirm_btn.callback = self._on_confirm
        self.add_item(self.confirm_btn)

        self.cancel_btn = discord.ui.Button(label="Close", style=discord.ButtonStyle.secondary)
        self.cancel_btn.callback = self._on_cancel
        self.add_item(self.cancel_btn)

    @staticmethod
    def _match_option(match: dict) -> discord.SelectOption:
        alliance = (match.get("Alliance") or "").strip()
        weekend = match.get("ArkWeekendDate")
        day = match.get("MatchDay") or ""
        match_time = match.get("MatchTimeUtc")
        time_str = (
            match_time.strftime("%H:%M") if hasattr(match_time, "strftime") else str(match_time)
        )
        weekend_str = weekend.strftime("%Y-%m-%d") if hasattr(weekend, "strftime") else str(weekend)
        label = f"{alliance} — {weekend_str} {day} {time_str} UTC"
        return discord.SelectOption(label=label[:100], value=str(match["MatchId"]))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ This setup flow isn’t for you.", ephemeral=True
            )
            return False
        return True

    def _apply_match_selection(self, match_id: int) -> None:
        """Internal helper to apply match selection (used by tests)."""
        self.selection.match_id = match_id
        self.confirm_btn.disabled = self.selection.match_id is None

    async def _on_match(self, interaction: discord.Interaction):
        if not self.match_select.values:
            await interaction.response.send_message("❌ No match selected.", ephemeral=True)
            return
        self._apply_match_selection(int(self.match_select.values[0]))
        await interaction.response.edit_message(view=self)

    async def _on_notify_toggle(self, interaction: discord.Interaction):
        if not self.notify_toggle_enabled:
            await interaction.response.send_message(
                "ℹ️ Notify players is not enabled yet.", ephemeral=True
            )
            return
        self.selection.notify_players = not self.selection.notify_players
        state = "On" if self.selection.notify_players else "Off"
        self.notify_btn.label = f"Notify players: {state}"
        await interaction.response.edit_message(view=self)

    async def _on_confirm(self, interaction: discord.Interaction):
        if not self.selection.match_id:
            await interaction.response.send_message("❌ No match selected.", ephemeral=True)
            return
        try:
            await self.on_confirm(interaction, self.selection)
        except Exception:
            logger.exception("[ARK] Cancel match confirm handler failed")
            await interaction.response.send_message(
                "❌ Failed to cancel the match. Please try again.", ephemeral=True
            )

    async def _on_cancel(self, interaction: discord.Interaction):
        if self.on_cancel:
            await self.on_cancel(interaction)
            return
        await interaction.response.edit_message(content="Cancelled.", view=None)


GovernorSelectCallback = Callable[[discord.Interaction, str], object]


class ArkGovernorSelectView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        options: list[discord.SelectOption],
        on_select: GovernorSelectCallback,
        timeout: float = 120.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self._on_select = on_select

        self.select = discord.ui.Select(
            placeholder="Select a governor",
            options=options[:25],
            min_values=1,
            max_values=1,
        )
        self.select.callback = self._handle_select
        self.add_item(self.select)

    async def _handle_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return
        await self._on_select(interaction, self.select.values[0])


class ArkRegistrationView(LocalTimeToggleView):
    def __init__(
        self,
        *,
        match_id: int,
        match_name: str,
        match_datetime_utc: datetime,
        on_join_player: Callable[[discord.Interaction], object],
        on_join_sub: Callable[[discord.Interaction], object],
        on_leave: Callable[[discord.Interaction], object],
        on_switch: Callable[[discord.Interaction], object],
        on_admin_add: Callable[[discord.Interaction], object] | None = None,
        on_admin_remove: Callable[[discord.Interaction], object] | None = None,
        on_admin_move: Callable[[discord.Interaction], object] | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(
            events=[{"name": match_name, "start_time": match_datetime_utc}],
            prefix=f"arkmatch_{match_id}",
            timeout=timeout,
        )
        self.on_join_player = on_join_player
        self.on_join_sub = on_join_sub
        self.on_leave = on_leave
        self.on_switch = on_switch
        self.on_admin_add = on_admin_add
        self.on_admin_remove = on_admin_remove
        self.on_admin_move = on_admin_move

        self.join_player_btn = discord.ui.Button(
            label="Join as Player",
            style=discord.ButtonStyle.success,
            row=1,
            custom_id=f"{self.prefix}_join_player",
        )
        self.join_sub_btn = discord.ui.Button(
            label="Join as Sub",
            style=discord.ButtonStyle.primary,
            row=1,
            custom_id=f"{self.prefix}_join_sub",
        )
        self.leave_btn = discord.ui.Button(
            label="Leave",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id=f"{self.prefix}_leave",
        )
        self.switch_btn = discord.ui.Button(
            label="Switch Governor",
            style=discord.ButtonStyle.secondary,
            row=2,
            custom_id=f"{self.prefix}_switch",
        )

        self.admin_add_btn = discord.ui.Button(
            label="Admin Add",
            style=discord.ButtonStyle.primary,
            row=3,
            custom_id=f"{self.prefix}_admin_add",
        )
        self.admin_remove_btn = discord.ui.Button(
            label="Admin Remove",
            style=discord.ButtonStyle.danger,
            row=3,
            custom_id=f"{self.prefix}_admin_remove",
        )
        self.admin_move_btn = discord.ui.Button(
            label="Admin Move",
            style=discord.ButtonStyle.secondary,
            row=3,
            custom_id=f"{self.prefix}_admin_move",
        )

        self.join_player_btn.callback = self._on_join_player
        self.join_sub_btn.callback = self._on_join_sub
        self.leave_btn.callback = self._on_leave
        self.switch_btn.callback = self._on_switch
        self.admin_add_btn.callback = self._on_admin_add
        self.admin_remove_btn.callback = self._on_admin_remove
        self.admin_move_btn.callback = self._on_admin_move

        self.add_item(self.join_player_btn)
        self.add_item(self.join_sub_btn)
        self.add_item(self.leave_btn)
        self.add_item(self.switch_btn)
        self.add_item(self.admin_add_btn)
        self.add_item(self.admin_remove_btn)
        self.add_item(self.admin_move_btn)

    async def _on_join_player(self, interaction: discord.Interaction):
        try:
            await self.on_join_player(interaction)
        except Exception:
            logger.exception("[ARK] Join as Player handler failed")
            await interaction.followup.send("❌ Failed to join as player.", ephemeral=True)

    async def _on_join_sub(self, interaction: discord.Interaction):
        try:
            await self.on_join_sub(interaction)
        except Exception:
            logger.exception("[ARK] Join as Sub handler failed")
            await interaction.followup.send("❌ Failed to join as sub.", ephemeral=True)

    async def _on_leave(self, interaction: discord.Interaction):
        try:
            await self.on_leave(interaction)
        except Exception:
            logger.exception("[ARK] Leave handler failed")
            await interaction.followup.send("❌ Failed to leave the match.", ephemeral=True)

    async def _on_switch(self, interaction: discord.Interaction):
        try:
            await self.on_switch(interaction)
        except Exception:
            logger.exception("[ARK] Switch handler failed")
            await interaction.followup.send("❌ Failed to switch governor.", ephemeral=True)

    async def _on_admin_add(self, interaction: discord.Interaction):
        if not self.on_admin_add:
            await interaction.response.send_message("❌ Admin add not configured.", ephemeral=True)
            return
        try:
            await self.on_admin_add(interaction)
        except Exception:
            logger.exception("[ARK] Admin add handler failed")
            await interaction.followup.send("❌ Failed to add signup.", ephemeral=True)

    async def _on_admin_remove(self, interaction: discord.Interaction):
        if not self.on_admin_remove:
            await interaction.response.send_message(
                "❌ Admin remove not configured.", ephemeral=True
            )
            return
        try:
            await self.on_admin_remove(interaction)
        except Exception:
            logger.exception("[ARK] Admin remove handler failed")
            await interaction.followup.send("❌ Failed to remove signup.", ephemeral=True)

    async def _on_admin_move(self, interaction: discord.Interaction):
        if not self.on_admin_move:
            await interaction.response.send_message("❌ Admin move not configured.", ephemeral=True)
            return
        try:
            await self.on_admin_move(interaction)
        except Exception:
            logger.exception("[ARK] Admin move handler failed")
            await interaction.followup.send("❌ Failed to move signup.", ephemeral=True)


class ArkAdminAddNameModal(discord.ui.Modal):
    def __init__(self, *, author_id: int, on_submit) -> None:
        super().__init__(title="Admin Add — Governor Name")
        self.author_id = author_id
        self._on_submit = on_submit

        self.add_item(
            discord.ui.InputText(
                label="Governor name",
                placeholder="Enter governor name (name_cache lookup)",
                style=discord.InputTextStyle.short,
                max_length=64,
            )
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You can't use someone else's modal.", ephemeral=True
            )
            return
        raw = (self.children[0].value or "").strip()
        await self._on_submit(interaction, raw)


class ArkAdminSlotSelectView(discord.ui.View):
    def __init__(
        self,
        *,
        author_id: int,
        on_select,
        player_label: str = "Add as Player",
        sub_label: str = "Add as Sub",
        timeout: float = 120.0,
    ) -> None:
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self._on_select = on_select

        self.player_btn = discord.ui.Button(
            label=player_label,
            style=discord.ButtonStyle.success,
        )
        self.sub_btn = discord.ui.Button(
            label=sub_label,
            style=discord.ButtonStyle.primary,
        )
        self.cancel_btn = discord.ui.Button(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
        )

        self.player_btn.callback = self._on_player
        self.sub_btn.callback = self._on_sub
        self.cancel_btn.callback = self._on_cancel

        self.add_item(self.player_btn)
        self.add_item(self.sub_btn)
        self.add_item(self.cancel_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ This menu isn’t for you.", ephemeral=True)
            return False
        return True

    async def _on_player(self, interaction: discord.Interaction):
        await self._on_select(interaction, "Player")

    async def _on_sub(self, interaction: discord.Interaction):
        await self._on_select(interaction, "Sub")

    async def _on_cancel(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="Cancelled.", view=None)


class ArkConfirmationView(LocalTimeToggleView):
    def __init__(
        self,
        *,
        match_id: int,
        match_name: str,
        match_datetime_utc: datetime,
        on_check_in: Callable[[discord.Interaction], object],
        on_emergency_withdraw: Callable[[discord.Interaction], object],
        show_check_in: bool = False,
        timeout: float | None = None,
    ) -> None:
        super().__init__(
            events=[{"name": match_name, "start_time": match_datetime_utc}],
            prefix=f"arkconfirm_{match_id}",
            timeout=timeout,
        )
        self.on_check_in = on_check_in
        self.on_emergency_withdraw = on_emergency_withdraw

        if show_check_in:
            self.check_in_btn = discord.ui.Button(
                label="Check in",
                style=discord.ButtonStyle.success,
                row=1,
                custom_id=f"{self.prefix}_check_in",
            )
            self.check_in_btn.callback = self._on_check_in
            self.add_item(self.check_in_btn)

        self.emergency_btn = discord.ui.Button(
            label="Emergency — can't attend",
            style=discord.ButtonStyle.danger,
            row=1,
            custom_id=f"{self.prefix}_emergency_withdraw",
        )
        self.emergency_btn.callback = self._on_emergency_withdraw
        self.add_item(self.emergency_btn)

    async def _send_error_message(self, interaction: discord.Interaction, message: str) -> None:
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    async def _on_check_in(self, interaction: discord.Interaction):
        try:
            await self.on_check_in(interaction)
        except Exception:
            logger.exception("[ARK] Check-in handler failed")
            await self._send_error_message(interaction, "❌ Failed to check in.")

    async def _on_emergency_withdraw(self, interaction: discord.Interaction):
        try:
            await self.on_emergency_withdraw(interaction)
        except Exception:
            logger.exception("[ARK] Emergency withdraw handler failed")
            await self._send_error_message(interaction, "❌ Failed to withdraw.")
