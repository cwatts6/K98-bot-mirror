from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from voting.option_emojis import OptionEmoji

REPORT_CONTENT_VOTE = "vote"
REPORT_CONTENT_SURVEY = "survey"

REPORT_PRIVACY_PROFILE = "admin_leadership_private_dashboard_safe"
ENGAGEMENT_PRIVACY_PROFILE = "admin_leadership_private_engagement_identity"


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
    rating_scale_min: int = 1
    rating_scale_max: int = 5
    rating_low_label: str | None = None
    rating_high_label: str | None = None
    rating_labels: str = ""
    rating_distribution: str = ""
    rating6_count: int = 0
    rating7_count: int = 0
    rating8_count: int = 0
    rating9_count: int = 0
    rating10_count: int = 0


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
    option_emoji: OptionEmoji | None = None
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


@dataclass(frozen=True)
class EngagementEligibleUser:
    discord_user_id: int
    display_name: str
    role_ids: tuple[int, ...] = ()
    role_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngagementItemSummary:
    content_kind: str
    content_id: int
    created_at_utc: datetime
    status: str
    title: str = ""


@dataclass(frozen=True)
class EngagementParticipant:
    content_kind: str
    content_id: int
    discord_user_id: int
    participated_at_utc: datetime


@dataclass(frozen=True)
class EngagementUserSummary:
    discord_user_id: int
    display_name: str
    role_names: tuple[str, ...]
    participation_count: int
    possible_count: int
    engagement_rate: float
    last_participated_at_utc: datetime | None
    vote_participation_count: int = 0
    survey_participation_count: int = 0


@dataclass(frozen=True)
class EngagementMonthlyBucket:
    month_key: str
    month_label: str
    vote_post_count: int
    survey_post_count: int
    possible_participations: int
    actual_participations: int
    engagement_rate: float


@dataclass(frozen=True)
class EngagementItemParticipation:
    content_kind: str
    content_id: int
    title: str
    created_at_utc: datetime
    possible_participations: int
    actual_participations: int
    engagement_rate: float


@dataclass(frozen=True)
class EngagementReportingContract:
    generated_at_utc: datetime
    privacy_profile: str
    window_key: str
    window_label: str
    window_start_utc: datetime
    window_end_utc: datetime
    role_filter_value: str
    role_filter_label: str
    eligible_user_count: int
    vote_post_count: int
    survey_post_count: int
    possible_participations: int
    actual_participations: int
    engagement_rate: float
    user_summaries: tuple[EngagementUserSummary, ...]
    monthly_buckets: tuple[EngagementMonthlyBucket, ...]
    best_item: EngagementItemParticipation | None = None
    worst_item: EngagementItemParticipation | None = None
    dashboard_safe: bool = True
    contains_raw_text_or_detail: bool = False
    contains_discord_identity: bool = True
    raw_detail_access_profile: str = "not_included"
