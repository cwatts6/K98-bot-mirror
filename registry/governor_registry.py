# governor_registry.py
"""
Governor registry façade.

Persistence and business logic are now owned by:
  registry_dal.py     — SQL data access layer
  registry_service.py — validation, duplicate rules, orchestration

This module is retained for:
  1. Backward-compatible load_registry() signature called throughout the codebase.
  2. register_account() called by registry UI confirmation views.
  3. get_discord_name_for_governor() called by stats/embed helpers.
  4. get_user_main_governor_id / get_user_main_governor_name dict-based helpers.
  5. Backward-compatible lazy re-exports for moved registry UI View classes.

KVKStatsView and KVKAccountButton have been moved to ui/views/stats_views.py.
RegisterGovernorView, ModifyGovernorView, and ConfirmRemoveView live in ui/views/registry_views.py.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Backward-compat persistence façade
# ---------------------------------------------------------------------------


def load_registry() -> dict:
    """
    Return current Active registrations as the legacy dict format.
    Reads from SQL via registry_service.load_registry_as_dict().

    Returns {} on SQL failure after logging at ERROR level.
    Commands that present registry data to users must treat an empty
    result from this function as a possible SQL failure, not as
    "no registrations exist", and should guard accordingly.

    Commands that already wrap load_registry() in try/except
    (e.g. my_registrations) are unaffected.
    Commands that use the result for safety guards
    (e.g. duplicate pre-checks before a write) are safe — the
    stored procedure enforces constraints regardless.
    Commands that present registry data as their primary output
    (registration_audit, bulk_export_registrations) must wrap
    this call in try/except and fail explicitly.
    """
    try:
        from registry.registry_service import load_registry_as_dict

        return load_registry_as_dict(use_cache=True, allow_stale_on_error=True)
    except Exception:
        logger.exception(
            "[governor_registry] load_registry FAILED — SQL unavailable or query error. "
            "Commands relying on registry read data will behave as if registry is empty."
        )
        return {}


# ---------------------------------------------------------------------------
# register_account — used by registry UI confirmation views
# ---------------------------------------------------------------------------


def register_account(
    discord_id: str,
    discord_name: str,
    account_type: str,
    governor_id: str,
    governor_name: str,
    *,
    created_by: int | None = None,
    provenance: str = "bot_command",
) -> tuple[bool, str | None]:
    """
    Register or update a governor account slot.

    Routes to registry_service.register_governor().
    If the slot already exists, automatically calls modify_governor()
    so that register and modify confirmation views can share
    this single entry point without worrying about which SP to call.
    """
    from registry.registry_service import (
        modify_governor,
        register_governor,
    )

    uid = int(discord_id)

    # Check if the slot is already active for this user (→ modify path)
    from registry.dal import registry_dal

    existing_rows = registry_dal.get_by_discord_id(uid)
    slot_exists = any(r.get("AccountType") == account_type for r in existing_rows)

    if slot_exists:
        ok, err = modify_governor(
            discord_user_id=uid,
            discord_name=discord_name,
            account_type=account_type,
            new_governor_id=governor_id,
            new_governor_name=governor_name,
            updated_by=created_by,
        )
    else:
        ok, err = register_governor(
            discord_user_id=uid,
            discord_name=discord_name,
            account_type=account_type,
            governor_id=governor_id,
            governor_name=governor_name,
            created_by=created_by,
            provenance=provenance,
        )

    return ok, err


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------


def get_discord_name_for_governor(governor_id: str) -> str | None:
    """Return the registered Discord display name for a GovernorID, or None."""
    from registry.registry_service import get_discord_user_for_governor

    info = get_discord_user_for_governor(governor_id)
    if not info:
        return None
    return info.get("DiscordName") or None


def get_user_main_governor_id(registry: dict, user_id: str | int) -> str | None:
    """
    Return the GovernorID string for the user's Main slot.

    Accepts the legacy registry dict for backward compat, but also
    falls back to a direct SQL lookup if the slot isn't in the dict
    (e.g. stale caller that built the dict before a recent write).
    """
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if rec:
        main = (rec.get("accounts") or {}).get("Main")
        gid = (main or {}).get("GovernorID")
        if gid:
            return str(gid)
    # Fallback: live SQL lookup
    from registry.registry_service import get_user_main_governor_id as svc_main

    return svc_main(int(user_id))


def get_user_main_governor_name(registry: dict, user_id: str | int) -> str | None:
    """
    Return the GovernorName string for the user's Main slot.

    Accepts the legacy registry dict for backward compat with a live SQL fallback.
    """
    rec = registry.get(str(user_id)) or registry.get(user_id)
    if rec:
        main = (rec.get("accounts") or {}).get("Main")
        name = (main or {}).get("GovernorName")
        if name:
            return str(name)
    from registry.registry_service import get_user_main_governor_name as svc_name

    return svc_name(int(user_id))


_MOVED_VIEW_NAMES = {
    "RegisterGovernorView",
    "ModifyGovernorView",
    "ConfirmRemoveView",
}


def __getattr__(name: str):
    if name in _MOVED_VIEW_NAMES:
        from ui.views import registry_views

        return getattr(registry_views, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ConfirmRemoveView",  # noqa: F822 - provided lazily by __getattr__
    "ModifyGovernorView",  # noqa: F822 - provided lazily by __getattr__
    "RegisterGovernorView",  # noqa: F822 - provided lazily by __getattr__
    "get_discord_name_for_governor",
    "get_user_main_governor_id",
    "get_user_main_governor_name",
    "load_registry",
    "register_account",
]
