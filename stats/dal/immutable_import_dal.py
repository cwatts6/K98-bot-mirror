"""Read-only reconciliation DAL for the immutable fallback import handoff."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

_COMPLETED_FILE_PATTERN = re.compile(r"^stats_[0-9a-f]{32}\.ready\.csv$")
_TERMINAL_STATUSES = frozenset({"archived", "duplicate_archived"})


@dataclass(frozen=True, slots=True)
class ImmutableImportOutcome:
    completed_filename: str
    claim_status: str
    file_digest_hex: str | None
    scan_order: int | None
    archive_status: str | None

    @property
    def is_terminal(self) -> bool:
        if self.claim_status not in _TERMINAL_STATUSES:
            return False
        if self.claim_status == "archived":
            return self.archive_status == "archived" and self.scan_order is not None
        return self.file_digest_hex is not None

    @property
    def is_duplicate(self) -> bool:
        return self.claim_status == "duplicate_archived"


def fetch_immutable_import_outcome(
    cursor: Any,
    completed_filename: str,
) -> ImmutableImportOutcome | None:
    """Return durable claim/receipt state for one validated completed identity."""
    if _COMPLETED_FILE_PATTERN.fullmatch(str(completed_filename)) is None:
        raise ValueError("Invalid immutable fallback completed filename")

    cursor.execute(
        """
        SELECT
            claim.CompletedFileName,
            claim.ClaimStatus,
            CONVERT(varchar(64), claim.FileDigest, 2) AS FileDigestHex,
            receipt.ScanOrder,
            receipt.ArchiveStatus
        FROM dbo.KS4_ImportFileClaim AS claim
        LEFT JOIN dbo.KS4_ImportFileReceipt AS receipt
          ON receipt.FileDigest = claim.FileDigest
        WHERE claim.CompletedFileName = ?;
        """,
        completed_filename,
    )
    row = cursor.fetchone()
    if not row:
        return None
    return ImmutableImportOutcome(
        completed_filename=str(row[0]),
        claim_status=str(row[1]),
        file_digest_hex=str(row[2]) if row[2] is not None else None,
        scan_order=int(row[3]) if row[3] is not None else None,
        archive_status=str(row[4]) if row[4] is not None else None,
    )
