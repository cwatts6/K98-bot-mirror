# stats_alerts/embeds/kvk.py
"""
KVK embed builder/sender (async-safe).

Splits output into two embeds:
  - Embed 1 (orange): our kingdom highlights, metadata, quick commands, links
  - Embed 2 (aqua): overall KVK performance lists (Top 5)

Changes in this revision:
- Send both embeds together in a single channel.send(...) with embeds=[e1, e2]
  so they appear as a single grouped message.
- Add truncation safeguards for embed field values (Discord limit: 1024 chars).
  Truncation events are logged with logger.warning so they can be investigated.
- Embed 2 color set to Aqua (RGB 0,255,255).
- Top lists render Top 5 (medals for 1..3, numeric labels for 4..5).
- Include KP and healed troops metric alongside kills/deads/dkp for players, kingdoms and camps.
- Fixed KP field naming: changed from 'kp' to 'kp_gain' to match SQL query output
- Fixed DKP calculation: removed division by starting power, now using abbr() instead of fmt_dkp()
- Added blank line between Top 5 kills and kingdom kills for better readability
"""

import asyncio
import logging
from typing import Any

import discord

from constants import CUSTOM_AVATAR_URL, KVK_BANNER_MAP, STATS_SHEET_ID
from stats_alerts.allkingdoms import load_allkingdom_blocks
from stats_alerts.delivery_outcomes import delivery_outcome
from stats_alerts.formatters import abbr
from stats_alerts.honors import get_latest_honor_top
from stats_alerts.kvk_meta import (
    get_kvk_metadata_sql,
    get_latest_kvk_metadata,
    get_latest_kvk_metadata_sql,
)

logger = logging.getLogger(__name__)

# Try once to import the centralized helper so we can use it consistently.
try:
    from file_utils import run_blocking_in_thread  # type: ignore
except Exception:
    run_blocking_in_thread = None  # type: ignore


def _truncate_and_log(field_name: str, text: str, max_len: int = 1024) -> str:
    """
    Truncate `text` to `max_len` characters if needed and log a warning.
    Discord embed field value max length is 1024.
    """
    if text is None:
        return "—"
    try:
        if len(text) > max_len:
            logger.warning(
                "[KVK EMBED] Field '%s' truncated from %d to %d characters",
                field_name,
                len(text),
                max_len,
            )
            # keep room for ellipsis
            return text[: max_len - 1] + "…"
    except Exception:
        # If len() fails for any weird reason, fall back to str() and truncate
        t = str(text)
        if len(t) > max_len:
            logger.warning(
                "[KVK EMBED] Field '%s' truncated (fallback) from %d to %d characters",
                field_name,
                len(t),
                max_len,
            )
            return t[: max_len - 1] + "…"
        return t
    return text


def _fmt_top_list(
    rows: list[dict],
    name_key: str,
    kills_key: str = "kills_gain",
    limit: int = 5,
    *,
    kp_key: str | None = None,
    deads_key: str = "deads",
    dkp_key: str = "dkp",
    healed_key: str | None = None,
) -> str:
    """
    Format top-N rows as lines with the requested fields in this order:
    Kills, KP, deads, dkp, healed.
    Example line:
      🥇 Alice — Kills:12.3k | KP: 92.3k | deads: 20k | dkp: 12k | healed: 45k
    """
    if not rows:
        return "—"
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, r in enumerate(rows[:limit]):
        label = medals[i] if i < 3 else f"{i+1}."
        n = r.get(name_key) or r.get("name") or "Unknown"

        # Kills
        k = r.get(kills_key)
        try:
            k_s = abbr(k)
        except Exception:
            k_s = str(k)

        parts = [f"Kills:{k_s}"]

        # KP
        if kp_key:
            kp = r.get(kp_key)
            try:
                kp_s = abbr(kp)
            except Exception:
                kp_s = str(kp)
            parts.append(f"KP: {kp_s}")

        # deads
        d = r.get(deads_key)
        try:
            d_s = abbr(d)
        except Exception:
            d_s = str(d)
        parts.append(f"deads: {d_s}")

        # dkp (now using abbr instead of fmt_dkp)
        dk = r.get(dkp_key)
        try:
            dk_s = abbr(dk)
        except Exception:
            dk_s = str(dk)
        parts.append(f"dkp: {dk_s}")

        # healed
        if healed_key:
            h = r.get(healed_key)
            try:
                h_s = abbr(h)
            except Exception:
                h_s = str(h)
            parts.append(f"healed: {h_s}")

        line = f"{label} {n} — " + " | ".join(parts)
        lines.append(line)
    return "\n".join(lines)


