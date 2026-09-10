# target_utils.py (patched)
from __future__ import annotations

import asyncio
from collections.abc import Mapping
import logging
import time
from typing import Any

import discord
from rapidfuzz import fuzz, process
from unidecode import unidecode

# NOTE: _conn is the repo's SQL connection helper imported from constants
from kvk.dal import kvk_targets_dal
from kvk.models.kvk_target_row import TargetRow, serialize_target_row
from kvk.models.kvk_targets_card import KvkTargetsPresentationInput
from kvk.services.kvk_targets_card_service import build_kvk_targets_presentation_input
from targets_sql_cache import refresh_targets_cache

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
def sync_refresh_worker() -> dict[str, Any]:
    """
    Module-level wrapper that performs the synchronous refresh work that was
    previously implemented as a nested function. Being module-level allows
    the maintenance subprocess to import and call it via 'target_utils:sync_refresh_worker'.
    """
    try:
        logger.debug("[TARGET_UTILS] Starting SQL name cache refresh (module-level worker)")
        fetched = kvk_targets_dal.fetch_governor_lookup_rows()
        name_map: dict[str, str] = {}
        norm_to_row: dict[str, dict[str, Any]] = {}
        rows: list[dict[str, Any]] = []
        for raw_row in fetched:
            try:
                gov_id = int(raw_row.get("GovernorID"))
                original = str(raw_row.get("GovernorName") or "").strip()
            except (TypeError, ValueError, OverflowError):
                continue
            if not original:
                continue
            norm = _normalize_name(original)
            row = {
                "GovernorName": original,
                "GovernorID": str(gov_id),
                "CityHallLevel": raw_row.get("CityHallLevel"),
            }
            if norm not in norm_to_row:
                norm_to_row[norm] = row
                name_map[norm] = original
            rows.append(row)

        _name_cache["names"] = name_map
        _name_cache["norm_to_row"] = norm_to_row
        _name_cache["rows"] = rows
        _name_cache["last_updated"] = int(time.time())
        logger.info("[TARGET_UTILS] Name cache refreshed from SQL (%d rows)", len(rows))
        return {
            "names": name_map,
            "norm_to_row": norm_to_row,
            "rows": rows,
            "last_updated": _name_cache["last_updated"],
        }
    except Exception:
        logger.exception("[TARGET_UTILS] sync_refresh_worker failed")
        raise


# --- Back-compat shim for older imports (e.g., processing_pipeline.py) ---
async def warm_target_cache() -> None:
    """
    Legacy async wrapper kept for compatibility.
    Uses the target-domain repository through the compatibility refresh entrypoint.
    Process and in-thread callers share the same bounded durable single-flight lease.
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
    Refresh the in-memory name cache from SQL.
    Runs sync_refresh_worker in a thread (not a subprocess) so that
    _name_cache mutations happen in the parent process directly.
    """
    try:
        try:
            from file_utils import run_blocking_in_thread

            await run_blocking_in_thread(
                sync_refresh_worker,
                name="refresh_name_cache_from_sql",
                meta={"source": "vw_All_Governors_Clean"},
            )
        except ImportError:
            await asyncio.to_thread(sync_refresh_worker)
    except Exception:
        logger.warning("[TARGET_UTILS] refresh_name_cache_from_sql failed; keeping existing cache")


async def lookup_governor_row_by_id(governor_id: str | int) -> dict[str, Any] | None:
    """
    Return the cached governor row for a numeric GovernorID, warming the cache if needed.

    Command and view code should use this public helper instead of reading the
    private _name_cache structure directly.
    """
    gid = str(governor_id or "").strip()
    if not gid or not gid.isdigit():
        return None

    rows = _name_cache.get("rows", []) if isinstance(_name_cache, dict) else []
    if not rows:
        try:
            await refresh_name_cache_from_sql()
        except Exception:
            logger.exception("[TARGET_UTILS] lookup_governor_row_by_id cache warm failed")

    rows = _name_cache.get("rows", []) if isinstance(_name_cache, dict) else []
    for row in rows:
        if str(row.get("GovernorID", "")).strip() == gid:
            return dict(row)
    return None


