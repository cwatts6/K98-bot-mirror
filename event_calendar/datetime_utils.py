from __future__ import annotations

from datetime import UTC, datetime

from utils import parse_isoformat_utc


def parse_iso_utc_nullable(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parse_isoformat_utc(value)
    except Exception:
        return None


def now_utc() -> datetime:
    return datetime.now(UTC)
