# target_utils.py (patched)
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import discord
from rapidfuzz import fuzz, process
from unidecode import unidecode

# NOTE: _conn is the repo's SQL connection helper imported from constants
from constants import _conn
from kvk_state import get_kvk_context_today
from targets_embed import build_kvk_targets_embed
from targets_sql_cache import get_targets_for_governor, refresh_targets_cache

logger = logging.getLogger(__name__)

# ---------------- Name cache (unchanged structure but enriched) ----------------

_name_cache = {
    "names": {},  # normalized -> original (for autocomplete)
    "norm_to_row": {},  # normalized -> row (for exact lookup)
    "last_updated": 0,
    "rows": [],  # full ALL_COMMANDERS rows
}
CACHE_DURATION_SECONDS = 86400  # 24h


# small normalization helper to keep behavior consistent across file
def _normalize_name(name: str) -> str:
    return unidecode(str(name or "").strip().lower())


# ----------------------------------------------------------------------
# Module-level synchronous worker for name cache refresh
# ----------------------------------------------------------------------
# This function is intentionally module-level so it can be referenced as
# "target_utils:sync_refresh_worker" by subprocess-based maintenance workers.
def sync_refresh_worker() -> None:
    """
    Module-level wrapper that performs the synchronous refresh work that was
    previously implemented as a nested function. Being module-level allows
    the maintenance subprocess to import and call it via 'target_utils:sync_refresh_worker'.
    """
    try:
        import traceback

        import pandas as pd

        logger.debug("[TARGET_UTILS] Starting SQL name cache refresh (module-level worker)")
        sql = """
        SELECT [GovernorID], [GovernorName], [CityHallLevel]
        FROM dbo.vw_All_Governors_Clean
        WHERE GovernorName IS NOT NULL
        """

        conn = _conn()
        use_pandas = True
        try:
            df = pd.read_sql(sql, conn)
            logger.debug("[TARGET_UTILS] pandas.read_sql returned %d rows", len(df))
        except Exception as e:
            logger.warning(
                "[TARGET_UTILS] pandas.read_sql failed (%s). Falling back to cursor fetch. Trace: %s",
                type(e).__name__,
                traceback.format_exc(),
            )
            use_pandas = False

        name_map: dict[str, str] = {}
        norm_to_row: dict[str, dict] = {}
        rows: list[dict[str, Any]] = []

        if use_pandas:
            for _, r in df.iterrows():
                original = str(r["GovernorName"]).strip()
                if not original:
                    continue
                try:
                    gov_id = int(r["GovernorID"])
                except Exception:
                    continue
                norm = _normalize_name(original)
                row = {
                    "GovernorName": original,
                    "GovernorID": str(gov_id),
                    "CityHallLevel": r.get("CityHallLevel"),
                }
                if norm not in norm_to_row:
                    norm_to_row[norm] = row
                    name_map[norm] = original
                rows.append(row)
        else:
            cur = conn.cursor()
            try:
                cur.execute(sql)
                fetched = cur.fetchall()
                logger.debug("[TARGET_UTILS] cursor.fetchall returned %d rows", len(fetched))
                for row in fetched:
                    try:
                        gov_id = int(row[0])
                        original = str(row[1]).strip()
                        city_hall = row[2] if len(row) > 2 else None
                    except Exception:
                        continue
                    if not original:
                        continue
                    norm = _normalize_name(original)
                    item = {
                        "GovernorName": original,
                        "GovernorID": str(gov_id),
                        "CityHallLevel": city_hall,
                    }
                    if norm not in norm_to_row:
                        norm_to_row[norm] = item
                        name_map[norm] = original
                    rows.append(item)
            finally:
                try:
                    cur.close()
                except Exception:
                    pass

        # Atomically swap cache contents
        _name_cache["names"] = name_map
        _name_cache["norm_to_row"] = norm_to_row
        _name_cache["rows"] = rows
        _name_cache["last_updated"] = int(time.time())
        logger.info("[TARGET_UTILS] Name cache refreshed from SQL (%d rows)", len(rows))
    except Exception:
        logger.exception("[TARGET_UTILS] sync_refresh_worker failed")
        raise


