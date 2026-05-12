"""Canonical account resolution helpers for stats command flows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from registry import registry_service
from registry.account_slots import ACCOUNT_ORDER

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StatsAccountSummary:
    ok: bool
    accounts: dict[str, dict[str, str]]
    ordered_accounts: dict[str, dict[str, str]]
    governor_ids: list[int]
    account_names: list[str]
    name_to_id: dict[str, int]
    default_choice: str
    error: str | None = None

    @property
    def has_accounts(self) -> bool:
        return bool(self.governor_ids)


def order_accounts(accounts: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    ordered: dict[str, dict[str, str]] = {}
    for slot in ACCOUNT_ORDER:
        if slot in accounts:
            ordered[slot] = dict(accounts[slot] or {})
    for slot in sorted(accounts):
        if slot not in ordered:
            ordered[slot] = dict(accounts[slot] or {})
    return ordered


def summarize_accounts(accounts: dict[str, dict[str, str]]) -> StatsAccountSummary:
    ordered_accounts = order_accounts(accounts or {})
    governor_ids: list[int] = []
    account_names: list[str] = []
    name_to_id: dict[str, int] = {}

    for info in ordered_accounts.values():
        try:
            gid = int(str(info.get("GovernorID") or info.get("GovernorId") or "").strip())
        except (TypeError, ValueError):
            continue
        if gid <= 0:
            continue
        if gid not in governor_ids:
            governor_ids.append(gid)
        name = str(info.get("GovernorName") or info.get("governor_name") or "").strip()
        if name:
            account_names.append(name)
            name_to_id[name] = gid

    default_choice = "ALL"
    main = ordered_accounts.get("Main") or {}
    main_name = str(main.get("GovernorName") or "").strip()
    if main_name and main_name in name_to_id:
        default_choice = main_name
    elif account_names:
        default_choice = account_names[0]

    return StatsAccountSummary(
        ok=True,
        accounts=dict(accounts or {}),
        ordered_accounts=ordered_accounts,
        governor_ids=governor_ids,
        account_names=account_names,
        name_to_id=name_to_id,
        default_choice=default_choice,
    )


async def get_account_summary_for_user(discord_user_id: int) -> StatsAccountSummary:
    """Load and normalize registered stats accounts for one Discord user."""
    try:
        accounts = await asyncio.to_thread(registry_service.get_user_accounts, int(discord_user_id))
    except Exception as exc:
        logger.exception("stats_account_lookup_failed discord_user_id=%s", discord_user_id)
        return StatsAccountSummary(
            ok=False,
            accounts={},
            ordered_accounts={},
            governor_ids=[],
            account_names=[],
            name_to_id={},
            default_choice="ALL",
            error=f"{type(exc).__name__}: {exc}",
        )
    return summarize_accounts(dict(accounts or {}))
