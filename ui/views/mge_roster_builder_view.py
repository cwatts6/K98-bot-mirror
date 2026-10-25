from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_or_leadership_interaction
from mge import mge_roster_service
from mge.mge_review_service import get_signup_review_pool

logger = logging.getLogger(__name__)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status(value: Any) -> str:
    return str(value or "").strip().lower()


def _name_from_row(row: dict[str, Any]) -> str:
    return (
        str(
            row.get("GovernorNameDisplay")
            or row.get("GovernorNameSnapshot")
            or row.get("GovernorName")
            or "Unknown"
        ).strip()
        or "Unknown"
    )


def _applicant_summary(row: dict[str, Any]) -> str:
    commander = str(
        row.get("CommanderNameDisplay") or row.get("RequestedCommanderName") or "Unknown"
    )
    priority = str(row.get("PriorityDisplay") or row.get("RequestPriority") or "Unknown")
    latest_kvk = row.get("LatestKVKRank")
    last_kvk = row.get("LastKVKRank")
    latest_kills = row.get("LatestT4T5Kills")
    last_kills = row.get("LastT4T5Kills")
    latest_pct = row.get("LatestPercentOfKillTarget")
    last_pct = row.get("LastPercentOfKillTarget")
    same_awards = _to_int(row.get("PriorAwardsRequestedCommanderCount"))
    awards_2y = _to_int(row.get("PriorAwardsOverallLast2YearsCount"))

    def _fmt(v: Any) -> Any:
        return v if v is not None else "—"

    return (
        f"{commander} • {priority} • "
        f"KVK {_fmt(last_kvk)}→{_fmt(latest_kvk)} • "
        f"T4/T5 {_fmt(last_kills)}→{_fmt(latest_kills)} • "
        f"%Target {_fmt(last_pct)}→{_fmt(latest_pct)} • "
        f"same={same_awards} • 2y={awards_2y}"
    )


def _format_award_line(row: dict[str, Any]) -> str:
    rank = row.get("AwardedRank")
    waitlist = row.get("WaitlistOrder")
    gov = _name_from_row(row)
    commander = str(row.get("RequestedCommanderName") or "Unknown")
    status = str(row.get("AwardStatus") or "Unknown")
    if _status(status) == "waitlist":
        return f"W{waitlist or '?'} • {gov} • {commander}"
    return f"#{rank or '?'} • {gov} • {commander}"


def _build_roster_embed_from_state(
    event_id: int, state: mge_roster_service.RosterState
) -> discord.Embed:
    embed = discord.Embed(title=f"MGE Roster Builder • Event {event_id}", color=0x5865F2)

    awarded_lines = [_format_award_line(r) for r in state.awarded[:15]]
    waitlist_lines = [_format_award_line(r) for r in state.waitlist[:25]]

    embed.add_field(
        name=f"Awarded ({len(state.awarded)}/15)",
        value="\n".join(awarded_lines) if awarded_lines else "None",
        inline=False,
    )
    embed.add_field(
        name=f"Waitlist ({len(state.waitlist)})",
        value="\n".join(waitlist_lines) if waitlist_lines else "None",
        inline=False,
    )
    embed.set_footer(text="Selection-first roster management. Notes/reasons remain free text.")
    return embed


class _SelectRow(discord.ui.Select):
    def __init__(self, *, placeholder: str, options: list[discord.SelectOption], on_pick):
        super().__init__(
            placeholder=placeholder,
            options=options[:25],
            min_values=1,
            max_values=1,
        )
        self._on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self._on_pick(interaction, self.values[0])


