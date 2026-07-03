from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import logging

from voting import survey_dal
from voting.result_visibility import normalize_result_visibility
from voting.service import (
    MAX_CLOSE_REASON_LEN,
    MAX_OPTION_LABEL_LEN,
    MAX_TITLE_LEN,
    VoteValidationError,
    _validate_description,
    parse_close_time,
    parse_reminder_offsets,
)
from voting.survey_models import (
    SURVEY_QUESTION_MULTI_SELECT,
    SURVEY_QUESTION_SINGLE_CHOICE,
    SurveyCloseResult,
    SurveyCreateRequest,
    SurveyLookupChoice,
    SurveyQuestionCreateRequest,
    SurveySnapshot,
    SurveySubmitResult,
)

logger = logging.getLogger(__name__)

MIN_SURVEY_QUESTIONS = 2
MAX_SURVEY_QUESTIONS = 5
MIN_SURVEY_OPTIONS = 2
MAX_SURVEY_OPTIONS = 6
MAX_SURVEY_QUESTION_PROMPT_LEN = 180
SURVEY_QUESTION_TYPE_CHOICES: dict[str, str] = {
    SURVEY_QUESTION_SINGLE_CHOICE: "Single choice",
    SURVEY_QUESTION_MULTI_SELECT: "Multi-select",
}


def _normalize_question_type(value: str | None, *, max_selections: int | None = None) -> str:
    text = str(value or "").strip()
    if not text:
        if max_selections is not None and int(max_selections) > 1:
            return SURVEY_QUESTION_MULTI_SELECT
        return SURVEY_QUESTION_SINGLE_CHOICE
    by_casefold = {item.casefold(): item for item in SURVEY_QUESTION_TYPE_CHOICES}
    normalized = by_casefold.get(text.casefold())
    if normalized is None:
        raise VoteValidationError("Choose a valid survey question type.")
    return normalized


def _validate_close_reason(reason: str) -> str:
    clean_reason = (reason or "").strip() or "closed"
    if len(clean_reason) > MAX_CLOSE_REASON_LEN:
        raise VoteValidationError(
            f"Close reason must be {MAX_CLOSE_REASON_LEN} characters or fewer."
        )
    return clean_reason


def _validate_survey_option_labels(labels: tuple[str, ...]) -> tuple[str, ...]:
    if len(labels) < MIN_SURVEY_OPTIONS:
        raise VoteValidationError("Each survey question needs at least two options.")
    if len(labels) > MAX_SURVEY_OPTIONS:
        raise VoteValidationError(
            f"Each survey question supports at most {MAX_SURVEY_OPTIONS} options."
        )
    seen: set[str] = set()
    output: list[str] = []
    for label in labels:
        clean_label = str(label or "").strip()
        if not clean_label:
            continue
        if len(clean_label) > MAX_OPTION_LABEL_LEN:
            raise VoteValidationError(
                f"Survey option labels must be {MAX_OPTION_LABEL_LEN} characters or fewer."
            )
        key = clean_label.casefold()
        if key in seen:
            raise VoteValidationError("Survey question options must be unique after trimming.")
        seen.add(key)
        output.append(clean_label)
    if len(output) < MIN_SURVEY_OPTIONS:
        raise VoteValidationError("Each survey question needs at least two options.")
    return tuple(output)


