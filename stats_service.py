# stats_service.py
import asyncio
import io
import logging
import time

import matplotlib

from embed_utils import fmt_short
from file_utils import (
    fetch_all_dicts,
    fetch_one_dict,
    get_conn_with_retries,
)
from governor_registry import load_registry  # ← use your JSON loader
from stats_helpers import is_single_day_slice
from utils import csv_from_ids, ensure_aware_utc, to_ints

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

logger = logging.getLogger(__name__)

TTL_SECONDS = 45
_cache: dict[tuple[int, str, tuple[int, ...]], tuple[float, dict]] = {}
_inflight: dict[tuple[int, str, tuple[int, ...]], asyncio.Future] = {}

# Drop '1d' to avoid confusion with 'yesterday'
SLICES = ["yesterday", "wtd", "last_week", "mtd", "last_month", "last_3m", "last_6m"]


def _key(discord_id: int, slice_key: str, gov_ids: list[int]) -> tuple[int, str, tuple[int, ...]]:
    return (discord_id, slice_key, tuple(sorted(gov_ids)))


async def get_registered_governor_ids_for_discord(discord_id: int) -> list[int]:
    """Read accounts from governor_registry.JSON (not SQL)."""
    try:
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        reg = await run_blocking_in_thread(
            load_registry,
            name="load_registry_for_ids",
            meta={"discord_id": discord_id},
        )
    else:
        reg = await asyncio.to_thread(load_registry)
    reg = reg or {}
    block = reg.get(str(discord_id)) or reg.get(discord_id) or {}
    accounts = block.get("accounts") or {}
    raw_ids = [acc.get("GovernorID") for acc in accounts.values() if acc]
    return to_ints(raw_ids)


async def get_registered_governor_names_for_discord(discord_id: int) -> list[str]:
    """Handy for the dropdown labels (GovernorName)."""
    try:
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        reg = await run_blocking_in_thread(
            load_registry,
            name="load_registry_for_names",
            meta={"discord_id": discord_id},
        )
    else:
        reg = await asyncio.to_thread(load_registry)
    reg = reg or {}
    block = reg.get(str(discord_id)) or reg.get(discord_id) or {}
    accounts = block.get("accounts") or {}
    names = []
    for slot, acc in accounts.items():
        gname = (acc or {}).get("GovernorName")
        if gname:
            names.append(str(gname))
    # Keep a stable order: Main, Alt 1..n, Farm 1..n, then the rest
    preferred = ["Main"] + [f"Alt {i}" for i in range(1, 10)] + [f"Farm {i}" for i in range(1, 20)]

    def slot_rank(item):
        for i, s in enumerate(preferred):
            if s in accounts and accounts[s].get("GovernorName") == item:
                return i
        return 10_000

    return sorted(set(names), key=slot_rank)


def _fetch_proc_sync(gov_ids: list[int], slices_csv: str, include_aggregate: bool) -> list[dict]:
    """
    Synchronous DB fetch for usp_GetPlayerStatsWindows.

    Extracted to module-level so maintenance_worker.py can import and offload to child process.

    Args:
        gov_ids: List of GovernorIDs to fetch stats for
        slices_csv: Comma-separated slice keys (e.g., "wtd,last_week")
        include_aggregate: Whether to include ALL aggregate rows

    Returns:
        List of stat row dicts from stored procedure
    """
    sql = """
    DECLARE @Ids dbo.IntList;
    INSERT INTO @Ids(ID) SELECT TRY_CAST(value AS int) FROM STRING_SPLIT(?, ',') WHERE value IS NOT NULL AND LTRIM(RTRIM(value))<>'';
    EXEC dbo.usp_GetPlayerStatsWindows
         @GovernorIDs=@Ids,
         @IncludeSlicesCsv=?,
         @UsePrevScanFor1d=1,
         @IncludeAggregate=?;
    """

    cn = get_conn_with_retries()
    try:
        cur = cn.cursor()
        cur.execute(sql, (csv_from_ids(gov_ids), slices_csv, 1 if include_aggregate else 0))

        # Advance through non-SELECT results until we hit an actual result set
        while True:
            if cur.description is not None:
                return fetch_all_dicts(cur)
            # Not a result set; try next
            if not cur.nextset():
                # Procedure returned no SELECT result
                return []
    finally:
        cn.close()


