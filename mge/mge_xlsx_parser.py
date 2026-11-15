from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import re
from typing import Any

import pandas as pd

_FILENAME_RX = re.compile(r"^mge_rankings_kd\d{4}_\d{8}\.xlsx$", re.IGNORECASE)
_REQUIRED_COLUMNS = ["Rank", "Player ID", "Player", "Score"]
_TARGET_SHEET = "Overall"
_HEADER_ROW_ZERO_BASED = 2  # Excel row 3


@dataclass(frozen=True)
class ParsedMgeResultRow:
    rank: int
    player_id: int
    player_name: str
    score: int


def validate_results_filename(filename: str) -> None:
    """Validate strict filename format for MGE ranking imports."""
    if not _FILENAME_RX.match((filename or "").strip()):
        raise ValueError("Invalid filename format. Expected: mge_rankings_kd####_YYYYMMDD.xlsx")


def _parse_score(raw: Any) -> int:
    if raw is None:
        raise ValueError("Score is required")
    s = str(raw).strip().replace(",", "")
    if not s:
        raise ValueError("Score is empty")
    return int(float(s))


def parse_mge_results_xlsx(content: bytes, filename: str) -> list[ParsedMgeResultRow]:
    """
    Parse MGE ranking xlsx payload into normalized rows.

    Expected workbook format:
    - First relevant sheet is named 'Overall'
    - Header row is Excel row 3 (0-based index 2)
    - Data starts from row 4
    """
    validate_results_filename(filename)

    try:
        df = pd.read_excel(
            BytesIO(content),
            sheet_name=_TARGET_SHEET,
            header=_HEADER_ROW_ZERO_BASED,
        )
    except ValueError as e:
        msg = str(e).lower()
        if "worksheet" in msg and "not found" in msg:
            raise ValueError("Missing required sheet 'Overall'.") from e
        raise ValueError(f"Unable to read results workbook: {e}") from e

    for c in _REQUIRED_COLUMNS:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")

    rows: list[ParsedMgeResultRow] = []
    for _, r in df.iterrows():
        if pd.isna(r.get("Rank")) and pd.isna(r.get("Player ID")) and pd.isna(r.get("Player")):
            continue

        rank = int(r["Rank"])
        player_id = int(r["Player ID"])
        player_name = str(r["Player"]).strip()
        score = _parse_score(r["Score"])

        if rank <= 0:
            raise ValueError("Rank must be a positive integer.")
        if player_id <= 0:
            raise ValueError("Player ID must be a positive integer.")
        if not player_name:
            raise ValueError("Player name cannot be blank")

        rows.append(
            ParsedMgeResultRow(
                rank=rank,
                player_id=player_id,
                player_name=player_name,
                score=score,
            )
        )

    if not rows:
        raise ValueError("No valid result rows found in Overall sheet.")

    return rows
