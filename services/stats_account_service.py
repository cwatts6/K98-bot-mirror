"""Canonical account resolution helpers for stats command flows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging

from registry import registry_service
from services import governor_account_service

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
    return governor_account_service.order_accounts(accounts)


def summarize_accounts(accounts: dict[str, dict[str, str]]) -> StatsAccountSummary:
    shared = governor_account_service.summarize_accounts(accounts or {})
    return _from_shared_summary(shared)


def _from_shared_summary(
    shared: governor_account_service.AccountResolutionSummary,
) -> StatsAccountSummary:
    return StatsAccountSummary(
        ok=shared.ok,
        accounts=shared.accounts,
        ordered_accounts=shared.ordered_accounts,
        governor_ids=list(shared.governor_ids),
        account_names=list(shared.account_names),
        name_to_id=dict(shared.name_to_id),
        default_choice=shared.default_choice,
        error=shared.error,
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
