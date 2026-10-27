"""Finite restoration accounting independent of Discord and storage adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)
OutcomeState = Literal["attached", "pruned", "superseded", "failed", "outcome_unconfirmed"]


@dataclass(frozen=True)
class EntryOutcome:
    state: OutcomeState
    reason: str = ""


async def restore_tracked_views(
    load: Callable[[], Awaitable[dict[str, Any]]],
    restore: Callable[[str, Any], Awaitable[EntryOutcome]],
    *,
    pause: float = 0.06,
    summary: dict | None = None,
) -> dict:
    result = summary if summary is not None else {}
    result.update(
        entries_total=None,
        tracker_state="unavailable",
        restoration_status="unavailable",
        rehydrated=0,
        attached=0,
        pruned=0,
        superseded=0,
        failed=0,
        outcome_unconfirmed=0,
        unattempted=0,
        reasons={},
    )
    active = False
    try:
        try:
            entries = await load()
        except Exception as exc:
            result["tracker_error"] = type(exc).__name__
            logger.warning("[VIEW] Tracker unavailable error_type=%s", type(exc).__name__)
            return result
        result.update(
            entries_total=len(entries),
            unattempted=len(entries),
            tracker_state="loaded" if entries else "empty",
            restoration_status="partial",
        )
        for key, entry in entries.items():
            active = True
            try:
                outcome = await restore(key, entry)
            except Exception as exc:
                outcome = EntryOutcome("failed", type(exc).__name__)
            result[outcome.state] += 1
            result["unattempted"] -= 1
            active = False
            if outcome.reason:
                reasons = result["reasons"]
                # Bounded aggregate reason labels; never retain raw payloads or exceptions.
                reason = (
                    outcome.reason if outcome.reason in reasons or len(reasons) < 16 else "other"
                )
                reasons[reason] = reasons.get(reason, 0) + 1
            logger.info(
                "[VIEW] restoration_entry key=%s state=%s reason=%s",
                key,
                outcome.state,
                outcome.reason,
            )
            if pause:
                await asyncio.sleep(pause)
        if not (result["failed"] or result["outcome_unconfirmed"] or result["unattempted"]):
            result["restoration_status"] = "complete"
        return result
    except asyncio.CancelledError:
        if active:
            result["unattempted"] -= 1
            result["outcome_unconfirmed"] += 1
        result["restoration_status"] = "cancelled"
        raise
    finally:
        result["rehydrated"] = result["attached"]
        logger.info("[VIEW] rehydration_summary %s", result)


async def restoration_completion(result):
    """Task completion is separate from complete feature restoration."""
    return dict(result)