async def _fetch_proc(gov_ids: list[int], slices_csv: str, include_aggregate: bool) -> list[dict]:
    """
    Fetch stats from DB using thread pool (not process isolation).

    Process isolation is designed for long-running maintenance tasks with side effects,
    not fast data queries. Thread pool is more efficient for DB queries.
    """
    try:
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        result = await run_blocking_in_thread(
            _fetch_proc_sync,
            gov_ids,
            slices_csv,
            include_aggregate,
            name="fetch_proc",
            meta={"gov_ids": gov_ids, "slice": slices_csv},
        )
    else:
        result = await asyncio.to_thread(_fetch_proc_sync, gov_ids, slices_csv, include_aggregate)

    # Normalize result (run_blocking_in_thread may return tuple with worker metadata)
    if isinstance(result, tuple) and len(result) == 2:
        first, second = result
        if isinstance(second, dict) and isinstance(first, list):
            return first

    if isinstance(result, (list, tuple)):
        return list(result)
    if result is None:
        return []

    logger.warning("fetch_proc final result not iterable; returning empty. raw=%r", result)
    return []


def _fetch_trendlines_sync(governor_ids: list[int], slice_key: str) -> list[tuple]:
    """
    Synchronous DB fetch for daily trendline data (RSS, Forts, Alliance Activity, Helps).

    Extracted to module-level so maintenance_worker.py can import and offload to child process.

    Args:
        governor_ids: List of GovernorIDs to fetch trends for
        slice_key: Slice key (e.g., "wtd", "last_month")

    Returns:
        List of tuples: (series_name, date_str, value_int)
    """
    ids_csv = csv_from_ids(governor_ids)
    sql = """
    DECLARE @Latest datetime2 = (SELECT MAX(AsOfDate) FROM dbo.vDaily_PlayerExport WITH (NOLOCK));
    IF @Latest IS NULL SET @Latest = SYSUTCDATETIME();
    -- Anchor Monday calculation so WTD/last_week are stable regardless of @@DATEFIRST
    DECLARE @Anchor date = '19000101';
    DECLARE @ThisMonday datetime2 = DATEADD(
        DAY,
        - (DATEDIFF(DAY, @Anchor, CAST(@Latest AS date)) % 7),
        CAST(CAST(@Latest AS date) AS datetime2)
    );
    DECLARE @LastMonday datetime2 = DATEADD(DAY, -7, @ThisMonday);
    DECLARE @EndLastWeek datetime2 = DATEADD(SECOND, -1, @ThisMonday);
    DECLARE @FirstOfThisMonth datetime2 = DATEFROMPARTS(YEAR(@Latest), MONTH(@Latest), 1);
    DECLARE @FirstOfLastMonth date = DATEADD(MONTH,-1, CAST(@FirstOfThisMonth AS date));
    DECLARE @EndOfLastMonth datetime2 = DATEADD(SECOND,-1,@FirstOfThisMonth);
    DECLARE @FirstOf3MoAgo date = DATEADD(MONTH,-3, CAST(@FirstOfThisMonth AS date));
    DECLARE @FirstOf6MoAgo date = DATEADD(MONTH,-6, CAST(@FirstOfThisMonth AS date));
    DECLARE @Today date = CAST(@Latest AS date);
    DECLARE @TodayStart datetime2 = CAST(@Today AS datetime2);
    DECLARE @YesterdayStart datetime2 = CAST(DATEADD(DAY,-1,@Today) AS datetime2);
    DECLARE @YesterdayEnd datetime2 = DATEADD(SECOND,-1,@TodayStart);
    DECLARE @SliceStart datetime2, @SliceEnd datetime2;
    -- Back-compat: treat '1d' as 'yesterday' if ever passed in
    IF LOWER(?)='1d'         SELECT @SliceStart=@YesterdayStart, @SliceEnd=@YesterdayEnd;
    ELSE IF LOWER(?)='yesterday'  SELECT @SliceStart=@YesterdayStart, @SliceEnd=@YesterdayEnd;
    ELSE IF LOWER(?)='wtd'        SELECT @SliceStart=@ThisMonday,     @SliceEnd=@Latest;
    ELSE IF LOWER(?)='last_week'  SELECT @SliceStart=@LastMonday,     @SliceEnd=@EndLastWeek;
    ELSE IF LOWER(?)='mtd'        SELECT @SliceStart=@FirstOfThisMonth,@SliceEnd=@Latest;
    ELSE IF LOWER(?)='last_month' SELECT @SliceStart=CAST(@FirstOfLastMonth AS datetime2), @SliceEnd=@EndOfLastMonth;
    ELSE IF LOWER(?)='last_3m'    SELECT @SliceStart=CAST(@FirstOf3MoAgo AS datetime2),    @SliceEnd=@Latest;
    ELSE IF LOWER(?)='last_6m'    SELECT @SliceStart=CAST(@FirstOf6MoAgo AS datetime2),    @SliceEnd=@Latest;
    ELSE SELECT @SliceStart=@ThisMonday, @SliceEnd=@Latest;
    ;WITH Ids AS (
      SELECT TRY_CAST(value AS int) AS GovernorID
      FROM STRING_SPLIT(?, ',')
    )
    SELECT 'AA_BUILD' AS Series, CONVERT(varchar(10), d.AsOfDate, 120) AS d,
           SUM(CONVERT(bigint, COALESCE(d.BuildingMinutes,0))) AS v
      FROM dbo.vDaily_PlayerExport d
     WHERE d.GovernorID IN (SELECT GovernorID FROM Ids)
       AND d.AsOfDate BETWEEN CAST(@SliceStart AS date) AND CAST(@SliceEnd AS date)
     GROUP BY d.AsOfDate
    UNION ALL
    SELECT 'AA_TECH', CONVERT(varchar(10), d.AsOfDate, 120),
           SUM(CONVERT(bigint, COALESCE(d.TechDonations,0)))
      FROM dbo.vDaily_PlayerExport d
     WHERE d.GovernorID IN (SELECT GovernorID FROM Ids)
       AND d.AsOfDate BETWEEN CAST(@SliceStart AS date) AND CAST(@SliceEnd AS date)
     GROUP BY d.AsOfDate
    UNION ALL
    SELECT 'FORTS', CONVERT(varchar(10), d.AsOfDate, 120),
           SUM(CONVERT(bigint, COALESCE(d.FortsTotal,0)))
      FROM dbo.vDaily_PlayerExport d
     WHERE d.GovernorID IN (SELECT GovernorID FROM Ids)
       AND d.AsOfDate BETWEEN CAST(@SliceStart AS date) AND CAST(@SliceEnd AS date)
     GROUP BY d.AsOfDate
    UNION ALL
    SELECT 'RSS', CONVERT(varchar(10), d.AsOfDate, 120),
           SUM(CONVERT(bigint, COALESCE(d.RSS_GatheredDelta,0)))
      FROM dbo.vDaily_PlayerExport d
     WHERE d.GovernorID IN (SELECT GovernorID FROM Ids)
       AND d.AsOfDate BETWEEN CAST(@SliceStart AS date) AND CAST(@SliceEnd AS date)
     GROUP BY d.AsOfDate
    UNION ALL
    SELECT 'HELPS', CONVERT(varchar(10), d.AsOfDate, 120),
           SUM(CONVERT(bigint, COALESCE(d.HelpsDelta,0)))
      FROM dbo.vDaily_PlayerExport d
     WHERE d.GovernorID IN (SELECT GovernorID FROM Ids)
       AND d.AsOfDate BETWEEN CAST(@SliceStart AS date) AND CAST(@SliceEnd AS date)
     GROUP BY d.AsOfDate
    ORDER BY d;
    """

    cn = get_conn_with_retries()
    try:
        cur = cn.cursor()
        cur.execute(
            sql,
            (
                slice_key,
                slice_key,
                slice_key,
                slice_key,
                slice_key,
                slice_key,
                slice_key,
                slice_key,
                ids_csv,
            ),
        )
        return cur.fetchall()
    finally:
        cn.close()


