from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import ClassVar

import discord

from ark.ark_draft_service import (
    ArkDraftPreconditionError,
    generate_draft_for_match,
    sync_manual_draft,
)
from ark.confirm_publish_service import (
    ArkPublishPreconditionError,
    load_team_review_state,
    publish_reviewed_teams,
    unpublish_final_teams,
)
from ark.dal.ark_dal import insert_audit_log
from decoraters import _has_leadership_role, _is_admin

logger = logging.getLogger(__name__)


def _name_from_row(row: dict) -> str:
    return (
        str(row.get("GovernorNameSnapshot") or row.get("GovernorName") or "Unknown").strip()
        or "Unknown"
    )


def _format_name_list(names: list[str], *, limit: int = 20) -> str:
    if not names:
        return "—"
    shown = names[:limit]
    lines = [f"{i+1}. {n}" for i, n in enumerate(shown)]
    if len(names) > limit:
        lines.append(f"… +{len(names) - limit} more")
    return "\n".join(lines)


def _is_admin_or_leadership(interaction: discord.Interaction) -> bool:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    guild = getattr(interaction, "guild", None)
    if not member and guild:
        try:
            member = guild.get_member(interaction.user.id)
        except Exception:
            member = None
    return bool(_is_admin(interaction.user) or _has_leadership_role(member))


def _build_embed(match: dict, assignment: _Assignment, player_rows: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="Ark Team Builder", color=discord.Color.blurple())
    embed.add_field(
        name="Match",
        value=f"{match.get('Alliance') or 'Unknown'} (ID {match.get('MatchId')})",
        inline=False,
    )

    team1_ids = list(assignment.team1_player_ids or [])
    team2_ids = list(assignment.team2_player_ids or [])
    unassigned_ids = list(assignment.unassigned_player_ids() or [])

    roster_by_id = {
        int(r["GovernorId"]): r for r in (player_rows or []) if r.get("GovernorId") is not None
    }

    team1_names = [_name_from_row(roster_by_id[g]) for g in team1_ids if g in roster_by_id]
    team2_names = [_name_from_row(roster_by_id[g]) for g in team2_ids if g in roster_by_id]
    unassigned_names = [
        _name_from_row(roster_by_id[g]) for g in unassigned_ids if g in roster_by_id
    ]

    embed.add_field(
        name=f"Team 1 ({len(team1_names)})",
        value=_format_name_list(team1_names, limit=25),
        inline=False,
    )
    embed.add_field(
        name=f"Team 2 ({len(team2_names)})",
        value=_format_name_list(team2_names, limit=25),
        inline=False,
    )
    embed.add_field(
        name=f"Unassigned ({len(unassigned_names)})",
        value=_format_name_list(unassigned_names, limit=25),
        inline=False,
    )

    return embed


class _GovSelect(discord.ui.Select):
    def __init__(self, *, placeholder: str, options: list[discord.SelectOption], on_pick):
        super().__init__(placeholder=placeholder, options=options[:25], min_values=1, max_values=1)
        self._on_pick = on_pick

    async def callback(self, interaction: discord.Interaction):
        await self._on_pick(interaction, self.values[0])


@dataclass
class _Assignment:
    roster_player_ids: list[int]
    team1_player_ids: list[int]
    team2_player_ids: list[int]

    def normalize(self) -> None:
        roster = [int(x) for x in (self.roster_player_ids or [])]
        roster_set = set(roster)

        seen: set[int] = set()
        t1: list[int] = []
        for gid in self.team1_player_ids or []:
            g = int(gid)
            if g in roster_set and g not in seen:
                t1.append(g)
                seen.add(g)

        t2: list[int] = []
        for gid in self.team2_player_ids or []:
            g = int(gid)
            if g in roster_set and g not in seen:
                t2.append(g)
                seen.add(g)

        self.roster_player_ids = roster
        self.team1_player_ids = t1
        self.team2_player_ids = t2

    def unassigned_player_ids(self) -> list[int]:
        assigned = set(self.team1_player_ids) | set(self.team2_player_ids)
        return [gid for gid in self.roster_player_ids if gid not in assigned]


