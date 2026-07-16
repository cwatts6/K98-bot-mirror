from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from io import BytesIO

from voting.option_emojis import OptionEmoji

SURVEY_QUESTION_SINGLE_CHOICE = "SingleChoice"
SURVEY_QUESTION_MULTI_SELECT = "MultiSelect"
SURVEY_QUESTION_TEXT = "Text"
SURVEY_QUESTION_RATING = "Rating"
SURVEY_QUESTION_RANKING = "Ranking"
DEFAULT_RATING_MIN_VALUE = 1
DEFAULT_RATING_MAX_VALUE = 5
MAX_RATING_VALUE = 10


@dataclass(frozen=True)
class SurveyRankingCount:
    rank_value: int
    response_count: int


@dataclass(frozen=True)
class SurveyQuestionOption:
    option_id: int
    survey_question_id: int
    option_key: str
    label: str
    sort_order: int
    emoji: OptionEmoji | None = None
    response_count: int = 0
    ranking_average: float | None = None
    ranking_first_place_count: int = 0
    ranking_counts: tuple[SurveyRankingCount, ...] = ()


@dataclass(frozen=True)
class SurveyRatingCount:
    rating_value: int
    response_count: int


@dataclass(frozen=True)
class SurveyRatingLabel:
    rating_value: int
    label: str


@dataclass(frozen=True)
class SurveyQuestion:
    question_id: int
    survey_id: int
    question_key: str
    prompt: str
    question_type: str
    sort_order: int
    min_selections: int
    max_selections: int
    options: tuple[SurveyQuestionOption, ...]
    allow_details: bool = False
    is_required: bool = True
    answered_response_count: int | None = None
    rating_counts: tuple[SurveyRatingCount, ...] = ()
    rating_average: float | None = None
    rating_min: int | None = None
    rating_max: int | None = None
    rating_min_value: int = DEFAULT_RATING_MIN_VALUE
    rating_max_value: int = DEFAULT_RATING_MAX_VALUE
    rating_low_label: str | None = None
    rating_high_label: str | None = None
    rating_labels: tuple[SurveyRatingLabel, ...] = ()


def rating_count_for_value(question: SurveyQuestion, rating_value: int) -> int:
    for item in question.rating_counts:
        if int(item.rating_value) == int(rating_value):
            return int(item.response_count)
    return 0


def rating_values_for_question(question: SurveyQuestion) -> range:
    minimum = int(
        getattr(question, "rating_min_value", DEFAULT_RATING_MIN_VALUE) or DEFAULT_RATING_MIN_VALUE
    )
    maximum = int(
        getattr(question, "rating_max_value", DEFAULT_RATING_MAX_VALUE) or DEFAULT_RATING_MAX_VALUE
    )
    if maximum < minimum:
        maximum = minimum
    return range(minimum, maximum + 1)


def rating_label_for_value(question: SurveyQuestion, rating_value: int) -> str:
    for item in getattr(question, "rating_labels", ()):
        if int(item.rating_value) == int(rating_value):
            return item.label
    return str(int(rating_value))


def rating_choice_display(question: SurveyQuestion, rating_value: int) -> str:
    label = rating_label_for_value(question, rating_value)
    value = int(rating_value)
    return str(value) if label == str(value) else f"{value} - {label}"


def rating_scale_text(question: SurveyQuestion) -> str:
    minimum = int(
        getattr(question, "rating_min_value", DEFAULT_RATING_MIN_VALUE) or DEFAULT_RATING_MIN_VALUE
    )
    maximum = int(
        getattr(question, "rating_max_value", DEFAULT_RATING_MAX_VALUE) or DEFAULT_RATING_MAX_VALUE
    )
    base = f"{minimum}-{maximum}"
    low = str(getattr(question, "rating_low_label", "") or "").strip()
    high = str(getattr(question, "rating_high_label", "") or "").strip()
    if low and high:
        return f"{base} ({low} to {high})"
    if low:
        return f"{base} ({low} low)"
    if high:
        return f"{base} ({high} high)"
    return base


def rating_distribution_text(question: SurveyQuestion) -> str:
    return " ".join(
        f"{rating_label_for_value(question, value)}:{rating_count_for_value(question, value)}"
        for value in rating_values_for_question(question)
    )


def rating_labels_text(question: SurveyQuestion) -> str:
    return "; ".join(
        f"{int(item.rating_value)}={item.label}"
        for item in sorted(
            getattr(question, "rating_labels", ()) or (),
            key=lambda rating_label: int(rating_label.rating_value),
        )
    )


def ranking_count_for_value(option: SurveyQuestionOption, rank_value: int) -> int:
    for item in option.ranking_counts:
        if int(item.rank_value) == int(rank_value):
            return int(item.response_count)
    return 0


@dataclass(frozen=True)
class SurveyReminder:
    reminder_id: int
    survey_id: int
    offset_minutes_before_close: int
    due_at_utc: datetime
    sent_at_utc: datetime | None = None
    message_id: int | None = None


@dataclass(frozen=True)
class SurveySnapshot:
    survey_id: int
    guild_id: int
    channel_id: int
    message_id: int | None
    created_by_discord_user_id: int
    title: str
    description: str | None
    status: str
    allow_response_change: bool
    launch_mention_everyone: bool
    reminder_mention_everyone: bool
    close_mention_everyone: bool
    opens_at_utc: datetime | None
    closes_at_utc: datetime
    closed_at_utc: datetime | None
    closed_by_discord_user_id: int | None
    closed_reason: str | None
    total_responses: int
    created_at_utc: datetime
    updated_at_utc: datetime
    questions: tuple[SurveyQuestion, ...]
    reminders: tuple[SurveyReminder, ...] = ()
    result_visibility: str = "PublicLive"


