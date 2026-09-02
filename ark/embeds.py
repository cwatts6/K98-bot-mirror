from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
import logging
from typing import Any

import discord

from core.discord_embed_limits import (
    MAX_FIELD_VALUE_CHARACTERS,
    MAX_FIELDS_PER_EMBED,
    MAX_TITLE_CHARACTERS,
    MAX_TOTAL_CHARACTERS,
    measure_embed_payload,
    require_valid_embed_payload,
    truncate_text,
)
from embed_utils import fmt_short
from utils import ensure_aware_utc

logger = logging.getLogger(__name__)

_SQL_GOVERNOR_NAME_MAX = 128


@dataclass(frozen=True, slots=True)
class _FieldCandidate:
    name: str
    value: str
    omitted: Mapping[str, int] = field(default_factory=dict)

    @property
    def character_cost(self) -> int:
        return len(self.name) + len(self.value)


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


def compact_ark_title(prefix: str, value: Any) -> tuple[str, bool]:
    """Return a valid title and whether the dynamic value was visibly compacted."""

    full = f"{prefix}{'' if value is None else value}"
    compacted = len(full) > MAX_TITLE_CHARACTERS
    return truncate_text(full, MAX_TITLE_CHARACTERS), compacted


def _field_label(title: str, index: int) -> str:
    return title if index == 0 else f"{title} (cont. {index + 1})"


def _split_text(value: Any, *, limit: int = MAX_FIELD_VALUE_CHARACTERS) -> list[str]:
    """Split text without dropping characters, preferring newline/word boundaries."""

    text = "" if value is None else str(value)
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + limit)
        if end < len(text):
            window = text[start:end]
            newline = window.rfind("\n")
            space = window.rfind(" ")
            boundary = max(newline, space)
            if boundary > 0:
                end = start + boundary + 1
        chunks.append(text[start:end])
        start = end
    return chunks


def _compact_roster_name(value: Any) -> tuple[str, bool]:
    text = str(value or "Unknown")
    compacted = len(text) > _SQL_GOVERNOR_NAME_MAX
    return truncate_text(text, _SQL_GOVERNOR_NAME_MAX), compacted


def _line_field_candidates(
    title: str,
    lines: Sequence[str],
    *,
    omission_key: str,
) -> list[_FieldCandidate]:
    if not lines:
        return [_FieldCandidate(title, "—")]

    groups: list[list[str]] = []
    current: list[str] = []
    current_length = 0
    for line in lines:
        line_length = len(line) + (1 if current else 0)
        if current and current_length + line_length > MAX_FIELD_VALUE_CHARACTERS:
            groups.append(current)
            current = [line]
            current_length = len(line)
        else:
            current.append(line)
            current_length += line_length
    if current:
        groups.append(current)

    return [
        _FieldCandidate(
            _field_label(title, index),
            "\n".join(group),
            {omission_key: len(group)},
        )
        for index, group in enumerate(groups)
    ]


def roster_field_candidates(
    title: str,
    names: Sequence[Any],
    cap: int,
    *,
    omission_key: str,
    label: str | None = None,
) -> tuple[list[_FieldCandidate], int]:
    """Build complete roster-line fields under the SQL governor-name contract."""

    compacted = 0
    numbered: list[str] = []
    for index, raw_name in enumerate(names):
        name, was_compacted = _compact_roster_name(raw_name)
        compacted += int(was_compacted)
        numbered.append(f"{index + 1}. {name}")
    field_label = label or f"{title} ({len(names)}/{cap})"
    return _line_field_candidates(field_label, numbered, omission_key=omission_key), compacted


def text_field_candidates(
    title: str,
    value: Any,
    *,
    omission_key: str,
) -> list[_FieldCandidate]:
    chunks = _split_text(value)
    return [
        _FieldCandidate(
            _field_label(title, index),
            chunk,
            {omission_key: len(chunk)},
        )
        for index, chunk in enumerate(chunks)
    ]


def update_field_candidates(updates: Sequence[Any] | None) -> list[_FieldCandidate]:
    """Pack complete update units; split only a single over-contract update."""

    candidates: list[_FieldCandidate] = []
    current: list[str] = []
    current_units = 0

    def flush() -> None:
        nonlocal current, current_units
        if not current:
            return
        candidates.append(
            _FieldCandidate(
                _field_label("Updates", len(candidates)),
                "\n".join(current),
                {"updates": current_units},
            )
        )
        current = []
        current_units = 0

    for raw_update in updates or []:
        if not raw_update:
            continue
        line = f"• {raw_update}"
        if len(line) > MAX_FIELD_VALUE_CHARACTERS:
            flush()
            chunks = _split_text(line)
            for index, chunk in enumerate(chunks):
                candidates.append(
                    _FieldCandidate(
                        _field_label("Updates", len(candidates)),
                        chunk,
                        {
                            "updates": 1 if index == 0 else 0,
                            "update characters": len(chunk),
                        },
                    )
                )
            continue
        candidate_value = "\n".join([*current, line])
        if current and len(candidate_value) > MAX_FIELD_VALUE_CHARACTERS:
            flush()
        current.append(line)
        current_units += 1
    flush()
    return candidates


