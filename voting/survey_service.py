from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import logging

from voting import survey_dal
from voting.option_emojis import OptionEmoji
from voting.result_visibility import normalize_result_visibility
from voting.service import (
    MAX_CLOSE_REASON_LEN,
    MAX_OPTION_LABEL_LEN,
    MAX_TITLE_LEN,
    VoteValidationError,
    _validate_description,
    parse_close_time,
    parse_option_emoji,
    parse_reminder_offsets,
)
from voting.survey_models import (
    DEFAULT_RATING_MAX_VALUE,
    DEFAULT_RATING_MIN_VALUE,
    MAX_RATING_VALUE,
    SURVEY_QUESTION_MULTI_SELECT,
    SURVEY_QUESTION_RANKING,
    SURVEY_QUESTION_RATING,
    SURVEY_QUESTION_SINGLE_CHOICE,
    SURVEY_QUESTION_TEXT,
    SurveyCloseResult,
    SurveyCreateRequest,
    SurveyDraftSaveResult,
    SurveyLookupChoice,
    SurveyQuestionCreateRequest,
    SurveyRatingLabel,
    SurveyResponseDraft,
    SurveyResponsePayload,
    SurveySnapshot,
    SurveySubmitResult,
)

logger = logging.getLogger(__name__)

MIN_SURVEY_QUESTIONS = 2
MAX_SURVEY_QUESTIONS = 5
MIN_SURVEY_OPTIONS = 2
MAX_SURVEY_OPTIONS = 6
MAX_SURVEY_QUESTION_PROMPT_LEN = 180
MAX_SURVEY_TEXT_ANSWER_LEN = 500
MAX_SURVEY_DETAIL_LEN = 300
MAX_RATING_SCALE_LABEL_LEN = 40
SURVEY_QUESTION_TYPE_CHOICES: dict[str, str] = {
    SURVEY_QUESTION_SINGLE_CHOICE: "Single choice",
    SURVEY_QUESTION_MULTI_SELECT: "Multi-select",
    SURVEY_QUESTION_TEXT: "Text",
    SURVEY_QUESTION_RATING: "Rating",
    SURVEY_QUESTION_RANKING: "Ranking",
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


def _validate_option_emojis(
    values: tuple[OptionEmoji | str | None, ...] | None,
    *,
    option_count: int,
) -> tuple[OptionEmoji | None, ...]:
    if not values:
        return tuple(None for _ in range(option_count))
    if len(values) > option_count:
        raise VoteValidationError("Option icons cannot be set for missing options.")
    output: list[OptionEmoji | None] = []
    for value in values:
        if isinstance(value, OptionEmoji) or value is None:
            output.append(value)
        else:
            output.append(parse_option_emoji(value))
    while len(output) < option_count:
        output.append(None)
    return tuple(output)


def _clean_limited_text(
    value: str | None, *, limit: int, field_name: str, required: bool
) -> str | None:
    clean = str(value or "").strip()
    if not clean:
        if required:
            raise VoteValidationError(f"{field_name} is required.")
        return None
    if len(clean) > limit:
        raise VoteValidationError(f"{field_name} must be {limit} characters or fewer.")
    return clean


def _rating_bounds_for_question(question) -> tuple[int, int]:
    minimum = int(
        getattr(question, "rating_min_value", DEFAULT_RATING_MIN_VALUE) or DEFAULT_RATING_MIN_VALUE
    )
    maximum = int(
        getattr(question, "rating_max_value", DEFAULT_RATING_MAX_VALUE) or DEFAULT_RATING_MAX_VALUE
    )
    return minimum, maximum


def _rating_range_message(question) -> str:
    minimum, maximum = _rating_bounds_for_question(question)
    low = str(getattr(question, "rating_low_label", "") or "").strip()
    high = str(getattr(question, "rating_high_label", "") or "").strip()
    if low and high:
        return f"from {minimum} to {maximum} ({low} to {high})"
    if low:
        return f"from {minimum} to {maximum} ({low} low)"
    if high:
        return f"from {minimum} to {maximum} ({high} high)"
    return f"from {minimum} to {maximum}"


def _clean_optional_label(value: str | None, *, field_name: str, limit: int) -> str | None:
    clean = str(value or "").strip()
    if not clean:
        return None
    if len(clean) > limit:
        raise VoteValidationError(f"{field_name} must be {limit} characters or fewer.")
    return clean


def _coerce_rating_scale_value(value: int | str | None, *, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise VoteValidationError(f"{field_name} must be a whole number.") from exc


def _validate_rating_scale(
    *,
    min_value: int | None,
    max_value: int | None,
    low_label: str | None,
    high_label: str | None,
    rating_labels: Mapping[int, str] | tuple[SurveyRatingLabel, ...] | None,
) -> tuple[int, int, str | None, str | None, tuple[SurveyRatingLabel, ...]]:
    minimum = (
        DEFAULT_RATING_MIN_VALUE
        if min_value is None
        else _coerce_rating_scale_value(min_value, field_name="Rating scale minimum")
    )
    maximum = (
        DEFAULT_RATING_MAX_VALUE
        if max_value is None
        else _coerce_rating_scale_value(max_value, field_name="Rating scale maximum")
    )
    if minimum < DEFAULT_RATING_MIN_VALUE or maximum > MAX_RATING_VALUE:
        raise VoteValidationError(
            f"Rating scales must stay between {DEFAULT_RATING_MIN_VALUE} and {MAX_RATING_VALUE}."
        )
    if maximum <= minimum:
        raise VoteValidationError("Rating scale maximum must be greater than the minimum.")
    clean_low = _clean_optional_label(
        low_label,
        field_name="Rating low label",
        limit=MAX_RATING_SCALE_LABEL_LEN,
    )
    clean_high = _clean_optional_label(
        high_label,
        field_name="Rating high label",
        limit=MAX_RATING_SCALE_LABEL_LEN,
    )
    raw_items: list[tuple[int, str]] = []
    if isinstance(rating_labels, Mapping):
        raw_items = [
            (
                _coerce_rating_scale_value(key, field_name="Rating choice label value"),
                str(value or ""),
            )
            for key, value in rating_labels.items()
        ]
    else:
        raw_items = [
            (
                _coerce_rating_scale_value(
                    item.rating_value,
                    field_name="Rating choice label value",
                ),
                str(item.label or ""),
            )
            for item in (rating_labels or ())
        ]
    seen: set[int] = set()
    clean_labels: list[SurveyRatingLabel] = []
    for rating_value, label in raw_items:
        if rating_value < minimum or rating_value > maximum:
            raise VoteValidationError("Rating choice labels must be within the rating scale.")
        if rating_value in seen:
            raise VoteValidationError("Rating choice labels must use each value only once.")
        clean_label = _clean_optional_label(
            label,
            field_name=f"Rating label {rating_value}",
            limit=MAX_OPTION_LABEL_LEN,
        )
        if clean_label is None:
            continue
        seen.add(rating_value)
        clean_labels.append(SurveyRatingLabel(rating_value=rating_value, label=clean_label))
    return (
        minimum,
        maximum,
        clean_low,
        clean_high,
        tuple(sorted(clean_labels, key=lambda item: item.rating_value)),
    )


def build_question_request(
    *,
    prompt: str,
    question_type: str | None,
    options: tuple[str, ...] | None = None,
    min_selections: int | None = None,
    max_selections: int | None = None,
    allow_details: bool = False,
    is_required: bool = True,
    rating_min_value: int | None = None,
    rating_max_value: int | None = None,
    rating_low_label: str | None = None,
    rating_high_label: str | None = None,
    rating_labels: Mapping[int, str] | tuple[SurveyRatingLabel, ...] | None = None,
    option_emojis: tuple[OptionEmoji | str | None, ...] | None = None,
) -> SurveyQuestionCreateRequest:
    clean_prompt = str(prompt or "").strip()
    if not clean_prompt:
        raise VoteValidationError("Survey question prompt is required.")
    if len(clean_prompt) > MAX_SURVEY_QUESTION_PROMPT_LEN:
        raise VoteValidationError(
            f"Survey question prompt must be {MAX_SURVEY_QUESTION_PROMPT_LEN} characters or fewer."
        )
    minimum = 1 if min_selections is None else int(min_selections)
    maximum = 1 if max_selections is None else int(max_selections)
    normalized_type = _normalize_question_type(question_type, max_selections=maximum)
    raw_options = tuple(options or ())
    if normalized_type == SURVEY_QUESTION_RATING:
        if tuple(str(item or "").strip() for item in raw_options if str(item or "").strip()):
            raise VoteValidationError("Rating survey questions do not use options.")
        if allow_details:
            raise VoteValidationError("Rating survey questions cannot allow choice details.")
        scale_min, scale_max, low_label, high_label, clean_rating_labels = _validate_rating_scale(
            min_value=rating_min_value,
            max_value=rating_max_value,
            low_label=rating_low_label,
            high_label=rating_high_label,
            rating_labels=rating_labels,
        )
        return SurveyQuestionCreateRequest(
            prompt=clean_prompt,
            question_type=normalized_type,
            options=(),
            option_emojis=(),
            min_selections=0,
            max_selections=0,
            allow_details=False,
            is_required=bool(is_required),
            rating_min_value=scale_min,
            rating_max_value=scale_max,
            rating_low_label=low_label,
            rating_high_label=high_label,
            rating_labels=clean_rating_labels,
        )
    if normalized_type == SURVEY_QUESTION_RANKING:
        clean_options = _validate_survey_option_labels(raw_options)
        if allow_details:
            raise VoteValidationError("Ranking survey questions cannot allow choice details.")
        return SurveyQuestionCreateRequest(
            prompt=clean_prompt,
            question_type=normalized_type,
            options=clean_options,
            option_emojis=_validate_option_emojis(option_emojis, option_count=len(clean_options)),
            min_selections=len(clean_options),
            max_selections=len(clean_options),
            allow_details=False,
            is_required=bool(is_required),
        )
    if normalized_type == SURVEY_QUESTION_TEXT:
        if tuple(str(item or "").strip() for item in raw_options if str(item or "").strip()):
            raise VoteValidationError("Text survey questions do not use options.")
        if allow_details:
            raise VoteValidationError("Text survey questions cannot allow choice details.")
        return SurveyQuestionCreateRequest(
            prompt=clean_prompt,
            question_type=normalized_type,
            options=(),
            option_emojis=(),
            min_selections=0,
            max_selections=0,
            allow_details=False,
            is_required=bool(is_required),
        )
    clean_options = _validate_survey_option_labels(raw_options)
    if normalized_type == SURVEY_QUESTION_SINGLE_CHOICE:
        if minimum != 1 or maximum != 1:
            raise VoteValidationError(
                "Single-choice survey questions must use exactly one selection."
            )
        return SurveyQuestionCreateRequest(
            prompt=clean_prompt,
            question_type=normalized_type,
            options=clean_options,
            option_emojis=_validate_option_emojis(option_emojis, option_count=len(clean_options)),
            min_selections=1,
            max_selections=1,
            allow_details=bool(allow_details),
            is_required=bool(is_required),
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
        option_emojis=_validate_option_emojis(option_emojis, option_count=len(clean_options)),
        min_selections=minimum,
        max_selections=maximum,
        allow_details=bool(allow_details),
        is_required=bool(is_required),
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
    return validate_response_payload(
        snapshot,
        answers_by_question_id=answers_by_question_id,
    ).selected_option_ids


def validate_response_payload(
    snapshot: SurveySnapshot,
    *,
    answers_by_question_id: Mapping[int, tuple[int, ...]] | None = None,
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    rating_answers_by_question_id: Mapping[int, int | str | None] | None = None,
    ranking_answers_by_question_id: Mapping[int, tuple[int, ...] | list[int] | None] | None = None,
) -> SurveyResponsePayload:
    choice_answers = answers_by_question_id or {}
    text_answers = text_answers_by_question_id or {}
    detail_answers = detail_text_by_question_option or {}
    rating_answers: dict[int, int | str | None] = {}
    ranking_answers: dict[int, tuple[int, ...] | list[int] | None] = {}
    selected_output: dict[int, tuple[int, ...]] = {}
    text_output: dict[int, str] = {}
    detail_output: dict[tuple[int, int], str] = {}
    rating_output: dict[int, int] = {}
    ranking_output: dict[int, tuple[int, ...]] = {}
    questions_by_id = {question.question_id: question for question in snapshot.questions}
    for raw_question_id in choice_answers:
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            raise VoteValidationError("One or more selected answers are not valid.") from None
        if question_id not in questions_by_id:
            raise VoteValidationError("One or more selected answers are not valid.")
    for raw_question_id in text_answers:
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            raise VoteValidationError("One or more text answers are not valid.") from None
        if question_id not in questions_by_id:
            raise VoteValidationError("One or more text answers are not valid.")
    for raw_question_id, raw_rating in (rating_answers_by_question_id or {}).items():
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            raise VoteValidationError("One or more rating answers are not valid.") from None
        if question_id not in questions_by_id:
            raise VoteValidationError("One or more rating answers are not valid.")
        if question_id in rating_answers:
            raise VoteValidationError("One or more rating answers are not valid.")
        rating_answers[question_id] = raw_rating
    for raw_question_id, raw_ranking in (ranking_answers_by_question_id or {}).items():
        try:
            question_id = int(raw_question_id)
        except (TypeError, ValueError):
            raise VoteValidationError("One or more ranking answers are not valid.") from None
        if question_id not in questions_by_id:
            raise VoteValidationError("One or more ranking answers are not valid.")
        if question_id in ranking_answers:
            raise VoteValidationError("One or more ranking answers are not valid.")
        ranking_answers[question_id] = raw_ranking
    for question in snapshot.questions:
        if question.question_type == SURVEY_QUESTION_RANKING:
            if choice_answers.get(question.question_id):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: ranking questions do not use selections."
                )
            if (
                question.question_id in text_answers
                and str(text_answers.get(question.question_id) or "").strip()
            ):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: this question does not accept text."
                )
            if question.question_id in rating_answers:
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: this question does not accept ratings."
                )
            raw_ranking = ranking_answers.get(question.question_id)
            if raw_ranking in (None, (), []):
                if question.is_required:
                    raise VoteValidationError(
                        f"Answer question {question.sort_order}: rank every option."
                    )
                continue
            try:
                if isinstance(raw_ranking, (str, bytes)):
                    raise TypeError
                ranked_option_ids = tuple(int(option_id) for option_id in raw_ranking or ())
            except (TypeError, ValueError):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: one or more ranked options are not valid."
                ) from None
            expected_option_ids = {option.option_id for option in question.options}
            if len(ranked_option_ids) != len(question.options):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: rank every option."
                )
            if len(set(ranked_option_ids)) != len(ranked_option_ids):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: each option can only be ranked once."
                )
            if set(ranked_option_ids) != expected_option_ids:
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: one or more ranked options are not valid."
                )
            ranking_output[question.question_id] = ranked_option_ids
            continue
        if question.question_type == SURVEY_QUESTION_RATING:
            if choice_answers.get(question.question_id):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: rating questions do not use options."
                )
            if (
                question.question_id in text_answers
                and str(text_answers.get(question.question_id) or "").strip()
            ):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: this question does not accept text."
                )
            raw_rating = rating_answers.get(question.question_id)
            if raw_rating in (None, ""):
                if question.is_required:
                    raise VoteValidationError(
                        f"Answer question {question.sort_order}: choose a rating {_rating_range_message(question)}."
                    )
                continue
            try:
                rating_value = int(raw_rating)
            except (TypeError, ValueError):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: rating must be {_rating_range_message(question)}."
                ) from None
            rating_min, rating_max = _rating_bounds_for_question(question)
            if rating_value < rating_min or rating_value > rating_max:
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: rating must be {_rating_range_message(question)}."
                )
            rating_output[question.question_id] = rating_value
            continue
        if question.question_type == SURVEY_QUESTION_TEXT:
            if choice_answers.get(question.question_id):
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: text questions do not use options."
                )
            if question.question_id in rating_answers:
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: this question does not accept ratings."
                )
            if question.question_id in ranking_answers:
                raise VoteValidationError(
                    f"Answer question {question.sort_order}: this question does not accept rankings."
                )
            clean_text = _clean_limited_text(
                text_answers.get(question.question_id),
                limit=MAX_SURVEY_TEXT_ANSWER_LEN,
                field_name=f"Answer question {question.sort_order}",
                required=question.is_required,
            )
            if clean_text is not None:
                text_output[question.question_id] = clean_text
            continue
        if question.question_id in rating_answers:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept ratings."
            )
        if question.question_id in ranking_answers:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept rankings."
            )
        raw_selected_ids = choice_answers.get(question.question_id, ())
        try:
            if raw_selected_ids is None or isinstance(raw_selected_ids, (str, bytes)):
                raise TypeError
            selected_ids = tuple(sorted({int(option_id) for option_id in raw_selected_ids}))
        except (TypeError, ValueError):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more options are not valid."
            ) from None
        if not selected_ids and not question.is_required:
            continue
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
        selected_output[question.question_id] = selected_ids

    for question_id, text in text_answers.items():
        normalized_question_id = int(question_id)
        question = questions_by_id.get(normalized_question_id)
        if question is None:
            raise VoteValidationError("One or more text answers are not valid.")
        if question.question_type != SURVEY_QUESTION_TEXT:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept text."
            )
        if normalized_question_id in rating_answers:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept ratings."
            )
        if normalized_question_id in ranking_answers:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept rankings."
            )
        if normalized_question_id not in text_output:
            clean_text = _clean_limited_text(
                text,
                limit=MAX_SURVEY_TEXT_ANSWER_LEN,
                field_name=f"Answer question {question.sort_order}",
                required=question.is_required,
            )
            if clean_text is not None:
                text_output[normalized_question_id] = clean_text

    for raw_key, text in detail_answers.items():
        try:
            question_id, option_id = int(raw_key[0]), int(raw_key[1])
        except (IndexError, TypeError, ValueError):
            raise VoteValidationError("One or more detail notes are not valid.") from None
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more detail notes are not valid.")
        if (
            question.question_type in {SURVEY_QUESTION_TEXT, SURVEY_QUESTION_RATING}
            or question.question_type == SURVEY_QUESTION_RANKING
            or not question.allow_details
        ):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: details are not enabled."
            )
        if option_id not in selected_output.get(question_id, ()):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: details can only be added to selected options."
            )
        clean_detail = _clean_limited_text(
            text,
            limit=MAX_SURVEY_DETAIL_LEN,
            field_name=f"Detail for question {question.sort_order}",
            required=False,
        )
        if clean_detail is not None:
            detail_output[(question_id, option_id)] = clean_detail

    return SurveyResponsePayload(
        selected_option_ids=selected_output,
        text_answers=text_output,
        detail_text_by_option=detail_output,
        rating_answers=rating_output,
        ranking_answers=ranking_output,
    )