# --- Back-compat shim for older imports (e.g., processing_pipeline.py) ---
async def warm_target_cache() -> None:
    """
    Legacy async wrapper kept for compatibility.
    Uses the existing SQL-backed refresh_targets_cache for full targets cache.
    Prefer process offload for heavy refresh when available.
    """
    try:
        # Local import to avoid module-level import cycles
        try:
            from file_utils import run_maintenance_with_isolation  # type: ignore
        except Exception:
            run_maintenance_with_isolation = None

        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        if run_maintenance_with_isolation is not None:
            await run_maintenance_with_isolation(
                refresh_targets_cache,
                name="refresh_targets_cache",
                prefer_process=True,
                meta={"caller": "warm_target_cache"},
            )
        elif run_blocking_in_thread is not None:
            await run_blocking_in_thread(
                refresh_targets_cache,
                name="refresh_targets_cache",
                meta={"caller": "warm_target_cache"},
            )
        else:
            await asyncio.to_thread(refresh_targets_cache)
    except Exception:
        logger.exception("[TARGET_UTILS] warm_target_cache() failed")


# ---------------- New: SQL-backed name cache refresher ----------------
# Reads from the view dbo.vw_All_Governors_Clean which exposes GovernorID and GovernorName.
async def refresh_name_cache_from_sql() -> None:
    """
    Async function to refresh the in-memory name cache from SQL.
    Offloads the actual DB work to a process (preferred) or thread as fallback.
    """
    try:
        # Local import to avoid module-level import cycles
        try:
            from file_utils import run_maintenance_with_isolation  # type: ignore
        except Exception:
            run_maintenance_with_isolation = None

        try:
            from file_utils import run_blocking_in_thread
        except Exception:
            run_blocking_in_thread = None

        # Prefer module-level worker for subprocess execution (resolvable in child process)
        if run_maintenance_with_isolation is not None:
            await run_maintenance_with_isolation(
                sync_refresh_worker,
                name="refresh_name_cache_from_sql",
                prefer_process=True,
                meta={"source": "vw_All_Governors_Clean"},
            )
        elif run_blocking_in_thread is not None:
            await run_blocking_in_thread(
                sync_refresh_worker,
                name="refresh_name_cache_from_sql",
                meta={"source": "vw_All_Governors_Clean"},
            )
        else:
            await asyncio.to_thread(sync_refresh_worker)
    except Exception:
        logger.warning("[TARGET_UTILS] refresh_name_cache_from_sql failed; keeping existing cache")


# Small diagnostic helper to inspect cache state (useful in logs / REPL)
def get_name_cache_status() -> dict[str, Any]:
    return {
        "last_updated": _name_cache.get("last_updated", 0),
        "rows_count": len(_name_cache.get("rows") or []),
        "names_count": len(_name_cache.get("names") or {}),
    }


# ---------------- Targets: EXEMPT/NOT ACTIVE fallback (still via SQL) ----------------


