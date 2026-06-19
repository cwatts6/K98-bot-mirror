from __future__ import annotations

from dataclasses import dataclass
import io

from kvk.models.kvk_rankings import RankingPayload
from kvk.rendering.kvk_rankings_csv import (
    build_current_rankings_csv_bytes,
    current_rankings_csv_filename,
)
from kvk.services import kvk_rankings_service

DISCORD_CSV_UPLOAD_MAX_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class CurrentRankingsCsvExport:
    filename: str
    csv_bytes: io.BytesIO
    row_count: int
    payload: RankingPayload

    @property
    def byte_count(self) -> int:
        return len(self.csv_bytes.getvalue())

    def is_oversized(self, *, max_bytes: int = DISCORD_CSV_UPLOAD_MAX_BYTES) -> bool:
        return self.byte_count > max_bytes


def build_current_rankings_csv_export_from_payload(
    payload: RankingPayload,
) -> CurrentRankingsCsvExport:
    csv_bytes = build_current_rankings_csv_bytes(payload)
    return CurrentRankingsCsvExport(
        filename=current_rankings_csv_filename(payload),
        csv_bytes=csv_bytes,
        row_count=len(payload.rows),
        payload=payload,
    )


async def build_current_rankings_csv_export(
    *,
    mode: str,
    metric: str | None = None,
    limit: int = 10,
) -> CurrentRankingsCsvExport:
    payload = await kvk_rankings_service.build_current_rankings_payload(
        mode=mode,
        metric=metric,
        limit=limit,
        include_all=True,
    )
    return build_current_rankings_csv_export_from_payload(payload)
