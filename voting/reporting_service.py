from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from voting import reporting_dal, survey_dal
from voting.reporting_models import (
    ENGAGEMENT_PRIVACY_PROFILE,
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
    EngagementEligibleUser,
    EngagementItemParticipation,
    EngagementItemSummary,
    EngagementMonthlyBucket,
    EngagementParticipant,
    EngagementReportingContract,
    EngagementUserSummary,
)
from voting.service import VoteValidationError

if TYPE_CHECKING:
    from voting.survey_models import SurveyReportingOptionRow, SurveyReportingQuestionRow


MAX_DASHBOARD_REPORT_ITEMS = 50
ENGAGEMENT_WINDOW_LAST_MONTH = "last_month"
ENGAGEMENT_WINDOW_LAST_3_MONTHS = "last_3_months"
ENGAGEMENT_WINDOW_LAST_6_MONTHS = "last_6_months"
ENGAGEMENT_ROLE_FILTER_EXPECTED = "expected"
ENGAGEMENT_ROLE_FILTER_ALL = "all"

_ENGAGEMENT_WINDOWS = {
    ENGAGEMENT_WINDOW_LAST_MONTH: ("Last month", 31),
    ENGAGEMENT_WINDOW_LAST_3_MONTHS: ("Last 3 months", 92),
    ENGAGEMENT_WINDOW_LAST_6_MONTHS: ("Last 6 months", 184),
}


def _cap_limit(limit: int) -> int:
    if int(limit) < 1:
        raise VoteValidationError("Dashboard report limit must be at least 1.")
    return min(int(limit), MAX_DASHBOARD_REPORT_ITEMS)


def _sort_summaries(
    summaries: tuple[DashboardReportingSummary, ...],
) -> tuple[DashboardReportingSummary, ...]:
    return tuple(
        sorted(
            summaries,
            key=lambda row: (
                row.closes_at_utc,
                row.closed_at_utc or datetime.min.replace(tzinfo=UTC),
                row.content_kind,
                row.content_id,
            ),
            reverse=True,
        )
    )


def _top_summary(options: tuple[DashboardReportingOptionAggregate, ...]) -> str:
    if not options:
        return "No options"
    total_participants = max((option.total_participants for option in options), default=0)
    if total_participants <= 0:
        return "No responses"
    top_options = tuple(option for option in options if option.is_top_selection)
    if not top_options:
        return "No top selection"
    top_count = max(option.selection_count for option in top_options)
    labels = ", ".join(option.option_label for option in top_options)
    noun = "Top selection" if len(top_options) == 1 else "Top selections"
    suffix = f"{top_count}" if len(top_options) == 1 else f"{top_count} each"
    return f"{noun}: {labels} ({suffix})"


def _survey_question_aggregate(
    row: SurveyReportingQuestionRow,
) -> DashboardReportingQuestionAggregate:
    return DashboardReportingQuestionAggregate(
        content_kind=REPORT_CONTENT_SURVEY,
        content_id=row.survey_id,
        question_id=row.question_id,
        question_key=row.question_key,
        question_prompt=row.question_prompt,
        question_type=row.question_type,
        question_sort_order=row.question_sort_order,
        is_required=row.is_required,
        allow_details=row.allow_details,
        total_responses=row.total_responses,
        answered_responses=row.answered_responses,
        skipped_responses=row.skipped_responses,
        choice_selection_count=row.choice_selection_count,
        ranked_option_count=row.ranked_option_count,
        ranking_first_place_count=row.ranking_first_place_count,
        average_rating=row.average_rating,
        minimum_rating=row.minimum_rating,
        maximum_rating=row.maximum_rating,
        rating1_count=row.rating1_count,
        rating2_count=row.rating2_count,
        rating3_count=row.rating3_count,
        rating4_count=row.rating4_count,
        rating5_count=row.rating5_count,
        rating_scale_min=row.rating_scale_min,
        rating_scale_max=row.rating_scale_max,
        rating_low_label=row.rating_low_label,
        rating_high_label=row.rating_high_label,
        rating_labels=row.rating_labels,
        rating_distribution=row.rating_distribution,
        rating6_count=row.rating6_count,
        rating7_count=row.rating7_count,
        rating8_count=row.rating8_count,
        rating9_count=row.rating9_count,
        rating10_count=row.rating10_count,
    )


