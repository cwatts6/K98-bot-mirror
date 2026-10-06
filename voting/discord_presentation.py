from __future__ import annotations

from datetime import UTC, datetime

import discord

from voting.models import VoteSnapshot
from voting.outcomes import vote_outcome
from voting.render_service import render_vote_card
from voting.result_visibility import public_results_hidden, result_visibility_label
from voting.vote_modes import VOTE_MODE_MULTI_SELECT, normalize_vote_mode, vote_mode_label


def no_broad_mentions() -> discord.AllowedMentions:
    return discord.AllowedMentions(everyone=False, roles=False, users=False)


def configured_everyone_mentions(enabled: bool) -> discord.AllowedMentions:
    return discord.AllowedMentions(everyone=bool(enabled), roles=False, users=False)


def mention_content(enabled: bool, body: str) -> str:
    return f"@everyone\n{body}" if enabled else body


def message_link(snapshot: VoteSnapshot) -> str:
    if snapshot.message_id is None:
        return f"<#{snapshot.channel_id}>"
    return f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}"


def build_vote_embed(snapshot: VoteSnapshot) -> discord.Embed:
    now = datetime.now(UTC)
    hidden_results = public_results_hidden(snapshot, now_utc=now)
    color = discord.Color.green() if snapshot.status == "Open" else discord.Color.red()
    embed = discord.Embed(
        title=snapshot.title, description=snapshot.description or None, color=color
    )
    embed.add_field(name="Status", value=snapshot.status, inline=True)
    embed.add_field(
        name="Closes",
        value=snapshot.closes_at_utc.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        inline=True,
    )
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
    if hidden_results:
        embed.add_field(name="Results", value="Hidden until close", inline=True)
    else:
        embed.add_field(
            name="Total voters" if is_multi_select else "Total votes",
            value=str(snapshot.total_votes),
            inline=True,
        )
        if is_multi_select:
            embed.add_field(
                name="Total selections",
                value=str(snapshot.total_selections),
                inline=True,
            )
    if is_multi_select:
        embed.add_field(
            name="Vote mode",
            value=(
                f"{vote_mode_label(snapshot.vote_mode)} "
                f"({snapshot.min_selections}-{snapshot.max_selections} selections)"
            ),
            inline=True,
        )
    if not hidden_results and (
        snapshot.status == "Closed"
        or snapshot.closed_at_utc is not None
        or snapshot.closes_at_utc <= now
    ):
        embed.add_field(name="Outcome", value=vote_outcome(snapshot).summary, inline=False)
    if getattr(snapshot, "result_visibility", "PublicLive") != "PublicLive":
        embed.add_field(
            name="Result visibility",
            value=result_visibility_label(snapshot.result_visibility),
            inline=True,
        )
    embed.set_footer(text=f"Vote #{snapshot.vote_post_id}")
    embed.timestamp = now
    embed.set_image(url=f"attachment://vote_{snapshot.vote_post_id}.png")
    return embed


def build_vote_file(snapshot: VoteSnapshot) -> discord.File:
    rendered = render_vote_card(snapshot)
    return discord.File(rendered.image_bytes, filename=rendered.filename)


def build_reminder_embed(snapshot: VoteSnapshot) -> discord.Embed:
    embed = discord.Embed(
        title=f"Vote reminder: {snapshot.title}",
        description=f"Voting closes at {snapshot.closes_at_utc.astimezone(UTC):%Y-%m-%d %H:%M UTC}.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Vote post", value=message_link(snapshot), inline=False)
    embed.set_footer(text=f"Vote #{snapshot.vote_post_id}")
    return embed


def build_close_embed(snapshot: VoteSnapshot) -> discord.Embed:
    outcome = vote_outcome(snapshot)
    embed = discord.Embed(
        title=f"Vote closed: {snapshot.title}",
        description=(
            f"{outcome.summary}\n\n"
            f"Final results are available on the original vote post: {message_link(snapshot)}"
        ),
        color=discord.Color.red(),
    )
    is_multi_select = normalize_vote_mode(snapshot.vote_mode) == VOTE_MODE_MULTI_SELECT
    embed.add_field(
        name="Total voters" if is_multi_select else "Total votes",
        value=str(snapshot.total_votes),
        inline=True,
    )
    if is_multi_select:
        embed.add_field(
            name="Total selections",
            value=str(snapshot.total_selections),
            inline=True,
        )
    embed.set_footer(text=f"Vote #{snapshot.vote_post_id}")
    return embed
