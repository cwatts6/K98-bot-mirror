"""Compatibility wrapper for KVK all-kingdom reporting blocks."""

from __future__ import annotations

from typing import Any

from kvk.services.kvk_reporting_service import load_allkingdom_reporting_blocks


def load_allkingdom_blocks(kvk_no: int) -> dict[str, list[dict[str, Any]]]:
    return load_allkingdom_reporting_blocks(kvk_no)
