from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC

import discord

from utils import fmt_short
from voting.option_emojis import option_display_label
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
    EngagementItemParticipation,
    EngagementReportingContract,
)
from voting.result_visibility import result_visibility_label
from voting.survey_models import (
    SURVEY_QUESTION_RANKING,
    SURVEY_QUESTION_RATING,
    SURVEY_QUESTION_TEXT,
)
from voting.vote_modes import VOTE_MODE_ONE_CHOICE, normalize_vote_mode, vote_mode_label

DASHBOARD_FILTER_ALL = "all"
DASHBOARD_FILTER_VOTES = "votes"
DASHBOARD_FILTER_SURVEYS = "surveys"
DASHBOARD_FILTER_OPEN = "open"
DASHBOARD_FILTER_CLOSED = "closed"
DASHBOARD_FILTER_VALUES = {
    DASHBOARD_FILTER_ALL,
    DASHBOARD_FILTER_VOTES,
    DASHBOARD_FILTER_SURVEYS,
    DASHBOARD_FILTER_OPEN,
    DASHBOARD_FILTER_CLOSED,
}

_FILTER_LABELS = {
    DASHBOARD_FILTER_ALL: "All",
    DASHBOARD_FILTER_VOTES: "Votes",
    DASHBOARD_FILTER_SURVEYS: "Surveys",
    DASHBOARD_FILTER_OPEN: "Open",
    DASHBOARD_FILTER_CLOSED: "Closed",
}

_QUESTION_LABELS = {
    "SingleChoice": "choice",
    "MultiSelect": "multi-select",
    SURVEY_QUESTION_TEXT: "text",
    SURVEY_QUESTION_RATING: "rating",
    SURVEY_QUESTION_RANKING: "ranking",
}


def normalize_dashboard_filter(value: str | None) -> str:
    text = str(value or "").strip().casefold()
    for candidate in DASHBOARD_FILTER_VALUES:
        if candidate.casefold() == text:
            return candidate
    return DASHBOARD_FILTER_ALL


def dashboard_filter_label(value: str | None) -> str:
    return _FILTER_LABELS[normalize_dashboard_filter(value)]


def dashboard_filter_options(selected: str | None = None) -> list[discord.SelectOption]:
    normalized = normalize_dashboard_filter(selected)
    return [
        discord.SelectOption(label=label, value=value, default=value == normalized)
        for value, label in _FILTER_LABELS.items()
    ]


def filter_dashboard_summaries(
    summaries: Iterable[DashboardReportingSummary],
    filter_value: str | None,
) -> tuple[DashboardReportingSummary, ...]:
    normalized = normalize_dashboard_filter(filter_value)
    rows = tuple(summaries)
    if normalized == DASHBOARD_FILTER_VOTES:
        return tuple(row for row in rows if row.content_kind == REPORT_CONTENT_VOTE)
    if normalized == DASHBOARD_FILTER_SURVEYS:
        return tuple(row for row in rows if row.content_kind == REPORT_CONTENT_SURVEY)
    if normalized == DASHBOARD_FILTER_OPEN:
        return tuple(row for row in rows if row.status.casefold() == "open")
    if normalized == DASHBOARD_FILTER_CLOSED:
        return tuple(row for row in rows if row.status.casefold() == "closed")
    return rows


def build_dashboard_embeds(
    contract: DashboardReportingContract,
    *,
    filter_value: str | None = None,
) -> tuple[discord.Embed, ...]:
    if not _is_dashboard_safe_contract(contract):
        return (_unsafe_contract_embed(filter_value),)

    filtered = filter_dashboard_summaries(contract.summaries, filter_value)
    if not filtered:
        return (_empty_embed(contract, filter_value),)

    question_rows = _questions_by_content(contract.question_aggregates)
    option_rows = _options_by_content(contract.option_aggregates)
    pages = [
        _summary_embed(
            contract,
            summary,
            filter_value=filter_value,
            page_number=index + 1,
            total_pages=len(filtered),
            question_rows=question_rows.get((summary.content_kind, summary.content_id), ()),
            option_rows=option_rows.get((summary.content_kind, summary.content_id), ()),
        )
        for index, summary in enumerate(filtered)
    ]
    return tuple(pages)