async def _fetch_trendlines(
    governor_ids: list[int], slice_key: str
) -> dict[str, list[tuple[str, int]]]:
    """
    Fetch trendline data from DB using thread pool (not process isolation).

    Process isolation is designed for long-running maintenance tasks with side effects,
    not fast data queries. Thread pool is more efficient for DB queries.
    """
    try:
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        rows = await run_blocking_in_thread(
            _fetch_trendlines_sync,
            governor_ids,
            slice_key,
            name="fetch_trendlines",
            meta={"gov_ids": governor_ids, "slice": slice_key},
        )
    else:
        rows = await asyncio.to_thread(_fetch_trendlines_sync, governor_ids, slice_key)

    # Normalize result (run_blocking_in_thread may return tuple with worker metadata)
    if isinstance(rows, tuple) and len(rows) == 2:
        first, second = rows
        if isinstance(second, dict) and isinstance(first, (list, tuple)):
            rows = first

    # Ensure rows is iterable
    if isinstance(rows, bool) or rows is None:
        logger.warning(
            "fetch_trendlines final result non-rows (bool/None); treating as empty. raw=%r", rows
        )
        rows = []

    if isinstance(rows, dict):
        logger.warning("fetch_trendlines final result dict; treating as empty. raw=%r", rows)
        rows = []

    try:
        rows = list(rows) if not isinstance(rows, list) else rows
    except TypeError:
        logger.warning(
            "fetch_trendlines final result non-iterable; treating as empty. raw=%r", rows
        )
        rows = []

    # Convert pyodbc.Row objects to tuples (thread execution returns pyodbc.Row)
    if rows and len(rows) > 0:
        first_row = rows[0]
        if type(first_row).__name__ == "Row":
            logger.debug("fetch_trendlines: converting pyodbc.Row objects to tuples...")
            rows = [tuple(row) for row in rows]
            logger.debug("fetch_trendlines: converted %d Row objects to tuples", len(rows))

    # Validate structure
    if rows and len(rows) > 0:
        first_row = rows[0]
        if not isinstance(first_row, (tuple, list)) or len(first_row) != 3:
            logger.error(
                "fetch_trendlines: rows have unexpected structure. First row: %r (type=%s, len=%s)",
                first_row,
                type(first_row).__name__,
                len(first_row) if isinstance(first_row, (tuple, list)) else "N/A",
            )
            rows = []

    series = {"AA_BUILD": [], "AA_TECH": [], "RSS": [], "FORTS": [], "HELPS": []}

    for row in rows:
        try:
            s, d, v = row
            series[s].append((d, int(v or 0)))
        except (ValueError, TypeError) as e:
            logger.warning("fetch_trendlines: failed to unpack row %r: %s. Skipping.", row, e)
            continue

    # Build a combined AA series (AA = AA_BUILD + AA_TECH) for the embed's "AA Daily" chart
    aa_by_date = {}
    for d, v in series["AA_BUILD"]:
        aa_by_date[d] = aa_by_date.get(d, 0) + v
    for d, v in series["AA_TECH"]:
        aa_by_date[d] = aa_by_date.get(d, 0) + v
    series["AA"] = [(d, aa_by_date[d]) for d in sorted(aa_by_date.keys())]

    return series


