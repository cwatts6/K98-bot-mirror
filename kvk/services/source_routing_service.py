"""Ordinary fixed-source reporting. SQL remains the authority on every request."""

from dataclasses import replace
import logging

from file_utils import get_conn_with_retries
from kvk.dal import source_routing_dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.source_integration import LegacyReportingBlocks, SeasonRead

logger = logging.getLogger(__name__)


def unavailable_report(read):
    from kvk.services.new_source_reporting_service import BLOCK_KEYS

    return dict(
        schema_version=2,
        source_key=read.source_key,
        kvk_no=read.kvk_no,
        period_id=read.period_id,
        publication_id=None,
        is_current=False,
        availability=read.availability,
        availability_reason=read.reason,
        public_read=read.as_dict(),
        blocks={key: [] for key in BLOCK_KEYS},
    )


def load_public_report(kvk_no, *, our_kingdom, connect=None):
    """No source, publication or token injection on this ordinary entry point."""
    from kvk.dal import kvk_reporting_dal
    from kvk.services.kvk_reporting_service import _normalise_blocks
    from kvk.services.new_source_reporting_service import load_complete_report

    read = source_routing_dal.resolve_season_read(kvk_no, connect=connect)
    if not read.available:
        return unavailable_report(read)
    if read.source_key == "legacy_full_data":
        blocks = kvk_reporting_dal.fetch_allkingdom_reporting_rows(kvk_no, our_kingdom, read=read)
        return LegacyReportingBlocks(_normalise_blocks(blocks), read)
    try:
        return load_complete_report(
            read, connect=connect or get_conn_with_retries, our_kingdom=our_kingdom
        )
    except Exception as exc:
        logger.warning(
            "[KVK ROUTING] immutable read failed kvk_no=%s error_type=%s",
            kvk_no,
            type(exc).__name__,
        )
        return unavailable_report(
            replace(read, availability="unavailable", reason="publication_integrity_failed")
        )


def require_current_read(saved, *, connect=None):
    """Action check only; never selects, refreshes or repairs the saved result."""
    read = SeasonRead(**saved)
    current = source_routing_dal.resolve_season_read(read.kvk_no, connect=connect)
    if not read.available or not current.available or current != read:
        raise SourceConflict(
            "Report authority changed; retain this session and create a new preview."
        )
    return current