def _format_count(count: int, label: str) -> str:
    if count == 1 and label.endswith("s"):
        label = label[:-1]
    return f"{count} {label}"


def _omission_marker(omitted: Mapping[str, int]) -> str:
    parts = [_format_count(count, key) for key, count in omitted.items() if count > 0]
    return "Discord limit reached: " + ", ".join(parts) + " omitted."


def _select_candidates(
    *,
    embed: discord.Embed,
    sections: Mapping[str, Sequence[_FieldCandidate]],
    priority_order: Sequence[str],
) -> tuple[dict[str, list[_FieldCandidate]], dict[str, int]]:
    base_usage = measure_embed_payload(embed)
    remaining_fields = MAX_FIELDS_PER_EMBED - base_usage.field_counts[0]
    remaining_characters = MAX_TOTAL_CHARACTERS - base_usage.total_characters
    selected: dict[str, list[_FieldCandidate]] = {key: [] for key in sections}

    for key in priority_order:
        for candidate in sections.get(key, ()):
            if remaining_fields <= 0 or candidate.character_cost > remaining_characters:
                break
            selected[key].append(candidate)
            remaining_fields -= 1
            remaining_characters -= candidate.character_cost

    def omitted_counts() -> dict[str, int]:
        counts: dict[str, int] = {}
        for key, candidates in sections.items():
            kept = len(selected.get(key, ()))
            for candidate in candidates[kept:]:
                for omission_key, count in candidate.omitted.items():
                    if int(count) > 0:
                        counts[omission_key] = counts.get(omission_key, 0) + int(count)
        return counts

    omitted = omitted_counts()
    while omitted:
        marker = _omission_marker(omitted)
        marker_cost = len("More details") + len(marker)
        selected_count = sum(len(items) for items in selected.values())
        selected_cost = sum(
            candidate.character_cost for items in selected.values() for candidate in items
        )
        if (
            base_usage.field_counts[0] + selected_count + 1 <= MAX_FIELDS_PER_EMBED
            and base_usage.total_characters + selected_cost + marker_cost <= MAX_TOTAL_CHARACTERS
        ):
            break

        removed = False
        for key in reversed(priority_order):
            if selected.get(key):
                selected[key].pop()
                removed = True
                break
        if not removed:
            break
        omitted = omitted_counts()

    return selected, omitted


def add_bounded_sections(
    embed: discord.Embed,
    *,
    sections: Mapping[str, Sequence[_FieldCandidate]],
    display_order: Sequence[str],
    priority_order: Sequence[str] | None = None,
    route: str,
    compacted_units: int = 0,
) -> discord.Embed:
    """Add valid candidate fields and one truthful marker when content cannot fit."""

    priorities = tuple(priority_order or display_order)
    selected, omitted = _select_candidates(
        embed=embed,
        sections=sections,
        priority_order=priorities,
    )
    for key in display_order:
        for candidate in selected.get(key, ()):
            embed.add_field(name=candidate.name, value=candidate.value, inline=False)
    if omitted:
        embed.add_field(name="More details", value=_omission_marker(omitted), inline=False)

    usage = require_valid_embed_payload(embed)
    logger.info(
        "ark_payload_built route=%s fields=%s chars=%s compacted_units=%s omitted_units=%s",
        route,
        usage.field_counts[0],
        usage.total_characters,
        compacted_units,
        sum(omitted.values()),
    )
    return embed


def _alliance_title_and_field(
    *,
    prefix: str,
    alliance: str,
) -> tuple[str, list[_FieldCandidate], int]:
    title, compacted = compact_ark_title(prefix, alliance)
    fields = [_FieldCandidate("Alliance", alliance)] if compacted else []
    return title, fields, int(compacted)