def build_question_request(
    *,
    prompt: str,
    question_type: str | None,
    options: tuple[str, ...],
    min_selections: int | None = None,
    max_selections: int | None = None,
) -> SurveyQuestionCreateRequest:
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt:
        raise VoteValidationError("Survey question prompt is required.")
    if len(clean_prompt) > MAX_SURVEY_QUESTION_PROMPT_LEN:
        raise VoteValidationError(
            f"Survey question prompt must be {MAX_SURVEY_QUESTION_PROMPT_LEN} characters or fewer."
        )
    clean_options = _validate_survey_option_labels(options)
    minimum = 1 if min_selections is None else int(min_selections)
    maximum = 1 if max_selections is None else int(max_selections)
    normalized_type = _normalize_question_type(question_type, max_selections=maximum)
    if normalized_type == SURVEY_QUESTION_SINGLE_CHOICE:
        if minimum != 1 or maximum != 1:
            raise VoteValidationError(
                "Single-choice survey questions must use exactly one selection."
            )
        return SurveyQuestionCreateRequest(
            prompt=clean_prompt,
            question_type=normalized_type,
            options=clean_options,
            min_selections=1,
            max_selections=1,
        )
    if minimum < 1:
        raise VoteValidationError("Minimum selections must be at least 1.")
    if maximum < minimum:
        raise VoteValidationError("Maximum selections must be at least the minimum selections.")
    if maximum > len(clean_options):
        raise VoteValidationError("Maximum selections cannot exceed the number of options.")
    if maximum < 2:
        raise VoteValidationError(
            "Multi-select survey questions must allow at least two selections."
        )
    return SurveyQuestionCreateRequest(
        prompt=clean_prompt,
        question_type=normalized_type,
        options=clean_options,
        min_selections=minimum,
        max_selections=maximum,
    )


def build_create_request(
    *,
    guild_id: int,
    channel_id: int,
    created_by_discord_user_id: int,
    title: str,
    description: str | None,
    questions: tuple[SurveyQuestionCreateRequest, ...],
    close_time_utc: str,
    reminder_offsets: str | None,
    allow_response_change: bool,
    launch_mention_everyone: bool,
    reminder_mention_everyone: bool,
    close_mention_everyone: bool,
    result_visibility: str | None = None,
    now_utc: datetime | None = None,
) -> SurveyCreateRequest:
    now = now_utc or datetime.now(UTC)
    clean_title = str(title or "").strip()
    if not clean_title:
        raise VoteValidationError("Survey title is required.")
    if len(clean_title) > MAX_TITLE_LEN:
        raise VoteValidationError(f"Survey title must be {MAX_TITLE_LEN} characters or fewer.")
    clean_description = _validate_description(description)
    if len(questions) < MIN_SURVEY_QUESTIONS:
        raise VoteValidationError(f"Surveys need at least {MIN_SURVEY_QUESTIONS} questions.")
    if len(questions) > MAX_SURVEY_QUESTIONS:
        raise VoteValidationError(f"Surveys support at most {MAX_SURVEY_QUESTIONS} questions.")
    closes_at = parse_close_time(close_time_utc, now_utc=now)
    if closes_at <= now:
        raise VoteValidationError("Survey close time must be in the future.")
    try:
        normalized_visibility = normalize_result_visibility(result_visibility)
    except ValueError as exc:
        raise VoteValidationError(str(exc)) from exc
    offsets = tuple(
        offset
        for offset in parse_reminder_offsets(reminder_offsets)
        if closes_at.timestamp() - (offset * 60) > now.timestamp()
    )
    return SurveyCreateRequest(
        guild_id=int(guild_id),
        channel_id=int(channel_id),
        created_by_discord_user_id=int(created_by_discord_user_id),
        title=clean_title,
        description=clean_description,
        questions=questions,
        closes_at_utc=closes_at,
        reminder_offsets_minutes=offsets,
        allow_response_change=bool(allow_response_change),
        launch_mention_everyone=bool(launch_mention_everyone),
        reminder_mention_everyone=bool(reminder_mention_everyone),
        close_mention_everyone=bool(close_mention_everyone),
        result_visibility=normalized_visibility,
    )


def validate_answers(
    snapshot: SurveySnapshot,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
) -> dict[int, tuple[int, ...]]:
    output: dict[int, tuple[int, ...]] = {}
    for question in snapshot.questions:
        selected_ids = tuple(
            sorted(
                {
                    int(option_id)
                    for option_id in answers_by_question_id.get(question.question_id, ())
                }
            )
        )
        if len(selected_ids) < question.min_selections:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: choose at least {question.min_selections}."
            )
        if len(selected_ids) > question.max_selections:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: choose at most {question.max_selections}."
            )
        valid_ids = {option.option_id for option in question.options}
        if any(option_id not in valid_ids for option_id in selected_ids):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more options are not valid."
            )
        output[question.question_id] = selected_ids
    return output


