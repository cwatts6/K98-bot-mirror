"""Canonical governor account resolution helpers."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
import re
from typing import Any

from registry import registry_service
from registry.account_slots import ACCOUNT_ORDER as _ACCOUNT_ORDER

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AccountLookup:
    ok: bool
    accounts: dict[str, dict[str, str]]
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedAccount:
    slot: str
    governor_id: int
    governor_id_str: str
    governor_name: str
    raw: dict[str, str]


@dataclass(frozen=True, slots=True)
class AccountResolutionSummary:
    ok: bool
    accounts: dict[str, dict[str, str]]
    ordered_accounts: dict[str, dict[str, str]]
    resolved_accounts: tuple[ResolvedAccount, ...]
    governor_ids: tuple[int, ...]
    governor_id_strings: tuple[str, ...]
    account_names: tuple[str, ...]
    name_to_id: dict[str, int]
    default_choice: str
    error: str | None = None

    @property
    def has_accounts(self) -> bool:
        return bool(self.governor_ids)

    @property
    def classification(self) -> tuple[str, str | None]:
        if not self.governor_id_strings:
            return "none", None
        if len(self.governor_id_strings) == 1:
            return "single", self.governor_id_strings[0]
        return "multi", None

    @property
    def first_account(self) -> ResolvedAccount | None:
        return self.resolved_accounts[0] if self.resolved_accounts else None

    def contains_governor_id(self, governor_id: str | int) -> bool:
        gid = _normalize_governor_id_str(governor_id)
        return bool(gid and gid in self.governor_id_strings)

    def free_slots(self) -> list[str]:
        return free_account_slots(self.accounts)


def _normalize_governor_id_str(value: Any) -> str:
    try:
        gid = int(str(value).strip())
    except (TypeError, ValueError):
        return ""
    return str(gid) if gid > 0 else ""


def _governor_name(info: dict[str, Any], fallback: str = "Unknown") -> str:
    name = str(info.get("GovernorName") or info.get("governor_name") or "").strip()
    return name or fallback


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


def order_accounts(accounts: dict[str, dict[str, Any]]) -> dict[str, dict[str, str]]:
    ordered: dict[str, dict[str, str]] = {}
    source = accounts or {}
    for slot in _ACCOUNT_ORDER:
        if slot in source:
            ordered[slot] = dict(source[slot] or {})
    for slot in sorted(source):
        if slot not in ordered:
            ordered[slot] = dict(source[slot] or {})
    return ordered


def summarize_accounts(
    accounts: dict[str, dict[str, Any]],
    *,
    ok: bool = True,
    error: str | None = None,
) -> AccountResolutionSummary:
    ordered_accounts = order_accounts(accounts or {})
    resolved: list[ResolvedAccount] = []
    governor_ids: list[int] = []
    governor_id_strings: list[str] = []
    account_names: list[str] = []
    name_to_id: dict[str, int] = {}

    for slot, info in ordered_accounts.items():
        gid_str = _normalize_governor_id_str(
            info.get("GovernorID") or info.get("GovernorId") or info.get("governor_id")
        )
        if not gid_str:
            continue
        gid = int(gid_str)
        name = _governor_name(info)
        resolved.append(
            ResolvedAccount(
                slot=str(slot),
                governor_id=gid,
                governor_id_str=gid_str,
                governor_name=name,
                raw=dict(info),
            )
        )
        if gid not in governor_ids:
            governor_ids.append(gid)
            governor_id_strings.append(gid_str)
        if name and name != "Unknown" and name not in name_to_id:
            account_names.append(name)
            name_to_id[name] = gid
        elif name and name_to_id.get(name) not in (None, gid):
            logger.warning(
                "account_resolution_summary: name %r maps to multiple GovernorIDs (%s, %s); first wins",
                name,
                name_to_id[name],
                gid,
            )

    default_choice = "ALL"
    main = ordered_accounts.get("Main") or {}
    main_gid = _normalize_governor_id_str(
        main.get("GovernorID") or main.get("GovernorId") or main.get("governor_id")
    )
    main_name = _governor_name(main, fallback="") if main_gid else ""
    if main_name and main_name in name_to_id:
        default_choice = main_name
    elif account_names:
        default_choice = account_names[0]

    return AccountResolutionSummary(
        ok=ok,
        accounts=dict(accounts or {}),
        ordered_accounts=ordered_accounts,
        resolved_accounts=tuple(resolved),
        governor_ids=tuple(governor_ids),
        governor_id_strings=tuple(governor_id_strings),
        account_names=tuple(account_names),
        name_to_id=name_to_id,
        default_choice=default_choice,
        error=error,
    )


async def get_account_summary_for_user(discord_user_id: int) -> AccountResolutionSummary:
    try:
        accounts = await asyncio.to_thread(registry_service.get_user_accounts, int(discord_user_id))
    except Exception as exc:
        logger.exception("governor_account_summary_failed discord_user_id=%s", discord_user_id)
        return summarize_accounts({}, ok=False, error=f"{type(exc).__name__}: {exc}")
    return summarize_accounts(dict(accounts or {}))


def get_account_summary_for_user_sync(discord_user_id: int) -> AccountResolutionSummary:
    try:
        accounts = registry_service.get_user_accounts(int(discord_user_id))
    except Exception as exc:
        logger.exception("governor_account_summary_failed discord_user_id=%s", discord_user_id)
        return summarize_accounts({}, ok=False, error=f"{type(exc).__name__}: {exc}")
    return summarize_accounts(dict(accounts or {}))


async def get_accounts_for_user(discord_user_id: int) -> AccountLookup:
    summary = await get_account_summary_for_user(discord_user_id)
    return AccountLookup(summary.ok, summary.accounts, summary.error)


def classify_accounts(accounts: dict[str, dict[str, str]]) -> tuple[str, str | None]:
    """Return ('none'|'single'|'multi', governor_id_if_single)."""
    return summarize_accounts(accounts).classification


async def resolve_governor_label(discord_user_id: int, governor_id: str) -> str:
    summary = await get_account_summary_for_user(discord_user_id)
    gid = str(governor_id)
    if not summary.ok:
        return f"Governor {gid}"
    for account in summary.resolved_accounts:
        if account.governor_id_str == gid:
            name = account.governor_name
            return f"{name} ({gid})" if name and name != "Unknown" else f"Governor {gid}"
    return f"Governor {gid}"


def free_account_slots(accounts: dict[str, dict[str, str]]) -> list[str]:
    used = set(accounts.keys())
    return [slot for slot in _ACCOUNT_ORDER if slot not in used]
