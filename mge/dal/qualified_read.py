"""MGE reads that distinguish a valid empty result from an invalid result set."""

from contextlib import closing

from file_utils import get_conn_with_retries
from mge.dataset_errors import MgeDatasetError


def qualified_read(sql, params, *, columns, stage):
    """Check metadata before fetching, including for a zero-row result."""
    try:
        with closing(get_conn_with_retries()) as conn, closing(conn.cursor()) as cur:
            cur.execute(sql, tuple(params))
            names = [str(col[0]) for col in (cur.description or ())]
            if not names or len(set(names)) != len(names) or not set(columns) <= set(names):
                raise MgeDatasetError("incomplete", stage + "_columns")
            rows = cur.fetchall()
            if any(len(row) != len(names) for row in rows):
                raise MgeDatasetError("incomplete", stage + "_shape")
            return [dict(zip(names, row, strict=True)) for row in rows]
    except MgeDatasetError:
        raise
    except Exception:
        raise MgeDatasetError("unavailable", stage) from None