def _build_registration_embed(
    *,
    alliance: str,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
    players_cap: int,
    subs_cap: int,
    notes: str | None,
    roster: list[Mapping[str, Any]] | None,
    status: str | None,
    color: discord.Color,
    footer: str,
    route: str,
) -> discord.Embed:
    match_dt = ensure_aware_utc(match_datetime_utc)
    close_dt = ensure_aware_utc(signup_close_utc)
    roster = roster or []
    players = [
        r.get("GovernorNameSnapshot") or "Unknown"
        for r in roster
        if (r.get("SlotType") or "").lower() == "player"
    ]
    subs = [
        r.get("GovernorNameSnapshot") or "Unknown"
        for r in roster
        if (r.get("SlotType") or "").lower() == "sub"
    ]

    title, alliance_fields, compacted = _alliance_title_and_field(
        prefix="Ark of Osiris — ", alliance=alliance
    )
    embed = discord.Embed(title=title, color=color)
    if status:
        embed.add_field(name="Status", value=status, inline=False)
    for candidate in alliance_fields:
        embed.add_field(name=candidate.name, value=candidate.value, inline=False)
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
    embed.set_footer(text=footer)

    player_fields, player_compacted = roster_field_candidates(
        "Players", players, players_cap, omission_key="players"
    )
    sub_fields, sub_compacted = roster_field_candidates(
        "Subs", subs, subs_cap, omission_key="substitutes"
    )
    sections = {
        "players": player_fields,
        "subs": sub_fields,
        "notes": text_field_candidates("Notes", notes, omission_key="note characters"),
    }
    return add_bounded_sections(
        embed,
        sections=sections,
        display_order=("players", "subs", "notes"),
        route=route,
        compacted_units=compacted + player_compacted + sub_compacted,
    )


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
    return _build_registration_embed(
        alliance=alliance,
        match_datetime_utc=match_datetime_utc,
        signup_close_utc=signup_close_utc,
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=notes,
        roster=roster,
        status=None,
        color=discord.Color.blue(),
        footer="Signups close Friday 23:00 UTC. After close, contact leadership.",
        route="registration",
    )


def _build_registration_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None,
    status: str | None,
    color: discord.Color,
    footer: str,
    route: str,
) -> discord.Embed:
    match_datetime = resolve_ark_match_datetime(
        match["ArkWeekendDate"], match["MatchDay"], match["MatchTimeUtc"]
    )
    return _build_registration_embed(
        alliance=(match.get("Alliance") or "").strip(),
        match_datetime_utc=match_datetime,
        signup_close_utc=match["SignupCloseUtc"],
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=match.get("Notes"),
        roster=roster,
        status=status,
        color=color,
        footer=footer,
        route=route,
    )


def build_ark_registration_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    return _build_registration_embed_from_match(
        match,
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
        status=None,
        color=discord.Color.blue(),
        footer="Signups close Friday 23:00 UTC. After close, contact leadership.",
        route="registration",
    )


def build_ark_cancelled_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    return _build_registration_embed_from_match(
        match,
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
        status="❌ Cancelled",
        color=discord.Color.red(),
        footer="Signups close Friday 23:00 UTC. After close, contact leadership.",
        route="registration_cancelled",
    )


def build_ark_locked_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
) -> discord.Embed:
    return _build_registration_embed_from_match(
        match,
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
        status="🔒 Signups Closed",
        color=discord.Color.orange(),
        footer="Signups are closed. Contact leadership for changes.",
        route="registration_locked",
    )


