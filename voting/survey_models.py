from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO


SURVEY_QUESTION_SINGLE_CHOICE = "SingleChoice"
SURVEY_QUESTION_MULTI_SELECT = "MultiSelect"


@dataclass(frozen=True)
class SurveyQuestionOption:
    option_id: int
    survey_question_id: int
    option_key: str
    label: str
    sort_order: int
    response_count: int = 0


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
    min_selections: int = 1
    max_selections: int = 1


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


@dataclass(frozen=True)
class RenderedSurveyCard:
    filename: str
    image_bytes: BytesIO