# Small diagnostic helper to inspect cache state (useful in logs / REPL)
def get_name_cache_status() -> dict[str, Any]:
    return {
        "last_updated": _name_cache.get("last_updated", 0),
        "rows_count": len(_name_cache.get("rows") or []),
        "names_count": len(_name_cache.get("names") or {}),
    }


def get_name_cache_rows() -> list[dict[str, Any]]:
    """Return a copy of cached governor rows for service-layer search helpers."""
    rows = _name_cache.get("rows", []) if isinstance(_name_cache, dict) else []
    return [dict(row) for row in rows if isinstance(row, dict)]


_LEGACY_TARGET_ALIASES: dict[str, tuple[str, ...]] = {
    "GovernorID": ("governor_id", "Governor ID", "Governor_ID", "Gov_ID"),
    "GovernorName": ("governor_name", "Governor Name", "Governor_Name"),
    "Power": ("power", "Starting Power"),
    "DKP_Target": ("DKP Target", "DKPTarget", "dkp_target"),
    "Kill_Target": ("Kill Target", "KillTarget", "kill_target"),
    "Deads_Target": ("Dead_Target", "Dead Target", "DeadTarget", "deads_target"),
    "Min_Kill_Target": (
        "Minimum_Kill_Target",
        "Min Kill Target",
        "Min Kills",
        "min_kill_target",
    ),
    "TargetRank": ("Target Rank", "target_rank"),
    "KVK_NO": ("KVK NO", "kvk_no", "KVK"),
}

_LEGACY_TARGET_CONTEXT_FIELDS = (
    "TargetState",
    "PublicationReason",
    "TargetSourceScan",
    "TargetSourceType",
    "TargetPublishedAt",
    "PublicationVersion",
    "PublicationSignature",
    "last_kvk",
)


