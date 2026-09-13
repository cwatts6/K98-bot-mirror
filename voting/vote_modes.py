from __future__ import annotations

from typing import Any

VOTE_MODE_ONE_CHOICE = "OneChoice"
VOTE_MODE_MULTI_SELECT = "MultiSelect"
VOTE_MODE_VALUES = {
    VOTE_MODE_ONE_CHOICE,
    VOTE_MODE_MULTI_SELECT,
}


def normalize_vote_mode(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return VOTE_MODE_ONE_CHOICE
    by_casefold = {item.casefold(): item for item in VOTE_MODE_VALUES}
    normalized = by_casefold.get(text.casefold())
    if normalized is None:
        raise ValueError("Choose a valid vote mode.")
    return normalized


def is_multi_select(value: Any) -> bool:
    return normalize_vote_mode(str(value or "")) == VOTE_MODE_MULTI_SELECT


def vote_mode_label(value: str | None) -> str:
    normalized = normalize_vote_mode(value)
    if normalized == VOTE_MODE_MULTI_SELECT:
        return "Multi-select"
    return "One choice"