@dataclass(frozen=True)
class SurveyQuestionCreateRequest:
    prompt: str
    question_type: str
    options: tuple[str, ...]
    option_emojis: tuple[OptionEmoji | None, ...] = ()
    min_selections: int = 1
    max_selections: int = 1
    allow_details: bool = False
    is_required: bool = True
    rating_min_value: int = DEFAULT_RATING_MIN_VALUE
    rating_max_value: int = DEFAULT_RATING_MAX_VALUE
    rating_low_label: str | None = None
    rating_high_label: str | None = None
    rating_labels: tuple[SurveyRatingLabel, ...] = ()


@dataclass(frozen=True)
class SurveyResponsePayload:
    selected_option_ids: dict[int, tuple[int, ...]]
    text_answers: dict[int, str]
    detail_text_by_option: dict[tuple[int, int], str]
    rating_answers: dict[int, int] = field(default_factory=dict)
    ranking_answers: dict[int, tuple[int, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class SurveyResponseDraft:
    survey_id: int
    discord_user_id: int
    payload: SurveyResponsePayload
    revision: int
    status: str
    created_at_utc: datetime
    updated_at_utc: datetime
    expires_at_utc: datetime | None = None


@dataclass(frozen=True)
class SurveyDraftSaveResult:
    status: str
    survey_id: int
    revision: int | None = None
    message: str = ""

    @property
    def accepted(self) -> bool:
        return self.status == "saved" and self.revision is not None


@dataclass(frozen=True)
class SurveyCreateRequest:
    guild_id: int
    channel_id: int
    created_by_discord_user_id: int
    title: str
    description: str | None
    questions: tuple[SurveyQuestionCreateRequest, ...]
    closes_at_utc: datetime
    reminder_offsets_minutes: tuple[int, ...]
    allow_response_change: bool = True
    launch_mention_everyone: bool = False
    reminder_mention_everyone: bool = False
    close_mention_everyone: bool = False
    opens_at_utc: datetime | None = None
    result_visibility: str = "PublicLive"


@dataclass(frozen=True)
class SurveySubmitResult:
    status: str
    survey_id: int
    response_id: int | None = None
    message: str = ""

    @property
    def accepted(self) -> bool:
        return self.status in {"recorded", "changed"}


@dataclass(frozen=True)
class SurveyCloseResult:
    status: str
    survey_id: int
    message: str = ""

    @property
    def closed(self) -> bool:
        return self.status == "closed"


@dataclass(frozen=True)
class SurveyLookupChoice:
    survey_id: int
    title: str
    status: str
    channel_id: int
    closes_at_utc: datetime
    closed_at_utc: datetime | None = None


@dataclass(frozen=True)
class SurveyAnswerAuditRow:
    survey_id: int
    title: str
    closed_at_utc: datetime | None
    response_id: int
    discord_user_id: int
    response_created_at_utc: datetime
    response_updated_at_utc: datetime
    question_id: int
    question_key: str
    question_prompt: str
    question_type: str
    selected_option_ids: tuple[int, ...]
    selected_option_keys: tuple[str, ...]
    selected_option_labels: tuple[str, ...]
    original_option_ids: tuple[int, ...]
    original_option_keys: tuple[str, ...]
    original_option_labels: tuple[str, ...]
    is_required: bool = True
    text_answer: str | None = None
    original_text_answer: str | None = None
    selected_option_detail_notes: tuple[str, ...] = ()
    original_selected_option_detail_notes: tuple[str, ...] = ()
    rating_value: int | None = None
    original_rating_value: int | None = None
    rating_label: str | None = None
    original_rating_label: str | None = None
    ranking_option_id: int | None = None
    ranking_option_key: str | None = None
    ranking_option_label: str | None = None
    ranking_rank_value: int | None = None
    original_ranking_rank_value: int | None = None


@dataclass(frozen=True)
class SurveyReportingQuestionRow:
    survey_id: int
    title: str
    status: str
    result_visibility: str
    question_id: int
    question_key: str
    question_prompt: str
    question_type: str
    question_sort_order: int
    is_required: bool
    min_selections: int
    max_selections: int
    allow_details: bool
    total_responses: int
    option_count: int
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
    rating_scale_min: int = DEFAULT_RATING_MIN_VALUE
    rating_scale_max: int = DEFAULT_RATING_MAX_VALUE
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
class SurveyReportingOptionRow:
    survey_id: int
    title: str
    status: str
    result_visibility: str
    question_id: int
    question_key: str
    question_prompt: str
    question_type: str
    question_sort_order: int
    is_required: bool
    option_id: int
    option_key: str
    option_label: str
    option_sort_order: int
    total_responses: int
    selection_count: int
    is_top_selection: bool
    ranked_count: int
    average_rank: float | None
    rank1_count: int
    rank2_count: int
    rank3_count: int
    rank4_count: int
    rank5_count: int
    rank6_count: int
    option_emoji: OptionEmoji | None = None


@dataclass(frozen=True)
class RenderedSurveyCard:
    filename: str
    image_bytes: BytesIO
