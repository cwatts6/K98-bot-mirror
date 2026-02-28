from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime, time, timedelta
from typing import Any

import discord

from utils import ensure_aware_utc


def _normalize_match_day(match_day: str) -> str:
    raw = (match_day or "").strip().lower()
    if raw.startswith("sun"):
        return "Sunday"
    if raw.startswith("sat"):
        return "Saturday"
    return match_day


def resolve_ark_match_datetime(
    ark_weekend_date: date,
    match_day: str,
    match_time_utc: time | str,
) -> datetime:
    day = _normalize_match_day(match_day).lower()
    match_date = ark_weekend_date + timedelta(days=1) if day.startswith("sun") else ark_weekend_date
    if isinstance(match_time_utc, str):
        match_time = datetime.strptime(match_time_utc, "%H:%M").time()
    else:
        match_time = match_time_utc
    return ensure_aware_utc(datetime.combine(match_date, match_time))


def _split_lines(lines: list[str], max_chars: int = 1024) -> list[list[str]]:
    chunks: list[list[str]] = []
    current: list[str] = []
    total = 0
    for line in lines:
        safe_line = line if len(line) <= 1000 else f"{line[:997]}…"
        line_len = len(safe_line) + 1
        if current and total + line_len > max_chars:
            chunks.append(current)
            current = [safe_line]
            total = line_len
        else:
            current.append(safe_line)
            total += line_len
    if current:
        chunks.append(current)
    return chunks


def _format_roster_fields(title: str, names: list[str], cap: int) -> list[tuple[str, str]]:
    if not names:
        return [(f"{title} (0/{cap})", "—")]
    numbered = [f"{i + 1}. {name}" for i, name in enumerate(names)]
    chunks = _split_lines(numbered)
    fields: list[tuple[str, str]] = []
    for idx, chunk in enumerate(chunks):
        label = f"{title} ({len(names)}/{cap})" if idx == 0 else f"{title} (cont.)"
        fields.append((label, "\n".join(chunk)))
    return fields


def build_ark_registration_embed(
    *,
    alliance: str,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
    players_cap: int,
    subs_cap: int,
    notes: str | None = None,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    match_dt = ensure_aware_utc(match_datetime_utc)
    close_dt = ensure_aware_utc(signup_close_utc)

    roster = roster or []
    players = [
        (r.get("GovernorNameSnapshot") or "Unknown")
        for r in roster
        if (r.get("SlotType") or "").lower() == "player"
    ]
    subs = [
        (r.get("GovernorNameSnapshot") or "Unknown")
        for r in roster
        if (r.get("SlotType") or "").lower() == "sub"
    ]

    embed = discord.Embed(
        title=f"Ark of Osiris — {alliance}",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Match Time (UTC)",
        value=match_dt.strftime("%Y-%m-%d %H:%M UTC"),
        inline=False,
    )
    embed.add_field(
        name="Signup Close (UTC)",
        value=close_dt.strftime("%Y-%m-%d %H:%M UTC"),
        inline=False,
    )

    for name, value in _format_roster_fields("Players", players, players_cap):
        embed.add_field(name=name, value=value, inline=False)
    for name, value in _format_roster_fields("Subs", subs, subs_cap):
        embed.add_field(name=name, value=value, inline=False)

    if notes:
        embed.add_field(name="Notes", value=notes, inline=False)

    embed.set_footer(text="Signups close Friday 23:00 UTC. After close, contact leadership.")
    return embed


def build_ark_registration_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    match_datetime = resolve_ark_match_datetime(
        match["ArkWeekendDate"],
        match["MatchDay"],
        match["MatchTimeUtc"],
    )
    return build_ark_registration_embed(
        alliance=(match.get("Alliance") or "").strip(),
        match_datetime_utc=match_datetime,
        signup_close_utc=match["SignupCloseUtc"],
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=match.get("Notes"),
        roster=roster,
    )


def build_ark_cancelled_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    embed = build_ark_registration_embed_from_match(
        match,
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
    )
    embed.color = discord.Color.red()
    embed.insert_field_at(0, name="Status", value="❌ Cancelled", inline=False)
    return embed


def build_ark_locked_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    embed = build_ark_registration_embed_from_match(
        match,
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
    )
    embed.color = discord.Color.orange()
    embed.insert_field_at(0, name="Status", value="🔒 Signups Closed", inline=False)
    embed.set_footer(text="Signups are closed. Contact leadership for changes.")
    return embed


def build_ark_confirmation_embed(
    *,
    alliance: str,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
    players_cap: int,
    subs_cap: int,
    notes: str | None = None,
    roster: list[Mapping[str, Any]] | None = None,
    updates: list[str] | None = None,
) -> discord.Embed:
    match_dt = ensure_aware_utc(match_datetime_utc)
    close_dt = ensure_aware_utc(signup_close_utc)

    roster = roster or []
    players = [
        (r.get("GovernorNameSnapshot") or "Unknown")
        for r in roster
        if (r.get("SlotType") or "").lower() == "player"
    ]
    subs = [
        (r.get("GovernorNameSnapshot") or "Unknown")
        for r in roster
        if (r.get("SlotType") or "").lower() == "sub"
    ]
    checked_in = [
        (r.get("GovernorNameSnapshot") or "Unknown")
        for r in roster
        if r.get("CheckedIn") or r.get("CheckedInAtUtc")
    ]
    total_roster = len(roster)

    embed = discord.Embed(
        title=f"Ark of Osiris — {alliance}",
        color=discord.Color.green(),
    )
    embed.add_field(name="Status", value="✅ Signups Closed", inline=False)
    embed.add_field(
        name="Match Time (UTC)",
        value=match_dt.strftime("%Y-%m-%d %H:%M UTC"),
        inline=False,
    )
    embed.add_field(
        name="Signup Close (UTC)",
        value=close_dt.strftime("%Y-%m-%d %H:%M UTC"),
        inline=False,
    )

    for name, value in _format_roster_fields("Players", players, players_cap):
        embed.add_field(name=name, value=value, inline=False)
    for name, value in _format_roster_fields("Subs", subs, subs_cap):
        embed.add_field(name=name, value=value, inline=False)
    for name, value in _format_roster_fields("Checked in", checked_in, total_roster):
        embed.add_field(name=name, value=value, inline=False)

    if notes:
        embed.add_field(name="Notes", value=notes, inline=False)

    if updates:
        update_lines = [f"• {line}" for line in updates if line]
        if update_lines:
            embed.add_field(name="Updates", value="\n".join(update_lines), inline=False)

    embed.set_footer(
        text="Check-in opens 12h before match start. Emergency withdrawals are only via this embed."
    )
    return embed


def build_ark_confirmation_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
    updates: list[str] | None = None,
) -> discord.Embed:
    match_datetime = resolve_ark_match_datetime(
        match["ArkWeekendDate"],
        match["MatchDay"],
        match["MatchTimeUtc"],
    )
    return build_ark_confirmation_embed(
        alliance=(match.get("Alliance") or "").strip(),
        match_datetime_utc=match_datetime,
        signup_close_utc=match["SignupCloseUtc"],
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=match.get("Notes"),
        roster=roster,
        updates=updates,
    )
