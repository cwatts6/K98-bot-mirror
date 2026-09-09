"""Service layer for KVK reporting block assembly."""

from __future__ import annotations

import logging
from typing import Any

from kvk.dal import kvk_reporting_dal

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
    raw_blocks = kvk_reporting_dal.fetch_allkingdom_reporting_rows(
        int(kvk_no),
        resolved_kingdom,
    )
    blocks = _normalise_blocks(raw_blocks)
    logger.info(
        "[KVK REPORTING] assembled blocks kvk_no=%s players=%d kingdoms=%d camps=%d",
        kvk_no,
        len(blocks["players_by_kills"]),
        len(blocks["kingdoms_by_kills"]),
        len(blocks["camps_by_kills"]),
    )
    return blocks