async def build_kvk_preview(
    timestamp: str, *, kvk_no: int | None = None, source_selection=None, connect=None
):
    from stats_alerts.kvk_diagnostics import PreviewPayload

    if source_selection is not None:
        from kvk.schemas.new_source_schema import SOURCE_KEY
        from stats_alerts.allkingdoms import load_allkingdom_report_v2

        if source_selection.get("source_key") != SOURCE_KEY or connect is None:
            raise ValueError("Explicit source selection and connection provider required.")
        report = await asyncio.to_thread(
            load_allkingdom_report_v2,
            kvk_no,
            connect=connect,
            period_id=source_selection["period_id"],
            publication_id=source_selection["publication_id"],
        )
        return build_source_preview(report)

    selected_kvk = kvk_no
    if selected_kvk is not None and (
        type(selected_kvk) is not int or not 1 <= selected_kvk <= 2147483647
    ):
        raise ValueError("Invalid KVK selection")
    # Prefer SQL metadata (blocking) -> offload
    try:
        if selected_kvk is not None:
            if run_blocking_in_thread is not None:
                meta_sql = await run_blocking_in_thread(
                    get_kvk_metadata_sql,
                    selected_kvk,
                    name="get_selected_kvk_metadata_sql",
                    meta={"kvk_no": selected_kvk},
                )
            else:
                meta_sql = await asyncio.to_thread(get_kvk_metadata_sql, selected_kvk)
        elif run_blocking_in_thread is not None:
            meta_sql = await run_blocking_in_thread(
                get_latest_kvk_metadata_sql,
                name="get_latest_kvk_metadata_sql",
                meta={"caller": "stats_alerts.embeds.kvk.send_kvk_embed"},
            )
        else:
            logger.debug(
                "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for get_latest_kvk_metadata_sql (consider converting to run_blocking_in_thread)"
            )
            meta_sql = await asyncio.to_thread(get_latest_kvk_metadata_sql)
    except Exception:
        if selected_kvk is None:
            logger.exception("[KVK EMBED] get_latest_kvk_metadata_sql failed")
        else:
            logger.exception("[KVK EMBED] SQL metadata failed selected_kvk=%s", selected_kvk)
        meta_sql = None

    if selected_kvk is not None and (not meta_sql or meta_sql.get("kvk_no") != selected_kvk):
        return PreviewPayload(
            [],
            False,
            f"KVK {selected_kvk} SQL metadata unavailable; no fallback or publication.",
            "",
        )

    if meta_sql and (
        selected_kvk is not None or (meta_sql.get("start_date") and meta_sql.get("end_date"))
    ):
        kvk_no = meta_sql["kvk_no"]
        kvk_name = meta_sql["kvk_name"]
        start_dt, end_dt = meta_sql["start_date"], meta_sql["end_date"]
        try:
            kvk_date_range = f"{start_dt:%d %b} – {end_dt:%d %b}"
        except Exception:
            kvk_date_range = ""
        banner_url = KVK_BANNER_MAP.get((kvk_name or "KVK").lower(), None)
    else:
        # sheets fallback (blocking) -> offload
        try:
            if run_blocking_in_thread is not None:
                meta = await run_blocking_in_thread(
                    get_latest_kvk_metadata,
                    name="get_latest_kvk_metadata_sheets",
                    meta={"caller": "stats_alerts.embeds.kvk.send_kvk_embed"},
                )
            else:
                logger.debug(
                    "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for get_latest_kvk_metadata (consider converting to run_blocking_in_thread)"
                )
                meta = await asyncio.to_thread(get_latest_kvk_metadata)
        except Exception:
            logger.exception("[KVK EMBED] get_latest_kvk_metadata (sheets) failed")
            meta = None

        if meta:
            kvk_no = meta["kvk_no"]
            kvk_name = meta["kvk_name"]
            kvk_date_range = f"{meta['start_date']} – {meta['end_date']}"
            banner_url = KVK_BANNER_MAP.get(kvk_name.lower(), None)
        else:
            kvk_no = "?"
            kvk_name = "KVK"
            kvk_date_range = ""
            banner_url = None

    # Load heavy all-kingdom blocks off-thread
    try:
        if run_blocking_in_thread is not None:
            blocks = await run_blocking_in_thread(
                load_allkingdom_blocks,
                kvk_no,
                name="load_allkingdom_blocks",
                meta={"kvk_no": kvk_no},
            )
        else:
            logger.debug(
                "[KVK EMBED] run_blocking_in_thread not available; using asyncio.to_thread fallback for load_allkingdom_blocks (consider converting to run_blocking_in_thread)"
            )
            blocks = await asyncio.to_thread(load_allkingdom_blocks, kvk_no)
    except Exception:
        logger.exception("[KVK EMBED] Failed to load all kingdom blocks")
        blocks = {
            "players_by_kills": [],
            "players_by_deads": [],
            "players_by_dkp": [],
            "kingdoms_by_kills": [],
            "kingdoms_by_deads": [],
            "kingdoms_by_dkp": [],
            "camps_by_kills": [],
            "camps_by_deads": [],
            "camps_by_dkp": [],
            "our_top_players": [],
            "our_kingdom": [],
            "our_camp": [],
        }

    # Include KP and healed_troops in top lists where available - using 'kp_gain' instead of 'kp'
    players_kills = _fmt_top_list(
        blocks.get("players_by_kills", []),
        name_key="name",
        kills_key="kills_gain",
        limit=5,
        kp_key="kp_gain",
        deads_key="deads",
        dkp_key="dkp",
        healed_key="healed_troops",
    )
    kingdoms_kills = _fmt_top_list(
        blocks.get("kingdoms_by_kills", []),
        name_key="kingdom",
        kills_key="kills_gain",
        limit=5,
        kp_key="kp_gain",
        deads_key="deads",
        dkp_key="dkp",
        healed_key="healed_troops",
    )
    camps_kills = _fmt_top_list(
        blocks.get("camps_by_kills", []),
        name_key="camp_name",
        kills_key="kills_gain",
        limit=5,
        kp_key="kp_gain",
        deads_key="deads",
        dkp_key="dkp",
        healed_key="healed_troops",
    )

    our_topk = blocks.get("our_top_players", []) or []
    our_lines = []
    # Our Top players block (Top 5) — formatted with Kills, KP, deads, dkp, healed
    if our_topk:
        top_players_block = _fmt_top_list(
            our_topk,
            name_key="name",
            kills_key="kills_gain",
            limit=5,
            kp_key="kp_gain",
            deads_key="deads",
            dkp_key="dkp",
            healed_key="healed_troops",
        )
        our_lines.append("**1198 Top 5 (Kills):**\n" + top_players_block)

    our_king = blocks.get("our_kingdom")[0] if blocks.get("our_kingdom") else None
    our_camp = blocks.get("our_camp")[0] if blocks.get("our_camp") else None

    if our_king:
        try:
            k_kills = abbr(our_king.get("kills_gain"))
        except Exception:
            k_kills = str(our_king.get("kills_gain"))
        try:
            k_kp = abbr(our_king.get("kp_gain"))
        except Exception:
            k_kp = str(our_king.get("kp_gain"))
        try:
            k_deads = abbr(our_king.get("deads"))
        except Exception:
            k_deads = str(our_king.get("deads"))
        try:
            k_dkp = abbr(our_king.get("dkp"))
        except Exception:
            k_dkp = str(our_king.get("dkp"))
        try:
            k_healed = abbr(our_king.get("healed_troops"))
        except Exception:
            k_healed = str(our_king.get("healed_troops"))
        # Add blank line before kingdom stats to separate from Top 5 players
        our_lines.append("")
        our_lines.append(
            f"👑 **Kingdom:** kills `{k_kills}` | KP: `{k_kp}` | deads `{k_deads}` | dkp `{k_dkp}` | healed `{k_healed}`"
        )

    if our_camp:
        try:
            c_kills = abbr(our_camp.get("kills_gain"))
        except Exception:
            c_kills = str(our_camp.get("kills_gain"))
        try:
            c_kp = abbr(our_camp.get("kp_gain"))
        except Exception:
            c_kp = str(our_camp.get("kp_gain"))
        try:
            c_deads = abbr(our_camp.get("deads"))
        except Exception:
            c_deads = str(our_camp.get("deads"))
        try:
            c_dkp = abbr(our_camp.get("dkp"))
        except Exception:
            c_dkp = str(our_camp.get("dkp"))
        try:
            c_healed = abbr(our_camp.get("healed_troops"))
        except Exception:
            c_healed = str(our_camp.get("healed_troops"))
        our_lines.append(
            f"🏕️ **{our_camp.get('camp_name','Our Camp')}:** kills `{c_kills}` | KP: `{c_kp}` | deads `{c_deads}` | dkp `{c_dkp}` | healed `{c_healed}`"
        )

    our_block = "\n".join(our_lines) if our_lines else "—"

    # Honor Top-5 (get_latest_honor_top may return fewer; format as Top 5 if available)
    honor_top = []
    try:
        if selected_kvk is None:
            honor_top = await get_latest_honor_top(5)
    except Exception:
        logger.exception("[KVK EMBED] Honor block failed")
        honor_top = []

    honor_block = "—"
    if honor_top:
        # format as medals/numbering up to 5
        parts = []
        medals = ["🥇", "🥈", "🥉"]
        for i, r in enumerate(honor_top[:5]):
            label = medals[i] if i < 3 else f"{i+1}."
            name = r.get("GovernorName") or "Unknown"
            pts = r.get("HonorPoints") or 0
            try:
                pts_i = int(pts)
                parts.append(f"{label} {name} — {pts_i:,}")
            except Exception:
                parts.append(f"{label} {name} — {pts}")
        honor_block = "\n".join(parts)

    logger.info(
        "[KVK EMBED] Rows -> players(kills=%d) | kingdoms(kills=%d) | camps(kills=%d)",
        len(blocks.get("players_by_kills", [])),
        len(blocks.get("kingdoms_by_kills", [])),
        len(blocks.get("camps_by_kills", [])),
    )

    sheet_link = (
        f"https://docs.google.com/spreadsheets/d/{STATS_SHEET_ID}"
        if STATS_SHEET_ID
        else "https://docs.google.com"
    )

    # Embed 1: Our kingdom highlights + metadata + quick commands + links
    e1 = discord.Embed(
        title=f"🔥 {kvk_name} (KVK {kvk_no})",
        description=(
            (f"**{kvk_date_range}**\n" if kvk_date_range else "")
            + f"Stats updated **{timestamp}**\n\n"
        ),
        color=discord.Color.orange(),
    )
    if CUSTOM_AVATAR_URL and CUSTOM_AVATAR_URL.lower().startswith(("http://", "https://")):
        try:
            e1.set_thumbnail(url=CUSTOM_AVATAR_URL)
        except Exception:
            logger.exception("[KVK EMBED] Failed to set thumbnail")
    if banner_url:
        e1.set_image(url=banner_url)

    e1_val = _truncate_and_log("Our Highlights", our_block)
    e1.add_field(name="⭐ Our Highlights", value=e1_val, inline=False)
    if honor_block and honor_block != "—":
        e1.add_field(
            name="🏅 Honor Rankings (Top 5)",
            value=_truncate_and_log("Honor Rankings", honor_block),
            inline=False,
        )

    quick_cmds = "Use **/mykvkstats** to view your stats\nUse **/kvkrankings** to see top players"
    e1.add_field(
        name="📎 Quick Commands",
        value=_truncate_and_log("Quick Commands", quick_cmds),
        inline=False,
    )
    links_val = f"[Full KVK Stats]({sheet_link})"
    e1.add_field(name="🔗 Links", value=_truncate_and_log("Links", links_val), inline=False)
    e1.set_footer(text="KD98 Discord Bot")

    # Embed 2: Overall performance lists (Top 5) - color Aqua
    e2 = discord.Embed(
        title="📊 KVK Performance — Top 5",
        description="Overview of Top 5 performers across players, kingdoms and camps",
        color=discord.Color.from_rgb(0, 255, 255),
    )
    e2.add_field(
        name="👥 All Players — Top Kills",
        value=_truncate_and_log("All Players — Top Kills", players_kills),
        inline=False,
    )
    e2.add_field(
        name="🏰 Kingdoms — Top Kills",
        value=_truncate_and_log("Kingdoms — Top Kills", kingdoms_kills),
        inline=False,
    )
    e2.add_field(
        name="⛺ Camps — Top Kills",
        value=_truncate_and_log("Camps — Top Kills", camps_kills),
        inline=False,
    )
    e2.set_footer(text="KD98 Discord Bot")

    # The diagnostic reports absence honestly without changing legacy render output.
    from hashlib import sha256
    import json

    available = kvk_no != "?" and any(
        blocks.get(key)
        for key in ("players_by_kills", "kingdoms_by_kills", "camps_by_kills", "our_top_players")
    )
    payload = [e1, e2]
    digest = sha256(
        json.dumps([embed.to_dict() for embed in payload], sort_keys=True).encode()
    ).hexdigest()
    detail = (
        "Current fighting report; honor may use a separately selected scan."
        if available
        else "Fighting data is empty or unavailable; no preview published."
    )
    if selected_kvk is not None:
        detail = (
            f"Fighting report for KVK {selected_kvk}."
            if available
            else f"KVK {selected_kvk} fighting data is empty or unavailable; no preview published."
        )
        detail += " Honor omitted for selected-KVK previews to avoid mixing seasons."
    elif available and not honor_top:
        detail += " Honor data is empty or unavailable."
    return PreviewPayload(payload, available, detail, digest)


