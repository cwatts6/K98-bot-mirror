"""Service layer for KVK reporting block assembly."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

REPORTING_BLOCK_KEYS: tuple[str, ...] = (
    "players_by_kills",
    "players_by_deads",
    "players_by_dkp",
    "kingdoms_by_kills",
    "kingdoms_by_deads",
    "kingdoms_by_dkp",
    "camps_by_kills",
    "camps_by_deads",
    "camps_by_dkp",
    "our_top_players",
    "our_kingdom",
    "our_camp",
)

CONTRIBUTION_FIELDS: tuple[str, ...] = ("acclaim_gain",)


def load_allkingdom_report_v2(kvk_no, *, connect, period_id, our_kingdom=None, publication_id=None):
    """Explicit V2 entry point; preserve its metadata and nullable metric states."""
    from kvk.services.new_source_reporting_service import load_report_v2

    return load_report_v2(
        connect=connect,
        kvk_no=kvk_no,
        period_id=period_id,
        our_kingdom=_resolve_our_kingdom(our_kingdom),
        publication_id=publication_id,
    )


def _resolve_our_kingdom(our_kingdom: int | None) -> int:
    if our_kingdom is not None:
        return int(our_kingdom)

    from constants import OUR_KINGDOM

    return int(OUR_KINGDOM)


def _normalise_row(row: dict[str, Any]) -> dict[str, Any]:
    shaped = dict(row)
    for field in CONTRIBUTION_FIELDS:
        shaped.setdefault(field, 0)
    return shaped


def _normalise_blocks(
    raw_blocks: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    blocks: dict[str, list[dict[str, Any]]] = {}
    for key in REPORTING_BLOCK_KEYS:
        blocks[key] = [_normalise_row(row) for row in raw_blocks.get(key, [])]
    return blocks


def load_allkingdom_reporting_blocks(
    kvk_no: int,
    *,
    our_kingdom: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Return structured KVK all-kingdom reporting blocks.

    Acclaim gain is included in each row for downstream structured use,
    but the Discord embed phase intentionally does not render it.
    """
    resolved_kingdom = _resolve_our_kingdom(our_kingdom)
    from kvk.services.source_routing_service import load_public_report

    blocks = load_public_report(kvk_no, our_kingdom=resolved_kingdom)
    logger.info(
        "[KVK REPORTING] assembled blocks kvk_no=%s players=%d kingdoms=%d camps=%d",
        kvk_no,
        len(blocks.get("blocks", blocks).get("players_by_kills", [])),
        len(blocks.get("blocks", blocks).get("kingdoms_by_kills", [])),
        len(blocks.get("blocks", blocks).get("camps_by_kills", [])),
    )
    return blocks
