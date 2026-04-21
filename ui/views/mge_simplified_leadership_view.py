from __future__ import annotations

import asyncio
import logging
from typing import Any

import discord

from core.interaction_safety import send_ephemeral
from core.mge_permissions import is_admin_interaction, is_admin_or_leadership_interaction
from decoraters import (
    LEADERSHIP_ROLE_IDS as _LEADERSHIP_ROLE_IDS,
    _is_admin as _decoraters_is_admin,
)
from mge import (
    mge_embed_manager,
    mge_publish_service,
    mge_roster_service,
    mge_simplified_leadership_service,
)
from mge.dal import mge_signup_dal
from ui.views.mge_admin_view import ConfirmSwitchFixedView, ConfirmSwitchOpenView, MGEAdminViewDeps

logger = logging.getLogger(__name__)


def _get_admin_role_ids_for_interaction(interaction: discord.Interaction) -> set[int]:
    """Return role IDs that the service layer should treat as admin/leadership.

    Always includes the configured LEADERSHIP_ROLE_IDS. When the interacting
    user is the designated ADMIN_USER_ID their actual Discord role IDs are also
    included. If the admin cannot be resolved to a Member object, fall back to
    the guild's default @everyone role so the service-layer intersection
    check still has a guild-valid role ID to match against.
    """
    role_ids: set[int] = set(_LEADERSHIP_ROLE_IDS)
    if _decoraters_is_admin(interaction.user):
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        guild = getattr(interaction, "guild", None)
        if member is None and guild is not None:
            member = guild.get_member(interaction.user.id)
        if member is not None:
            role_ids.update(int(r.id) for r in member.roles)
        elif guild is not None:
            role_ids.add(int(guild.default_role.id))
    return role_ids


def _build_leadership_admin_deps(
    interaction: discord.Interaction,
) -> MGEAdminViewDeps:
    """Build refresh/admin dependencies for simplified leadership admin actions."""

    def _refresh_embed(target_event_id: int) -> None:
        async def _runner() -> None:
            await asyncio.sleep(0.5)
            await mge_embed_manager.refresh_mge_boards(
                bot=interaction.client,
                event_id=int(target_event_id),
                refresh_public=True,
                refresh_leadership=True,
                refresh_awards=False,
            )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_runner())
        except RuntimeError:
            logger.warning(
                "mge_simplified_leadership_refresh_schedule_failed event_id=%s",
                target_event_id,
            )

    return MGEAdminViewDeps(
        refresh_embed=_refresh_embed,
        is_admin=is_admin_interaction,
        admin_role_ids=_get_admin_role_ids_for_interaction(interaction),
    )


def _simple_row_label(row: dict[str, Any]) -> str:
    status = str(row.get("SimplifiedStatus") or "").strip().lower()
    name = str(
        row.get("GovernorNameDisplay")
        or row.get("GovernorNameSnapshot")
        or row.get("GovernorName")
        or "Unknown"
    )
    if status == "roster":
        rank = row.get("ComputedAwardedRank") or row.get("AwardedRank") or "?"
        return f"#{rank} • {name}"
    if status == "waitlist":
        order = row.get("ComputedWaitlistOrder") or row.get("WaitlistOrder") or "?"
        return f"W{order} • {name}"
    return name


def _build_step1_options(
    rows: list[dict[str, Any]],
    *,
    value_key: str,
    max_items: int = 25,
) -> list[discord.SelectOption]:
    options: list[discord.SelectOption] = []
    for row in rows[:max_items]:
        value = row.get(value_key)
        if value is None:
            continue
        label = _simple_row_label(row)
        desc = f"ID {value}"
        options.append(
            discord.SelectOption(label=label[:100], value=str(value), description=desc[:100])
        )
    return options