def build_source_preview(report):
    """Render all twelve blocks with complete-row budgets and separate stream times."""
    from hashlib import sha256
    import json

    from core.discord_embed_limits import require_valid_embed_payload, truncate_text
    from core.operator_diagnostic_payloads import neutralize_discord_mentions, pack_complete_units
    from kvk.services.new_source_reporting_service import BLOCK_KEYS
    from stats_alerts.kvk_diagnostics import PreviewPayload

    if report.get("schema_version") != 2:
        raise ValueError("Source renderer requires V2 metadata.")
    if report.get("publication_id") is None:
        return PreviewPayload([], False, "Source publication not_received; no legacy fallback.", "")
    status = report["player_state"] if report["is_current"] else "retained; configuration pending"
    description = (
        f"Source: {report['source_key']} | {report['period_key']}\n"
        f"Players: {status}; {report['selected_start_scan_id']} → {report['selected_end_scan_id']}\n"
        f"Scan start UTC: {report['player_start_utc']} → {report['player_end_utc']}\n"
        f"Requested endpoints: {report['requested_start_scan_id']} → {report['requested_end_scan_id']}\n"
        f"Aggregates: {report['aggregate_state']}; as-of {report['aggregate_as_of_utc']}\n"
        f"Coverage: {report['aggregate_coverage_start_utc']} → {report['aggregate_coverage_end_utc']}\n"
        f"B0 eligible: {report['eligible_count']}; each rank uses its available metric cohort.\n"
        "Aggregate tier KP is supplied; total KP is unsupported. Rounded reports retain source precision."
    )
    embed = discord.Embed(
        title=f"KVK {report['kvk_no']} — {report['period_label']}", description=description
    )
    embed.set_footer(
        text=f"Publication {report['publication_id']} | generation {report['generation']}"
    )

    def metric(row, key):
        if row[key] is None:
            return row["states"][key]
        reported = row["reported"].get(key)
        if reported:
            prefix = "≈ " if reported["precision"] != "reported_numeric" else ""
            return prefix + str(reported["raw"])
        return (
            format(row[key], "f").rstrip("0").rstrip(".")
            if "." in format(row[key], "f")
            else format(row[key], "f")
        )

    for key in BLOCK_KEYS:
        rows = report["blocks"][key]
        units = []
        for row in rows:
            name = row.get("name") or row.get("kingdom") or row.get("camp_name") or "Unknown"
            name = truncate_text(
                discord.utils.escape_markdown(neutralize_discord_mentions(str(name))).replace(
                    "\n", " "
                ),
                64,
            )
            rank = f"{row['rank']}/{row['population']} " if row.get("rank") else ""
            units.append(
                f"{rank}{name}: kills {metric(row, 'kills_gain')} | deaths {metric(row, 'deads')} | DKP {metric(row, 'dkp')} | total KP {metric(row, 'kp_gain')}"
            )
        # 12 * 360 leaves a fixed reserve for metadata, headings and footer.
        value = (
            pack_complete_units(units, limit=360, label="rows").text
            if units
            else (
                report["aggregate_state"]
                if key.startswith(("kingdom", "camp")) or key in ("our_kingdom", "our_camp")
                else "No available metric values"
            )
        )
        embed.add_field(name=key.replace("_", " ").title(), value=value, inline=False)
    payload = [embed]
    require_valid_embed_payload(payload)
    digest = sha256(json.dumps([e.to_dict() for e in payload], sort_keys=True).encode()).hexdigest()
    return PreviewPayload(payload, True, description, digest)


