"""Compose one invocation's main/last-KVK work without replacing SQL authority.

The context follows draining threads. It is never shared across independent
requests, and entered last-KVK work is never replayed, even when it returns None.
"""

from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4

from services.cache_outcomes import PROCESS_ID

_composition = ContextVar("player_stats_composition", default=None)
_report_lock = Lock()
_latest = {}


@dataclass
class StatsComposition:
    invocation_id: str = field(default_factory=lambda: uuid4().hex)
    last_entered: bool = False
    last_state: str = "not_entered"
    last_output: object = None
    main_output: object = None
    main_error: Exception | None = None


def record_composition(owner):
    global _latest
    main = owner.main_output if isinstance(owner.main_output, dict) else {}
    last = owner.last_output if isinstance(owner.last_output, dict) else {}
    main_meta, last_meta = main.get("_meta") or {}, last.get("_meta") or {}
    with _report_lock:
        _latest = {
            "process_id": PROCESS_ID,
            "invocation_id": owner.invocation_id,
            "last_execution": owner.last_state,
            "last_entered": owner.last_entered,
            "last_count": last_meta.get("count"),
            "last_kvk_no": last_meta.get("kvk_no"),
            "main_source": main_meta.get("source_refresh_status"),
            "main_count": main_meta.get("count"),
            "sql_execution_receipt": False,
        }


def report():
    with _report_lock:
        return deepcopy(_latest)


def observe_last(builder):
    owner = _composition.get()
    if owner is None:
        return builder()
    if owner.last_entered:
        return owner.last_output
    owner.last_entered, owner.last_state = True, "running"
    record_composition(owner)
    try:
        output = builder()
        owner.last_output = output
        owner.last_state = "succeeded" if output is not None else "outcome_unconfirmed"
        record_composition(owner)
        return output
    except BaseException:
        owner.last_state = "outcome_unconfirmed"
        record_composition(owner)
        raise


async def compose(main, last):
    owner = StatsComposition()
    token = _composition.set(owner)
    record_composition(owner)
    try:
        try:
            owner.main_output = await main()
        except Exception as exc:
            owner.main_error = exc
        if not owner.last_entered:
            # Independent read remains eligible only before any last-KVK entry.
            try:
                await last()
            except Exception:
                owner.last_state = "outcome_unconfirmed"
        record_composition(owner)
        return owner
    finally:
        _composition.reset(token)


async def build_startup():
    from player_stats_cache import build_lastkvk_player_stats_cache, build_player_stats_cache

    return await compose(build_player_stats_cache, build_lastkvk_player_stats_cache)


async def verify_startup(owner):
    from services.player_stats_startup import verify_completion

    if owner.main_error is not None:
        raise owner.main_error
    summary = await verify_completion(owner.main_output)
    last_verification = "unavailable"
    if owner.last_state == "succeeded":
        from services.legacy_export_snapshot_service import drain_thread

        last_verification = await drain_thread(_verify_last, owner.last_output)
    summary.update(
        invocation_id=owner.invocation_id,
        last_kvk_state=owner.last_state,
        last_kvk_entered=owner.last_entered,
        last_kvk_verification=last_verification,
    )
    return summary


def _verify_last(output):
    import json

    from player_stats_cache import _last_kvk_cache_path

    try:
        with open(_last_kvk_cache_path(), "rb") as source:
            raw = source.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024 or json.loads(raw) != output:
            return "readback_differs"
        return "original_snapshot"
    except (OSError, ValueError):
        return "unavailable"
