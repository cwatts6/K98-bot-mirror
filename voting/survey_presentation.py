from __future__ import annotations

from datetime import UTC, datetime

import discord

from voting.discord_presentation import configured_everyone_mentions, mention_content, no_broad_mentions
from voting.result_visibility import public_results_hidden, result_visibility_label
from voting.survey_models import SurveySnapshot
from voting.survey_render_service import render_survey_card


def message_link(snapshot: SurveySnapshot) -> str:
    if snapshot.message_id is None:
        return f"<#{snapshot.channel_id}>"
    return f"https://discord.com/channels/{snapshot.guild_id}/{snapshot.channel_id}/{snapshot.message_id}"


def build_survey_embed(snapshot: SurveySnapshot) -> discord.Embed:
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
    if hidden_results:
        embed.add_field(name="Results", value="Hidden until close", inline=True)
    else:
        embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
    embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
    if snapshot.result_visibility != "PublicLive":
        embed.add_field(
            name="Result visibility",
            value=result_visibility_label(snapshot.result_visibility),
            inline=True,
        )
    embed.set_footer(text=f"Survey #{snapshot.survey_id}")
    embed.timestamp = now
    embed.set_image(url=f"attachment://survey_{snapshot.survey_id}.png")
    return embed


def build_survey_file(snapshot: SurveySnapshot) -> discord.File:
    rendered = render_survey_card(snapshot)
    return discord.File(rendered.image_bytes, filename=rendered.filename)


def build_survey_reminder_embed(snapshot: SurveySnapshot) -> discord.Embed:
    embed = discord.Embed(
        title=f"Survey reminder: {snapshot.title}",
        description=f"Survey closes at {snapshot.closes_at_utc.astimezone(UTC):%Y-%m-%d %H:%M UTC}.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="Survey post", value=message_link(snapshot), inline=False)
    embed.set_footer(text=f"Survey #{snapshot.survey_id}")
    return embed


def build_survey_close_embed(snapshot: SurveySnapshot) -> discord.Embed:
    embed = discord.Embed(
        title=f"Survey closed: {snapshot.title}",
        description=f"Final results are available on the original survey post: {message_link(snapshot)}",
        color=discord.Color.red(),
    )
    embed.add_field(name="Responses", value=str(snapshot.total_responses), inline=True)
    embed.add_field(name="Questions", value=str(len(snapshot.questions)), inline=True)
    embed.set_footer(text=f"Survey #{snapshot.survey_id}")
    return embed


__all__ = [
    "build_survey_close_embed",
    "build_survey_embed",
    "build_survey_file",
    "build_survey_reminder_embed",
    "configured_everyone_mentions",
    "mention_content",
    "no_broad_mentions",
]
