from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import discord

from ark.dal.ark_dal import get_match, get_roster, insert_audit_log
from ark.embeds import resolve_ark_match_datetime
from ark.team_state import ArkTeamAssignment, ArkTeamStateStore
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)


def _governor_map(roster: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for r in roster or []:
        gid = r.get("GovernorId")
        if gid is None:
            continue
        try:
            out[int(gid)] = r
        except Exception:
            continue
    return out


def _fmt_player_line(row: dict[str, Any], idx: int) -> str:
    uid = row.get("DiscordUserId")
    name = str(row.get("GovernorNameSnapshot") or "Unknown")
    gid = row.get("GovernorId")
    if uid:
        return f"{idx}. <@{int(uid)}> — {name} (`{gid}`)"
    return f"{idx}. {name} (`{gid}`)"


def _team_embed(
    title: str, ids: list[int], rows_by_gid: dict[int, dict[str, Any]]
) -> discord.Embed:
    lines: list[str] = []
    for i, gid in enumerate(ids, 1):
        row = rows_by_gid.get(int(gid))
        if row:
            lines.append(_fmt_player_line(row, i))
        else:
            lines.append(f"{i}. Unknown (`{gid}`)")
    e = discord.Embed(title=title, color=discord.Color.blurple())
    e.description = "\n".join(lines) if lines else "—"
    return e


def _header_embed(match: dict[str, Any], assignment: ArkTeamAssignment) -> discord.Embed:
    match_dt = ensure_aware_utc(
        resolve_ark_match_datetime(
            match["ArkWeekendDate"],
            match["MatchDay"],
            match["MatchTimeUtc"],
        )
    )
    e = discord.Embed(title="Ark Teams Published", color=discord.Color.green())
    e.add_field(name="Alliance", value=str(match.get("Alliance") or "Unknown"), inline=False)
    e.add_field(
        name="Match Time (UTC)", value=match_dt.strftime("%Y-%m-%d %H:%M UTC"), inline=False
    )
    e.add_field(name="Status", value=assignment.status, inline=True)
    if assignment.created_by_discord_id:
        e.add_field(name="Created By", value=f"<@{assignment.created_by_discord_id}>", inline=True)
    e.set_footer(text=f"Match ID: {assignment.match_id}")
    return e


async def publish_ark_teams(
    *,
    client,
    match_id: int,
    target_channel_id: int,
    actor_discord_id: int,
    store: ArkTeamStateStore | None = None,
) -> bool:
    store = store or ArkTeamStateStore.load()
    assignment = store.assignments.get(int(match_id))
    if not assignment:
        return False

    match = await get_match(match_id)
    if not match:
        return False

    roster = await get_roster(match_id)
    rows_by_gid = _governor_map(roster)

    channel = client.get_channel(int(target_channel_id))
    if not channel:
        return False

    assignment.status = "published"
    assignment.published_at_utc = datetime.utcnow().isoformat() + "Z"
    assignment.updated_by_discord_id = actor_discord_id
    assignment.normalize()

    header = _header_embed(match, assignment)
    t1 = _team_embed("Ark Team 1", assignment.team1_player_ids, rows_by_gid)
    t2 = _team_embed("Ark Team 2", assignment.team2_player_ids, rows_by_gid)

    async def _send_or_edit(message_id: int | None, embed: discord.Embed):
        if message_id:
            try:
                msg = await channel.fetch_message(int(message_id))
                await msg.edit(embed=embed)
                return int(msg.id)
            except Exception:
                logger.warning("[ARK_TEAM_PUBLISH] Existing message missing, recreating.")
        msg = await channel.send(embed=embed)
        return int(msg.id)

    assignment.published_header_message_id = await _send_or_edit(
        assignment.published_header_message_id, header
    )
    assignment.published_team1_message_id = await _send_or_edit(
        assignment.published_team1_message_id, t1
    )
    assignment.published_team2_message_id = await _send_or_edit(
        assignment.published_team2_message_id, t2
    )
    store.save()

    await insert_audit_log(
        action_type="ark_team_publish",
        actor_discord_id=actor_discord_id,
        match_id=match_id,
        governor_id=None,
        details_json={
            "team1_count": len(assignment.team1_player_ids),
            "team2_count": len(assignment.team2_player_ids),
            "channel_id": int(target_channel_id),
        },
    )
    return True