async def _fallback_exempt_or_not_active(governor_id: str) -> dict[str, Any] | None:
    """
    SQL-backed check against dbo.EXEMPT_FROM_STATS.
    Returns:
      - {"status": "exempt", "message": "..."}          if exempt
      - {"status": "not_active", "message": "..."}      if not active this KVK
      - None                                            if no matching rule found
    """
    try:
        ctx = get_kvk_context_today()
        current_kvk_no = ctx["kvk_no"] if ctx else None

        conn = _conn()
        try:
            cur = conn.cursor()
            try:
                params: list[Any] = [int(governor_id)]
                where_kvk = ""
                if current_kvk_no is not None:
                    where_kvk = "AND (KVK_NO = ? OR KVK_NO = 0 OR KVK_NO IS NULL)"
                    params.append(int(current_kvk_no))
                else:
                    where_kvk = "AND (KVK_NO = 0 OR KVK_NO IS NULL)"

                sql = f"""
                SELECT
                    GovernorID,
                    COALESCE(GovernorName, '') AS GovernorName,
                    COALESCE(CAST(KVK_NO AS int), 0) AS KVK_NO,
                    COALESCE(Exempt_Reason, '') AS Exempt_Reason,
                    CASE
                        WHEN Status IS NOT NULL THEN Status
                        WHEN TRY_CAST(IsExempt AS int) = 1 THEN 'EXEMPT'
                        ELSE NULL
                    END AS Status
                FROM dbo.EXEMPT_FROM_STATS
                WHERE GovernorID = ?
                {where_kvk}
                """
                cur.execute(sql, params)
                row = cur.fetchone()
                if not row:
                    return None
                try:
                    r = {
                        k: getattr(row, k)
                        for k in ("GovernorID", "GovernorName", "KVK_NO", "Exempt_Reason", "Status")
                    }
                except Exception:
                    r = {
                        "GovernorID": row[0],
                        "GovernorName": row[1] if len(row) > 1 else "",
                        "KVK_NO": row[2] if len(row) > 2 else 0,
                        "Exempt_Reason": row[3] if len(row) > 3 else "",
                        "Status": row[4] if len(row) > 4 else None,
                    }

                status_field = (r.get("Status") or "").strip().upper()
                if status_field == "EXEMPT":
                    return {
                        "status": "exempt",
                        "message": f"Governor {r.get('GovernorName','?')} is exempt: {r.get('Exempt_Reason','')}",
                    }
                return None
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        logger.exception("[TARGETS] _fallback_exempt_or_not_active failed")
        return None


# ---------------- Governor name lookup + autocomplete ----------------


async def lookup_governor_id(governor_name: str):
    """
    Returns:
      - {"status": "found", "data": {"GovernorName": ..., "GovernorID": ...}}
      - {"status": "fuzzy_matches", "matches": [ {GovernorName, GovernorID, score}, ... ]}
      - {"status": "not_found", "message": "..."}
    """
    logger.debug("[TARGET_UTILS] lookup_governor_id called for %r", governor_name)
    now_ts = int(time.time())
    # If cache is stale, refresh via SQL (async)
    if now_ts - _name_cache["last_updated"] > CACHE_DURATION_SECONDS or not _name_cache["rows"]:
        logger.debug("[TARGET_UTILS] cache stale or empty; calling refresh_name_cache_from_sql()")
        try:
            await refresh_name_cache_from_sql()
        except Exception:
            logger.exception("[CACHE] SQL name cache refresh failed (leaving existing cache)")

    # Log current cache state for diagnostics
    status = get_name_cache_status()
    logger.debug(
        "[TARGET_UTILS] name cache status: last_updated=%s rows=%d names=%d",
        status["last_updated"],
        status["rows_count"],
        status["names_count"],
    )

    input_norm = _normalize_name(governor_name)
    logger.debug("[TARGET_UTILS] normalized input: %r", input_norm)

    # Exact lookup via cached normalized map
    try:
        exact_row = _name_cache.get("norm_to_row", {}).get(input_norm)
        if exact_row:
            logger.debug("[TARGET_UTILS] exact match found for %r -> %s", governor_name, exact_row)
            return {
                "status": "found",
                "data": {
                    "GovernorName": str(exact_row["GovernorName"]),
                    "GovernorID": str(exact_row["GovernorID"]),
                },
            }
    except Exception:
        logger.exception("[CACHE] exact lookup failed; falling back to fuzzy")

    # Fuzzy matching fallback
    try:
        names_map = _name_cache.get("names", {})
        if not names_map:
            logger.debug("[TARGET_UTILS] name cache empty; returning not_found")
            return {"status": "not_found", "message": "No governor data available"}

        choices = list(names_map.keys())
        # If the normalized input is empty, return top suggestions (insertion order) limited by 8
        if not input_norm:
            logger.debug("[TARGET_UTILS] empty input; returning top names by insertion order")
            matches = []
            for norm in choices[:8]:
                row = _name_cache["norm_to_row"].get(norm)
                if row:
                    matches.append(
                        {
                            "GovernorName": row["GovernorName"],
                            "GovernorID": str(row["GovernorID"]),
                            "score": 100,
                        }
                    )
            return {"status": "fuzzy_matches", "matches": matches}

        results = process.extract(input_norm, choices, scorer=fuzz.WRatio, limit=8)
        matches = []
        for match_norm, score, _ in results:
            row = _name_cache["norm_to_row"].get(match_norm)
            if row:
                matches.append(
                    {
                        "GovernorName": str(row["GovernorName"]),
                        "GovernorID": str(row["GovernorID"]),
                        "score": int(score),
                    }
                )

        if matches:
            logger.debug("[TARGET_UTILS] fuzzy matches found: %d", len(matches))
            return {"status": "fuzzy_matches", "matches": matches}
    except Exception:
        logger.exception("[CACHE] fuzzy lookup failed")

    logger.debug("[TARGET_UTILS] no matches found")
    return {"status": "not_found", "message": "Governor not found in the database"}