def validate_draft_response_payload(
    snapshot: SurveySnapshot,
    *,
    answers_by_question_id: Mapping[int, tuple[int, ...]] | None = None,
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    rating_answers_by_question_id: Mapping[int, int | str | None] | None = None,
    ranking_answers_by_question_id: Mapping[int, tuple[int, ...] | list[int] | None] | None = None,
) -> SurveyResponsePayload:
    """Validate a partial respondent draft without applying final-submit completeness rules."""

    choice_answers = answers_by_question_id or {}
    text_answers = text_answers_by_question_id or {}
    detail_answers = detail_text_by_question_option or {}
    rating_answers = rating_answers_by_question_id or {}
    ranking_answers = ranking_answers_by_question_id or {}
    questions_by_id = {question.question_id: question for question in snapshot.questions}
    selected_output: dict[int, tuple[int, ...]] = {}
    text_output: dict[int, str] = {}
    detail_output: dict[tuple[int, int], str] = {}
    rating_output: dict[int, int] = {}
    ranking_output: dict[int, tuple[int, ...]] = {}

    for raw_question_id, raw_selected_ids in choice_answers.items():
        question_id = _coerce_question_id(raw_question_id)
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more selected answers are not valid.")
        if question.question_type in {
            SURVEY_QUESTION_TEXT,
            SURVEY_QUESTION_RATING,
            SURVEY_QUESTION_RANKING,
        }:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept options."
            )
        try:
            if raw_selected_ids is None or isinstance(raw_selected_ids, (str, bytes)):
                raise TypeError
            selected_ids = tuple(sorted({int(option_id) for option_id in raw_selected_ids}))
        except (TypeError, ValueError):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more options are not valid."
            ) from None
        if not selected_ids:
            continue
        if len(selected_ids) > question.max_selections:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: choose at most {question.max_selections}."
            )
        valid_ids = {option.option_id for option in question.options}
        if any(option_id not in valid_ids for option_id in selected_ids):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more options are not valid."
            )
        selected_output[question_id] = selected_ids

    for raw_question_id, raw_text in text_answers.items():
        question_id = _coerce_question_id(raw_question_id)
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more text answers are not valid.")
        if question.question_type != SURVEY_QUESTION_TEXT:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept text."
            )
        clean_text = _clean_limited_text(
            raw_text,
            limit=MAX_SURVEY_TEXT_ANSWER_LEN,
            field_name=f"Answer question {question.sort_order}",
            required=False,
        )
        if clean_text is not None:
            text_output[question_id] = clean_text

    for raw_question_id, raw_rating in rating_answers.items():
        question_id = _coerce_question_id(raw_question_id)
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more rating answers are not valid.")
        if question.question_type != SURVEY_QUESTION_RATING:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept ratings."
            )
        if raw_rating in (None, ""):
            continue
        try:
            rating_value = int(raw_rating)
        except (TypeError, ValueError):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: rating must be {_rating_range_message(question)}."
            ) from None
        rating_min, rating_max = _rating_bounds_for_question(question)
        if rating_value < rating_min or rating_value > rating_max:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: rating must be {_rating_range_message(question)}."
            )
        rating_output[question_id] = rating_value

    for raw_question_id, raw_ranking in ranking_answers.items():
        question_id = _coerce_question_id(raw_question_id)
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more ranking answers are not valid.")
        if question.question_type != SURVEY_QUESTION_RANKING:
            raise VoteValidationError(
                f"Answer question {question.sort_order}: this question does not accept rankings."
            )
        if raw_ranking in (None, (), []):
            continue
        try:
            if isinstance(raw_ranking, (str, bytes)):
                raise TypeError
            ranked_option_ids = tuple(int(option_id) for option_id in raw_ranking or ())
        except (TypeError, ValueError):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more ranked options are not valid."
            ) from None
        if len(ranked_option_ids) > len(question.options):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: rank at most {len(question.options)} options."
            )
        nonzero_option_ids = tuple(option_id for option_id in ranked_option_ids if option_id)
        if len(set(nonzero_option_ids)) != len(nonzero_option_ids):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: each option can only be ranked once."
            )
        valid_ids = {option.option_id for option in question.options}
        if any(option_id not in valid_ids for option_id in nonzero_option_ids):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: one or more ranked options are not valid."
            )
        if nonzero_option_ids:
            ranking_output[question_id] = ranked_option_ids

    for raw_key, text in detail_answers.items():
        try:
            question_id, option_id = int(raw_key[0]), int(raw_key[1])
        except (IndexError, TypeError, ValueError):
            raise VoteValidationError("One or more detail notes are not valid.") from None
        question = questions_by_id.get(question_id)
        if question is None:
            raise VoteValidationError("One or more detail notes are not valid.")
        if (
            question.question_type in {SURVEY_QUESTION_TEXT, SURVEY_QUESTION_RATING}
            or question.question_type == SURVEY_QUESTION_RANKING
            or not question.allow_details
        ):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: details are not enabled."
            )
        if option_id not in selected_output.get(question_id, ()):
            raise VoteValidationError(
                f"Answer question {question.sort_order}: details can only be added to selected options."
            )
        clean_detail = _clean_limited_text(
            text,
            limit=MAX_SURVEY_DETAIL_LEN,
            field_name=f"Detail for question {question.sort_order}",
            required=False,
        )
        if clean_detail is not None:
            detail_output[(question_id, option_id)] = clean_detail

    return SurveyResponsePayload(
        selected_option_ids=selected_output,
        text_answers=text_output,
        detail_text_by_option=detail_output,
        rating_answers=rating_output,
        ranking_answers=ranking_output,
    )


