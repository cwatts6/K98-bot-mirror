"""Bounded, once-only Ark reads for startup view restoration; no mutations."""

from file_utils import fetch_one_dict, get_conn_with_retries
from services.legacy_export_snapshot_service import drain_thread


def _load_registration(match_id: int):
    # The canonical connection factory has a five-second login timeout. Do not use
    # the legacy async fallback wrappers: cancellation must retain worker custody.
    conn = get_conn_with_retries(retries=1, backoff_base=0, backoff_max=0)
    cursor = None
    try:
        conn.timeout = 5
        cursor = conn.cursor()
        cursor.execute("SELECT TOP 1 * FROM dbo.ArkConfig ORDER BY ConfigId DESC;")
        config = fetch_one_dict(cursor)
        cursor.execute("SELECT * FROM dbo.ArkMatches WHERE MatchId = ?;", (match_id,))
        match = fetch_one_dict(cursor)
        return config, match
    finally:
        try:
            if cursor is not None:
                cursor.close()
        finally:
            conn.close()


async def get_registration_rehydration_data(match_id: int):
    return await drain_thread(_load_registration, match_id)
