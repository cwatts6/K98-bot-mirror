from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from voting import reporting_dal, survey_dal
from voting.reporting_models import (
    REPORT_CONTENT_SURVEY,
    REPORT_CONTENT_VOTE,
    REPORT_PRIVACY_PROFILE,
    DashboardReportingContract,
    DashboardReportingOptionAggregate,
    DashboardReportingQuestionAggregate,
    DashboardReportingSummary,
)
from voting.service import VoteValidationError

if TYPE_CHECKING:
    from voting.survey_models import SurveyReportingOptionRow, SurveyReportingQuestionRow


MAX_DASHBOARD_REPORT_ITEMS = 50


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
