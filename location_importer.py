# location_importer.py

import csv
import io
import logging
import os

import pyodbc

from constants import DATABASE, PASSWORD, SERVER, USERNAME

log = logging.getLogger(__name__)


def _get_conn():
    user = os.getenv("IMPORT_SQL_USERNAME", USERNAME)
    pwd = os.getenv("IMPORT_SQL_PASSWORD", PASSWORD)
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={user};PWD={pwd}",
        autocommit=False,
    )


def parse_output_csv(csv_bytes: bytes) -> list[tuple]:
    """
    Returns tuples matching dbo.PlayerLocation_Staging insert order:
    (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
    """
    text = csv_bytes.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows: list[tuple] = []
    for r in reader:
        try:
            pid = int(str(r.get("player_id", "")).strip())
            name = (r.get("player_name") or "").strip()
            pwr = int(str(r.get("player_power", "0") or 0))
            kills = int(str(r.get("player_kills", "0") or 0))
            ch = int(str(r.get("player_ch", "0") or 0))
            ally = (r.get("player_alliance") or "").strip()
            x = int(str(r.get("x", "")).strip())
            y = int(str(r.get("y", "")).strip())
            rows.append((pid, name, pwr, kills, ch, ally, x, y))
        except Exception as e:
            log.warning(f"[location_import] Skipping bad row {r}: {e}")
    return rows


def load_staging_and_merge(rows: list[tuple]) -> tuple[int, int]:
    """
    Truncate staging, bulk-insert rows, run merge proc.
    Returns (staging_rows, total_tracked).
    """
    if not rows:
        return (0, 0)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # cur.execute("TRUNCATE TABLE dbo.PlayerLocation_Staging;")
            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.PlayerLocation_Staging
                (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            cur.execute("EXEC dbo.sp_ImportPlayerLocationFromStaging;")
            result = cur.fetchone()
        conn.commit()

        staging_rows = result[0] if result else len(rows)
        total_tracked = result[1] if result and len(result) > 1 else 0
        return staging_rows, total_tracked

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def load_staging_and_replace(rows: list[tuple]) -> tuple[int, int]:
    """
    Clears staging, bulk-inserts rows, then atomically replaces dbo.PlayerLocation
    only if staging has >0 rows. Returns (imported_rows, total_tracked).
    """
    if not rows:
        return (0, 0)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            # Clear staging (requires ALTER on staging for TRUNCATE; otherwise use DELETE)
            cur.execute("TRUNCATE TABLE dbo.PlayerLocation_Staging;")

            cur.fast_executemany = True
            cur.executemany(
                """
                INSERT INTO dbo.PlayerLocation_Staging
                (player_id, player_name, player_power, player_kills, player_ch, player_alliance, x, y)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

            # Atomic full-replace (only if >0 rows in staging)
            cur.execute("EXEC dbo.sp_ReplacePlayerLocationFromStaging;")
            result = cur.fetchone()

        conn.commit()

        imported = result[0] if result else 0
        total = result[1] if result and len(result) > 1 else 0
        return imported, total

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