def _coerce_question_id(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise VoteValidationError("One or more answers are not valid.") from None


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


async def update_survey(
    *,
    survey_id: int,
    actor_discord_user_id: int,
    title: str | None = None,
    description: str | None = None,
    close_time_utc: str | None = None,
    reminder_offsets: str | None = None,
    reminder_mention_everyone: bool | None = None,
    close_mention_everyone: bool | None = None,
    allow_response_change: bool | None = None,
    result_visibility: str | None = None,
    now_utc: datetime | None = None,
) -> SurveySnapshot:
    now = now_utc or datetime.now(UTC)
    closes_at = parse_close_time(close_time_utc, now_utc=now) if close_time_utc else None
    if closes_at is not None and closes_at <= now:
        raise VoteValidationError("Updated survey close time must be in the future.")
    offsets = parse_reminder_offsets(reminder_offsets) if reminder_offsets is not None else None
    if offsets is not None:
        close_for_offsets = closes_at
        if close_for_offsets is None:
            current = await survey_dal.get_survey_snapshot(int(survey_id))
            close_for_offsets = current.closes_at_utc if current is not None else None
        if close_for_offsets is not None:
            offsets = tuple(
                offset
                for offset in offsets
                if close_for_offsets.timestamp() - (offset * 60) > now.timestamp()
            )
    clean_title = str(title or "").strip() if title is not None else None
    clean_description = (
        _validate_description(description, blank_as_none=False) if description is not None else None
    )
    if clean_title is not None and not clean_title:
        raise VoteValidationError("Survey title cannot be blank.")
    if clean_title is not None and len(clean_title) > MAX_TITLE_LEN:
        raise VoteValidationError(f"Survey title must be {MAX_TITLE_LEN} characters or fewer.")
    clean_result_visibility: str | None = None
    if result_visibility is not None:
        try:
            clean_result_visibility = normalize_result_visibility(result_visibility)
        except ValueError as exc:
            raise VoteValidationError(str(exc)) from exc
    result = await survey_dal.update_survey_post(
        survey_id=int(survey_id),
        actor_discord_user_id=int(actor_discord_user_id),
        title=clean_title,
        description=clean_description,
        closes_at_utc=closes_at,
        reminder_offsets_minutes=offsets,
        reminder_mention_everyone=reminder_mention_everyone,
        close_mention_everyone=close_mention_everyone,
        allow_response_change=allow_response_change,
        result_visibility=clean_result_visibility,
    )
    if result == "not_open":
        raise VoteValidationError("Survey was not found or is already closed.")
    if result == "has_responses":
        raise VoteValidationError("This survey field cannot be changed after responses exist.")
    if result != "updated":
        raise VoteValidationError("Survey could not be updated.")
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        raise RuntimeError("Survey could not be loaded after update.")
    logger.info("survey_updated survey_id=%s actor_discord_id=%s", survey_id, actor_discord_user_id)
    return snapshot


async def update_survey_option_emoji(
    *,
    survey_id: int,
    option_id: int,
    emoji_value: str | None,
    actor_discord_user_id: int,
) -> SurveySnapshot:
    emoji = parse_option_emoji(emoji_value)
    try:
        snapshot = await survey_dal.update_survey_option_emoji(
            survey_id=int(survey_id),
            option_id=int(option_id),
            emoji=emoji,
            actor_discord_user_id=int(actor_discord_user_id),
        )
    except ValueError as exc:
        raise VoteValidationError(str(exc)) from exc
    logger.info(
        "survey_option_emoji_updated survey_id=%s option_id=%s actor_discord_id=%s cleared=%s",
        survey_id,
        option_id,
        actor_discord_user_id,
        emoji is None,
    )
    return snapshot


async def submit_survey_response(
    *,
    survey_id: int,
    discord_user_id: int,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    rating_answers_by_question_id: Mapping[int, int | str | None] | None = None,
    ranking_answers_by_question_id: Mapping[int, tuple[int, ...] | list[int] | None] | None = None,
    now_utc: datetime | None = None,
) -> tuple[SurveySubmitResult, SurveySnapshot | None]:
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        return (
            SurveySubmitResult("missing", int(survey_id), message="This survey no longer exists."),
            None,
        )
    validated = validate_response_payload(
        snapshot,
        answers_by_question_id=answers_by_question_id,
        text_answers_by_question_id=text_answers_by_question_id,
        detail_text_by_question_option=detail_text_by_question_option,
        rating_answers_by_question_id=rating_answers_by_question_id,
        ranking_answers_by_question_id=ranking_answers_by_question_id,
    )
    result = await survey_dal.submit_survey_response(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
        answers_by_question_id=validated.selected_option_ids,
        text_answers_by_question_id=validated.text_answers,
        detail_text_by_question_option=validated.detail_text_by_option,
        rating_answers_by_question_id=validated.rating_answers,
        ranking_answers_by_question_id=validated.ranking_answers,
        now_utc=now_utc or datetime.now(UTC),
    )
    refreshed = await survey_dal.get_survey_snapshot(int(survey_id)) if result.accepted else None
    return result, refreshed


async def has_submitted_response(*, survey_id: int, discord_user_id: int) -> bool:
    return await survey_dal.has_submitted_response(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
    )


async def get_survey_response_draft(
    *, survey_id: int, discord_user_id: int
) -> SurveyResponseDraft | None:
    return await survey_dal.get_survey_response_draft(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
    )


async def save_survey_response_draft(
    *,
    survey_id: int,
    discord_user_id: int,
    answers_by_question_id: Mapping[int, tuple[int, ...]],
    text_answers_by_question_id: Mapping[int, str] | None = None,
    detail_text_by_question_option: Mapping[tuple[int, int], str] | None = None,
    rating_answers_by_question_id: Mapping[int, int | str | None] | None = None,
    ranking_answers_by_question_id: Mapping[int, tuple[int, ...] | list[int] | None] | None = None,
    expected_revision: int | None = None,
    now_utc: datetime | None = None,
) -> SurveyDraftSaveResult:
    snapshot = await survey_dal.get_survey_snapshot(int(survey_id))
    if snapshot is None:
        return SurveyDraftSaveResult(
            "missing", int(survey_id), message="This survey no longer exists."
        )
    validated = validate_draft_response_payload(
        snapshot,
        answers_by_question_id=answers_by_question_id,
        text_answers_by_question_id=text_answers_by_question_id,
        detail_text_by_question_option=detail_text_by_question_option,
        rating_answers_by_question_id=rating_answers_by_question_id,
        ranking_answers_by_question_id=ranking_answers_by_question_id,
    )
    result = await survey_dal.save_survey_response_draft(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
        payload=validated,
        expected_revision=expected_revision,
        now_utc=now_utc or datetime.now(UTC),
    )
    logger.info(
        "survey_draft_save status=%s survey_id=%s actor_discord_id=%s revision=%s",
        result.status,
        survey_id,
        discord_user_id,
        result.revision,
    )
    return result


async def discard_survey_response_draft(
    *,
    survey_id: int,
    discord_user_id: int,
    expected_revision: int | None = None,
) -> SurveyDraftSaveResult:
    result = await survey_dal.discard_survey_response_draft(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
        expected_revision=expected_revision,
    )
    logger.info(
        "survey_draft_discard status=%s survey_id=%s actor_discord_id=%s",
        result.status,
        survey_id,
        discord_user_id,
    )
    return result


async def get_existing_answer_option_ids(
    *, survey_id: int, discord_user_id: int
) -> dict[int, tuple[int, ...]]:
    return await survey_dal.get_existing_answer_option_ids(
        survey_id=int(survey_id),
        discord_user_id=int(discord_user_id),
    )


async def get_existing_response_payload(
    *, survey_id: int, discord_user_id: int
) -> SurveyResponsePayload:
    return await survey_dal.get_existing_response_payload(
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
