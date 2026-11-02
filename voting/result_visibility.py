from __future__ import annotations

from datetime import datetime
from typing import Any

RESULT_VISIBILITY_PUBLIC_LIVE = "PublicLive"
RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE = "HiddenUntilClose"
RESULT_VISIBILITY_VALUES = {
    RESULT_VISIBILITY_PUBLIC_LIVE,
    RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE,
}


def normalize_result_visibility(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return RESULT_VISIBILITY_PUBLIC_LIVE
    by_casefold = {item.casefold(): item for item in RESULT_VISIBILITY_VALUES}
    normalized = by_casefold.get(text.casefold())
    if normalized is None:
        raise ValueError("Choose a valid result visibility mode.")
    return normalized


def public_results_hidden(snapshot: Any, *, now_utc: datetime | None = None) -> bool:
    del now_utc
    return (
        normalize_result_visibility(getattr(snapshot, "result_visibility", None))
        == RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE
        and str(getattr(snapshot, "status", "")) == "Open"
        and getattr(snapshot, "closed_at_utc", None) is None
    )


def result_visibility_label(value: str | None) -> str:
    normalized = normalize_result_visibility(value)
    if normalized == RESULT_VISIBILITY_HIDDEN_UNTIL_CLOSE:
        return "Hidden until close"
    return "Public live"