def _build_confirmation_embed(
    *,
    alliance: str,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
    players_cap: int,
    subs_cap: int,
    notes: str | None,
    roster: list[Mapping[str, Any]] | None,
    updates: list[str] | None,
    result: str | None,
    result_notes: str | None,
    completed_at_utc: datetime | None,
    team_assignment: str | None,
    status: str,
    color: discord.Color,
    footer: str,
    route: str,
) -> discord.Embed:
    match_dt = ensure_aware_utc(match_datetime_utc)
    close_dt = ensure_aware_utc(signup_close_utc)
    roster = roster or []
    players = [
        r.get("GovernorNameSnapshot") or "Unknown"
        for r in roster
        if (r.get("SlotType") or "").lower() == "player"
    ]
    subs = [
        r.get("GovernorNameSnapshot") or "Unknown"
        for r in roster
        if (r.get("SlotType") or "").lower() == "sub"
    ]
    checked_in = [
        r.get("GovernorNameSnapshot") or "Unknown"
        for r in roster
        if r.get("CheckedIn") or r.get("CheckedInAtUtc")
    ]

    title, alliance_fields, compacted = _alliance_title_and_field(
        prefix="Ark of Osiris — ", alliance=alliance
    )
    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="Status", value=status, inline=False)
    for candidate in alliance_fields:
        embed.add_field(name=candidate.name, value=candidate.value, inline=False)
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
    embed.set_footer(text=footer)

    player_fields, player_compacted = roster_field_candidates(
        "Players", players, players_cap, omission_key="players"
    )
    sub_fields, sub_compacted = roster_field_candidates(
        "Subs", subs, subs_cap, omission_key="substitutes"
    )
    checkin_fields, checkin_compacted = roster_field_candidates(
        "Checked in", checked_in, len(roster), omission_key="checked-in players"
    )

    result_detail = ""
    if result:
        completed_at = fmt_short(ensure_aware_utc(completed_at_utc)) if completed_at_utc else None
        result_detail = f"**{result}**"
        if completed_at:
            result_detail += f" ({completed_at})"
        if result_notes:
            result_detail += f"\n{result_notes}"

    sections = {
        "players": player_fields,
        "subs": sub_fields,
        "checked_in": checkin_fields,
        "notes": text_field_candidates("Notes", notes, omission_key="note characters"),
        "updates": update_field_candidates(updates),
        "result": text_field_candidates("Result", result_detail, omission_key="result characters"),
        "team_assignment": (
            [_FieldCandidate("Team Assignment", team_assignment, {"team assignments": 1})]
            if team_assignment
            else []
        ),
    }
    return add_bounded_sections(
        embed,
        sections=sections,
        display_order=(
            "players",
            "subs",
            "checked_in",
            "notes",
            "updates",
            "result",
            "team_assignment",
        ),
        priority_order=(
            "result",
            "team_assignment",
            "players",
            "subs",
            "checked_in",
            "notes",
            "updates",
        ),
        route=route,
        compacted_units=(compacted + player_compacted + sub_compacted + checkin_compacted),
    )


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
    result: str | None = None,
    result_notes: str | None = None,
    completed_at_utc: datetime | None = None,
    team_assignment: str | None = None,
) -> discord.Embed:
    return _build_confirmation_embed(
        alliance=alliance,
        match_datetime_utc=match_datetime_utc,
        signup_close_utc=signup_close_utc,
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=notes,
        roster=roster,
        updates=updates,
        result=result,
        result_notes=result_notes,
        completed_at_utc=completed_at_utc,
        team_assignment=team_assignment,
        status="✅ Signups Closed",
        color=discord.Color.green(),
        footer=(
            "Check-in opens 12h before match start. "
            "Emergency withdrawals are only via this embed."
        ),
        route="confirmation",
    )


def build_ark_match_complete_embed(
    *,
    alliance: str,
    match_datetime_utc: datetime,
    signup_close_utc: datetime,
    players_cap: int,
    subs_cap: int,
    notes: str | None = None,
    roster: list[Mapping[str, Any]] | None = None,
    updates: list[str] | None = None,
    result: str | None = None,
    result_notes: str | None = None,
    completed_at_utc: datetime | None = None,
    team_assignment: str | None = None,
) -> discord.Embed:
    return _build_confirmation_embed(
        alliance=alliance,
        match_datetime_utc=match_datetime_utc,
        signup_close_utc=signup_close_utc,
        players_cap=players_cap,
        subs_cap=subs_cap,
        notes=notes,
        roster=roster,
        updates=updates,
        result=result,
        result_notes=result_notes,
        completed_at_utc=completed_at_utc,
        team_assignment=team_assignment,
        status="🏁 Match Complete",
        color=discord.Color.dark_green(),
        footer="Match complete.",
        route="match_complete",
    )


def build_ark_confirmation_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
    updates: list[str] | None = None,
    team_assignment: str | None = None,
) -> discord.Embed:
    match_datetime = resolve_ark_match_datetime(
        match["ArkWeekendDate"], match["MatchDay"], match["MatchTimeUtc"]
    )
    return build_ark_confirmation_embed(
        alliance=(match.get("Alliance") or "").strip(),
        match_datetime_utc=match_datetime,
        signup_close_utc=match["SignupCloseUtc"],
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
        updates=updates,
        result=(match.get("Result") or "").strip() or None,
        result_notes=(match.get("ResultNotes") or "").strip() or None,
        completed_at_utc=match.get("CompletedAtUtc"),
        team_assignment=team_assignment,
    )


def build_ark_match_complete_embed_from_match(
    match: Mapping[str, Any],
    *,
    players_cap: int,
    subs_cap: int,
    roster: list[Mapping[str, Any]] | None = None,
    updates: list[str] | None = None,
    team_assignment: str | None = None,
) -> discord.Embed:
    match_datetime = resolve_ark_match_datetime(
        match["ArkWeekendDate"], match["MatchDay"], match["MatchTimeUtc"]
    )
    return build_ark_match_complete_embed(
        alliance=(match.get("Alliance") or "").strip(),
        match_datetime_utc=match_datetime,
        signup_close_utc=match["SignupCloseUtc"],
        players_cap=players_cap,
        subs_cap=subs_cap,
        roster=roster,
        updates=updates,
        result=(match.get("Result") or "").strip() or None,
        result_notes=(match.get("ResultNotes") or "").strip() or None,
        completed_at_utc=match.get("CompletedAtUtc"),
        team_assignment=team_assignment,
    )