def build_engagement_dashboard_embeds(
    contract: EngagementReportingContract,
) -> tuple[discord.Embed, ...]:
    if not _is_engagement_safe_contract(contract):
        return (_unsafe_engagement_contract_embed(),)

    embed = discord.Embed(
        title="Voting engagement",
        description=(
            f"{contract.window_label} | {contract.role_filter_label} | "
            f"{contract.window_start_utc:%Y-%m-%d} to {contract.window_end_utc:%Y-%m-%d}"
        ),
        color=discord.Color.blurple(),
    )
    total_items = contract.vote_post_count + contract.survey_post_count
    embed.add_field(
        name="Total Polls",
        value=(
            f"{fmt_short(total_items)} total\n"
            f"{fmt_short(contract.vote_post_count)} vote(s), "
            f"{fmt_short(contract.survey_post_count)} survey(s)"
        ),
        inline=True,
    )
    embed.add_field(
        name="Total Users",
        value=f"{fmt_short(contract.eligible_user_count)} Discord user(s)",
        inline=True,
    )
    embed.add_field(
        name="Participation levels",
        value=(
            f"{fmt_short(contract.actual_participations)}/"
            f"{fmt_short(contract.possible_participations)}\n"
            f"{_rate_text(contract.engagement_rate)}"
        ),
        inline=True,
    )
    embed.add_field(
        name="Monthly Snapshots",
        value=_clip(_engagement_month_lines(contract), 1024),
        inline=False,
    )
    embed.add_field(
        name="Best single Poll",
        value=_clip(_engagement_item_participation_line(contract.best_item), 1024),
        inline=True,
    )
    embed.add_field(
        name="Worst single Poll",
        value=_clip(_engagement_item_participation_line(contract.worst_item), 1024),
        inline=True,
    )
    generated = contract.generated_at_utc.astimezone(UTC)
    embed.set_footer(
        text=(
            f"Generated {generated:%Y-%m-%d %H:%M UTC} | "
            "Private leadership engagement. Raw answers not included."
        )
    )
    return (embed,)


def _is_dashboard_safe_contract(contract: DashboardReportingContract) -> bool:
    return (
        contract.dashboard_safe
        and contract.privacy_profile == REPORT_PRIVACY_PROFILE
        and not contract.contains_discord_identity
        and not contract.contains_raw_text_or_detail
    )


def _is_engagement_safe_contract(contract: EngagementReportingContract) -> bool:
    return (
        contract.dashboard_safe
        and contract.privacy_profile == ENGAGEMENT_PRIVACY_PROFILE
        and contract.contains_discord_identity
        and not contract.contains_raw_text_or_detail
    )


