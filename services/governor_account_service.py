"""Canonical governor account resolution helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from account_picker import ACCOUNT_ORDER
from registry import registry_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AccountLookup:
    ok: bool
    accounts: dict[str, dict[str, str]]
    error: str | None = None


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

    for slot in ACCOUNT_ORDER:
        if slot in accounts:
            visit(slot, accounts[slot])
    for slot, info in accounts.items():
        if slot not in ACCOUNT_ORDER:
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
    return [slot for slot in ACCOUNT_ORDER if slot not in used]
