# target_utils.py (refactored)
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

import time
from typing import Any

import discord
from google.oauth2.service_account import Credentials
import gspread_asyncio
from rapidfuzz import fuzz, process
from unidecode import unidecode

from constants import CREDENTIALS_FILE, KVK_SHEET_ID, _conn
from kvk_state import get_kvk_context_today
from targets_embed import build_kvk_targets_embed  # new unified look
from targets_sql_cache import get_targets_for_governor, refresh_targets_cache

# ---------------- Name cache (unchanged) ----------------

_name_cache = {
    "names": {},  # normalized -> original (for autocomplete)
    "last_updated": 0,
    "rows": [],  # full ALL_COMMANDERS rows
}
CACHE_DURATION_SECONDS = 86400  # 24h


def get_creds():
    return Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )


# --- Back-compat shim for older imports (e.g., processing_pipeline.py) ---
async def warm_target_cache() -> None:
    """
    Legacy async wrapper kept for compatibility.
    Uses the new SQL-backed cache refresher under the hood.
    """
    try:
        # run the sync refresher off the event loop
        await asyncio.to_thread(refresh_targets_cache)
    except Exception:
        logger.exception("[TARGET_UTILS] warm_target_cache() failed")


# ---------------- Targets: EXEMPT/NOT ACTIVE fallback (still via GSheets) ----------------


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

        with _conn() as conn, conn.cursor() as cur:
            # We accept either current KVK, or global (0), or NULL if present
            params = [int(governor_id)]
            where_kvk = ""
            if current_kvk_no is not None:
                where_kvk = "AND (KVK_NO = ? OR KVK_NO = 0 OR KVK_NO IS NULL)"
                params.append(int(current_kvk_no))
            else:
                where_kvk = "AND (KVK_NO = 0 OR KVK_NO IS NULL)"

            cur.execute(
                f"""
                SELECT
                    GovernorID,
                    COALESCE(GovernorName, '') AS GovernorName,
                    COALESCE(CAST(KVK_NO AS int), 0) AS KVK_NO,
                    COALESCE(Exempt_Reason, '') AS Exempt_Reason,
                    -- support multiple schema variants defensively:
                    CASE
                        WHEN Status IS NOT NULL THEN Status
                        WHEN TRY_CAST(IsExempt AS int) = 1 THEN 'EXEMPT'
                        WHEN TRY_CAST(NotActive AS int) = 1 THEN 'NOT_ACTIVE'
                        ELSE NULL
                    END AS StatusNorm
                FROM dbo.EXEMPT_FROM_STATS
                WHERE GovernorID = ?
                  {where_kvk}
            """,
                params,
            )

            rows = cur.fetchall()

        if not rows:
            return None

        # Prefer a row explicitly matching current KVK if present; otherwise fall back to global.
        def _row_state(r) -> str | None:
            # r columns: GovernorID, GovernorName, KVK_NO, Exempt_Reason, StatusNorm
            status = (r[4] or "").strip().upper()
            reason = (r[3] or "").strip()
            if status in ("EXEMPT", "NOT_ACTIVE"):
                return status
            # Heuristic: if there’s a reason but no explicit flags, treat as EXEMPT
            if reason:
                return "EXEMPT"
            return None

        # Prioritize selection by KVK specificity
        preferred = None
        fallback = None
        for r in rows:
            state = _row_state(r)
            if not state:
                continue
            kvk_no = int(r[2] or 0)
            if current_kvk_no is not None and kvk_no == current_kvk_no:
                preferred = r
                break
            if kvk_no in (0, None):  # global
                fallback = r

        use = preferred or fallback
        if not use:
            return None

        gov_name = (use[1] or "Governor").strip() or "Governor"
        reason = (use[3] or "").strip()
        state = _row_state(use)

        if state == "EXEMPT":
            msg = f"{gov_name} – Exempt from targets" + (f": Reason - {reason}" if reason else ".")
            return {"status": "exempt", "message": msg}

        if state == "NOT_ACTIVE":
            return {
                "status": "not_active",
                "message": f"{gov_name} – Not active during MatchMaking therefore no target set.",
            }

        return None

    except Exception:
        logger.exception("[TARGET_UTILS] SQL EXEMPT/NOT_ACTIVE check failed.")
        return None


# ---------------- Public helpers used by commands/UI ----------------


