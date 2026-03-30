from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import discord

from ark.dal.ark_dal import (
    get_match,
    get_roster,
    insert_audit_log,
    list_match_team_rows,
    mark_teams_first_published,
)
from ark.embeds import resolve_ark_match_datetime
from ark.team_state import ArkTeamAssignment, ArkTeamStateStore
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)

MENTION_CHUNK_LIMIT = 1800


async def _assignment_from_sql(match_id: int) -> ArkTeamAssignment | None:
    rows = await list_match_team_rows(match_id=int(match_id), draft_only=False)
    final_rows = [r for r in (rows or []) if int(r.get("IsFinal") or 0) == 1]
    source_rows = final_rows or [r for r in (rows or []) if int(r.get("IsDraft") or 0) == 1]
    if not source_rows:
        return None

    team1: list[int] = []
    team2: list[int] = []
    seen: set[int] = set()
    for row in source_rows:
        gid = row.get("GovernorId")
        team_no = row.get("TeamNumber")
        if gid is None or team_no is None:
            continue
        gid_i = int(gid)
        if gid_i in seen:
            continue
        seen.add(gid_i)
        if int(team_no) == 1:
            team1.append(gid_i)
        elif int(team_no) == 2:
            team2.append(gid_i)

    assignment = ArkTeamAssignment(match_id=int(match_id))
    assignment.roster_player_ids = list(team1) + list(team2)
    assignment.team1_player_ids = team1
    assignment.team2_player_ids = team2
    assignment.status = "published"
    assignment.normalize()
    return assignment