class _SingleActionConfirmView(discord.ui.View):
    """Base class for one-shot confirmation views with repeated-click safeguards."""

    def __init__(self, *, timeout: float | None = 120) -> None:
        super().__init__(timeout=timeout)
        self._completed = False

    def _mark_completed(self) -> None:
        self._completed = True
        for child in self.children:
            child.disabled = True
        self.stop()

    async def _reject_if_completed(self, interaction: discord.Interaction) -> bool:
        if self._completed:
            await send_ephemeral(
                interaction,
                "⚠️ This confirmation has already been used. Refresh the leadership board if you need to run the action again.",
            )
            return True
        return False


class _AdjustRankModal(discord.ui.Modal):
    def __init__(self, *, event_id: int, award_id: int) -> None:
        super().__init__(title="Adjust Rank", timeout=300)
        self.event_id = int(event_id)
        self.award_id = int(award_id)
        self.rank_value = discord.ui.InputText(
            label="New Rank (1-15)",
            placeholder="1",
            required=True,
            max_length=2,
        )
        self.add_item(self.rank_value)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        try:
            new_rank = int(str(self.rank_value.value).strip())
        except Exception:
            await send_ephemeral(interaction, "❌ Invalid rank.")
            return

        result = await asyncio.to_thread(
            mge_roster_service.set_rank,
            award_id=self.award_id,
            new_rank=new_rank,
            actor_discord_id=int(interaction.user.id),
        )
        if result.success:
            await mge_embed_manager.refresh_mge_boards(
                bot=interaction.client,
                event_id=self.event_id,
                refresh_public=True,
                refresh_leadership=True,
            )
        await send_ephemeral(interaction, ("✅ " if result.success else "❌ ") + result.message)


class _NotesOnlyModal(discord.ui.Modal):
    def __init__(self, *, title: str, event_id: int, on_submit):
        super().__init__(title=title, timeout=300)
        self.event_id = int(event_id)
        self._on_submit = on_submit
        self.reason = discord.ui.InputText(
            label="Reason / Notes (optional)",
            required=False,
            style=discord.InputTextStyle.long,
        )
        self.add_item(self.reason)

    async def callback(self, interaction: discord.Interaction) -> None:
        notes = str(self.reason.value or "").strip() or None
        await self._on_submit(interaction, notes)