def _unsafe_contract_embed(filter_value: str | None) -> discord.Embed:
    embed = discord.Embed(
        title="Voting dashboard unavailable",
        description=(
            "Dashboard data failed privacy validation, so no report content was rendered."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(
        text=(
            f"Filter: {dashboard_filter_label(filter_value)} | "
            "Private dashboard blocked: reporting contract is not dashboard-safe"
        )
    )
    return embed


def _unsafe_engagement_contract_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Voting engagement unavailable",
        description=(
            "Engagement data failed privacy validation, so no report content was rendered."
        ),
        color=discord.Color.red(),
    )
    embed.set_footer(
        text="Private engagement blocked: reporting contract is not identity-dashboard-safe"
    )
    return embed


def _questions_by_content(
    rows: Sequence[DashboardReportingQuestionAggregate],
) -> dict[tuple[str, int], tuple[DashboardReportingQuestionAggregate, ...]]:
    grouped: defaultdict[tuple[str, int], list[DashboardReportingQuestionAggregate]] = defaultdict(
        list
    )
    for row in rows:
        grouped[(row.content_kind, row.content_id)].append(row)
    return {
        key: tuple(sorted(value, key=lambda row: (row.question_sort_order, row.question_id)))
        for key, value in grouped.items()
    }


def _options_by_content(
    rows: Sequence[DashboardReportingOptionAggregate],
) -> dict[tuple[str, int], tuple[DashboardReportingOptionAggregate, ...]]:
    grouped: defaultdict[tuple[str, int], list[DashboardReportingOptionAggregate]] = defaultdict(
        list
    )
    for row in rows:
        grouped[(row.content_kind, row.content_id)].append(row)
    return {
        key: tuple(
            sorted(
                value,
                key=lambda row: (
                    row.question_id or 0,
                    row.option_sort_order,
                    row.option_id,
                ),
            )
        )
        for key, value in grouped.items()
    }


def _empty_embed(
    contract: DashboardReportingContract,
    filter_value: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title="Voting dashboard",
        description="No vote or survey summaries match this filter.",
        color=discord.Color.blurple(),
    )
    _add_privacy_footer(embed, contract, filter_value, page_number=1, total_pages=1)
    return embed


def _summary_embed(
    contract: DashboardReportingContract,
    summary: DashboardReportingSummary,
    *,
    filter_value: str | None,
    page_number: int,
    total_pages: int,
    question_rows: Sequence[DashboardReportingQuestionAggregate],
    option_rows: Sequence[DashboardReportingOptionAggregate],
) -> discord.Embed:
    kind_label = "Vote" if summary.content_kind == REPORT_CONTENT_VOTE else "Survey"
    color = discord.Color.green() if summary.status.casefold() == "open" else discord.Color.red()
    embed = discord.Embed(
        title=f"Voting dashboard: {kind_label} #{summary.content_id}",
        description=_clip(summary.title, 240),
        color=color,
    )
    embed.add_field(name="State", value=_state_text(summary), inline=False)
    embed.add_field(name="Participation", value=_participation_text(summary), inline=True)
    embed.add_field(name="Structure", value=_structure_text(summary), inline=True)

    if summary.content_kind == REPORT_CONTENT_VOTE:
        embed.add_field(
            name="Option totals",
            value=_clip(_vote_option_lines(summary, option_rows), 1024),
            inline=False,
        )
    else:
        embed.add_field(
            name="Question summaries",
            value=_clip(_survey_question_lines(question_rows, option_rows), 1024),
            inline=False,
        )

    if summary.message_link:
        embed.add_field(name="Original post", value=summary.message_link, inline=False)
    _add_privacy_footer(
        embed,
        contract,
        filter_value,
        page_number=page_number,
        total_pages=total_pages,
    )
    return embed


def _state_text(summary: DashboardReportingSummary) -> str:
    closed = (
        f"closed {summary.closed_at_utc:%Y-%m-%d %H:%M UTC}"
        if summary.closed_at_utc is not None
        else f"closes {summary.closes_at_utc:%Y-%m-%d %H:%M UTC}"
    )
    return f"{summary.status} | {result_visibility_label(summary.result_visibility)} | {closed}"


def _participation_text(summary: DashboardReportingSummary) -> str:
    participant_label = "voters" if summary.content_kind == REPORT_CONTENT_VOTE else "responses"
    selection_label = "votes" if _is_one_choice_vote(summary) else "selections"
    return (
        f"{fmt_short(summary.total_participants)} {participant_label}\n"
        f"{fmt_short(summary.total_selections)} {selection_label}"
    )


def _structure_text(summary: DashboardReportingSummary) -> str:
    if summary.content_kind == REPORT_CONTENT_VOTE:
        return (
            f"{vote_mode_label(summary.vote_mode)}\n" f"{fmt_short(summary.option_count)} options"
        )
    answer_types = summary.answer_type_summary or "no answer types"
    return (
        f"{fmt_short(summary.question_count)} questions "
        f"({fmt_short(summary.required_question_count)} required, "
        f"{fmt_short(summary.optional_question_count)} optional)\n"
        f"{answer_types}"
    )


def _vote_option_lines(
    summary: DashboardReportingSummary,
    option_rows: Sequence[DashboardReportingOptionAggregate],
) -> str:
    if not option_rows:
        return summary.top_summary or "No option totals available."
    lines = []
    for option in option_rows[:12]:
        marker = "top " if option.is_top_selection else ""
        percent = _percentage(option.selection_count, option.total_participants)
        label = option_display_label(option.option_label, option.option_emoji)
        lines.append(f"{marker}{label}: {fmt_short(option.selection_count)}" f"{percent}")
    if len(option_rows) > 12:
        lines.append(f"+{len(option_rows) - 12} more option(s)")
    return "\n".join(lines)


def _survey_question_lines(
    question_rows: Sequence[DashboardReportingQuestionAggregate],
    option_rows: Sequence[DashboardReportingOptionAggregate],
) -> str:
    if not question_rows:
        return "No question summaries available."
    options_by_question: defaultdict[int, list[DashboardReportingOptionAggregate]] = defaultdict(
        list
    )
    for option in option_rows:
        if option.question_id is not None:
            options_by_question[int(option.question_id)].append(option)

    lines = []
    for question in question_rows[:8]:
        requirement = "required" if question.is_required else "optional"
        label = _QUESTION_LABELS.get(question.question_type, question.question_type)
        detail = _clip(
            _question_detail(question, options_by_question.get(question.question_id, ())),
            220,
        )
        lines.append(
            f"Q{question.question_sort_order} {label}: {detail} "
            f"({fmt_short(question.answered_responses)} answered, "
            f"{fmt_short(question.skipped_responses)} skipped, {requirement})"
        )
    if len(question_rows) > 8:
        lines.append(f"+{len(question_rows) - 8} more question(s)")
    return "\n".join(lines)


def _question_detail(
    question: DashboardReportingQuestionAggregate,
    option_rows: Sequence[DashboardReportingOptionAggregate],
) -> str:
    if question.question_type == SURVEY_QUESTION_TEXT:
        return "private text responses counted only"
    if question.question_type == SURVEY_QUESTION_RATING:
        if question.average_rating is None:
            return "no ratings"
        counts_by_value = {
            1: question.rating1_count,
            2: question.rating2_count,
            3: question.rating3_count,
            4: question.rating4_count,
            5: question.rating5_count,
            6: question.rating6_count,
            7: question.rating7_count,
            8: question.rating8_count,
            9: question.rating9_count,
            10: question.rating10_count,
        }
        distribution = question.rating_distribution or " ".join(
            f"{value}:{fmt_short(counts_by_value.get(value, 0))}"
            for value in range(question.rating_scale_min, question.rating_scale_max + 1)
        )
        default_scale = (
            question.rating_scale_min == 1
            and question.rating_scale_max == 5
            and not question.rating_low_label
            and not question.rating_high_label
            and not question.rating_labels
        )
        if default_scale:
            average = f"avg {question.average_rating:.1f}/5"
        else:
            scale = f"{question.rating_scale_min}-{question.rating_scale_max}"
            if question.rating_low_label and question.rating_high_label:
                scale = f"{scale} ({question.rating_low_label} to {question.rating_high_label})"
            elif question.rating_low_label:
                scale = f"{scale} ({question.rating_low_label} low)"
            elif question.rating_high_label:
                scale = f"{scale} ({question.rating_high_label} high)"
            average = f"avg {question.average_rating:.1f} on {scale}"
        labels = (
            f"; labels {question.rating_labels}"
            if question.rating_labels and question.rating_labels not in distribution
            else ""
        )
        return (
            f"{average}, "
            f"min {question.minimum_rating or '-'}, max {question.maximum_rating or '-'}, "
            f"{distribution}{labels}"
        )
    if question.question_type == SURVEY_QUESTION_RANKING:
        ranked = [option for option in option_rows if option.average_rank is not None]
        if not ranked:
            return "no rankings"
        best = min(float(option.average_rank or 99) for option in ranked)
        leaders = [
            option_display_label(option.option_label, option.option_emoji)
            for option in ranked
            if option.average_rank is not None and abs(float(option.average_rank) - best) < 0.0001
        ]
        first_count = max((option.rank1_count for option in ranked), default=0)
        return (
            f"best avg {', '.join(leaders[:2])} ({best:.1f}); "
            f"top first-place count {fmt_short(first_count)}"
        )

    leaders = [option for option in option_rows if option.is_top_selection]
    if not leaders:
        return "no responses"
    top_count = max(option.selection_count for option in leaders)
    labels = ", ".join(
        option_display_label(option.option_label, option.option_emoji) for option in leaders[:2]
    )
    suffix = " each" if len(leaders) > 1 else ""
    return f"top {labels} ({fmt_short(top_count)}{suffix})"


def _is_one_choice_vote(summary: DashboardReportingSummary) -> bool:
    if summary.content_kind != REPORT_CONTENT_VOTE:
        return False
    return normalize_vote_mode(summary.vote_mode) == VOTE_MODE_ONE_CHOICE


def _percentage(count: int, total: int) -> str:
    if total <= 0:
        return ""
    return f" ({(count / total) * 100:.0f}%)"


def _rate_text(rate: float) -> str:
    return f"{max(0.0, min(1.0, float(rate))) * 100:.0f}%"


def _engagement_month_lines(contract: EngagementReportingContract) -> str:
    if not contract.monthly_buckets:
        return "No published vote or survey items in this window."
    lines = []
    for bucket in contract.monthly_buckets[:6]:
        total_items = bucket.vote_post_count + bucket.survey_post_count
        lines.append(
            f"{bucket.month_label}: {fmt_short(total_items)} item(s), "
            f"{fmt_short(bucket.actual_participations)}/"
            f"{fmt_short(bucket.possible_participations)} ({_rate_text(bucket.engagement_rate)})"
        )
    if len(contract.monthly_buckets) > 6:
        lines.append(f"+{len(contract.monthly_buckets) - 6} more month(s)")
    return "\n".join(lines)


def _engagement_item_participation_line(item: EngagementItemParticipation | None) -> str:
    if item is None:
        return "No closed poll data in this window."
    title = item.title.strip() or (
        f"{'Vote' if item.content_kind == REPORT_CONTENT_VOTE else 'Survey'} #{item.content_id}"
    )
    return (
        f"{_clip(title, 180)}\n"
        f"{fmt_short(item.actual_participations)}/"
        f"{fmt_short(item.possible_participations)} ({_rate_text(item.engagement_rate)})"
    )


def _clip(value: str, limit: int) -> str:
    text = str(value or "")
    if len(text) <= limit:
        return text or "-"
    if limit <= 3:
        return "." * max(0, limit)
    return text[: max(0, limit - 3)].rstrip() + "..."


def _add_privacy_footer(
    embed: discord.Embed,
    contract: DashboardReportingContract,
    filter_value: str | None,
    *,
    page_number: int,
    total_pages: int,
) -> None:
    generated = contract.generated_at_utc.astimezone(UTC)
    embed.set_footer(
        text=(
            f"Page {page_number}/{total_pages} | Filter: {dashboard_filter_label(filter_value)} | "
            f"Generated {generated:%Y-%m-%d %H:%M UTC} | "
            "Aggregate-only private dashboard"
        )
    )


__all__ = [
    "DASHBOARD_FILTER_ALL",
    "DASHBOARD_FILTER_CLOSED",
    "DASHBOARD_FILTER_OPEN",
    "DASHBOARD_FILTER_SURVEYS",
    "DASHBOARD_FILTER_VALUES",
    "DASHBOARD_FILTER_VOTES",
    "build_dashboard_embeds",
    "build_engagement_dashboard_embeds",
    "dashboard_filter_label",
    "dashboard_filter_options",
    "filter_dashboard_summaries",
    "normalize_dashboard_filter",
]
