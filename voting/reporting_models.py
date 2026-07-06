from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

REPORT_CONTENT_VOTE = "vote"
REPORT_CONTENT_SURVEY = "survey"

REPORT_PRIVACY_PROFILE = "admin_leadership_private_dashboard_safe"


@dataclass(frozen=True)
class DashboardReportingSummary:
    content_kind: str
    content_id: int
    title: str
    status: str
    result_visibility: str
    created_at_utc: datetime
    closes_at_utc: datetime
    closed_at_utc: datetime | None
    total_participants: int
    total_selections: int
    option_count: int
    question_count: int
    required_question_count: int
    optional_question_count: int
    vote_mode: str | None = None
    answer_type_summary: str = ""
    top_summary: str = ""
    message_link: str = ""


@dataclass(frozen=True)
class DashboardReportingQuestionAggregate:
    content_kind: str
    content_id: int
    question_id: int
    question_key: str
    question_prompt: str
    question_type: str
    question_sort_order: int
    is_required: bool
    allow_details: bool
    total_responses: int
    answered_responses: int
    skipped_responses: int
    choice_selection_count: int
    ranked_option_count: int
    ranking_first_place_count: int
    average_rating: float | None
    minimum_rating: int | None
    maximum_rating: int | None
    rating1_count: int
    rating2_count: int
    rating3_count: int
    rating4_count: int
    rating5_count: int


@dataclass(frozen=True)
class DashboardReportingOptionAggregate:
    content_kind: str
    content_id: int
    option_id: int
    option_key: str
    option_label: str
    option_sort_order: int
    total_participants: int
    selection_count: int
    is_top_selection: bool
    question_id: int | None = None
    question_key: str | None = None
    question_type: str | None = None
    ranked_count: int = 0
    average_rank: float | None = None
    rank1_count: int = 0
    rank2_count: int = 0
    rank3_count: int = 0
    rank4_count: int = 0
    rank5_count: int = 0
    rank6_count: int = 0


@dataclass(frozen=True)
class DashboardReportingContract:
    generated_at_utc: datetime
    privacy_profile: str
    summaries: tuple[DashboardReportingSummary, ...]
    question_aggregates: tuple[DashboardReportingQuestionAggregate, ...]
    option_aggregates: tuple[DashboardReportingOptionAggregate, ...]
    dashboard_safe: bool = True
    contains_raw_text_or_detail: bool = False
    contains_discord_identity: bool = False
    raw_detail_access_profile: str = "private_exports_only"