def adapt_target_row_for_legacy(
    row: TargetRow | Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Confine legacy target aliases to the fallback compatibility path.

    Canonical values always win when a mapping contains both a canonical key and
    one or more historical aliases.
    """
    if row is None:
        return None
    if isinstance(row, TargetRow):
        return serialize_target_row(row)
    if not isinstance(row, Mapping):
        return None

    result: dict[str, Any] = {}
    for canonical, aliases in _LEGACY_TARGET_ALIASES.items():
        if canonical in row:
            result[canonical] = row[canonical]
            continue
        for alias in aliases:
            if alias in row:
                result[canonical] = row[alias]
                break
    for field in _LEGACY_TARGET_CONTEXT_FIELDS:
        if field in row:
            result[field] = row[field]
    return result


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


async def autocomplete_governor_names(ctx: discord.AutocompleteContext):
    """
    Canonical Discord autocomplete callback for governor names.

    Returns OptionChoice items whose:
      - name is "GovernorName (GovernorID)"
      - value is the GovernorID string
    """
    try:
        q = (ctx.value or "").strip()
        if len(q) < 2:
            return []

        try:
            OptionChoice = discord.OptionChoice
        except AttributeError:
            from discord import OptionChoice

        # Ensure cache is populated before searching
        now_ts = int(time.time())
        if now_ts - _name_cache["last_updated"] > CACHE_DURATION_SECONDS or not _name_cache["rows"]:
            try:
                await refresh_name_cache_from_sql()
            except Exception:
                logger.exception("[TARGET_UTILS] autocomplete: SQL cache refresh failed")

        prefix_norm = _normalize_name(q)
        names_map = _name_cache.get("names", {}) or {}
        norm_to_row = _name_cache.get("norm_to_row", {}) or {}

        results: list[tuple[str, str]] = []
        seen_norms: set[str] = set()

        # Fast prefix matches for best UX
        if prefix_norm:
            for norm in names_map.keys():
                if norm.startswith(prefix_norm):
                    row = norm_to_row.get(norm)
                    if row:
                        results.append(
                            (f"{row['GovernorName']} ({row['GovernorID']})", str(row["GovernorID"]))
                        )
                        seen_norms.add(norm)
                        if len(results) >= 25:
                            break

        # If not enough results, use fuzzy matching to supplement
        if len(results) < 25 and names_map:
            choices = list(names_map.keys())
            fuzzy_limit = 50
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
                            (f"{row['GovernorName']} ({row['GovernorID']})", str(row["GovernorID"]))
                        )
                        seen_norms.add(match_norm)
                        if len(results) >= 25:
                            break
            except Exception:
                logger.exception("[TARGET_UTILS] autocomplete fuzzy match failed")

        return [OptionChoice(name=label, value=value) for label, value in results[:25]]

    except Exception:
        # Fail quietly to avoid breaking the slash UI
        return []


def _legacy_data_from_presentation(
    result: KvkTargetsPresentationInput,
) -> dict[str, Any] | None:
    row = adapt_target_row_for_legacy(result.target_row)
    if row is None:
        return None
    payload = result.payload
    row.update(
        {
            "TargetState": payload.publication_state,
            "PublicationReason": payload.publication_reason,
            "TargetSourceScan": payload.target_source_scan,
            "TargetSourceType": payload.target_source_type,
            "TargetPublishedAt": payload.target_published_at,
            "PublicationVersion": payload.publication_version,
            "PublicationSignature": payload.publication_signature,
        }
    )
    if result.last_kvk:
        row["last_kvk"] = dict(result.last_kvk)
    return row


def _legacy_missing_result(result: KvkTargetsPresentationInput) -> dict[str, Any]:
    payload = result.payload
    if payload.progress_state == "exempt":
        message = f"Governor {payload.governor_name} is exempt from KVK targets."
    elif payload.progress_state == "missing_governor":
        message = payload.status_detail
    else:
        message = "No targets found for that GovernorID"
    return {"status": "not_found", "message": message}


async def _send_legacy_target_payload(
    interaction: discord.Interaction,
    result: KvkTargetsPresentationInput,
    *,
    ephemeral: bool,
) -> None:
    from targets_embed import build_targets_fallback_embed

    await _respond(
        interaction,
        embed=build_targets_fallback_embed(result.payload),
        content=None,
        view=None,
        ephemeral_flag=ephemeral,
    )


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
            gid = str(query).strip()
            try:
                result = await build_kvk_targets_presentation_input(gid)
                legacy_data = _legacy_data_from_presentation(result)
                if interaction:
                    if legacy_data is not None:
                        await _send_legacy_target_payload(
                            interaction,
                            result,
                            ephemeral=ephemeral,
                        )
                    else:
                        missing = _legacy_missing_result(result)
                        await _respond(
                            interaction,
                            content=missing["message"],
                            embed=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                    return None
                if legacy_data is not None:
                    return {"status": "found", "data": legacy_data}
                return _legacy_missing_result(result)
            except Exception:
                logger.exception("[TARGETS] target service failed for id=%s", gid)
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
            gid = str(lookup["data"]["GovernorID"])
            try:
                result = await build_kvk_targets_presentation_input(gid)
                legacy_data = _legacy_data_from_presentation(result)
                if interaction:
                    if legacy_data is not None:
                        await _send_legacy_target_payload(
                            interaction,
                            result,
                            ephemeral=ephemeral,
                        )
                    else:
                        missing = _legacy_missing_result(result)
                        message = (
                            missing["message"]
                            if result.payload.progress_state == "exempt"
                            else "Governor found but no targets configured"
                        )
                        await _respond(
                            interaction,
                            content=message,
                            embed=None,
                            view=None,
                            ephemeral_flag=ephemeral,
                        )
                    return None
                if legacy_data is not None:
                    return {"status": "found", "data": legacy_data}
                missing = _legacy_missing_result(result)
                if result.payload.progress_state != "exempt":
                    missing["message"] = "Governor found but no targets configured"
                return missing
            except Exception:
                logger.exception("[TARGETS] target service failed for id=%s", gid)
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
            if interaction:
                from ui.views.kvk_personal_views import KvkTargetsLookupSelectView

                sel_options = []
                for m in matches[:25]:  # cap for safety
                    name = m.get("GovernorName") or "Governor"
                    gid = str(m.get("GovernorID") or "")
                    label = f"{name} • {gid}"
                    sel_options.append(discord.SelectOption(label=label, value=gid))

                view = KvkTargetsLookupSelectView(
                    sel_options,
                    on_select=run_target_lookup,
                    ephemeral=ephemeral,
                    timeout=300,
                )
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