def _make_sparkline_sync(
    points: list[tuple[str, int]], title: str, average: float | None = None
) -> io.BytesIO | None:
    """
    Synchronous sparkline chart generation using matplotlib.

    Extracted for thread offload to prevent blocking the event loop.

    Args:
        points: List of (date_str, value_int) tuples
        title: Chart title
        average: Optional average value to draw as dashed line

    Returns:
        BytesIO buffer containing PNG chart, or None if no points
    """
    if not points:
        return None

    xs = [p[0] for p in points]
    ys = [int(p[1] or 0) for p in points]

    fig, ax = plt.subplots(figsize=(6.5, 2.0), dpi=170)
    xidx = list(range(len(xs)))

    if len(xidx) == 1:
        # Single point: draw a marker so it's visible
        ax.scatter(xidx, ys, s=30)
        ax.set_xlim(-0.5, 0.5)
    else:
        # Multi-point: draw a line with small markers
        ax.plot(xidx, ys, linewidth=2, marker="o", markersize=3)

    # Dashed mean line + small label (only when average provided and series has >1 point)
    if average is not None and len(ys) > 1:
        ax.axhline(average, linestyle="--")
        ax.text(xidx[-1], average, f" avg {fmt_short(average)}", va="bottom", ha="left", fontsize=8)

    # Y axis setup
    y_max = max(ys) if ys else 0
    if y_max <= 0:
        y_max = 1
    step = max(1, int(round(y_max / 4.0)))
    ax.set_ylim(0, y_max * 1.10)
    ax.set_yticks([i for i in range(0, int(y_max * 1.10) + 1, step)])

    # Compact Y labels for big magnitudes (RSS especially)
    if "RSS" in (title or "") or y_max >= 10_000_000:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: fmt_short(v)))

    # X axis: pick sensible tick density
    n = len(xs)
    if n <= 10:
        idxs = list(range(n))
    elif n <= 20:
        idxs = list(range(0, n, 2)) + [n - 1]
    elif n <= 35:
        idxs = list(range(0, n, 3)) + [n - 1]
    else:
        step = max(1, n // 8)
        idxs = list(range(0, n, step))
        if idxs[-1] != n - 1:
            idxs.append(n - 1)
    idxs = sorted(set(i for i in idxs if 0 <= i < n))
    ax.set_xticks(idxs)
    ax.set_xticklabels([xs[i] for i in idxs], rotation=0, fontsize=8)

    ax.set_title(title, fontsize=11, pad=6)
    ax.grid(True, linestyle=":", alpha=0.35, axis="both")
    ax.tick_params(axis="both", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


async def _make_sparkline(
    points: list[tuple[str, int]], title: str, average: float | None = None
) -> io.BytesIO | None:
    """
    Async wrapper for sparkline generation - offloads matplotlib to thread pool.

    Args:
        points: List of (date_str, value_int) tuples
        title: Chart title
        average: Optional average value to draw as dashed line

    Returns:
        BytesIO buffer containing PNG chart, or None if no points
    """
    if not points:
        return None

    try:
        from file_utils import run_blocking_in_thread
    except Exception:
        run_blocking_in_thread = None

    if run_blocking_in_thread is not None:
        return await run_blocking_in_thread(
            _make_sparkline_sync,
            points,
            title,
            average,
            name="make_sparkline",
            meta={"title": title, "points": len(points)},
        )
    else:
        return await asyncio.to_thread(_make_sparkline_sync, points, title, average)


async def get_stats_payload(
    discord_id: int, governor_ids: list[int], slice_key_or_csv: str
) -> dict:
    """
    Fetch stats payload with caching and deduplication.

    Returns dict with keys: rows, trends, trend_avgs, freshness
    """
    # normalize slice list (supports one or many)
    slices_csv = slice_key_or_csv
    # cache on (user, EXACT ids set, slices string) to protect DB when switching accounts/slices
    k = (discord_id, slices_csv.lower().strip(), tuple(sorted(governor_ids)))
    now = time.time()
    if k in _cache and _cache[k][0] > now:
        return _cache[k][1]
    if k in _inflight:
        return await _inflight[k]

    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    _inflight[k] = fut
    try:
        rows = await _fetch_proc(governor_ids, slices_csv, include_aggregate=True) or []

        # trends only for single-slice views; for multi-slice exports we skip charts
        trends = {}
        if slices_csv.count(",") == 0:
            trends = await _fetch_trendlines(governor_ids, slices_csv)

        # --- Compute per-series averages for multi-day slices
        trend_avgs: dict[str, float | None] = {}
        try:
            slice_key = slices_csv.lower().strip()
            if trends and not is_single_day_slice(slice_key):

                def _avg_from_points(pts: list[tuple[str, int]]) -> float | None:
                    vals = [float(v) for _, v in pts if v is not None]
                    return (sum(vals) / len(vals)) if len(vals) > 1 else None

                for s in ("RSS", "FORTS", "AA", "AA_BUILD", "AA_TECH", "HELPS"):
                    if s in trends:
                        trend_avgs[s] = _avg_from_points(trends.get(s) or [])
        except Exception:
            # don't let averages calculation break the panel
            trend_avgs = {}

        # freshness
        def _fresh():
            cn = get_conn_with_retries()
            try:
                cur = cn.cursor()
                cur.execute("SELECT MAX(AsOfDate) FROM dbo.vDaily_PlayerExport WITH (NOLOCK);")
                row = fetch_one_dict(cur)
            finally:
                cn.close()

            # Normalize to project's UTC standard if possible
            if not row:
                return {"daily": None}

            latest = next(iter(row.values()))
            if latest is None:
                return {"daily": None}
            try:
                latest_utc = ensure_aware_utc(latest)
            except Exception:
                latest_utc = latest
            return {"daily": latest_utc}

        # Prefer start_callable_offload for freshness/readers for process-level visibility,
        # fall back to run_blocking_in_thread or asyncio.to_thread
        try:
            from file_utils import start_callable_offload  # type: ignore
        except Exception:
            start_callable_offload = None

        try:
            if start_callable_offload is not None:
                res = await start_callable_offload(
                    _fresh, name="fetch_freshness", prefer_process=True
                )
                if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict):
                    freshness = res[0]
                else:
                    freshness = res
            else:
                from file_utils import run_blocking_in_thread

                freshness = await run_blocking_in_thread(_fresh, name="fetch_freshness")
        except Exception:
            # fallback to to_thread
            freshness = await asyncio.to_thread(_fresh)

        payload = {"rows": rows, "trends": trends, "trend_avgs": trend_avgs, "freshness": freshness}
        _cache[k] = (now + TTL_SECONDS, payload)
        fut.set_result(payload)
        return payload
    except Exception as e:
        logger.exception(
            "Failed to fetch stats payload: discord_id=%s gov_ids=%s slice=%s",
            discord_id,
            governor_ids,
            slices_csv,
        )
        # Set exception on future so other waiters know it failed
        try:
            fut.set_exception(e)
        except Exception:
            # Future may already be done (race condition)
            pass

        # Return empty payload instead of raising (graceful degradation)
        empty_payload = {"rows": [], "trends": {}, "trend_avgs": {}, "freshness": {}}
        return empty_payload
    finally:
        _inflight.pop(k, None)