async def create_survey_record(req: SurveyCreateRequest) -> SurveySnapshot:
    survey_id = await survey_dal.create_survey(req)
    if survey_id <= 0:
        raise RuntimeError("Survey was not created.")
    snapshot = await survey_dal.get_survey_snapshot(survey_id)
    if snapshot is None:
        raise RuntimeError("Survey was created but could not be loaded.")
    logger.info(
        "survey_created survey_id=%s guild_id=%s channel_id=%s actor_discord_id=%s closes_at=%s",
        snapshot.survey_id,
        snapshot.guild_id,
        snapshot.channel_id,
        req.created_by_discord_user_id,
        snapshot.closes_at_utc.isoformat(),
    )
    return snapshot


async def attach_survey_message(
    snapshot: SurveySnapshot, *, channel_id: int, message_id: int
) -> SurveySnapshot:
    updated = await survey_dal.update_survey_message(
        snapshot.survey_id, channel_id=channel_id, message_id=message_id
    )
    if not updated:
        raise RuntimeError("Survey message identifiers could not be persisted.")
    refreshed = await survey_dal.get_survey_snapshot(snapshot.survey_id)
    if refreshed is None:
        raise RuntimeError("Survey could not be reloaded after launch.")
    return refreshed


async def submit_survey_response(
    *,
    survey_id: int,
    discord_user_id: int,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
    now_utc: datetime | None = None,
) -> tuple[SurveySubmitResult, SurveySnapshot | None]:
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        return (
            SurveySubmitResult("missing", int(survey_id), message="This survey no longer exists."),
            None,
        )
    validated = validate_answers(snapshot, answers_by_question_id)
    result = await survey_dal.submit_survey_response(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
        answers_by_question_id=validated,
        now_utc=now_utc or datetime.now(UTC),
    )
    refreshed = await survey_dal.get_survey_snapshot(int(survey_id)) if result.accepted else None
    return result, refreshed


async def get_existing_answer_option_ids(
    *, survey_id: int, discord_user_id: int
) -> dict[int, tuple[int, ...]]:
    return await survey_dal.get_existing_answer_option_ids(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
    )


async def get_survey_snapshot(survey_id: int) -> SurveySnapshot | None:
    return await survey_dal.get_survey_snapshot(int(survey_id))


async def close_survey(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    reason: str,
    now_utc: datetime | None = None,
) -> tuple[SurveyCloseResult, SurveySnapshot | None]:
    clean_reason = _validate_close_reason(reason)
    result = await survey_dal.close_survey(
        survey_id=int(survey_id),
        actor_discord_user_id=actor_discord_user_id,
        reason=clean_reason,
        now_utc=now_utc or datetime.now(UTC),
    )
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id)) if result.closed else None
    logger.info(
        "survey_close status=%s survey_id=%s actor_discord_id=%s reason=%s",
        result.status,
        survey_id,
        actor_discord_user_id,
        clean_reason,
    )
    return result, snapshot


async def cancel_survey_launch_failure(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    reason: str = "launch failed",
    now_utc: datetime | None = None,
) -> bool:
    clean_reason = _validate_close_reason(reason)
    ok = await survey_dal.cancel_survey_launch_failure(
        survey_id=int(survey_id),
        actor_discord_user_id=actor_discord_user_id,
        reason=clean_reason,
        now_utc=now_utc or datetime.now(UTC),
    )
    logger.info(
        "survey_launch_failure_cancelled=%s survey_id=%s actor_discord_id=%s reason=%s",
        ok,
        survey_id,
        actor_discord_user_id,
        clean_reason,
    )
    return ok


async def search_survey_choices(
    query: str | None = None, *, limit: int = 25
) -> list[SurveyLookupChoice]:
    return await survey_dal.search_surveys(query=query, limit=limit)


async def search_closed_survey_choices(
    query: str | None = None, *, limit: int = 25
) -> list[SurveyLookupChoice]:
    return await survey_dal.search_closed_surveys(query=query, limit=limit)


async def record_message_edit_failed(
    *,
    survey_id: int,
    actor_discord_user_id: int | None,
    source: str,
) -> None:
    await survey_dal.insert_audit(
        survey_id=int(survey_id),
        actor_discord_user_id=actor_discord_user_id,
        action_type="MessageEditFailed",
        details={"source": source},
    )