async def run_target_lookup(
    interaction: discord.Interaction, governor_id: str, ephemeral: bool = False
):
    """Main flow used by /mykvktargets (and selector UI). Always shows targets if present:
    - DRAFT before KVK start (from next_kvk table if available)
    - ACTIVE during KVK
    - ENDED after KVK (last KVK table)
    """
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=ephemeral)

    gid = (governor_id or "").strip()
    if not gid.isdigit():
        await interaction.edit_original_response(
            content="❌ Invalid Governor ID. Please enter numbers only."
        )
        return

    try:
        governor_id_int = int(gid)

        # 1) Try SQL-backed cache first
        tgt = get_targets_for_governor(governor_id_int)
        if not tgt:
            # one refresh attempt (e.g., first call after restart)
            refresh_targets_cache()
            tgt = get_targets_for_governor(governor_id_int)

        if tgt:
            # Optional: low-power courtesy message (if Power present)
            try:
                power = tgt.get("Power")
                if isinstance(power, int) and power < 40_000_000:
                    await interaction.edit_original_response(
                        content=f"{tgt.get('GovernorName','Governor')} – Power too low, just do what you can!",
                        embed=None,
                        view=None,
                    )
                    return
            except Exception:
                pass

            ctx = get_kvk_context_today()
            kvk_name = ctx["kvk_name"] if ctx else None

            embed = build_kvk_targets_embed(
                gov_name=tgt.get("GovernorName") or "Governor",
                governor_id=governor_id_int,
                targets=tgt,
                kvk_name=kvk_name,
            )
            await interaction.edit_original_response(content=None, embed=embed, view=None)
            return

        # 2) Fallback paths (EXEMPT / NOT ACTIVE / NOT FOUND)
        fb = await _fallback_exempt_or_not_active(gid)
        if fb:
            if fb["status"] in ("exempt", "not_active"):
                await interaction.edit_original_response(
                    content=fb["message"], embed=None, view=None
                )
                return

        await interaction.edit_original_response(
            content="Governor ID not found in the database, please check and try again.",
            embed=None,
            view=None,
        )

    except Exception as e:
        logger.exception("[/mykvktargets] lookup failed for gid=%s", gid)
        await interaction.edit_original_response(
            content=f"❌ Error:\n```{type(e).__name__}: {e}```", view=None
        )


# ---------------- Governor name lookup + autocomplete (unchanged) ----------------


async def lookup_governor_id(governor_name: str):
    now = time.time()
    if now - _name_cache["last_updated"] > CACHE_DURATION_SECONDS or not _name_cache["rows"]:
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        client = await agcm.authorize()
        kvk_list_doc = await client.open_by_key(KVK_SHEET_ID)
        commanders_ws = await kvk_list_doc.worksheet("ALL_COMMANDERS")
        commanders = await commanders_ws.get_all_records()

        name_map = {
            unidecode(str(row["GovernorName"]).strip().lower()): str(row["GovernorName"]).strip()
            for row in commanders
            if "GovernorName" in row
        }
        _name_cache["names"] = name_map
        _name_cache["rows"] = commanders
        _name_cache["last_updated"] = now
    else:
        commanders = _name_cache["rows"]

    input_norm = unidecode(str(governor_name).strip().lower())

    # Exact first
    for row in commanders:
        if unidecode(str(row.get("GovernorName", "")).strip().lower()) == input_norm:
            return {
                "status": "found",
                "data": {
                    "GovernorName": str(row["GovernorName"]),
                    "GovernorID": str(row["GovernorID"]),
                },
            }

    # Fuzzy fallback
    name_to_row = {
        str(r["GovernorName"]).strip(): r
        for r in commanders
        if "GovernorName" in r and "GovernorID" in r
    }
    names_list = list(name_to_row.keys())
    matches = process.extract(
        query=input_norm,
        choices=[unidecode(n.lower()) for n in names_list],
        scorer=fuzz.token_sort_ratio,
        limit=10,
    )

    # Map back to originals
    original_map = {unidecode(n.lower()): n for n in names_list}
    if not matches:
        return {
            "status": "not_found",
            "message": "❌ Governor Name not found. Please check your spelling and try again.",
        }

    match_data = []
    for norm_name, score, _ in matches:
        original = original_map.get(norm_name)
        if not original:
            continue
        row = name_to_row[original]
        match_data.append(
            {
                "GovernorName": str(row["GovernorName"]),
                "GovernorID": str(row["GovernorID"]),
                "score": score,
            }
        )

    return {"status": "fuzzy_matches", "matches": match_data}


async def autocomplete_governor_names(ctx: discord.AutocompleteContext):
    current = (ctx.value or "").strip()
    if len(current) < 2:
        return []

    name_map = _name_cache.get("names", {})
    if not name_map:
        return []

    try:
        matches = process.extract(
            unidecode(current.lower()),
            list(name_map.keys()),
            scorer=fuzz.token_sort_ratio,
            limit=20,
        )
        # convert back to original names
        return [
            discord.OptionChoice(name=_name_cache["names"][k], value=_name_cache["names"][k])
            for k, score, _ in matches
            if score > 50
        ][:15]
    except Exception:
        return []


async def warm_name_cache():
    try:
        agcm = gspread_asyncio.AsyncioGspreadClientManager(get_creds)
        client = await agcm.authorize()
        kvk_list_doc = await client.open_by_key(KVK_SHEET_ID)
        commanders_ws = await kvk_list_doc.worksheet("ALL_COMMANDERS")
        commanders = await commanders_ws.get_all_records()

        name_map = {
            unidecode(str(row["GovernorName"]).strip().lower()): str(row["GovernorName"]).strip()
            for row in commanders
            if "GovernorName" in row
        }
        _name_cache["names"] = name_map
        _name_cache["rows"] = commanders
        _name_cache["last_updated"] = time.time()
    except Exception as e:
        logger.exception("[CACHE] Failed to warm name cache: %s", e)
