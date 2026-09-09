from __future__ import annotations

from typing import Any


def _stable_key(row: dict[str, Any]) -> tuple[str, int]:
    name = str(row.get("GovernorNameSnapshot") or "").strip().lower()
    gid = int(row.get("GovernorId") or 0)
    return (name, gid)


def auto_balance_team_ids(roster_rows: list[dict[str, Any]]) -> tuple[list[int], list[int]]:
    """
    Deterministic even split from roster rows.
    Team1 gets first half, Team2 gets second half.
    For odd size N, Team2 receives ceil(N/2), Team1 floor(N/2).
    """
    active_players: list[dict[str, Any]] = []
    for r in roster_rows or []:
        if (r.get("Status") or "").lower() != "active":
            continue
        if (r.get("SlotType") or "").lower() != "player":
            continue
        if not r.get("GovernorId"):
            continue
        active_players.append(r)

    ordered = sorted(active_players, key=_stable_key)
    ids = [int(r["GovernorId"]) for r in ordered]

    split = len(ids) // 2
    # odd -> extra to team2
    team1 = ids[:split]
    team2 = ids[split:]
    return team1, team2