def _survey_option_aggregate(row: SurveyReportingOptionRow) -> DashboardReportingOptionAggregate:
    return DashboardReportingOptionAggregate(
        content_kind=REPORT_CONTENT_SURVEY,
        content_id=row.survey_id,
        question_id=row.question_id,
        question_key=row.question_key,
        question_type=row.question_type,
        option_id=row.option_id,
        option_key=row.option_key,
        option_label=row.option_label,
        option_sort_order=row.option_sort_order,
        total_participants=row.total_responses,
        selection_count=row.selection_count,
        is_top_selection=row.is_top_selection,
        option_emoji=row.option_emoji,
        ranked_count=row.ranked_count,
        average_rank=row.average_rank,
        rank1_count=row.rank1_count,
        rank2_count=row.rank2_count,
        rank3_count=row.rank3_count,
        rank4_count=row.rank4_count,
        rank5_count=row.rank5_count,
        rank6_count=row.rank6_count,
    )


async def build_admin_leadership_dashboard_report(*, limit: int = 25) -> DashboardReportingContract:
    """Build an aggregate-only private reporting contract for approved admin/leadership consumers."""

    capped_limit = _cap_limit(limit)
    vote_summaries = await reporting_dal.list_vote_dashboard_summaries(limit=capped_limit)
    survey_summaries = await reporting_dal.list_survey_dashboard_summaries(limit=capped_limit)
    summaries = _sort_summaries(vote_summaries + survey_summaries)[:capped_limit]

    vote_ids = tuple(
        summary.content_id for summary in summaries if summary.content_kind == REPORT_CONTENT_VOTE
    )
    survey_ids = tuple(
        summary.content_id for summary in summaries if summary.content_kind == REPORT_CONTENT_SURVEY
    )

    vote_options = await reporting_dal.list_vote_dashboard_option_aggregates(vote_ids)
    vote_options_by_id: dict[int, list[DashboardReportingOptionAggregate]] = defaultdict(list)
    for option in vote_options:
        vote_options_by_id[option.content_id].append(option)

    enriched_summaries: list[DashboardReportingSummary] = []
    for summary in summaries:
        if summary.content_kind == REPORT_CONTENT_VOTE:
            enriched_summaries.append(
                replace(
                    summary, top_summary=_top_summary(tuple(vote_options_by_id[summary.content_id]))
                )
            )
        else:
            enriched_summaries.append(summary)

    survey_question_rows = await survey_dal.list_reporting_question_rows_for_surveys(survey_ids)
    survey_option_rows = await survey_dal.list_reporting_option_rows_for_surveys(survey_ids)

    question_aggregates: list[DashboardReportingQuestionAggregate] = [
        _survey_question_aggregate(row) for row in survey_question_rows
    ]
    option_aggregates: list[DashboardReportingOptionAggregate] = list(vote_options)
    option_aggregates.extend(_survey_option_aggregate(row) for row in survey_option_rows)

    return DashboardReportingContract(
        generated_at_utc=datetime.now(UTC),
        privacy_profile=REPORT_PRIVACY_PROFILE,
        summaries=tuple(enriched_summaries),
        question_aggregates=tuple(question_aggregates),
        option_aggregates=tuple(option_aggregates),
    )


def normalize_engagement_window(value: str | None) -> str:
    text = str(value or "").strip().casefold()
    for candidate in _ENGAGEMENT_WINDOWS:
        if text == candidate.casefold():
            return candidate
    return ENGAGEMENT_WINDOW_LAST_3_MONTHS


def engagement_window_label(value: str | None) -> str:
    return _ENGAGEMENT_WINDOWS[normalize_engagement_window(value)][0]


