"""Discord-free governor lookup helpers for Ark admin add flows."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from typing import Any, Literal

from target_utils import (
    get_name_cache_rows,
    get_name_cache_status,
    lookup_governor_id,
    refresh_name_cache_from_sql,
    sync_refresh_worker,
)

logger = logging.getLogger(__name__)

LookupStatus = Literal["found", "matches", "not_found"]


@dataclass(frozen=True, slots=True)
class ArkAdminGovernorLookupResult:
    status: LookupStatus
    query: str
    governor_id: str | None = None
    governor_name: str | None = None
    matches: tuple[dict[str, str], ...] = ()
    message: str = "No matches found."


def _normalise_match(row: dict[str, Any]) -> dict[str, str]:
    return {
        "GovernorName": str(row.get("GovernorName") or "").strip(),
        "GovernorID": str(row.get("GovernorID") or "").strip(),
    }


async def ensure_name_cache_ready() -> None:
    """
    Ensure the SQL-backed name cache is populated in this process.

    The normal refresh helper may offload work, so keep the established same-process
    fallback for admin lookup paths that immediately inspect the cache rows.
    """
    try:
        status = get_name_cache_status()
        if status.get("rows_count", 0) > 0:
            return

        await refresh_name_cache_from_sql()

        status = get_name_cache_status()
        if status.get("rows_count", 0) == 0:
            await asyncio.to_thread(sync_refresh_worker)
    except Exception:
        logger.exception("[ARK] Failed ensuring name cache is ready")


def find_partial_governor_id_matches(query: str, limit: int = 25) -> list[dict[str, str]]:
    q = (query or "").strip()
    if not q:
        return []

    matches: list[dict[str, str]] = []
    for row in get_name_cache_rows():
        gid = str(row.get("GovernorID") or "").strip()
        if not gid or q not in gid:
            continue
        matches.append(_normalise_match(row))
        if len(matches) >= limit:
            break
    return matches


def find_substring_name_matches(query: str, limit: int = 25) -> list[dict[str, str]]:
    q = (query or "").strip().lower()
    if not q:
        return []

    matches: list[dict[str, str]] = []
    for row in get_name_cache_rows():
        name = str(row.get("GovernorName") or "").strip()
        if not name or q not in name.lower():
            continue
        matches.append(_normalise_match(row))
        if len(matches) >= limit:
            break
    return matches


async def resolve_admin_governor_query(raw_query: str) -> ArkAdminGovernorLookupResult:
    query = (raw_query or "").strip()
    if not query:
        return ArkAdminGovernorLookupResult(
            status="not_found",
            query=query,
            message="Name is required.",
        )

    if query.isdigit():
        await ensure_name_cache_ready()
        for row in get_name_cache_rows():
            if str(row.get("GovernorID") or "").strip() == query:
                match = _normalise_match(row)
                if match["GovernorName"]:
                    return ArkAdminGovernorLookupResult(
                        status="found",
                        query=query,
                        governor_id=match["GovernorID"],
                        governor_name=match["GovernorName"],
                    )

        matches = find_partial_governor_id_matches(query)
        if matches:
            return ArkAdminGovernorLookupResult(
                status="matches",
                query=query,
                matches=tuple(matches),
            )

        return ArkAdminGovernorLookupResult(
            status="not_found",
            query=query,
            message="❌ GovernorID not found in name cache. Please verify the ID.",
        )

    result = await lookup_governor_id(query)
    status = (result or {}).get("status")

    if status == "not_found":
        await ensure_name_cache_ready()
        result = await lookup_governor_id(query)
        status = (result or {}).get("status")

    if status == "not_found":
        matches = find_substring_name_matches(query)
        if matches:
            return ArkAdminGovernorLookupResult(
                status="matches",
                query=query,
                matches=tuple(matches),
            )

    if status == "found":
        data = result.get("data") or {}
        return ArkAdminGovernorLookupResult(
            status="found",
            query=query,
            governor_id=str(data.get("GovernorID") or ""),
            governor_name=str(data.get("GovernorName") or "Unknown"),
        )

    if status == "fuzzy_matches":
        matches = tuple(_normalise_match(m) for m in (result.get("matches") or []))
        if not matches:
            matches = tuple(find_substring_name_matches(query))
        if matches:
            return ArkAdminGovernorLookupResult(
                status="matches",
                query=query,
                matches=matches,
            )

        return ArkAdminGovernorLookupResult(
            status="not_found",
            query=query,
            message="No matches found.",
        )

    return ArkAdminGovernorLookupResult(
        status="not_found",
        query=query,
        message=(result or {}).get("message", "No matches found."),
    )
