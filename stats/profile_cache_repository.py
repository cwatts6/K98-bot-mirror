"""Profile SQL read/mapping contract. No cache or filesystem publication."""

from contextlib import nullcontext
from datetime import datetime
import logging

from constants import _conn

logger = logging.getLogger(__name__)


def _connect():
    """
    Return a pyodbc.Connection using our centralized retry helper when available.

    - Prefer file_utils.get_conn_with_retries if present; falls back to constants._conn().
    """
    try:
        # lazy import to avoid circulars
        from file_utils import get_conn_with_retries

        return get_conn_with_retries()
    except Exception:
        # fallback: use constants._conn (may raise)
        logger.debug(
            "file_utils.get_conn_with_retries not available; falling back to constants._conn()"
        )
        return _conn()


def _rowdicts(cursor, rows):
    """Convert pyodbc rows to list[dict] using cursor.description."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r, strict=False)) for r in rows]


def _to_int(v):
    try:
        return int(v) if v is not None else None
    except Exception:
        try:
            return int(float(v)) if v is not None else None
        except Exception:
            return None


def _to_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


# If you might have numpy types; leave import optional
try:
    import numpy as np  # type: ignore
except Exception:
    np = None


def _safe_utc(dt):
    """
    Defensive wrapper: if dt is a datetime, try to make it aware UTC using utils.ensure_aware_utc.
    If conversion fails or dt is falsy, return it unchanged (None or original).
    """
    if not dt:
        return dt
    try:
        # lazy import
        from utils import ensure_aware_utc

        if isinstance(dt, datetime):
            return ensure_aware_utc(dt)
    except Exception:
        # If utils can't be imported or conversion fails, return original
        pass
    return dt


def read_profiles(connect=None):
    out, omitted = {}, []
    conn = (connect or _connect)()
    managed = hasattr(conn, "__enter__") and hasattr(conn, "__exit__")
    cur = None
    try:
        with conn if managed else nullcontext(conn) as active:
            cur = active.cursor()
            # v_PlayerProfile is the one-stop view we joined earlier
            cur.execute("SELECT * FROM dbo.v_PlayerProfile WITH (NOLOCK)")
            rows = cur.fetchall()
            for row in _rowdicts(cur, rows):
                gid = _to_int(row.get("GovernorID"))
                if gid is None:
                    continue

                # Handle City Hall column naming (alias or with space)
                ch_val = row.get("CityHallLevel", row.get("City Hall"))

                # Defensive timestamp conversions
                forts_updated = _safe_utc(row.get("FortsUpdated"))
                location_updated = _safe_utc(row.get("LocationUpdated"))
                shield_ends_at_utc = _safe_utc(row.get("ShieldEndsAtUtc"))
                status_updated = _safe_utc(row.get("StatusUpdated"))

                out[str(gid)] = {
                    "GovernorID": gid,
                    "GovernorName": (row.get("Governor_Name") or "").strip(),
                    "Alliance": (row.get("Alliance") or "").strip(),
                    "CityHallLevel": _to_int(ch_val),
                    "Power": _to_int(row.get("Power")),
                    "Kills": _to_int(row.get("Kills")),
                    "Deads": _to_int(row.get("Deads")),
                    "RSS_Gathered": _to_int(row.get("RSS_Gathered")),
                    "Helps": _to_int(row.get("Helps")),
                    "X": _to_int(row.get("X")),
                    "Y": _to_int(row.get("Y")),
                    "ShieldEndsAtUnix": _to_int(row.get("ShieldEndsAtUnix")),
                    "ShieldEndsAtUtc": shield_ends_at_utc,
                    "Status": row.get("Status"),
                    "FortsRank": _to_int(row.get("FortsRank")),
                    "FortsStarted": _to_int(row.get("FortsStarted")),
                    "FortsJoined": _to_int(row.get("FortsJoined")),
                    "FortsTotal": _to_int(row.get("FortsTotal")),
                    # Timestamp fields
                    "FortsUpdated": forts_updated,
                    "LocationUpdated": location_updated,
                    "StatusUpdated": status_updated,
                    # NEW — pulled directly from v_PlayerProfile after your SQL change
                    "PowerRank": _to_int(row.get("PowerRank")),
                }

            # --- NEW: enrich with first/last scan and offline >30d ---
            try:
                cur.execute(
                    "SELECT GovernorID, FirstScanDate, LastScanDate, OfflineDaysOver30 FROM dbo.v_PlayerScanMeta WITH (NOLOCK)"
                )
                for r in _rowdicts(cur, cur.fetchall()):
                    gid = str(_to_int(r.get("GovernorID")))
                    if gid in out:
                        out_gid = out[gid]
                        out_gid["FirstScanDate"] = _safe_utc(r.get("FirstScanDate"))
                        out_gid["LastScanDate"] = _safe_utc(r.get("LastScanDate"))
                        out_gid["OfflineDaysOver30"] = _to_int(r.get("OfflineDaysOver30")) or 0
            except Exception:
                # If the view isn’t present, we just skip; embed will omit the line gracefully
                omitted.append("scan_meta")
                logger.debug(
                    "[CACHE] v_PlayerScanMeta not present or query failed; skipping enrichment",
                    exc_info=True,
                )

            # Optional KVK view — skip gracefully if it doesn't exist
            try:
                cur.execute(
                    "SELECT GovernorID, KVK_NUMBER, KVK_KILL_RANK, KillPercent FROM dbo.v_PlayerKVK_Last3 WITH (NOLOCK)"
                )
                kvkrows = cur.fetchall()
                for rr in _rowdicts(cur, kvkrows):
                    gid = str(_to_int(rr.get("GovernorID")))
                    if gid == "None":
                        continue
                    out.setdefault(gid, {}).setdefault("KVK", []).append(
                        {
                            "KVK": _to_int(rr.get("KVK_NUMBER")),
                            "Rank": _to_int(rr.get("KVK_KILL_RANK")),
                            "Percent": _to_float(rr.get("KillPercent")),
                        }
                    )
            except Exception:
                omitted.append("kvk_last3")
                logger.debug(
                    "[CACHE] v_PlayerKVK_Last3 not present or query failed; skipping KVK enrichment",
                    exc_info=True,
                )

    finally:
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if not managed:
            conn.close()
    for value in out.values():
        if isinstance(value.get("KVK"), list):
            value["KVK"].sort(key=lambda x: x.get("KVK") or 0, reverse=True)
    return out, tuple(omitted)
