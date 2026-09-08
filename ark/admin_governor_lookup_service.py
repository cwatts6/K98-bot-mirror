"""Ark admin add governor lookup adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from services.governor_lookup_service import (
    ensure_name_cache_ready,
    find_partial_governor_id_matches,
    find_substring_name_matches,
    get_name_cache_rows,
    lookup_governor_id,
    resolve_governor_query,
)

LookupStatus = Literal["found", "matches", "not_found"]


@dataclass(frozen=True, slots=True)
class ArkAdminGovernorLookupResult:
    status: LookupStatus
    query: str
    governor_id: str | None = None
    governor_name: str | None = None
    matches: tuple[dict[str, str], ...] = ()
    message: str = "No matches found."


async def resolve_admin_governor_query(raw_query: str) -> ArkAdminGovernorLookupResult:
    result = await resolve_governor_query(raw_query)
    return ArkAdminGovernorLookupResult(
        status=result.status,
        query=result.query,
        governor_id=result.governor_id,
        governor_name=result.governor_name,
        matches=result.matches,
        message=result.message,
    )


__all__ = [
    "ArkAdminGovernorLookupResult",
    "ensure_name_cache_ready",
    "find_partial_governor_id_matches",
    "find_substring_name_matches",
    "get_name_cache_rows",
    "lookup_governor_id",
    "resolve_admin_governor_query",
]