def _governor_map(roster: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for row in roster or []:
        gid = row.get("GovernorId")
        if gid is not None:
            result[int(gid)] = row
    return result


def _header_embed(
    match: dict[str, Any],
    assignment: ArkTeamAssignment,
) -> discord.Embed:
    match_dt = resolve_ark_match_datetime(
        match["ArkWeekendDate"],
        match["MatchDay"],
        match["MatchTimeUtc"],
    )
    match_dt_aware = ensure_aware_utc(match_dt) if match_dt else None
    alliance = str(match.get("Alliance") or "Unknown").strip()

    title = f"⚔️ Ark Teams — {alliance}"
    description_lines: list[str] = []
    if match_dt_aware:
        ts = int(match_dt_aware.timestamp())
        description_lines.append(f"🕐 Match time: <t:{ts}:F>")
    status_label = (assignment.status or "").replace("_", " ").title()
    description_lines.append(f"📋 Status: {status_label}")

    embed = discord.Embed(
        title=title,
        description="\n".join(description_lines),
        color=discord.Color.gold(),
    )
    return embed


def _team_embed(
    team_name: str,
    player_ids: list[int],
    rows_by_gid: dict[int, dict[str, Any]],
) -> discord.Embed:
    lines: list[str] = []
    for gid in player_ids:
        row = rows_by_gid.get(gid)
        name = str((row or {}).get("GovernorNameSnapshot") or f"Governor {gid}")
        lines.append(f"• {name}")

    embed = discord.Embed(
        title=team_name,
        description="\n".join(lines) if lines else "*(no players)*",
        color=discord.Color.blue() if "1" in team_name else discord.Color.red(),
    )
    embed.set_footer(text=f"{len(player_ids)} player(s)")
    return embed


async def _send_mention_message(
    *,
    channel: Any,
    match: dict[str, Any],
    assignment: ArkTeamAssignment,
    rows_by_gid: dict[int, dict[str, Any]],
    match_id: int,
) -> None:
    """Build and send the @mention message for first-publish.

    Chunked to stay under MENTION_CHUNK_LIMIT. CR6: the length guard covers the
    full composed message (header line + mention tokens together).
    """
    all_assigned_ids = set(assignment.team1_player_ids) | set(assignment.team2_player_ids)
    mention_parts: list[str] = []
    no_discord_names: list[str] = []

    for gid in sorted(all_assigned_ids):
        row = rows_by_gid.get(gid)
        if not row:
            continue
        uid = row.get("DiscordUserId")
        if uid:
            mention_parts.append(f"<@{int(uid)}>")
        else:
            name = str(row.get("GovernorNameSnapshot") or f"Governor {gid}")
            no_discord_names.append(name)

    if not mention_parts and not no_discord_names:
        logger.warning(
            "[ARK_TEAM_PUBLISH] mention_message_skipped match_id=%s reason=no_players_in_roster_map",
            match_id,
        )
        return

    alliance = str(match.get("Alliance") or "").strip()
    header_line = f"🏆 **Ark teams have been published — {alliance}!**"

    # CR6: build full candidate message first to measure length before sending.
    # Chunk mention tokens so no single message exceeds MENTION_CHUNK_LIMIT
    # (measured against the full composed string: header + mentions).
    chunks: list[list[str]] = []
    current_chunk: list[str] = []
    # Reserve space for header line + newline + trailing no_discord line
    no_discord_suffix = (
        f"\n*(No Discord link: {', '.join(no_discord_names)})*" if no_discord_names else ""
    )
    header_cost = len(header_line) + 1  # +1 for the newline before mention block
    suffix_cost = len(no_discord_suffix)

    for token in mention_parts:
        candidate = " ".join(current_chunk + [token])
        full_msg_len = header_cost + len(candidate) + (suffix_cost if not chunks else 0)
        if current_chunk and full_msg_len > MENTION_CHUNK_LIMIT:
            chunks.append(current_chunk)
            current_chunk = [token]
        else:
            current_chunk.append(token)
    if current_chunk:
        chunks.append(current_chunk)

    if not chunks:
        # Only no_discord names — send a single message
        chunks = [[]]

    for i, chunk in enumerate(chunks):
        content_lines = [header_line]
        if chunk:
            content_lines.append(" ".join(chunk))
        # Append no_discord names to the last chunk only
        if i == len(chunks) - 1 and no_discord_names:
            content_lines.append(f"*(No Discord link: {', '.join(no_discord_names)})*")
        await channel.send(
            content="\n".join(content_lines),
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    logger.info(
        "[ARK_TEAM_PUBLISH] mention_message_sent match_id=%s pinged=%s no_discord=%s chunks=%s",
        match_id,
        len(mention_parts),
        len(no_discord_names),
        len(chunks),
    )


async def publish_ark_teams(
    *,
    client: Any,
    match_id: int,
    target_channel_id: int,
    actor_discord_id: int,
    store: ArkTeamStateStore | None = None,
) -> bool:
    """Publish the final Ark team assignment to Discord.

    Sends three embed messages (header, team 1, team 2) and, on first publish only,
    a fourth plain-text message that @mentions every assigned player.

    First-publish detection uses SQL (TeamsFirstPublishedAtUtc) so the flag
    survives bot restarts. The in-memory ``assignment.published_at_utc`` check
    is no longer used for this purpose (Part 3 / H-SQL).

    Returns True on success, False if required data is missing.
    A failure in the mention message does not cause this function to return False.

    Discord API failures during the embed sends or edits (for example, from
    ``channel.send``, ``fetch_message``, or ``edit``) are not caught by this
    function and will propagate as exceptions (such as ``discord.HTTPException``,
    ``discord.Forbidden``, or ``discord.NotFound``).
    """
    assignment: ArkTeamAssignment | None = None
    if store is not None:
        assignment = store.assignments.get(int(match_id))
    if assignment is None:
        assignment = await _assignment_from_sql(int(match_id))
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

    # Part 3 (H-SQL): Replace in-memory published_at_utc check with SQL flag.
    # mark_teams_first_published is idempotent — returns True only on first publish.
    is_first_publish = await mark_teams_first_published(int(match_id))

    # Keep published_at_utc on the assignment object in sync for any callers that
    # read it, but do NOT use it for first-publish detection.
    assignment.status = "published"
    assignment.published_at_utc = datetime.utcnow().isoformat() + "Z"
    assignment.updated_by_discord_id = actor_discord_id
    assignment.normalize()

    header = _header_embed(match, assignment)
    t1 = _team_embed("Ark Team 1", assignment.team1_player_ids, rows_by_gid)
    t2 = _team_embed("Ark Team 2", assignment.team2_player_ids, rows_by_gid)

    async def _send_or_edit(message_id: int | None, embed: discord.Embed) -> int:
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
    if store is not None:
        store.save()

    if is_first_publish:
        try:
            await _send_mention_message(
                channel=channel,
                match=match,
                assignment=assignment,
                rows_by_gid=rows_by_gid,
                match_id=match_id,
            )
        except Exception:
            logger.exception(
                "[ARK_TEAM_PUBLISH] mention_message_failed match_id=%s — continuing",
                match_id,
            )

    await insert_audit_log(
        action_type="ark_team_publish",
        actor_discord_id=actor_discord_id,
        match_id=match_id,
        governor_id=None,
        details_json={
            "team1_count": len(assignment.team1_player_ids),
            "team2_count": len(assignment.team2_player_ids),
            "channel_id": int(target_channel_id),
            "is_first_publish": is_first_publish,
        },
    )
    return True