class MgeRosterBuilderView(discord.ui.View):
    def __init__(self, event_id: int, actor_discord_id: int, timeout: float | None = 900) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self.actor_discord_id = int(actor_discord_id)

    def _session_key(self) -> tuple[int, int]:
        return (self.event_id, self.actor_discord_id)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return False
        return True

    async def _load_state(self) -> mge_roster_service.RosterState:
        return await asyncio.to_thread(mge_roster_service.load_roster_state, self.event_id)

    async def _load_review_rows(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(get_signup_review_pool, self.event_id)

    async def _load_embed(self) -> discord.Embed:
        state = await self._load_state()
        return _build_roster_embed_from_state(self.event_id, state)

    async def on_timeout(self) -> None:
        mge_roster_service.clear_undo_session(self.event_id, self.actor_discord_id)
        self.stop()

    def _applicant_options(self, rows: list[dict[str, Any]]) -> list[discord.SelectOption]:
        options: list[discord.SelectOption] = []
        for row in rows[:25]:
            signup_id = row.get("SignupId")
            if signup_id is None:
                continue
            label = _name_from_row(row)[:100]
            desc = _applicant_summary(row)[:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    description=desc,
                    value=str(signup_id),
                )
            )
        return options

    def _award_options(self, rows: list[dict[str, Any]]) -> list[discord.SelectOption]:
        options: list[discord.SelectOption] = []
        for row in rows[:25]:
            award_id = row.get("AwardId")
            if award_id is None:
                continue
            label = _format_award_line(row)[:100]
            options.append(
                discord.SelectOption(
                    label=label,
                    value=str(award_id),
                )
            )
        return options

    async def _applicant_snapshot(self, signup_id: int) -> dict[str, Any] | None:
        rows = await self._load_review_rows()
        for row in rows:
            if _to_int(row.get("SignupId")) == int(signup_id):
                return row
        return None

    async def _award_snapshot(self, award_id: int) -> dict[str, Any] | None:
        return await asyncio.to_thread(
            mge_roster_service.mge_roster_dal.fetch_award_by_id, award_id
        )

    @discord.ui.button(label="Show Current Roster", style=discord.ButtonStyle.secondary, row=0)
    async def show_roster(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        embed = await self._load_embed()
        await send_ephemeral(interaction, "Roster snapshot:", embed=embed)

    @discord.ui.button(label="Add Signup To Roster", style=discord.ButtonStyle.success, row=0)
    async def add_signup(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return

        review_rows = await self._load_review_rows()
        state = await self._load_state()
        occupied_governors = {
            _to_int(r.get("GovernorId")) for r in (state.awarded + state.waitlist + state.other)
        }
        eligible = [
            r for r in review_rows if _to_int(r.get("GovernorId")) not in occupied_governors
        ]
        options = self._applicant_options(eligible)

        if not options:
            await send_ephemeral(interaction, "No eligible applicants are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _AddModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, signup_snapshot: dict[str, Any]):
                    super().__init__(title="Add Applicant To Roster", timeout=300)
                    self.parent = parent
                    self.snapshot = signup_snapshot
                    self.rank = discord.ui.InputText(
                        label="Rank (1-15)",
                        required=True,
                        max_length=2,
                        placeholder="1",
                    )
                    self.internal_notes = discord.ui.InputText(
                        label="Internal Notes (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.rank)
                    self.add_item(self.internal_notes)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    try:
                        rank = int(str(self.rank.value).strip())
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid rank.")
                        return

                    target_rank = int(rank)
                    occupied = await self.parent._load_state()
                    used_ranks = {
                        _to_int(r.get("AwardedRank"))
                        for r in occupied.awarded
                        if _status(r.get("AwardStatus")) == "awarded"
                    }
                    if target_rank in used_ranks:
                        await send_ephemeral(modal_interaction, "❌ That rank is already occupied.")
                        return

                    res = await asyncio.to_thread(
                        mge_roster_service.add_signup_with_rank,
                        event_id=self.parent.event_id,
                        signup_id=int(self.snapshot["SignupId"]),
                        target_rank=target_rank,
                        actor_discord_id=int(modal_interaction.user.id),
                        internal_notes=str(self.internal_notes.value or "").strip() or None,
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_AddModal(self, snap))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select an applicant",
                options=options,
                on_pick=lambda i, v: self._on_pick_applicant(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select an applicant to add:", view=view, ephemeral=True
        )

    async def _on_pick_applicant(
        self,
        interaction: discord.Interaction,
        signup_id_value: str,
        after_pick,
    ) -> None:
        try:
            signup_id = int(signup_id_value)
        except Exception:
            await send_ephemeral(interaction, "❌ Invalid applicant selection.")
            return

        snap = await self._applicant_snapshot(signup_id)
        if not snap:
            await send_ephemeral(interaction, "❌ Applicant not found.")
            return
        await after_pick(interaction, snap)

    async def _on_pick_award(
        self,
        interaction: discord.Interaction,
        award_id_value: str,
        after_pick,
    ) -> None:
        try:
            award_id = int(award_id_value)
        except Exception:
            await send_ephemeral(interaction, "❌ Invalid roster selection.")
            return

        snap = await self._award_snapshot(award_id)
        if not snap:
            await send_ephemeral(interaction, "❌ Roster row not found.")
            return
        await after_pick(interaction, snap)

    @discord.ui.button(label="Adjust Rank", style=discord.ButtonStyle.primary, row=1)
    async def set_rank(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.awarded)
        if not options:
            await send_ephemeral(interaction, "No awarded rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _SetRankModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Adjust Award Rank", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.rank = discord.ui.InputText(
                        label="Rank (1-15)",
                        required=True,
                        max_length=2,
                        placeholder="1",
                    )
                    self.add_item(self.rank)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    try:
                        rank = int(str(self.rank.value).strip())
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid rank.")
                        return

                    occupied = await self.parent._load_state()
                    used_ranks = {
                        _to_int(r.get("AwardedRank"))
                        for r in occupied.awarded
                        if _status(r.get("AwardStatus")) == "awarded"
                    }
                    if rank in used_ranks:
                        await send_ephemeral(modal_interaction, "❌ That rank is already occupied.")
                        return

                    res = await asyncio.to_thread(
                        mge_roster_service.set_rank,
                        award_id=self.award_id,
                        new_rank=rank,
                        actor_discord_id=int(modal_interaction.user.id),
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_SetRankModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select an awarded row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select a row to re-rank:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Move To Waitlist", style=discord.ButtonStyle.primary, row=1)
    async def to_waitlist(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.awarded)
        if not options:
            await send_ephemeral(interaction, "No awarded rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _WaitlistModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Move To Waitlist", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.order = discord.ui.InputText(
                        label="Waitlist Order (optional)",
                        required=False,
                        max_length=4,
                        placeholder="auto",
                    )
                    self.notes = discord.ui.InputText(
                        label="Internal Notes (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.order)
                    self.add_item(self.notes)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    order_text = str(self.order.value or "").strip()
                    try:
                        order = int(order_text) if order_text else None
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid waitlist order.")
                        return

                    res = await asyncio.to_thread(
                        mge_roster_service.move_to_waitlist,
                        award_id=self.award_id,
                        actor_discord_id=int(modal_interaction.user.id),
                        waitlist_order=order,
                        notes=str(self.notes.value or "").strip() or None,
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_WaitlistModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select an awarded row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select a row to move to waitlist:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Move To Roster", style=discord.ButtonStyle.primary, row=1)
    async def move_to_roster(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.waitlist)
        if not options:
            await send_ephemeral(interaction, "No waitlist rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _PromoteModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Move Waitlist Row To Roster", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.notes = discord.ui.InputText(
                        label="Additional Notes (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.notes)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    res = await asyncio.to_thread(
                        mge_roster_service.promote_waitlist_to_roster,
                        award_id=self.award_id,
                        actor_discord_id=int(modal_interaction.user.id),
                        notes=str(self.notes.value or "").strip() or None,
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_PromoteModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select a waitlist row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select a waitlist row to promote:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Adjust Waitlist Order", style=discord.ButtonStyle.secondary, row=2)
    async def set_waitlist_order(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.waitlist)
        if not options:
            await send_ephemeral(interaction, "No waitlist rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _SetWaitOrderModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Adjust Waitlist Order", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.order = discord.ui.InputText(
                        label="Order >= 1",
                        required=True,
                        max_length=4,
                        placeholder="1",
                    )
                    self.add_item(self.order)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    try:
                        order = int(str(self.order.value).strip())
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid waitlist order.")
                        return
                    res = await asyncio.to_thread(
                        mge_roster_service.set_waitlist_order,
                        award_id=self.award_id,
                        waitlist_order=order,
                        actor_discord_id=int(modal_interaction.user.id),
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_SetWaitOrderModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select a waitlist row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message("Select a waitlist row:", view=view, ephemeral=True)

    @discord.ui.button(label="Update Internal Notes", style=discord.ButtonStyle.secondary, row=2)
    async def update_notes(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.awarded + state.waitlist + state.other)
        if not options:
            await send_ephemeral(interaction, "No roster rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _NotesModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Update Internal Notes", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.notes = discord.ui.InputText(
                        label="Notes (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.notes)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    res = await asyncio.to_thread(
                        mge_roster_service.update_internal_notes,
                        award_id=self.award_id,
                        notes=str(self.notes.value or "").strip() or None,
                        actor_discord_id=int(modal_interaction.user.id),
                    )
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                    )

            await inter.response.send_modal(_NotesModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select a roster row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select a row to annotate:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Remove Award", style=discord.ButtonStyle.danger, row=2)
    async def remove_award(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        state = await self._load_state()
        options = self._award_options(state.awarded + state.waitlist + state.other)
        if not options:
            await send_ephemeral(interaction, "No roster rows are available.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _RemoveModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView, award_id: int):
                    super().__init__(title="Remove Award Row", timeout=300)
                    self.parent = parent
                    self.award_id = award_id
                    self.reason = discord.ui.InputText(
                        label="Removal Reason (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.reason)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    reason = str(self.reason.value or "").strip() or None
                    res = await asyncio.to_thread(
                        mge_roster_service.remove_award_hard_delete,
                        award_id=self.award_id,
                        actor_discord_id=int(modal_interaction.user.id),
                        event_id=self.parent.event_id,
                        session_key=self.parent._session_key(),
                        removal_reason=reason,
                    )
                    embed = await self.parent._load_embed() if res.success else None
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                        embed=embed,
                    )

            await inter.response.send_modal(_RemoveModal(self, int(snap["AwardId"])))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select a roster row",
                options=options,
                on_pick=lambda i, v: self._on_pick_award(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select a row to remove:", view=view, ephemeral=True
        )

    @discord.ui.button(label="Undo Last Removal", style=discord.ButtonStyle.secondary, row=3)
    async def undo_last(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return
        res = await asyncio.to_thread(
            mge_roster_service.undo_last_removal_in_session,
            event_id=self.event_id,
            actor_discord_id=self.actor_discord_id,
        )
        msg = (
            ("✅ " if res.success else "❌ ")
            + res.message
            + "\n(Undo only works during current session.)"
        )
        embed = await self._load_embed() if res.success else None
        await send_ephemeral(interaction, msg, embed=embed)

    @discord.ui.button(label="Reject Signup (Audit)", style=discord.ButtonStyle.danger, row=3)
    async def reject_signup(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        review_rows = await self._load_review_rows()
        options = self._applicant_options(review_rows)
        if not options:
            await send_ephemeral(interaction, "No selectable applicants were found.")
            return

        async def _after_pick(inter: discord.Interaction, snap: dict[str, Any]) -> None:
            class _RejectModal(discord.ui.Modal):
                def __init__(self, parent: MgeRosterBuilderView):
                    super().__init__(title="Reject Applicant (Audit Only)", timeout=300)
                    self.parent = parent
                    self.reason = discord.ui.InputText(
                        label="Reason (optional)",
                        required=False,
                        max_length=1000,
                        style=discord.InputTextStyle.long,
                    )
                    self.add_item(self.reason)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not await self.parent._guard(modal_interaction):
                        return
                    res = await asyncio.to_thread(
                        mge_roster_service.reject_signup_audit_only,
                        event_id=self.parent.event_id,
                        signup_id=int(snap["SignupId"]),
                        actor_discord_id=int(modal_interaction.user.id),
                        reason=str(self.reason.value or "").strip() or None,
                    )
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if res.success else "❌ ") + res.message,
                    )

            await inter.response.send_modal(_RejectModal(self))

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _SelectRow(
                placeholder="Select an applicant",
                options=options,
                on_pick=lambda i, v: self._on_pick_applicant(i, v, _after_pick),
            )
        )
        await interaction.response.send_message(
            "Select an applicant to reject:", view=view, ephemeral=True
        )
