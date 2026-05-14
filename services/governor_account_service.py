"""Canonical governor account resolution helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import re

from registry import registry_service
from registry.account_slots import ACCOUNT_ORDER as _ACCOUNT_ORDER

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AccountLookup:
    ok: bool
    accounts: dict[str, dict[str, str]]
    error: str | None = None


def parse_discord_user_id(text: str | int | None) -> int | None:
    """Extract a Discord user id from raw text or a mention-like value."""
    if text is None:
        return None
    try:
        match = re.search(r"(?<!\d)\d{15,22}(?!\d)", str(text))
        return int(match.group(0)) if match else None
    except Exception:
        return None


def all_account_slots() -> list[str]:
    """Return the canonical account slots in display/autocomplete order."""
    return list(_ACCOUNT_ORDER)


def filter_account_slots(prefix: str | None = None, *, limit: int = 25) -> list[str]:
    """Return canonical account slots filtered by an optional autocomplete prefix."""
    value = (prefix or "").strip().casefold()
    slots = all_account_slots()
    if value:
        slots = [slot for slot in slots if slot.casefold().startswith(value)]
    return slots[:limit]


def registered_account_slots(
    accounts: dict[str, dict[str, str]], prefix: str | None = None, *, limit: int = 25
) -> list[str]:
    """Return registered slots in canonical order, preserving unknown slots after known ones."""
    if not accounts:
        return []
    ordered = [slot for slot in _ACCOUNT_ORDER if slot in accounts]
    ordered.extend(slot for slot in sorted(accounts) if slot not in set(ordered))
    value = (prefix or "").strip().casefold()
    if value:
        ordered = [slot for slot in ordered if slot.casefold().startswith(value)]
    return ordered[:limit]


async def get_accounts_for_user(discord_user_id: int) -> AccountLookup:
    try:
        accounts = await asyncio.to_thread(registry_service.get_user_accounts, int(discord_user_id))
    except Exception as exc:
        logger.exception("governor_account_lookup_failed discord_user_id=%s", discord_user_id)
        return AccountLookup(False, {}, f"{type(exc).__name__}: {exc}")
    return AccountLookup(True, dict(accounts or {}), None)


def classify_accounts(accounts: dict[str, dict[str, str]]) -> tuple[str, str | None]:
    """Return ('none'|'single'|'multi', governor_id_if_single)."""
    seen: list[str] = []

    def visit(slot: str, info: dict[str, str]) -> None:
        if not isinstance(info, dict):
            return
        gid = str(info.get("GovernorID") or info.get("GovernorId") or "").strip()
        if gid and gid not in seen:
            seen.append(gid)

    for slot in _ACCOUNT_ORDER:
        if slot in accounts:
            visit(slot, accounts[slot])
    for slot, info in accounts.items():
        if slot not in _ACCOUNT_ORDER:
            visit(slot, info)

    if not seen:
        return "none", None
    if len(seen) == 1:
        return "single", seen[0]
    return "multi", None


async def resolve_governor_label(discord_user_id: int, governor_id: str) -> str:
    lookup = await get_accounts_for_user(discord_user_id)
    gid = str(governor_id)
    if not lookup.ok:
        return f"Governor {gid}"
    for info in lookup.accounts.values():
        rec_gid = str(info.get("GovernorID") or info.get("governor_id") or "").strip()
        if rec_gid == gid:
            name = str(info.get("GovernorName") or info.get("governor_name") or "").strip()
            return f"{name} ({gid})" if name else f"Governor {gid}"
    return f"Governor {gid}"


def free_account_slots(accounts: dict[str, dict[str, str]]) -> list[str]:
    used = set(accounts.keys())
    return [slot for slot in _ACCOUNT_ORDER if slot not in used]