class _GenerateTargetsModal(discord.ui.Modal):
    def __init__(self, *, event_id: int) -> None:
        super().__init__(title="Generate Targets", timeout=300)
        self.event_id = int(event_id)
        self.rank1 = discord.ui.InputText(
            label="Rank 1 Target (millions)",
            required=True,
            placeholder="8 or 13.5",
            max_length=6,
        )
        self.add_item(self.rank1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        try:
            rank1_target = float(str(self.rank1.value).strip())
            if rank1_target <= 0 or rank1_target % 0.5 != 0:
                raise ValueError("out of range")
        except Exception:
            await send_ephemeral(
                interaction, "❌ Invalid rank 1 target. Use a whole number or .5 (e.g. 8 or 13.5)."
            )
            return

        result = await asyncio.to_thread(
            mge_publish_service.generate_targets_from_rank1,
            event_id=self.event_id,
            rank1_target_millions=rank1_target,
            actor_discord_id=int(interaction.user.id),
        )
        if result.success:
            await mge_embed_manager.refresh_mge_boards(
                bot=interaction.client,
                event_id=self.event_id,
                refresh_public=True,
                refresh_leadership=True,
                refresh_awards=True,
            )
        await send_ephemeral(interaction, ("✅ " if result.success else "❌ ") + result.message)


class _PublishConfirmView(_SingleActionConfirmView):
    def __init__(self, *, event_id: int, timeout: float | None = 120) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    @discord.ui.button(label="Confirm Publish / Republish", style=discord.ButtonStyle.success)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if await self._reject_if_completed(interaction):
            return
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        await interaction.response.defer(ephemeral=True)
        result = await mge_publish_service.publish_event_awards(
            bot=interaction.client,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )
        self._mark_completed()
        await interaction.followup.send(
            ("✅ " if result.success else "❌ ") + result.message,
            ephemeral=True,
        )


class _UnpublishConfirmView(_SingleActionConfirmView):
    def __init__(self, *, event_id: int, timeout: float | None = 120) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    @discord.ui.button(label="Confirm Unpublish", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if await self._reject_if_completed(interaction):
            return
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        await interaction.response.defer(ephemeral=True)
        result = await mge_publish_service.unpublish_event_awards(
            bot=interaction.client,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )
        self._mark_completed()
        await interaction.followup.send(
            ("✅ " if result.success else "❌ ") + result.message,
            ephemeral=True,
        )


class _ResetRanksConfirmView(_SingleActionConfirmView):
    def __init__(self, *, event_id: int, timeout: float | None = 120) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)

    @discord.ui.button(label="Confirm Reset Ranks", style=discord.ButtonStyle.danger)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if await self._reject_if_completed(interaction):
            return
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return
        result = await asyncio.to_thread(
            mge_simplified_leadership_service.reset_active_ranks,
            event_id=self.event_id,
            actor_discord_id=int(interaction.user.id),
        )
        if result.success:
            await mge_embed_manager.refresh_mge_boards(
                bot=interaction.client,
                event_id=self.event_id,
                refresh_public=True,
                refresh_leadership=True,
            )
        self._mark_completed()
        await send_ephemeral(interaction, ("✅ " if result.success else "❌ ") + result.message)


class _Step1SelectionView(discord.ui.View):
    def __init__(
        self,
        *,
        event_id: int,
        title: str,
        options: list[discord.SelectOption],
        on_pick,
        timeout: float | None = 180,
    ) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self._on_pick = on_pick
        self.title = title

        select = discord.ui.Select(
            placeholder=title[:100],
            min_values=1,
            max_values=1,
            options=options[:25] or [discord.SelectOption(label="No options", value="__none__")],
            custom_id=f"mge_step1_select_{self.event_id}_{abs(hash(title)) % 1_000_000}",
        )
        select.callback = self._select_callback  # type: ignore[method-assign]
        self.add_item(select)

    async def _select_callback(self, interaction: discord.Interaction) -> None:
        select = self.children[0]
        if not isinstance(select, discord.ui.Select):
            await send_ephemeral(interaction, "❌ Selection unavailable.")
            return
        value = str(select.values[0])
        if value == "__none__":
            await send_ephemeral(interaction, "⚠️ No selectable rows.")
            return
        await self._on_pick(interaction, value)


class MGESimplifiedLeadershipView(discord.ui.View):
    """Persistent leadership control-surface view for simplified-flow MGE."""

    def __init__(
        self,
        *,
        event_id: int,
        action_state: dict[str, bool] | None = None,
        timeout: float | None = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.event_id = int(event_id)
        self.action_state = action_state or {}
        self._apply_action_state()

    def _apply_action_state(self) -> None:
        for child in self.children:
            custom_id = getattr(child, "custom_id", "")
            if custom_id == "mge_lead_move_waitlist":
                child.disabled = not bool(self.action_state.get("can_move_to_waitlist"))
            elif custom_id == "mge_lead_move_roster":
                disabled = not bool(
                    self.action_state.get("can_move_to_roster")
                    or self.action_state.get("can_promote_with_swap")
                )
                child.disabled = disabled
            elif custom_id == "mge_lead_reject":
                child.disabled = not bool(self.action_state.get("can_reject_signup", True))
            elif custom_id == "mge_lead_reset":
                child.disabled = not bool(self.action_state.get("can_reset_ranks", True))

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if not is_admin_or_leadership_interaction(interaction):
            await send_ephemeral(interaction, "❌ Leadership/admin only.")
            return False
        return True

    async def _load_board_payload(self) -> dict[str, Any]:
        return await asyncio.to_thread(
            mge_simplified_leadership_service.get_leadership_board_payload, self.event_id
        )

    @discord.ui.button(
        label="Edit Rules",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="mge_lead_edit_rules",
    )
    async def edit_rules(self, button: discord.ui.Button, interaction: discord.Interaction) -> None:
        del button
        if not await self._guard(interaction):
            return
        from ui.views.mge_rules_edit_view import MgeRulesEditView

        await send_ephemeral(
            interaction, "Opened rules editor.", view=MgeRulesEditView(event_id=self.event_id)
        )

    @discord.ui.button(
        label="Switch to Open",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="mge_lead_switch_open",
    )
    async def switch_open(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not is_admin_interaction(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return
        await send_ephemeral(
            interaction,
            "⚠️ Confirm switch to open: this will delete all existing signups for the event and switch the ruleset to the open template.",
            view=ConfirmSwitchOpenView(
                event_id=self.event_id,
                deps=_build_leadership_admin_deps(interaction),
            ),
        )

    @discord.ui.button(
        label="Switch to Fixed",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="mge_lead_switch_fixed",
    )
    async def switch_fixed(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not is_admin_interaction(interaction):
            await send_ephemeral(interaction, "❌ Admin only.")
            return
        await send_ephemeral(
            interaction,
            "⚠️ Confirm switch to fixed: this keeps the event live but restores the fixed rules template and controlled mode.",
            view=ConfirmSwitchFixedView(
                event_id=self.event_id,
                deps=_build_leadership_admin_deps(interaction),
            ),
        )

    @discord.ui.button(
        label="Refresh Embed",
        style=discord.ButtonStyle.primary,
        row=0,
        custom_id="mge_lead_refresh",
    )
    async def refresh_embed(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        await mge_embed_manager.refresh_mge_boards(
            bot=interaction.client,
            event_id=self.event_id,
            refresh_public=False,
            refresh_leadership=True,
        )
        await send_ephemeral(interaction, "✅ Leadership embed refreshed.")

    @discord.ui.button(
        label="Admin Add Signup",
        style=discord.ButtonStyle.secondary,
        row=0,
        custom_id="mge_lead_admin_add_signup",
    )
    async def admin_add_signup(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        # Block if event is completed
        event = await asyncio.to_thread(mge_signup_dal.fetch_event_signup_context, self.event_id)
        if event:
            status = str(event.get("Status") or "").strip().lower()
            if status in {"completed", "finished"}:
                await send_ephemeral(
                    interaction,
                    "❌ This event is completed. No further signups can be added.",
                )
                return

        from ui.views.mge_admin_add_signup_view import MgeAdminAddLookupModal

        async def _on_governor_selected(
            modal_interaction: discord.Interaction,
            governor_id: int,
            governor_name: str,
        ) -> None:
            """Continue admin-add flow into a temporary signup view."""
            from ui.views.mge_admin_view import MGEAdminViewDeps
            from ui.views.mge_signup_view import MGESignupView

            def _refresh_embed(target_event_id: int) -> None:
                async def _runner() -> None:
                    await asyncio.sleep(0.5)
                    await mge_embed_manager.refresh_mge_boards(
                        bot=modal_interaction.client,
                        event_id=int(target_event_id),
                        refresh_public=True,
                        refresh_leadership=True,
                        refresh_awards=False,
                    )

                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(_runner())
                except RuntimeError:
                    logger.warning(
                        "mge_lead_admin_add_refresh_schedule_failed event_id=%s",
                        target_event_id,
                    )

            from core.mge_permissions import is_admin_interaction as _is_admin_check

            deps = MGEAdminViewDeps(
                refresh_embed=_refresh_embed,
                is_admin=_is_admin_check,
                admin_role_ids=_get_admin_role_ids_for_interaction(interaction),
            )
            temp_view = MGESignupView(event_id=self.event_id, admin_deps=deps, timeout=300)
            await temp_view._open_signup_modal(
                modal_interaction,
                governor_id=int(governor_id),
                governor_name=str(governor_name),
            )

        await interaction.response.send_modal(
            MgeAdminAddLookupModal(
                author_id=int(interaction.user.id),
                on_governor_selected=_on_governor_selected,
            )
        )

    @discord.ui.button(
        label="Step 1: Adjust Rank",
        style=discord.ButtonStyle.primary,
        row=1,
        custom_id="mge_lead_adjust_rank",
    )
    async def adjust_rank(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        payload = await self._load_board_payload()
        options = _build_step1_options(
            payload.get("selection_data", {}).get("roster_rows", []), value_key="AwardId"
        )
        if not options:
            await send_ephemeral(interaction, "⚠️ No roster rows available.")
            return

        async def _on_pick(i: discord.Interaction, value: str) -> None:
            await i.response.send_modal(
                _AdjustRankModal(event_id=self.event_id, award_id=int(value))
            )

        await send_ephemeral(
            interaction,
            "Select roster player to adjust rank:",
            view=_Step1SelectionView(
                event_id=self.event_id,
                title="Choose roster player",
                options=options,
                on_pick=_on_pick,
            ),
        )

    @discord.ui.button(
        label="Step 1a: Move to Waitlist",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_lead_move_waitlist",
    )
    async def move_waitlist(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        payload = await self._load_board_payload()
        if not payload.get("actions", {}).get("can_move_to_waitlist", False):
            await send_ephemeral(
                interaction, "⚠️ Move to Waitlist is only enabled when roster count exceeds 15."
            )
            return

        options = _build_step1_options(
            payload.get("selection_data", {}).get("roster_rows", []), value_key="AwardId"
        )
        if not options:
            await send_ephemeral(interaction, "⚠️ No roster rows available.")
            return

        async def _on_pick(i: discord.Interaction, value: str) -> None:
            award_id = int(value)

            async def _submit(j: discord.Interaction, notes: str | None) -> None:
                result = await asyncio.to_thread(
                    mge_roster_service.move_to_waitlist,
                    award_id=award_id,
                    actor_discord_id=int(j.user.id),
                    notes=notes,
                )
                if result.success:
                    await mge_embed_manager.refresh_mge_boards(
                        bot=j.client,
                        event_id=self.event_id,
                        refresh_public=True,
                        refresh_leadership=True,
                    )
                await send_ephemeral(j, ("✅ " if result.success else "❌ ") + result.message)

            await i.response.send_modal(
                _NotesOnlyModal(title="Move to Waitlist", event_id=self.event_id, on_submit=_submit)
            )

        await send_ephemeral(
            interaction,
            "Select roster player to move to waitlist:",
            view=_Step1SelectionView(
                event_id=self.event_id,
                title="Choose roster player",
                options=options,
                on_pick=_on_pick,
            ),
        )

    @discord.ui.button(
        label="Step 1b: Move to Roster",
        style=discord.ButtonStyle.secondary,
        row=1,
        custom_id="mge_lead_move_roster",
    )
    async def move_roster(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        payload = await self._load_board_payload()
        actions = payload.get("actions", {})
        can_direct = bool(actions.get("can_move_to_roster"))
        can_swap = bool(actions.get("can_promote_with_swap"))
        if not (can_direct or can_swap):
            await send_ephemeral(interaction, "⚠️ No eligible move-to-roster action available.")
            return

        waitlist_rows = payload.get("selection_data", {}).get("waitlist_rows", [])
        waitlist_options = _build_step1_options(waitlist_rows, value_key="AwardId")
        if not waitlist_options:
            await send_ephemeral(interaction, "⚠️ No waitlist rows available.")
            return

        async def _after_pick_waitlist(i: discord.Interaction, promote_value: str) -> None:
            promote_award_id = int(promote_value)

            if can_direct and not can_swap:

                async def _submit(j: discord.Interaction, notes: str | None) -> None:
                    result = await asyncio.to_thread(
                        mge_simplified_leadership_service.move_waitlist_to_roster_with_optional_demote,
                        event_id=self.event_id,
                        promote_award_id=promote_award_id,
                        actor_discord_id=int(j.user.id),
                        demote_award_id=None,
                        notes=notes,
                    )
                    if result.success:
                        await mge_embed_manager.refresh_mge_boards(
                            bot=j.client,
                            event_id=self.event_id,
                            refresh_public=True,
                            refresh_leadership=True,
                        )
                    await send_ephemeral(j, ("✅ " if result.success else "❌ ") + result.message)

                await i.response.send_modal(
                    _NotesOnlyModal(
                        title="Move to Roster", event_id=self.event_id, on_submit=_submit
                    )
                )
                return

            roster_rows = payload.get("selection_data", {}).get("roster_rows", [])
            roster_options = _build_step1_options(roster_rows, value_key="AwardId")
            if not roster_options:
                await send_ephemeral(i, "⚠️ Roster is full but no demote options are available.")
                return

            async def _after_pick_demote(j: discord.Interaction, demote_value: str) -> None:
                demote_award_id = int(demote_value)

                async def _submit(k: discord.Interaction, notes: str | None) -> None:
                    result = await asyncio.to_thread(
                        mge_simplified_leadership_service.move_waitlist_to_roster_with_optional_demote,
                        event_id=self.event_id,
                        promote_award_id=promote_award_id,
                        actor_discord_id=int(k.user.id),
                        demote_award_id=demote_award_id,
                        notes=notes,
                    )
                    if result.success:
                        await mge_embed_manager.refresh_mge_boards(
                            bot=k.client,
                            event_id=self.event_id,
                            refresh_public=True,
                            refresh_leadership=True,
                        )
                    await send_ephemeral(k, ("✅ " if result.success else "❌ ") + result.message)

                await j.response.send_modal(
                    _NotesOnlyModal(
                        title="Swap Promote/Demote", event_id=self.event_id, on_submit=_submit
                    )
                )

            await i.response.send_message(
                "Select roster player to demote (they will be appended to waitlist end):",
                ephemeral=True,
                view=_Step1SelectionView(
                    event_id=self.event_id,
                    title="Choose roster player to demote",
                    options=roster_options,
                    on_pick=_after_pick_demote,
                ),
            )

        await send_ephemeral(
            interaction,
            "Select waitlist player to promote:",
            view=_Step1SelectionView(
                event_id=self.event_id,
                title="Choose waitlist player",
                options=waitlist_options,
                on_pick=_after_pick_waitlist,
            ),
        )

    @discord.ui.button(
        label="Step 1c: Reject Signup",
        style=discord.ButtonStyle.danger,
        row=1,
        custom_id="mge_lead_reject",
    )
    async def reject_signup(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        payload = await self._load_board_payload()
        candidates = (
            list(payload.get("selection_data", {}).get("unassigned_rows", []))
            + list(payload.get("selection_data", {}).get("waitlist_rows", []))
            + list(payload.get("selection_data", {}).get("roster_rows", []))
        )
        options = _build_step1_options(candidates, value_key="SignupId")
        if not options:
            await send_ephemeral(interaction, "⚠️ No signups available to reject.")
            return

        async def _on_pick(i: discord.Interaction, value: str) -> None:
            signup_id = int(value)

            async def _submit(j: discord.Interaction, notes: str | None) -> None:
                result = await asyncio.to_thread(
                    mge_roster_service.reject_signup,
                    event_id=self.event_id,
                    signup_id=signup_id,
                    actor_discord_id=int(j.user.id),
                    reason=notes,
                )
                if result.success:
                    await mge_embed_manager.refresh_mge_boards(
                        bot=j.client,
                        event_id=self.event_id,
                        refresh_public=True,
                        refresh_leadership=True,
                    )
                await send_ephemeral(j, ("✅ " if result.success else "❌ ") + result.message)

            await i.response.send_modal(
                _NotesOnlyModal(title="Reject Signup", event_id=self.event_id, on_submit=_submit)
            )

        await send_ephemeral(
            interaction,
            "Select signup to reject:",
            view=_Step1SelectionView(
                event_id=self.event_id,
                title="Choose signup",
                options=options,
                on_pick=_on_pick,
            ),
        )

    @discord.ui.button(
        label="Reset Ranks", style=discord.ButtonStyle.danger, row=1, custom_id="mge_lead_reset"
    )
    async def reset_ranks(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        await send_ephemeral(
            interaction,
            "⚠️ Confirm reset: this clears manual order overrides for active roster/waitlist rows.",
            view=_ResetRanksConfirmView(event_id=self.event_id),
        )

    @discord.ui.button(
        label="Step 2: Generate Targets",
        style=discord.ButtonStyle.secondary,
        row=2,
        custom_id="mge_lead_generate_targets",
    )
    async def generate_targets(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(_GenerateTargetsModal(event_id=self.event_id))

    @discord.ui.button(
        label="Step 2a: Override Targets",
        style=discord.ButtonStyle.secondary,
        row=2,
        custom_id="mge_lead_override_targets",
    )
    async def override_targets(
        self,
        button: discord.ui.Button,
        interaction: discord.Interaction,
    ) -> None:
        del button
        if not await self._guard(interaction):
            return

        payload = await self._load_board_payload()
        # Targets are relevant for active rows (roster + waitlist)
        candidates = list(payload.get("selection_data", {}).get("roster_rows", [])) + list(
            payload.get("selection_data", {}).get("waitlist_rows", [])
        )
        options = _build_step1_options(candidates, value_key="AwardId")
        if not options:
            await send_ephemeral(interaction, "⚠️ No active awards available to override.")
            return

        async def _on_pick(i: discord.Interaction, value: str) -> None:
            award_id = int(value)

            class _OverrideTargetForSelectedAwardModal(discord.ui.Modal):
                def __init__(self, *, event_id: int, selected_award_id: int) -> None:
                    super().__init__(title="Override Target", timeout=300)
                    self.event_id = int(event_id)
                    self.selected_award_id = int(selected_award_id)
                    self.target_score = discord.ui.InputText(
                        label="Target Score",
                        required=True,
                        placeholder="7500000",
                        max_length=20,
                    )
                    self.add_item(self.target_score)

                async def callback(self, modal_interaction: discord.Interaction) -> None:
                    if not is_admin_or_leadership_interaction(modal_interaction):
                        await send_ephemeral(modal_interaction, "❌ Leadership/admin only.")
                        return
                    try:
                        target_score = int(str(self.target_score.value).strip())
                    except Exception:
                        await send_ephemeral(modal_interaction, "❌ Invalid target score.")
                        return

                    result = await asyncio.to_thread(
                        mge_publish_service.override_target_score,
                        award_id=self.selected_award_id,
                        target_score=target_score,
                        actor_discord_id=int(modal_interaction.user.id),
                    )
                    if result.success:
                        await mge_embed_manager.refresh_mge_boards(
                            bot=modal_interaction.client,
                            event_id=self.event_id,
                            refresh_public=True,
                            refresh_leadership=True,
                            refresh_awards=True,
                        )
                    await send_ephemeral(
                        modal_interaction,
                        ("✅ " if result.success else "❌ ") + result.message,
                    )

            await i.response.send_modal(
                _OverrideTargetForSelectedAwardModal(
                    event_id=self.event_id,
                    selected_award_id=award_id,
                )
            )

        await send_ephemeral(
            interaction,
            "Select active award to override target:",
            view=_Step1SelectionView(
                event_id=self.event_id,
                title="Choose award",
                options=options,
                on_pick=_on_pick,
            ),
        )

    @discord.ui.button(
        label="Step 3: Publish / Republish",
        style=discord.ButtonStyle.success,
        row=2,
        custom_id="mge_lead_publish",
    )
    async def publish_stub(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        await send_ephemeral(
            interaction,
            "Confirm publish / republish for the current roster.",
            view=_PublishConfirmView(event_id=self.event_id),
        )

    @discord.ui.button(
        label="Step 3a: Unpublish",
        style=discord.ButtonStyle.secondary,
        row=2,
        custom_id="mge_lead_unpublish",
    )
    async def unpublish_stub(
        self, button: discord.ui.Button, interaction: discord.Interaction
    ) -> None:
        del button
        if not await self._guard(interaction):
            return
        await send_ephemeral(
            interaction,
            "⚠️ Confirm unpublish: this removes the posted award board and reopens editability.",
            view=_UnpublishConfirmView(event_id=self.event_id),
        )