# ---------------- Helper: robust interaction responder ----------------
async def _respond(
    inter: discord.Interaction, *, content=None, embed=None, view=None, ephemeral_flag=False
):
    """
    Robust send helper for interactive mode. Tries, in order:
      1) interaction.response.edit_message(...) — edits the message the component is attached to (preferred for component callbacks)
      2) interaction.edit_original_response(...) — edits the application command original response (fallback)
      3) interaction.followup.send(...) — send a followup message (last resort)

    The helper logs failures and does not propagate exceptions.
    """
    try:
        # 1) Prefer component-style edit (edits the message the component lives on).
        try:
            await inter.response.edit_message(content=content, embed=embed, view=view)
            return
        except Exception as e:
            logger.debug("[TARGET_UTILS] response.edit_message failed: %s", e)

        # 2) Fallback: try to edit the original application command response
        try:
            await inter.edit_original_response(content=content, embed=embed, view=view)
            return
        except Exception as e:
            logger.debug("[TARGET_UTILS] edit_original_response failed: %s", e)

        # 3) Final fallback: send a followup (requires interaction to have been acknowledged or deferred)
        try:
            await inter.followup.send(
                content=content, embed=embed, view=view, ephemeral=ephemeral_flag
            )
            return
        except Exception as e:
            logger.exception("[TARGET_UTILS] followup.send failed: %s", e)
    except Exception:
        logger.exception("[TARGET_UTILS] failed to send response to interaction")


# ---------------- New functions requested / compatibility ----------------


async def warm_name_cache() -> None:
    """
    Async helper that warms the in-memory name cache from SQL.
    This is a thin wrapper around refresh_name_cache_from_sql for backwards
    compatibility with previous code that called warm_name_cache().
    """
    try:
        await refresh_name_cache_from_sql()
    except Exception:
        logger.exception("[TARGET_UTILS] warm_name_cache failed")


async def autocomplete_governor_names(prefix: str, limit: int = 10) -> list[dict[str, str]]:
    """
    Provide lightweight autocomplete suggestions for governor names.

    Returns a list of dicts:
      [{"GovernorName": "<display name>", "GovernorID": "<id>"}...]

    Behavior:
      - If prefix is short, perform a startswith filter on the normalized names for best UX.
      - If not enough matches are found, fall back to fuzzy-scored matches (rapidfuzz),
        merging and deduplicating results.
    """
    # Ensure cache warmed
    now_ts = int(time.time())
    if now_ts - _name_cache["last_updated"] > CACHE_DURATION_SECONDS or not _name_cache["rows"]:
        try:
            await refresh_name_cache_from_sql()
        except Exception:
            logger.exception("[TARGET_UTILS] autocomplete: SQL cache refresh failed")

    prefix_norm = _normalize_name(prefix or "")

    names_map = _name_cache.get("names", {}) or {}
    norm_to_row = _name_cache.get("norm_to_row", {}) or {}

    results: list[dict[str, str]] = []
    seen_norms: set[str] = set()

    # Fast prefix matches for good UX
    if prefix_norm:
        for norm, display in names_map.items():
            if norm.startswith(prefix_norm):
                row = norm_to_row.get(norm)
                if row:
                    results.append(
                        {"GovernorName": row["GovernorName"], "GovernorID": str(row["GovernorID"])}
                    )
                    seen_norms.add(norm)
                    if len(results) >= limit:
                        return results

    # If not enough results, use fuzzy matching to supplement
    if len(results) < limit and names_map:
        choices = list(names_map.keys())
        fuzzy_limit = max(limit * 2, 8)
        try:
            fuzzy = process.extract(
                prefix_norm or "", choices, scorer=fuzz.WRatio, limit=fuzzy_limit
            )
            for match_norm, score, _ in fuzzy:
                if match_norm in seen_norms:
                    continue
                row = norm_to_row.get(match_norm)
                if row:
                    results.append(
                        {"GovernorName": row["GovernorName"], "GovernorID": str(row["GovernorID"])}
                    )
                    seen_norms.add(match_norm)
                    if len(results) >= limit:
                        break
        except Exception:
            logger.exception("[TARGET_UTILS] autocomplete fuzzy match failed")

    return results[:limit]


