import logging
from datetime import datetime, timedelta

from utils import utcnow

logger = logging.getLogger(__name__)


def period_cutoff(period: str) -> datetime:
    """Return UTC datetime cutoff for the given period string ('24h', '7d', '30d')."""
    now = utcnow()
    if period == "24h":
        return now - timedelta(days=1)
    if period == "7d":
        return now - timedelta(days=7)
    return now - timedelta(days=30)


def fmt_rate(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.0%"
    return f"{(numer / denom) * 100:.1f}%"