async def publish_kvk_preview(bot, channel, preview, message_id, before_send, check_destination):
    """Discord adapter: validate, bind identity and publish once; never replace on failure."""
    from core.discord_embed_limits import require_valid_embed_payload

    require_valid_embed_payload(preview.payload)
    check_destination()
    message = None
    if message_id is not None:
        message = await channel.fetch_message(message_id)
        if (
            message.id != message_id
            or message.author.id != bot.user.id
            or message.channel.id != channel.id
        ):
            raise ValueError("Preview message identity mismatch")
    check_destination()
    await before_send()
    check_destination()
    if message is not None:
        await message.edit(
            content=None, embeds=preview.payload, allowed_mentions=discord.AllowedMentions.none()
        )
        return message.id
    sent = await channel.send(
        content=None, embeds=preview.payload, allowed_mentions=discord.AllowedMentions.none()
    )
    return sent.id


@delivery_outcome("fighting")
async def send_kvk_embed(
    bot: Any,
    channel: discord.abc.Messageable,
    timestamp: str,
    *,
    is_test: bool = False,
    _delivery=None,
) -> None:
    """Legacy production adapter: retain reads, formatting, mentions and return behavior."""
    if _delivery and channel is not None:
        _delivery.update(requested_channel_id=getattr(channel, "id", None))
    preview = await build_kvk_preview(timestamp)
    if _delivery:
        _delivery.update(data="available" if preview.available else "empty_or_unavailable")
    content = "@everyone" if not is_test else None
    allowed_mentions = discord.AllowedMentions(everyone=(not is_test))
    try:
        if _delivery and channel is not None:
            _delivery.enter(getattr(channel, "id", None))
        sent = await channel.send(
            content=content, embeds=preview.payload, allowed_mentions=allowed_mentions
        )
        if _delivery:
            _delivery.receipt(sent)
    except Exception as exc:
        if _delivery:
            _delivery.failure(exc)
        logger.exception("[KVK EMBED] Failed sending combined embeds")
