from __future__ import annotations

import logging

import discord

from ark.dal.ark_dal import get_match, get_roster, insert_audit_log
from ark.team_balancer import auto_balance_team_ids
from ark.team_publish import publish_ark_teams
from ark.team_state import ArkTeamStateStore
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


def _build_embed(match: dict, assignment, player_rows: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="Ark Team Builder", color=discord.Color.blurple())
    embed.add_field(
        name="Match",
        value=f"{match.get('Alliance') or 'Unknown'} (ID {match.get('MatchId')})",
        inline=False,
    )

    # existing summary/counters can stay
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


class ArkTeamBuilderView(discord.ui.View):
    def __init__(self, *, match_id: int, actor_discord_id: int):
        super().__init__(timeout=300.0)
        self.match_id = int(match_id)
        self.actor_discord_id = int(actor_discord_id)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if int(interaction.user.id) != self.actor_discord_id and not _is_admin_or_leadership(
            interaction
        ):
            await interaction.response.send_message(
                "❌ You can’t use this team builder.", ephemeral=True
            )
            return False
        return True

    async def _load(self):
        match = await get_match(self.match_id)
        if not match:
            return None, None, None
        roster = await get_roster(self.match_id)
        player_rows = [
            r
            for r in roster
            if (r.get("Status") or "").lower() == "active"
            and (r.get("SlotType") or "").lower() == "player"
            and r.get("GovernorId") is not None
        ]
        roster_ids = [int(r["GovernorId"]) for r in player_rows]
        store = ArkTeamStateStore.load()
        assignment = store.get_or_create(
            match_id=self.match_id,
            roster_player_ids=roster_ids,
            actor_discord_id=self.actor_discord_id,
        )
        assignment.normalize()
        store.save()
        return match, player_rows, (store, assignment)

    async def _refresh(self, interaction: discord.Interaction):
        match, player_rows, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        _, assignment = pair
        embed = _build_embed(match, assignment, player_rows)  # pass rows
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

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
        store, assignment = pair
        t1, t2 = auto_balance_team_ids(player_rows)
        assignment.team1_player_ids = t1
        assignment.team2_player_ids = t2
        assignment.status = "draft"
        assignment.updated_by_discord_id = interaction.user.id
        assignment.normalize()
        store.save()

        await insert_audit_log(
            action_type="ark_team_autobalance",
            actor_discord_id=interaction.user.id,
            match_id=self.match_id,
            governor_id=None,
            details_json={"team1_count": len(t1), "team2_count": len(t2)},
        )
        await self._refresh(interaction)

    @discord.ui.button(label="Reset Teams", style=discord.ButtonStyle.danger)
    async def reset(self, button: discord.ui.Button, interaction: discord.Interaction):
        match, _, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        store, assignment = pair
        assignment.team1_player_ids = []
        assignment.team2_player_ids = []
        assignment.status = "draft"
        assignment.updated_by_discord_id = interaction.user.id
        store.save()
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
        match, _, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        channel_id = int(interaction.channel_id)
        ok = await publish_ark_teams(
            client=interaction.client,
            match_id=self.match_id,
            target_channel_id=channel_id,
            actor_discord_id=interaction.user.id,
            store=pair[0],
        )
        if not ok:
            await interaction.response.send_message("❌ Failed to publish teams.", ephemeral=True)
            return
        await self._refresh(interaction)

    async def _assign(self, interaction: discord.Interaction, *, target_team: int):
        match, player_rows, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        store, assignment = pair

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
            gid = int(governor_id)
            if gid in assignment.team1_player_ids or gid in assignment.team2_player_ids:
                await inter.response.send_message("❌ Already assigned.", ephemeral=True)
                return
            if target_team == 1:
                assignment.team1_player_ids.append(gid)
            else:
                assignment.team2_player_ids.append(gid)
            assignment.status = "draft"
            assignment.updated_by_discord_id = inter.user.id
            assignment.normalize()
            store.save()
            await self._refresh(inter)

        view = discord.ui.View(timeout=120.0)
        view.add_item(_GovSelect(placeholder="Select player", options=options, on_pick=_pick))
        await interaction.response.send_message("Select a player:", view=view, ephemeral=True)

    async def _remove(self, interaction: discord.Interaction, *, from_team: int):
        match, player_rows, pair = await self._load()
        if not match or not pair:
            await interaction.response.send_message("❌ Match not found.", ephemeral=True)
            return
        store, assignment = pair

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
            gid = int(governor_id)
            team_ids = (
                assignment.team1_player_ids if from_team == 1 else assignment.team2_player_ids
            )
            if gid not in team_ids:
                await inter.response.send_message(
                    "❌ Player is no longer in that team.", ephemeral=True
                )
                return

            team_ids.remove(gid)
            assignment.status = "draft"
            assignment.updated_by_discord_id = inter.user.id
            assignment.normalize()
            store.save()

            await insert_audit_log(
                action_type="ark_team_remove",
                actor_discord_id=inter.user.id,
                match_id=self.match_id,
                governor_id=gid,
                details_json={"from_team": from_team},
            )

            await self._refresh(inter)

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