class ArkTeamBuilderView(discord.ui.View):
    # Class-level registry: (match_id, user_id) -> discord.Webhook
    # Stores the followup webhook of the most-recently-opened team builder for
    # each (match, user) pair.  Used both to deduplicate open() calls and to
    # edit the team builder message from inside select _pick callbacks where
    # inter.edit_original_response would target the dropdown, not the builder.
    _active_webhooks: ClassVar[dict[tuple[int, int], discord.Webhook]] = {}

    def __init__(self, *, match_id: int, actor_discord_id: int):
        super().__init__(timeout=300.0)
        self.match_id = int(match_id)
        self.actor_discord_id = int(actor_discord_id)
        self._registry_key = (self.match_id, self.actor_discord_id)

    # ------------------------------------------------------------------
    # Public factory: open or refresh the team builder
    # ------------------------------------------------------------------

    @classmethod
    async def open(
        cls,
        *,
        match_id: int,
        actor_discord_id: int,
        interaction: discord.Interaction,
        content: str = "Ark Team Review",
    ) -> None:
        """
        Open (or refresh) the team builder for (match_id, actor_discord_id).

        If a previous team builder message is already open for this pair the
        existing ephemeral message is edited in place via the stored followup
        webhook.  Otherwise a fresh ephemeral message is sent and its followup
        webhook is stored for future reuse.
        """
        view = cls(match_id=match_id, actor_discord_id=actor_discord_id)
        embed = await view.build_current_embed()
        if embed is None:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        key = (int(match_id), int(actor_discord_id))
        existing_webhook = cls._active_webhooks.get(key)

        if existing_webhook is not None:
            try:
                await existing_webhook.edit_message(
                    "@original", content=content, embed=embed, view=view
                )
                await interaction.response.defer()
                logger.info(
                    "[ARK_TEAM_BUILDER] reused_existing_message match_id=%s user_id=%s",
                    match_id,
                    actor_discord_id,
                )
                return
            except discord.HTTPException as exc:
                logger.info(
                    "[ARK_TEAM_BUILDER] existing_webhook_expired match_id=%s user_id=%s error=%s — sending new message",
                    match_id,
                    actor_discord_id,
                    str(exc),
                )
                cls._active_webhooks.pop(key, None)

        await interaction.response.send_message(content, embed=embed, view=view, ephemeral=True)
        cls._active_webhooks[key] = interaction.followup
        logger.info(
            "[ARK_TEAM_BUILDER] new_message match_id=%s user_id=%s",
            match_id,
            actor_discord_id,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_timeout(self) -> None:
        ArkTeamBuilderView._active_webhooks.pop(self._registry_key, None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(interaction.user.id) != self.actor_discord_id and not _is_admin_or_leadership(
            interaction
        ):
            await interaction.response.send_message(
                "❌ You can't use this team builder.", ephemeral=True
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load(self):
        try:
            state = await load_team_review_state(self.match_id)
        except ArkPublishPreconditionError:
            return None, [], None
        assignment = _Assignment(
            roster_player_ids=[int(r["GovernorId"]) for r in state.player_rows],
            team1_player_ids=list(state.team1_ids),
            team2_player_ids=list(state.team2_ids),
        )
        assignment.normalize()
        return state.match, state.player_rows, assignment

    async def build_current_embed(self) -> discord.Embed | None:
        match, player_rows, assignment = await self._load()
        if not match or not assignment:
            return None
        return _build_embed(match, assignment, player_rows or [])

    async def _refresh_via_webhook(self, *, notice: str | None = None) -> bool:
        """
        Edit the team builder message in place using the stored followup webhook.

        This is the correct path for calls originating from select _pick
        callbacks, where the interaction belongs to the dropdown message — not
        the team builder message.  Using the stored webhook always targets the
        team builder, regardless of which interaction triggered the update.

        Returns True if the edit succeeded, False if the webhook was missing or
        the edit failed (token expired).
        """
        webhook = ArkTeamBuilderView._active_webhooks.get(self._registry_key)
        if webhook is None:
            logger.warning(
                "[ARK_TEAM_BUILDER] _refresh_via_webhook no_webhook match_id=%s user_id=%s",
                self.match_id,
                self.actor_discord_id,
            )
            return False

        embed = await self.build_current_embed()
        if embed is None:
            return False

        content = notice or "Ark Team Review"
        try:
            await webhook.edit_message("@original", content=content, embed=embed, view=self)
            logger.info(
                "[ARK_TEAM_BUILDER] refreshed_via_webhook match_id=%s user_id=%s",
                self.match_id,
                self.actor_discord_id,
            )
            return True
        except discord.HTTPException as exc:
            logger.warning(
                "[ARK_TEAM_BUILDER] webhook_edit_failed match_id=%s user_id=%s error=%s",
                self.match_id,
                self.actor_discord_id,
                str(exc),
            )
            ArkTeamBuilderView._active_webhooks.pop(self._registry_key, None)
            return False

    async def _refresh(
        self, interaction: discord.Interaction, *, notice: str | None = None
    ) -> None:
        """
        Edit the team builder message in place for direct button interactions.

        For button interactions interaction.response is still fresh, so
        edit_message edits the team builder embed directly (the button IS on
        the team builder message).

        Do NOT call this from select _pick callbacks — use _refresh_via_webhook
        instead, because the select interaction belongs to a different (dropdown)
        message.
        """
        embed = await self.build_current_embed()
        if not embed:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        content = notice or "Ark Team Review"
        await interaction.response.edit_message(content=content, embed=embed, view=self)

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    @discord.ui.button(label="Assign to Team 1", style=discord.ButtonStyle.primary)
    async def assign_team1(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._assign(interaction, target_team=1)

    @discord.ui.button(label="Assign to Team 2", style=discord.ButtonStyle.primary)
    async def assign_team2(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._assign(interaction, target_team=2)

    @discord.ui.button(label="Remove from Team 1", style=discord.ButtonStyle.secondary)
    async def remove_team1(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._remove(interaction, from_team=1)

    @discord.ui.button(label="Remove from Team 2", style=discord.ButtonStyle.secondary)
    async def remove_team2(self, button: discord.ui.Button, interaction: discord.Interaction):
        await self._remove(interaction, from_team=2)

    @discord.ui.button(label="Auto-Balance Teams", style=discord.ButtonStyle.success)
    async def auto_balance(self, button: discord.ui.Button, interaction: discord.Interaction):
        match, player_rows, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        assignment = pair
        try:
            result = await generate_draft_for_match(
                self.match_id,
                actor_discord_id=interaction.user.id,
                source="team_builder_button",
                roster_rows=player_rows,
            )
        except ArkDraftPreconditionError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        except Exception:
            logger.exception("[ARK_TEAM] Auto-draft failed match_id=%s", self.match_id)
            await interaction.response.send_message(
                "❌ Failed to auto-draft teams.", ephemeral=True
            )
            return

        assignment.team1_player_ids = list(result.team1_ids)
        assignment.team2_player_ids = list(result.team2_ids)
        assignment.normalize()

        await insert_audit_log(
            action_type="ark_team_autobalance",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=None,
            details_json={
                "team1_count": len(result.team1_ids),
                "team2_count": len(result.team2_ids),
                "team1_power": result.team1_power,
                "team2_power": result.team2_power,
                "assigned_by_preference": result.assigned_by_preference,
                "assigned_by_balancer": result.assigned_by_balancer,
            },
        )
        await self._refresh(interaction)

    @discord.ui.button(label="Reset Teams", style=discord.ButtonStyle.danger)
    async def reset(self, button: discord.ui.Button, interaction: discord.Interaction):
        match, _, assignment = await self._load()
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        try:
            await sync_manual_draft(
                match_id=self.match_id,
                team1_ids=[],
                team2_ids=[],
                actor_discord_id=interaction.user.id,
                source="team_builder_reset",
            )
        except ArkDraftPreconditionError as exc:
            await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
            return
        await insert_audit_log(
            action_type="ark_team_reset",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=None,
            details_json={},
        )
        await self._refresh(interaction)

    @discord.ui.button(label="Publish Teams", style=discord.ButtonStyle.success, row=2)
    async def publish(self, button: discord.ui.Button, interaction: discord.Interaction):
        match, _, _ = await self._load()
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        # Defer immediately — publish_reviewed_teams sends multiple Discord messages
        # (3 embeds + optional mention message) and will exceed the 3-second
        # interaction deadline.  Deferring keeps the interaction token alive and
        # lets us use the followup webhook for the final edit.
        await interaction.response.defer()

        try:
            result = await publish_reviewed_teams(
                client=interaction.client,
                match_id=self.match_id,
                actor_discord_id=interaction.user.id,
            )
        except ArkPublishPreconditionError as exc:
            await interaction.followup.send(f"❌ {exc}", ephemeral=True)
            return
        except Exception:
            logger.exception("[ARK_TEAM] publish failed match_id=%s", self.match_id)
            await interaction.followup.send("❌ Failed to publish teams.", ephemeral=True)
            return

        notice = (
            f"✅ Teams published to confirmation channel (<#{result.confirmation_channel_id}>)."
        )
        # Use the stored followup webhook to edit the team builder message.
        # interaction.response is already consumed by the defer above, so
        # _refresh (which calls response.edit_message) would 404.
        refreshed = await self._refresh_via_webhook(notice=notice)
        if not refreshed:
            # Webhook unavailable (session restart, timeout, etc.) — fall back
            # to a followup message so the user always gets confirmation.
            await interaction.followup.send(notice, ephemeral=True)

    @discord.ui.button(label="Unpublish Teams", style=discord.ButtonStyle.secondary, row=2)
    async def unpublish(self, button: discord.ui.Button, interaction: discord.Interaction):
        match, _, _ = await self._load()
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        removed = await unpublish_final_teams(
            match_id=self.match_id,
            actor_discord_id=interaction.user.id,
        )
        await self._refresh(
            interaction,
            notice=f"✅ Unpublished final teams (removed {removed} final rows).",
        )

    # ------------------------------------------------------------------
    # Select-driven actions
    # ------------------------------------------------------------------

    async def _assign(self, interaction: discord.Interaction, *, target_team: int):
        match, player_rows, assignment = await self._load()
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        assigned = set(assignment.team1_player_ids) | set(assignment.team2_player_ids)
        eligible = [r for r in player_rows if int(r["GovernorId"]) not in assigned]
        if not eligible:
            await interaction.response.send_message("ℹ️ No unassigned players.", ephemeral=True)
            return

        options = [
            discord.SelectOption(
                label=f"{str(r.get('GovernorNameSnapshot') or 'Unknown')[:80]} • {r.get('GovernorId')}",
                value=str(r["GovernorId"]),
            )
            for r in eligible[:25]
        ]

        async def _pick(inter: discord.Interaction, governor_id: str):
            # ACK the select interaction with a deferred update so Discord does
            # not show "interaction failed".  We do NOT use inter for any further
            # edits — the team builder message belongs to a different interaction
            # context.  _refresh_via_webhook targets it correctly via the stored
            # followup webhook.
            await inter.response.defer()

            gid = int(governor_id)
            if gid in assignment.team1_player_ids or gid in assignment.team2_player_ids:
                await inter.followup.send("❌ Already assigned.", ephemeral=True)
                return
            if target_team == 1:
                assignment.team1_player_ids.append(gid)
            else:
                assignment.team2_player_ids.append(gid)
            assignment.normalize()
            try:
                await sync_manual_draft(
                    match_id=self.match_id,
                    team1_ids=assignment.team1_player_ids,
                    team2_ids=assignment.team2_player_ids,
                    actor_discord_id=inter.user.id,
                    source="team_builder_assign",
                )
            except ArkDraftPreconditionError as exc:
                await inter.followup.send(f"❌ {exc}", ephemeral=True)
                return

            ok = await self._refresh_via_webhook()
            if not ok:
                await inter.followup.send(
                    "✅ Player assigned. Dismiss this and re-open the team builder to see the update.",
                    ephemeral=True,
                )

        view = discord.ui.View(timeout=120.0)
        view.add_item(_GovSelect(placeholder="Select player", options=options, on_pick=_pick))
        await interaction.response.send_message("Select a player:", view=view, ephemeral=True)

    async def _remove(self, interaction: discord.Interaction, *, from_team: int):
        match, player_rows, assignment = await self._load()
        if not match:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return

        source_ids = assignment.team1_player_ids if from_team == 1 else assignment.team2_player_ids
        if not source_ids:
            await interaction.response.send_message(
                f"ℹ️ Team {from_team} has no players to remove.", ephemeral=True
            )
            return

        rows_by_gid = {
            int(r["GovernorId"]): r for r in (player_rows or []) if r.get("GovernorId") is not None
        }

        options = [
            discord.SelectOption(
                label=f"{str((rows_by_gid.get(gid) or {}).get('GovernorNameSnapshot') or 'Unknown')[:80]} • {gid}",
                value=str(gid),
            )
            for gid in source_ids[:25]
        ]

        async def _pick(inter: discord.Interaction, governor_id: str):
            # ACK the select interaction with a deferred update so Discord does
            # not show "interaction failed".  All further updates go through
            # _refresh_via_webhook which targets the team builder message via
            # the stored followup webhook, not the dropdown message.
            await inter.response.defer()

            gid = int(governor_id)
            team_ids = (
                assignment.team1_player_ids if from_team == 1 else assignment.team2_player_ids
            )
            if gid not in team_ids:
                await inter.followup.send("❌ Player is no longer in that team.", ephemeral=True)
                return

            team_ids.remove(gid)
            assignment.normalize()
            try:
                await sync_manual_draft(
                    match_id=self.match_id,
                    team1_ids=assignment.team1_player_ids,
                    team2_ids=assignment.team2_player_ids,
                    actor_discord_id=inter.user.id,
                    source="team_builder_remove",
                )
            except ArkDraftPreconditionError as exc:
                await inter.followup.send(f"❌ {exc}", ephemeral=True)
                return

            await insert_audit_log(
                action_type="ark_team_remove",
                actor_discord_id=inter.user.id,
                match_id=self.match_id,
                governor_id=gid,
                details_json={"from_team": from_team},
            )

            ok = await self._refresh_via_webhook()
            if not ok:
                await inter.followup.send(
                    "✅ Player removed. Dismiss this and re-open the team builder to see the update.",
                    ephemeral=True,
                )

        view = discord.ui.View(timeout=120.0)
        view.add_item(
            _GovSelect(
                placeholder=f"Select player from Team {from_team}",
                options=options,
                on_pick=_pick,
            )
        )
        await interaction.response.send_message(
            "Select a player to remove:", view=view, ephemeral=True
        )