def _window_bounds(window_key: str, *, now: datetime | None = None) -> tuple[datetime, datetime]:
    end_at = now or datetime.now(UTC)
    end_at = end_at.replace(tzinfo=UTC) if end_at.tzinfo is None else end_at.astimezone(UTC)
    _label, days = _ENGAGEMENT_WINDOWS[normalize_engagement_window(window_key)]
    return end_at - timedelta(days=days), end_at


def normalize_engagement_role_filter(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ENGAGEMENT_ROLE_FILTER_EXPECTED
    if text.casefold() == ENGAGEMENT_ROLE_FILTER_ALL:
        return ENGAGEMENT_ROLE_FILTER_ALL
    if text.casefold() == ENGAGEMENT_ROLE_FILTER_EXPECTED:
        return ENGAGEMENT_ROLE_FILTER_EXPECTED
    if text.casefold().startswith("role:"):
        suffix = text.split(":", 1)[1].strip()
        if suffix.isdigit():
            return f"role:{int(suffix)}"
    return ENGAGEMENT_ROLE_FILTER_EXPECTED


def _dedupe_eligible_users(
    users: tuple[EngagementEligibleUser, ...],
) -> tuple[EngagementEligibleUser, ...]:
    by_id: dict[int, EngagementEligibleUser] = {}
    for user in users:
        user_id = int(user.discord_user_id)
        role_ids, role_names = _dedupe_role_pairs(user.role_ids, user.role_names)
        display_name = str(user.display_name or "").strip() or str(user_id)
        existing = by_id.get(user_id)
        if existing is None:
            by_id[user_id] = EngagementEligibleUser(
                discord_user_id=user_id,
                display_name=display_name,
                role_ids=role_ids,
                role_names=role_names,
            )
            continue
        merged_role_ids, merged_role_names = _dedupe_role_pairs(
            existing.role_ids + role_ids,
            existing.role_names + role_names,
        )
        by_id[user_id] = EngagementEligibleUser(
            discord_user_id=user_id,
            display_name=existing.display_name or display_name,
            role_ids=merged_role_ids,
            role_names=merged_role_names,
        )
    return tuple(sorted(by_id.values(), key=lambda row: row.display_name.casefold()))


def _dedupe_role_pairs(
    role_ids: tuple[int, ...],
    role_names: tuple[str, ...],
) -> tuple[tuple[int, ...], tuple[str, ...]]:
    by_id: dict[int, str] = {}
    for index, raw_role_id in enumerate(role_ids):
        role_id = int(raw_role_id)
        role_name = str(role_names[index]).strip() if index < len(role_names) else ""
        existing_name = by_id.get(role_id)
        if existing_name is None or (not existing_name and role_name):
            by_id[role_id] = role_name
    return tuple(by_id), tuple(by_id.values())


def _role_filter_label(
    users: tuple[EngagementEligibleUser, ...],
    role_filter_value: str,
) -> str:
    normalized = normalize_engagement_role_filter(role_filter_value)
    if normalized == ENGAGEMENT_ROLE_FILTER_ALL:
        return "All non-bot members"
    if normalized == ENGAGEMENT_ROLE_FILTER_EXPECTED:
        return "Expected roles"
    role_id = int(normalized.split(":", 1)[1])
    for user in users:
        for index, candidate_id in enumerate(user.role_ids):
            if int(candidate_id) == role_id and index < len(user.role_names):
                return user.role_names[index]
    return f"Role {role_id}"


def _filter_eligible_users(
    users: tuple[EngagementEligibleUser, ...],
    role_filter_value: str,
) -> tuple[EngagementEligibleUser, ...]:
    normalized = normalize_engagement_role_filter(role_filter_value)
    if normalized == ENGAGEMENT_ROLE_FILTER_ALL:
        return users
    if normalized == ENGAGEMENT_ROLE_FILTER_EXPECTED:
        return tuple(user for user in users if user.role_ids)
    role_id = int(normalized.split(":", 1)[1])
    return tuple(user for user in users if any(int(value) == role_id for value in user.role_ids))


def _engagement_rate(actual: int, possible: int) -> float:
    if possible <= 0:
        return 0.0
    return float(actual) / float(possible)


def _month_key(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m")


def _month_label(month_key: str) -> str:
    return datetime.strptime(month_key, "%Y-%m").replace(tzinfo=UTC).strftime("%B %Y")


def _unique_participation_events(
    participants: tuple[EngagementParticipant, ...],
    *,
    selected_item_keys: set[tuple[str, int]],
    eligible_user_ids: set[int],
) -> dict[tuple[str, int, int], datetime]:
    events: dict[tuple[str, int, int], datetime] = {}
    for participant in participants:
        user_id = int(participant.discord_user_id)
        item_key = (participant.content_kind, int(participant.content_id))
        if user_id not in eligible_user_ids or item_key not in selected_item_keys:
            continue
        event_key = (participant.content_kind, int(participant.content_id), user_id)
        participated_at = participant.participated_at_utc.astimezone(UTC)
        previous = events.get(event_key)
        if previous is None or participated_at > previous:
            events[event_key] = participated_at
    return events


def _monthly_buckets(
    items: tuple[EngagementItemSummary, ...],
    events: dict[tuple[str, int, int], datetime],
    *,
    eligible_count: int,
) -> tuple[EngagementMonthlyBucket, ...]:
    items_by_month: defaultdict[str, list[EngagementItemSummary]] = defaultdict(list)
    item_month_by_key: dict[tuple[str, int], str] = {}
    for item in items:
        key = _month_key(item.created_at_utc)
        items_by_month[key].append(item)
        item_month_by_key[(item.content_kind, int(item.content_id))] = key

    actual_by_month: defaultdict[str, int] = defaultdict(int)
    for content_kind, content_id, _user_id in events:
        month_key = item_month_by_key.get((content_kind, int(content_id)))
        if month_key:
            actual_by_month[month_key] += 1

    buckets: list[EngagementMonthlyBucket] = []
    for key in sorted(items_by_month, reverse=True):
        month_items = items_by_month[key]
        vote_count = sum(1 for item in month_items if item.content_kind == REPORT_CONTENT_VOTE)
        survey_count = sum(1 for item in month_items if item.content_kind == REPORT_CONTENT_SURVEY)
        possible = eligible_count * len(month_items)
        actual = actual_by_month[key]
        buckets.append(
            EngagementMonthlyBucket(
                month_key=key,
                month_label=_month_label(key),
                vote_post_count=vote_count,
                survey_post_count=survey_count,
                possible_participations=possible,
                actual_participations=actual,
                engagement_rate=_engagement_rate(actual, possible),
            )
        )
    return tuple(buckets)


def _user_summaries(
    users: tuple[EngagementEligibleUser, ...],
    events: dict[tuple[str, int, int], datetime],
    *,
    item_count: int,
) -> tuple[EngagementUserSummary, ...]:
    counts_by_user: defaultdict[int, int] = defaultdict(int)
    last_by_user: dict[int, datetime] = {}
    for _content_kind, _content_id, user_id in events:
        counts_by_user[int(user_id)] += 1
        participated_at = events[(_content_kind, _content_id, user_id)]
        previous = last_by_user.get(int(user_id))
        if previous is None or participated_at > previous:
            last_by_user[int(user_id)] = participated_at

    summaries = [
        EngagementUserSummary(
            discord_user_id=int(user.discord_user_id),
            display_name=user.display_name,
            role_names=user.role_names,
            participation_count=counts_by_user[int(user.discord_user_id)],
            possible_count=item_count,
            engagement_rate=_engagement_rate(counts_by_user[int(user.discord_user_id)], item_count),
            last_participated_at_utc=last_by_user.get(int(user.discord_user_id)),
        )
        for user in users
    ]
    return tuple(
        sorted(
            summaries,
            key=lambda row: (
                row.engagement_rate,
                row.participation_count,
                row.display_name.casefold(),
            ),
        )
    )


def _item_participation_summaries(
    items: tuple[EngagementItemSummary, ...],
    events: dict[tuple[str, int, int], datetime],
    *,
    eligible_count: int,
) -> tuple[EngagementItemParticipation, ...]:
    actual_by_item: defaultdict[tuple[str, int], int] = defaultdict(int)
    for content_kind, content_id, _user_id in events:
        actual_by_item[(content_kind, int(content_id))] += 1

    return tuple(
        EngagementItemParticipation(
            content_kind=item.content_kind,
            content_id=int(item.content_id),
            title=item.title,
            created_at_utc=item.created_at_utc,
            possible_participations=eligible_count,
            actual_participations=actual_by_item[(item.content_kind, int(item.content_id))],
            engagement_rate=_engagement_rate(
                actual_by_item[(item.content_kind, int(item.content_id))],
                eligible_count,
            ),
        )
        for item in items
    )


def _best_item_participation(
    item_summaries: tuple[EngagementItemParticipation, ...],
) -> EngagementItemParticipation | None:
    if not item_summaries:
        return None
    return max(
        item_summaries,
        key=lambda row: (row.engagement_rate, row.created_at_utc.astimezone(UTC)),
    )


def _worst_item_participation(
    item_summaries: tuple[EngagementItemParticipation, ...],
) -> EngagementItemParticipation | None:
    if not item_summaries:
        return None
    return min(
        item_summaries,
        key=lambda row: (
            row.engagement_rate,
            -row.created_at_utc.astimezone(UTC).timestamp(),
        ),
    )


async def build_admin_leadership_engagement_report(
    *,
    eligible_users: tuple[EngagementEligibleUser, ...],
    window_key: str | None = None,
    role_filter_value: str | None = None,
    now: datetime | None = None,
) -> EngagementReportingContract:
    """Build a private Discord-user engagement summary for leadership follow-up."""

    normalized_window = normalize_engagement_window(window_key)
    normalized_role_filter = normalize_engagement_role_filter(role_filter_value)
    start_at, end_at = _window_bounds(normalized_window, now=now)
    all_users = _dedupe_eligible_users(eligible_users)
    selected_users = _filter_eligible_users(all_users, normalized_role_filter)
    eligible_user_ids = {int(user.discord_user_id) for user in selected_users}

    vote_items = await reporting_dal.list_vote_engagement_items(
        start_at_utc=start_at,
        end_at_utc=end_at,
    )
    survey_items = await reporting_dal.list_survey_engagement_items(
        start_at_utc=start_at,
        end_at_utc=end_at,
    )
    vote_participants = await reporting_dal.list_vote_engagement_participants(
        start_at_utc=start_at,
        end_at_utc=end_at,
    )
    survey_participants = await reporting_dal.list_survey_engagement_participants(
        start_at_utc=start_at,
        end_at_utc=end_at,
    )

    items = tuple(sorted(vote_items + survey_items, key=lambda row: row.created_at_utc))
    selected_item_keys = {(item.content_kind, int(item.content_id)) for item in items}
    events = _unique_participation_events(
        vote_participants + survey_participants,
        selected_item_keys=selected_item_keys,
        eligible_user_ids=eligible_user_ids,
    )

    possible = len(selected_users) * len(items)
    actual = len(events)
    item_summaries = _item_participation_summaries(
        items,
        events,
        eligible_count=len(selected_users),
    )
    return EngagementReportingContract(
        generated_at_utc=datetime.now(UTC),
        privacy_profile=ENGAGEMENT_PRIVACY_PROFILE,
        window_key=normalized_window,
        window_label=engagement_window_label(normalized_window),
        window_start_utc=start_at,
        window_end_utc=end_at,
        role_filter_value=normalized_role_filter,
        role_filter_label=_role_filter_label(all_users, normalized_role_filter),
        eligible_user_count=len(selected_users),
        vote_post_count=len(vote_items),
        survey_post_count=len(survey_items),
        possible_participations=possible,
        actual_participations=actual,
        engagement_rate=_engagement_rate(actual, possible),
        user_summaries=_user_summaries(selected_users, events, item_count=len(items)),
        monthly_buckets=_monthly_buckets(items, events, eligible_count=len(selected_users)),
        best_item=_best_item_participation(item_summaries),
        worst_item=_worst_item_participation(item_summaries),
    )
