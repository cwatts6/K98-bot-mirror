"""Profile-cache lookup helpers for player profile and location commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from profile_cache import search_by_governor_name

ProfileLookupStatus = Literal["found", "matches", "not_found", "missing_query"]


@dataclass(frozen=True, slots=True)
class ProfileLookupResult:
    status: ProfileLookupStatus
    governor_id: int | None = None
    matches: tuple[tuple[str, int, int | float], ...] = ()
    message: str = "No matches found."


def _normalise_matches(
    matches: list[tuple] | tuple[tuple, ...],
) -> tuple[tuple[str, int, int | float], ...]:
    normalised: list[tuple[str, int, int | float]] = []
    for match in matches:
        if not isinstance(match, (list, tuple)) or len(match) < 2:
            continue
        name = str(match[0] or "").strip()
        try:
            governor_id = int(match[1])
        except Exception:
            continue
        score = match[2] if len(match) > 2 else 0
        normalised.append((name, governor_id, score))
    return tuple(normalised)


def resolve_profile_lookup(
    *,
    governor_id: int | None = None,
    governor_name: str | None = None,
    limit: int = 10,
) -> ProfileLookupResult:
    """
    Resolve command input against the player profile cache.

    This intentionally uses `profile_cache.search_by_governor_name()` rather than the
    SQL-backed target-utils name cache because `/player_profile` and `/player_location`
    depend on profile/location cache freshness and disk-fallback semantics.
    """
    if governor_id is not None:
        try:
            parsed_id = int(governor_id)
        except Exception:
            parsed_id = 0
        if parsed_id > 0:
            return ProfileLookupResult(status="found", governor_id=parsed_id, message="")

    if governor_name is None:
        return ProfileLookupResult(
            status="missing_query",
            message="Provide either **governor_id** or pick a name from the list.",
        )

    name = governor_name.strip()
    if name.isdigit():
        return ProfileLookupResult(status="found", governor_id=int(name), message="")

    matches = _normalise_matches(search_by_governor_name(name, limit=limit))
    if not matches:
        return ProfileLookupResult(status="not_found", message="No matches found.")

    if len(matches) == 1:
        return ProfileLookupResult(status="found", governor_id=matches[0][1], message="")

    return ProfileLookupResult(
        status="matches",
        matches=matches,
        message="Multiple matches — pick one:",
    )