async def run_target_lookup(*args, **kwargs) -> dict[str, Any] | None:
    """
    Backwards-compatible run_target_lookup.

    Accepts either:
      - run_target_lookup(query: str)
      - run_target_lookup(interaction, query: str, ephemeral: bool=False)

    Two usage modes:
      - Non-interactive (no interaction arg): returns a dict with the lookup result.
      - Interactive (first arg is a discord Interaction): will RESPOND to the interaction
      (edit original response / followup) with an embed or a selectable disambiguation
      list. When acting interactively the function returns None after sending the UI.

    This preserves the legacy behaviour where Commands.py invoked this helper with
    an Interaction and expected the helper to produce the embed/select UI directly.
    """
    interaction = None
    ephemeral = bool(kwargs.get("ephemeral", False))
    query = None

    # Extract parameters supporting the old interaction-first signature
    if len(args) >= 2:
        first = args[0]
        second = args[1]
        if hasattr(first, "user") or hasattr(first, "response"):
            interaction = first
            query = second
            if len(args) >= 3:
                ephemeral = bool(args[2])
        else:
            query = first
    elif len(args) == 1:
        query = args[0]
    else:
        query = kwargs.get("query")

    if query is None:
        return {"status": "error", "message": "No query provided to run_target_lookup"}

    # If interactive, try to defer to ensure followups/edit message work
    if interaction:
        try:
            await interaction.response.defer(ephemeral=ephemeral)
        except Exception:
            # may already be deferred or impossible in some contexts; ignore and continue — _respond has fallbacks
            logger.debug(
                "[TARGET_UTILS] interaction.response.defer() raised or was not possible; continuing"
            )

    try:
        # numeric? treat as GovernorID
        if str(query).strip().isdigit():
            gid = int(str(query).strip())
            try:
                # Local import to avoid module-level cycles
                try:
                    from file_utils import run_maintenance_with_isolation  # type: ignore
                except Exception:
                    run_maintenance_with_isolation = None

                try:
                    from file_utils import run_blocking_in_thread
                except Exception:
                    run_blocking_in_thread = None

                if run_maintenance_with_isolation is not None:
                    res = await run_maintenance_with_isolation(
                        get_targets_for_governor,
                        gid,
                        name="get_targets_for_governor",
                        prefer_process=True,
                        meta={"governor_id": gid},
                    )
                    targets = (
                        res[0]
                        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict)
                        else res
                    )
                elif run_blocking_in_thread is not None:
                    targets = await run_blocking_in_thread(
                        get_targets_for_governor,
                        gid,
                        name="get_targets_for_governor",
                        meta={"governor_id": gid},
                    )
                else:
                    import asyncio as _asyncio

                    targets = await _asyncio.to_thread(get_targets_for_governor, gid)

                tgt = targets

                # ---- Attach last-KVK data (non-fatal) ----
                try:
                    # local import to avoid module-level cycles
                    from stats_cache_helpers import load_last_kvk_map

                    try:
                        last_map = await load_last_kvk_map()
                        if isinstance(last_map, dict):
                            lk = last_map.get(str(gid))
                            if lk and isinstance(tgt, dict):
                                tgt["last_kvk"] = lk
                    except Exception:
                        logger.debug(
                            "[TARGETS] load_last_kvk_map failed (continuing)", exc_info=True
                        )
                except Exception:
                    logger.debug("[TARGETS] stats_cache_helpers import failed (continuing)")

                if tgt:
                    if interaction:
                        kvk_ctx = get_kvk_context_today() or {}
                        kvk_name = kvk_ctx.get("kvk_name")
                        gov_name = tgt.get("GovernorName") or _name_cache.get("names", {}).get(
                            _normalize_name(tgt.get("GovernorName") or ""), "Governor"
                        )
                        embed = build_kvk_targets_embed(
                            gov_name=gov_name,
                            governor_id=gid,
                            targets=tgt,
                            kvk_name=kvk_name,
                        )
                        await _respond(
                            interaction,
                            embed=embed,
                            content=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                        return None
                    else:
                        return {"status": "found", "data": tgt}
                # no targets found, check exempt/not active
                fb = await _fallback_exempt_or_not_active(str(gid))
                if fb and fb.get("status") in ("exempt", "not_active"):
                    if interaction:
                        await _respond(
                            interaction,
                            content=fb.get("message", "No targets (exempt/not active)"),
                            embed=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                        return None
                    else:
                        return {
                            "status": "not_found",
                            "message": fb.get("message", "No targets (exempt/not active)"),
                        }
                if interaction:
                    await _respond(
                        interaction,
                        content="No targets found for that GovernorID",
                        embed=None,
                        view=None,
                        ephemeral_flag=ephemeral,
                    )
                    return None
                return {"status": "not_found", "message": "No targets found for that GovernorID"}
            except Exception:
                logger.exception("[TARGETS] get_targets_for_governor failed for id=%s", gid)
                if interaction:
                    await _respond(
                        interaction,
                        content="Internal error retrieving targets by ID",
                        embed=None,
                        view=None,
                        ephemeral_flag=ephemeral,
                    )
                    return None
                return {"status": "error", "message": "Internal error retrieving targets by ID"}

        # not numeric: name-based lookup
        lookup = await lookup_governor_id(query)
        if not lookup:
            if interaction:
                await _respond(
                    interaction,
                    content="No governor matches found",
                    embed=None,
                    view=None,
                    ephemeral_flag=ephemeral,
                )
                return None
            return {"status": "not_found", "message": "No governor matches found"}

        if lookup.get("status") == "found":
            gid = int(lookup["data"]["GovernorID"])
            try:
                try:
                    from file_utils import run_maintenance_with_isolation  # type: ignore
                except Exception:
                    run_maintenance_with_isolation = None

                try:
                    from file_utils import run_blocking_in_thread
                except Exception:
                    run_blocking_in_thread = None

                if run_maintenance_with_isolation is not None:
                    res = await run_maintenance_with_isolation(
                        get_targets_for_governor,
                        gid,
                        name="get_targets_for_governor",
                        prefer_process=True,
                        meta={"governor_id": gid},
                    )
                    targets = (
                        res[0]
                        if isinstance(res, tuple) and len(res) == 2 and isinstance(res[1], dict)
                        else res
                    )
                elif run_blocking_in_thread is not None:
                    targets = await run_blocking_in_thread(
                        get_targets_for_governor,
                        gid,
                        name="get_targets_for_governor",
                        meta={"governor_id": gid},
                    )
                else:
                    import asyncio as _asyncio

                    targets = await _asyncio.to_thread(get_targets_for_governor, gid)

                tgt = targets

                # ---- Attach last-KVK data (non-fatal) ----
                try:
                    from stats_cache_helpers import load_last_kvk_map

                    try:
                        last_map = await load_last_kvk_map()
                        if isinstance(last_map, dict):
                            lk = last_map.get(str(gid))
                            if lk and isinstance(tgt, dict):
                                tgt["last_kvk"] = lk
                    except Exception:
                        logger.debug(
                            "[TARGETS] load_last_kvk_map failed (continuing)", exc_info=True
                        )
                except Exception:
                    logger.debug("[TARGETS] stats_cache_helpers import failed (continuing)")

                if tgt:
                    if interaction:
                        kvk_ctx = get_kvk_context_today() or {}
                        kvk_name = kvk_ctx.get("kvk_name")
                        gov_name = lookup["data"].get("GovernorName") or "Governor"
                        embed = build_kvk_targets_embed(
                            gov_name=gov_name,
                            governor_id=gid,
                            targets=tgt,
                            kvk_name=kvk_name,
                        )
                        await _respond(
                            interaction,
                            embed=embed,
                            content=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                        return None
                    else:
                        return {"status": "found", "data": tgt}
                # no targets for found governor
                fb = await _fallback_exempt_or_not_active(str(gid))
                if fb and fb.get("status") in ("exempt", "not_active"):
                    if interaction:
                        await _respond(
                            interaction,
                            content=fb.get("message", "No targets (exempt/not active)"),
                            embed=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                        return None
                    return {
                        "status": "not_found",
                        "message": fb.get("message", "No targets (exempt/not active)"),
                    }
                if interaction:
                    await _respond(
                        interaction,
                        content="Governor found but no targets configured",
                        embed=None,
                        view=None,
                        ephemeral_flag=ephemeral,
                    )
                    return None
                return {
                    "status": "not_found",
                    "message": "Governor found but no targets configured",
                }
            except Exception:
                logger.exception("[TARGETS] get_targets_for_governor failed for id=%s", gid)
                if interaction:
                    await _respond(
                        interaction,
                        content="Internal error retrieving targets by GovernorID",
                        embed=None,
                        view=None,
                        ephemeral_flag=ephemeral,
                    )
                    return None
                return {
                    "status": "error",
                    "message": "Internal error retrieving targets by GovernorID",
                }

        elif lookup.get("status") == "fuzzy_matches":
            matches = lookup.get("matches", []) or []
            # Interactive: build select view to let user choose an account
            if interaction:

                class _KVKTargetsSelect(discord.ui.Select):
                    def __init__(self, options, ephemeral_flag: bool = False):
                        super().__init__(
                            placeholder="Choose an account to view…",
                            min_values=1,
                            max_values=1,
                            options=options,
                        )
                        self.ephemeral_flag = ephemeral_flag

                    async def callback(self, inter: discord.Interaction):
                        try:
                            chosen = self.values[0]
                            await run_target_lookup(inter, chosen, ephemeral=self.ephemeral_flag)
                        except Exception:
                            logger.exception("[TARGETS] _KVKTargetsSelect callback failed")
                            try:
                                await inter.followup.send(
                                    "Failed to process selection", ephemeral=self.ephemeral_flag
                                )
                            except Exception:
                                pass

                class _KVKTargetsView(discord.ui.View):
                    def __init__(
                        self, options, ephemeral_flag: bool = False, timeout: int | None = 300
                    ):
                        super().__init__(timeout=timeout)
                        self.add_item(_KVKTargetsSelect(options, ephemeral_flag=ephemeral_flag))

                sel_options = []
                for m in matches[:25]:  # cap for safety
                    name = m.get("GovernorName") or "Governor"
                    gid = str(m.get("GovernorID") or "")
                    label = f"{name} • {gid}"
                    sel_options.append(discord.SelectOption(label=label, value=gid))

                view = _KVKTargetsView(sel_options, ephemeral_flag=ephemeral, timeout=300)
                await _respond(
                    interaction,
                    content="Multiple matches found — choose one:",
                    embed=None,
                    view=view,
                    ephemeral_flag=ephemeral,
                )
                return None

            # Non-interactive: return the match list
            return {"status": "fuzzy_matches", "matches": matches}
        else:
            if interaction:
                await _respond(
                    interaction,
                    content=lookup.get("message", "Governor not found"),
                    embed=None,
                    view=None,
                    ephemeral_flag=ephemeral,
                )
                return None
            return {"status": "not_found", "message": lookup.get("message", "Governor not found")}
    except Exception as e:
        logger.exception("[TARGETS] run_target_lookup unexpected error: %s", e)
        if interaction:
            await _respond(
                interaction,
                content=f"Unexpected error: {type(e).__name__}: {e}",
                embed=None,
                view=None,
                ephemeral_flag=ephemeral,
            )
            return None
        return {"status": "error", "message": f"Unexpected error: {type(e).__name__}: {e}"}
