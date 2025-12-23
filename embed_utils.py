# embed_utils.py
from __future__ import annotations  # 🔒 avoid runtime eval of type hints

from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)
import hashlib
import io
import os
import re
import time
from typing import Any
import uuid

import aiofiles
import discord
from discord.ui import View
from discord.utils import format_dt

from constants import (
    CUSTOM_AVATAR_URL,
    DOWN_ARROW_EMOJI,
    UP_ARROW_EMOJI,
    VIEW_PRUNE_ON_FORBIDDEN,
    VIEW_TRACKING_FILE,
)
from file_utils import emit_telemetry_event, read_summary_log_rows
from generate_progress_image import generate_exempt_dial, generate_progress_dial
from utils import fmt_short, format_countdown, utcnow

# --- Emoji & color fallbacks ---
try:
    from constants import (
        DANGER_COLOR,
        INFO_COLOR,
        SUCCESS_COLOR,
        WARN_COLOR,
    )
except Exception:
    INFO_COLOR, SUCCESS_COLOR, WARN_COLOR, DANGER_COLOR = 0x3B82F6, 0x22C55E, 0xF59E0B, 0xEF4444

AUTO_REGENERATE = False  # Optional toggle to regenerate expired embeds

# Config: warn when embed building takes longer than this (seconds)
EMBED_BUILD_SLOW_THRESHOLD = 1.0

# Safe limits for Discord embed fields
_EMBED_FIELD_MAX = 1024
# Conservative total embed content size cap (title + fields). Discord has ~6000 characters cap overall.
_EMBED_TOTAL_CAP = 6000
# Fallback when a large "log-like" field should be attached instead of embedded
_LOG_FIELD_NAMES = ("log", "combined_log", "out", "output", "details")

# Default maximum characters of a log-like field to keep inside the embed.
# Larger content will be attached as a file and replaced with a short note in the embed.
_DEFAULT_MAX_LOG_EMBED_CHARS = int(os.getenv("EMBED_LOG_TRIM", "1200"))


def fmt_pct(p: float | None, *, decimals: int = 0) -> str:
    if p is None:
        return "\u2014"
    try:
        v = float(p)
    except Exception:
        return "\u2014"
    out = f"{v:.{decimals}f}%"
    if decimals and out.endswith(".0%"):
        out = out.replace(".0%", "%")
    return out


def fmt_delta(n: float | None) -> str:
    if n is None:
        return "\u2014"
    try:
        v = float(n)
    except Exception:
        return "\u2014"
    if v > 0:
        return f"{UP_ARROW_EMOJI} {fmt_short(v)}"
    if v < 0:
        return f"{DOWN_ARROW_EMOJI} {fmt_short(abs(v))}"
    return "\u2014"


def md_escape(s: str | None) -> str:
    if not s:
        return ""
    for ch in ("*", "_", "`", "~", "|", ">"):
        s = s.replace(ch, f"\\{ch}")
    return s


async def _safe_post_interaction_followup(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    files: list | None = None,
    ephemeral: bool = True,
) -> bool:
    """
    Try to send a followup; return True if sent. Catch NotFound and other
    exceptions so callers won't crash. Useful after response.defer().
    """
    try:
        if files:
            await interaction.followup.send(
                content=content, embed=embed, files=files, ephemeral=ephemeral
            )
        else:
            await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral)
        logger.debug(
            "[USAGE] followup.sent interaction_id=%s user_id=%s",
            getattr(interaction, "id", "<unknown>"),
            getattr(interaction.user, "id", "<unknown>") if interaction.user else "<no-user>",
        )
        return True
    except discord.NotFound as e:
        # Unknown webhook / interaction expired / message deleted
        logger.error(
            "[ERROR] Failed to send followup (NotFound). interaction_id=%s user_id=%s exc=%s",
            getattr(interaction, "id", "<unknown>"),
            getattr(interaction.user, "id", "<unknown>") if interaction.user else "<no-user>",
            e,
            exc_info=True,
        )
        return False
    except Exception:
        logger.exception(
            "[ERROR] Unexpected error sending followup. interaction_id=%s user_id=%s",
            getattr(interaction, "id", "<unknown>"),
            getattr(interaction.user, "id", "<unknown>") if interaction.user else "<no-user>",
        )
        return False


async def _send_dm_fallback(interaction: discord.Interaction, msg: str) -> bool:
    """
    Try to DM the user as a fallback if followup fails.
    Returns True if DM sent, False otherwise.
    """
    try:
        if interaction.user:
            await interaction.user.send(msg)
            logger.info(
                "[INFO] Sent DM fallback to user. interaction_id=%s user_id=%s",
                getattr(interaction, "id", "<unknown>"),
                interaction.user.id,
            )
            return True
        else:
            logger.warning(
                "[WARN] No interaction.user available for DM fallback. interaction_id=%s",
                getattr(interaction, "id", "<unknown>"),
            )
            return False
    except discord.Forbidden:
        logger.warning(
            "[WARN] Forbidden sending DM to user. user_id=%s",
            getattr(interaction.user, "id", "<unknown>"),
        )
        return False
    except Exception:
        logger.exception(
            "[ERROR] Failed to send DM fallback. interaction_id=%s user_id=%s",
            getattr(interaction, "id", "<unknown>"),
            getattr(interaction.user, "id", "<unknown>"),
        )
        return False


# New centralized sanitizer for view prefixes (shared across modules)
def sanitize_view_prefix(prefix: Any, *, max_len: int = 64) -> str:
    """
    Turn an arbitrary prefix into a safe token suitable for custom_id usage.

    Rules:
      - Convert to str and strip
      - Replace disallowed characters with underscore
      - Append a short deterministic hash suffix to avoid collisions
      - Ensure the total length does not exceed max_len (truncating base if needed)
      - Ensure non-empty fallback
    """
    try:
        s = str(prefix or "")
    except Exception:
        s = ""
    s = s.strip()
    # Keep only alphanumerics, hyphen and underscore
    base = re.sub(r"[^A-Za-z0-9_-]+", "_", s)
    if not base:
        base = f"view_{uuid.uuid4().hex[:8]}"

    try:
        hash_suffix = hashlib.sha1(s.encode("utf-8")).hexdigest()[:8]
    except Exception:
        hash_suffix = uuid.uuid4().hex[:8]

    sep_len = 1
    max_base_len = max_len - (sep_len + len(hash_suffix))
    if max_base_len < 1:
        max_base_len = max(1, max_len - (sep_len + len(hash_suffix)))

    if len(base) > max_base_len:
        base = base[:max_base_len]

    return f"{base}_{hash_suffix}"


# Backwards-compatible wrapper name used historically in this module
def _sanitize_prefix_for_custom_id(prefix: str | None) -> str:
    return sanitize_view_prefix(prefix or "default", max_len=64)


class LocalTimeButton(discord.ui.Button):
    def __init__(self, custom_id: str = "local_time_toggle"):
        super().__init__(
            label="\ud83d\udd52 Show in My Local Time",
            style=discord.ButtonStyle.success,
            custom_id=custom_id,
        )
        # prefix extracted from custom_id; kept for logging and view-scoped handling
        # Use removesuffix for clarity (Python 3.9+)
        try:
            self.prefix = custom_id.removesuffix("_local_time_toggle")
        except Exception:
            # Fallback if removesuffix is not available
            if custom_id.endswith("_local_time_toggle"):
                self.prefix = custom_id[: -len("_local_time_toggle")]
            else:
                self.prefix = custom_id

    async def callback(self, interaction: discord.Interaction):
        interaction_id = getattr(interaction, "id", "<unknown>")
        user_id = getattr(interaction.user, "id", "<no-user>") if interaction.user else "<no-user>"
        message_id = (
            getattr(interaction.message, "id", "<no-message")
            if hasattr(interaction, "message")
            else "<no-message>"
        )

        logger.info(
            f"[BUTTON] {self.custom_id} clicked (prefix: {self.prefix}) interaction_id={interaction_id} user_id={user_id} message_id={message_id}"
        )

        # 1) Acknowledge quickly to create the followup webhook.
        try:
            await interaction.response.defer(ephemeral=True)
            logger.debug(
                "[DEBUG] Deferred interaction. interaction_id=%s user_id=%s",
                interaction_id,
                user_id,
            )
        except discord.errors.InteractionResponded:
            # Already responded (maybe another handler). Continue to send followup.
            logger.debug(
                "[DEBUG] Interaction already responded; continuing to followup. interaction_id=%s",
                interaction_id,
            )
        except discord.NotFound:
            # Interaction already expired — followups will likely fail, but we try anyway below.
            logger.warning(
                "[WARN] Interaction not found when trying to defer. interaction_id=%s",
                interaction_id,
            )
        except Exception:
            logger.exception(
                "[ERROR] Unexpected error while deferring interaction. interaction_id=%s",
                interaction_id,
            )

        # 2) Build the embed (timed). build_local_time_embed is now async.
        start = time.monotonic()
        try:
            embed = await self.view.build_local_time_embed()
        except Exception:
            logger.exception(
                "[ERROR] Failed to build local time embed. interaction_id=%s user_id=%s",
                interaction_id,
                user_id,
            )
            # Try to notify via followup, then DM fallback if followup fails
            sent = await _safe_post_interaction_followup(
                interaction, content="Failed to build local time view.", ephemeral=True
            )
            if not sent:
                await _send_dm_fallback(
                    interaction,
                    "I couldn't build the local time view. Please try the command again.",
                )
            return
        elapsed = time.monotonic() - start

        if elapsed > EMBED_BUILD_SLOW_THRESHOLD:
            logger.warning(
                "[WARN] Embed build slow. interaction_id=%s user_id=%s elapsed=%.3fs threshold=%.3fs",
                interaction_id,
                user_id,
                elapsed,
                EMBED_BUILD_SLOW_THRESHOLD,
            )
        else:
            logger.debug(
                "[DEBUG] Embed built. interaction_id=%s user_id=%s elapsed=%.3fs",
                interaction_id,
                user_id,
                elapsed,
            )

        # 3) Send via followup (we deferred earlier). If followup fails, attempt DM fallback.
        sent = await _safe_post_interaction_followup(interaction, embed=embed, ephemeral=True)
        if sent:
            logger.info(
                "[INFO] Sent local time embed followup. interaction_id=%s user_id=%s elapsed_build=%.3fs",
                interaction_id,
                user_id,
                elapsed,
            )
            return

        # 4) If followup failed (likely NotFound), try DM fallback so user sees an explanation.
        dm_msg = "I couldn't show the local time view in the channel (interaction expired). Please try the command again."
        dm_sent = await _send_dm_fallback(interaction, dm_msg)
        if dm_sent:
            logger.info(
                "[INFO] DM fallback succeeded after followup failure. interaction_id=%s user_id=%s",
                interaction_id,
                user_id,
            )
        else:
            logger.error(
                "[ERROR] DM fallback failed after followup failure. interaction_id=%s user_id=%s",
                interaction_id,
                user_id,
            )


class LocalTimeToggleView(View):
    def __init__(self, events, prefix="default", timeout=None):
        """
        LocalTimeToggleView builds a single-button view that, when clicked,
        shows the same event(s) in the user's local time.

        Important for persistence:
         - The button's custom_id is deterministically derived from `prefix`.
         - custom_id is sanitized and trimmed so it remains stable across restarts.
         - Use timeout=None for persistent views that must survive process restarts
           when coupled with bot.add_view(view, message_id=...).
        """
        super().__init__(timeout=timeout)
        self.events = events
        # Normalize and store prefix for later diagnostics
        self.prefix = prefix  # ✅ Store prefix

        # Build deterministic, safe custom_id for the LocalTimeButton
        safe_prefix = sanitize_view_prefix(self.prefix, max_len=64)
        # Ensure the suffix is stable and readable
        custom_id = f"{safe_prefix}_local_time_toggle"
        # Truncate to a conservative maximum (Discord custom_id max historically 100 chars; keep 100)
        if len(custom_id) > 100:
            custom_id = custom_id[:100]

        # Add the single-button item with deterministic custom_id
        self.add_item(LocalTimeButton(custom_id=custom_id))

    async def build_local_time_embed(self):
        """
        Build the local-time embed asynchronously; if this needs to call async helpers
        (DB, network, or file I/O) we can await them here.
        """
        if not self.events:
            logger.warning(
                f"[LOCAL TIME EMBED] No events found in view with prefix '{self.prefix}'"
            )
            return discord.Embed(
                title="No events found",
                description="Unable to build local time view. This might be a stale or expired button.",
                color=discord.Color.red(),
            )

        is_single_event = len(self.events) == 1
        if is_single_event:
            embed_title = f"\ud83d\udcc5 {self.events[0].get('name') or self.events[0].get('title')} \u2013 Local Time View"
        else:
            # If all events are altar-type, call it fights; otherwise events.
            types = {(e.get("type") or "").lower() for e in self.events}
            embed_title = (
                "⚔️ Upcoming Fights \u2013 Local Time View"
                if types and types.issubset({"altar", "altars"})
                else "\ud83d\udcca Upcoming Events \u2013 Local Time View"
            )

        embed = discord.Embed(
            title=embed_title,
            description="These times are shown in **your local time**.",
            color=discord.Color.orange(),
            timestamp=utcnow(),
        )

        if is_single_event:
            # Just show the single event directly
            e = self.events[0]
            label = e.get("name") or e.get("title")
            time_str = format_dt(e["start_time"], style="F")
            embed.add_field(name=label, value=time_str, inline=False)
        else:
            # Group by type
            TYPE_MAP = {
                "ruins": "ruins",
                "next ruins": "ruins",
                "altar": "altars",
                "altars": "altars",
                "next altar fight": "altars",
                "chronicle": "chronicle",
                "major": "major",
            }

            grouped = {"ruins": [], "altars": [], "chronicle": [], "major": []}

            for e in self.events:
                raw_type = e.get("type", "").lower()
                normalized = TYPE_MAP.get(raw_type, raw_type)
                if normalized in grouped:
                    grouped[normalized].append(e)

            for key, items in grouped.items():
                if not items:
                    continue
                items.sort(key=lambda e: e["start_time"])

                lines = [
                    f"• **{e.get('name') or e.get('title')}**\n{format_dt(e['start_time'], style='F')}"
                    for e in items
                ]
                value = "\n".join(lines)
                if len(value) > 1024:
                    trimmed = []
                    total = 0
                    for line in lines:
                        ln = len(line) + 1
                        if total + ln > 1010:
                            break
                        trimmed.append(line)
                        total += ln
                    value = "\n".join(trimmed) + "\n…"
                embed.add_field(name=key.capitalize(), value=value, inline=False)

        embed.set_footer(text="K98 Bot \u2013 Local Time View")
        logger.info(
            f"[LOCAL TIME EMBED] Built embed for prefix '{self.prefix}' with {len(self.events)} event(s)."
        )
        return embed


def format_event_time(dt):
    """Formats a datetime object into a UTC string."""
    return dt.strftime("%A, %d %B %Y at %H:%M UTC")


class TargetLookupView(View):
    def __init__(self, matches: list[dict], timeout: float = 60):
        super().__init__(timeout=timeout)
        self.matches = matches

        for entry in matches[:5]:  # Limit to 5 buttons
            label = str(entry.get("GovernorName", ""))[:75]
            custom_id = str(entry.get("GovernorID", ""))
            button = discord.ui.Button(
                label=label,
                custom_id=custom_id,
                style=discord.ButtonStyle.primary,
            )
            button.callback = self.make_callback(custom_id)
            self.add_item(button)

    def make_callback(self, governor_id: str):
        async def callback(interaction: discord.Interaction):
            # Defer quickly to acknowledge
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                logger.debug("[DEBUG] TargetLookupView: defer failed, continuing")

            # Trigger the /mykvktargets command by editing the interaction message
            # This is simulated behavior since buttons can't invoke slash commands directly
            try:
                await interaction.followup.send(
                    f"📊 Looking up targets for Governor ID `{governor_id}`...", ephemeral=True
                )
            except Exception:
                # If followup fails, try DM fallback
                await _send_dm_fallback(
                    interaction, f"Looking up targets for Governor ID `{governor_id}`..."
                )

            # If your /mykvktargets command is callable as a function:
            try:
                from Commands import mykvktargets

                await mykvktargets(interaction, governorid=governor_id)
            except Exception:
                logger.exception(
                    "[ERROR] TargetLookupView: mykvktargets invocation failed for governor_id=%s",
                    governor_id,
                )
                try:
                    await interaction.followup.send("Failed to lookup targets.", ephemeral=True)
                except Exception:
                    await _send_dm_fallback(
                        interaction, "Failed to lookup targets. Please try the command manually."
                    )

            # Disable all buttons after click
            try:
                for item in self.children:
                    item.disabled = True
                if interaction.message:
                    await interaction.message.edit(view=self)
                elif getattr(interaction, "original_response", None):
                    msg = await interaction.original_response()
                    await msg.edit(view=self)
            except Exception:
                logger.debug(
                    "[DEBUG] TargetLookupView: could not disable/refresh buttons after click"
                )

        return callback


async def log_embed_to_file(embed: discord.Embed, log_path="embed_audit.log"):
    async with aiofiles.open(log_path, "a", encoding="utf-8") as f:
        await f.write(
            f"[{discord.utils.utcnow().isoformat()}] {embed.title} - {embed.description}\n"
        )


# New helper: standardized Context field builder
def build_context_field(
    filename: str | None = None, rank: int | None = None, seed: int | None = None
) -> dict:
    """
    Return a small dict suitable for merging into embed fields to provide
    a compact "Context" value for operational correlation.

    Example output:
      {"Context": "file.xlsx | rank=1 | seed=42"}

    Behavior:
      - Escapes filename for markdown safety.
      - Omits missing parts.
      - Returns {} if no information provided.
    """
    parts: list[str] = []
    try:
        if filename:
            parts.append(md_escape(str(filename)))
        if rank is not None:
            parts.append(f"rank={rank}")
        if seed is not None:
            parts.append(f"seed={seed}")
    except Exception:
        # Defensive: if something weird is passed, fall back to a safe string representation
        try:
            parts.append(md_escape(str(filename or "")))
        except Exception:
            pass

    if not parts:
        return {}
    return {"Context": " | ".join(parts)}


# New centralized status embed + telemetry helper
async def send_status_embed(
    title: str,
    status_map: dict,
    ok: bool | None,
    user,
    notify_channel,
    *,
    context_field: dict | None = None,
    max_log_embed_chars: int | None = None,
):
    """
    DRY helper to send a consistent status embed for pipeline steps and emit telemetry.

    - title: human title for the embed and telemetry event
    - status_map: dict of field name -> value (e.g., {"Excel File": "✅", "Log": "..."})
    - ok: boolean success indicator (True -> success color, False -> failure color, None -> neutral)
    - user, notify_channel: forwarded to send_embed_safe (callers must pass bot/fallback as needed)
    - context_field: optional dict to merge into embed fields for correlation
    - max_log_embed_chars: if provided overrides default trimming for "Log"-like fields
    """
    try:
        cf = context_field or {}
        # Merge status_map with context to build embed fields. Rows in status_map take precedence.
        fields = {**cf, **status_map}
        # Choose color
        if ok is True:
            color = 0x2ECC71
        elif ok is False:
            color = 0xE74C3C
        else:
            color = 0xF1C40F
        # If there is a "Log" or similar large field, ensure we only pass trimmed content to embed helper;
        if max_log_embed_chars is None:
            max_log_embed_chars = _DEFAULT_MAX_LOG_EMBED_CHARS

        if "Log" in fields and fields["Log"] is not None:
            try:
                fields["Log"] = str(fields["Log"])[:max_log_embed_chars]
            except Exception:
                pass

        # Use the shared send_embed_safe from this repo (imported by callers)
        # We don't call destination.send here because callers may pass user/channel objects.
        # Emit telemetry with safe trimming
        telemetry_payload = {
            "event": "pipeline_status",
            "title": title,
            "ok": bool(ok),
            "color": color,
        }
        telemetry_payload.update(
            {k: (v if len(str(v)) < 200 else str(v)[:200] + "...") for k, v in status_map.items()}
        )
        emit_telemetry_event(telemetry_payload)
        # Actual send is left to caller via embed_utils.send_embed_safe or other helper
    except Exception:
        logger.exception("[STATUS_EMBED] failed to build/send status embed")


# New robust send helper
async def send_embed_safe(
    destination,
    title: str,
    fields: dict,
    color: int,
    mention=None,
    fallback_channel: discord.TextChannel | None = None,
    bot: discord.Client | None = None,
    *,
    max_field_length: int = _EMBED_FIELD_MAX,
    total_cap: int = _EMBED_TOTAL_CAP,
    max_log_embed_chars: int | None = None,
) -> bool:
    """
    Safely send an embed to `destination` (Member/User/Channel). Returns True on success.

    Behavior:
    - Truncates non-log fields longer than max_field_length.
    - If a "log-like" field or the total embed content is too large, attach the large content
      as a file and replace the embed field text with a short note.
    - Catches discord.Forbidden and discord.HTTPException and attempts fallback behavior.
    - Honors constants.VIEW_PRUNE_ON_FORBIDDEN to treat Forbidden as prunable when configured.

    New:
    - max_log_embed_chars: explicit cap for how many characters of a log-like field are
                           left inside the embed. If omitted, uses environment/default.
    """
    embed = discord.Embed(title=title, color=color)
    # Prepare attachments if needed
    files: list[discord.File] = []
    # Work on a copy so we can mutate
    field_items = list(fields.items() or [])

    if max_log_embed_chars is None:
        max_log_embed_chars = _DEFAULT_MAX_LOG_EMBED_CHARS

    # Helper to decide log-like fields
    def _is_log_field(k: str) -> bool:
        try:
            return any(tok in k.lower() for tok in _LOG_FIELD_NAMES)
        except Exception:
            return False

    # First pass: handle log-like fields specially (attach full content if too large)
    remaining_fields: list[tuple[str, str]] = []
    for name, value in field_items:
        sval = "" if value is None else str(value)
        if _is_log_field(name):
            # If the log is large, attach it as a file and add a note in the embed
            if len(sval) > int(max_log_embed_chars):
                try:
                    fname = f"{title.replace(' ', '_')}_{name.replace(' ', '_')}.txt"
                except Exception:
                    fname = f"{uuid.uuid4().hex[:8]}_log.txt"
                try:
                    bio = io.BytesIO(sval.encode("utf-8"))
                    # Create a discord.File from the bytesIO
                    files.append(discord.File(bio, filename=fname))
                    note = f"(log attached as {fname})"
                    embed.add_field(name=name, value=note, inline=False)
                except Exception:
                    logger.exception("[EMBED] Failed to attach large log field %s", name)
                    # fallback to truncated content
                    if len(sval) > max_field_length:
                        sval = sval[: max_field_length - 3] + "..."
                    embed.add_field(name=name, value=sval, inline=False)
            else:
                # Small enough to include in embed (but still respect max_field_length)
                if len(sval) > max_field_length:
                    sval = sval[: max_field_length - 3] + "..."
                embed.add_field(name=name, value=sval, inline=False)
        else:
            remaining_fields.append((name, sval))

    # Second pass: add non-log fields, truncating as needed
    total_chars = len(title or "")
    for name, sval in remaining_fields:
        total_chars += len(name) + len(sval)
        if len(sval) > max_field_length:
            sval = sval[: max_field_length - 3] + "..."
        embed.add_field(name=name, value=sval, inline=False)

    # If total_chars already within cap, we're done
    if total_chars <= total_cap:
        try:
            if files:
                await destination.send(
                    content=mention if mention else None, embed=embed, files=files
                )
            else:
                await destination.send(content=mention if mention else None, embed=embed)
            try:
                await log_embed_to_file(embed)
            except Exception:
                logger.exception("[EMBED] log_embed_to_file failed")
            return True
        except discord.Forbidden as e:
            logger.warning(f"[EMBED] Forbidden sending to destination: {e}")
            if VIEW_PRUNE_ON_FORBIDDEN:
                logger.info("[EMBED] VIEW_PRUNE_ON_FORBIDDEN set: treating Forbidden as prunable.")
                return False
            # try fallback
            try:
                if fallback_channel is not None and bot is not None:
                    fallback_msg = discord.Embed(
                        title="Embed Delivery Failed (Forbidden)",
                        description=f"Failed to deliver embed titled: {title}",
                        color=0xE67E22,
                    )
                    await fallback_channel.send(embed=fallback_msg)
            except Exception:
                logger.exception("[EMBED] Failed to send fallback for Forbidden")
            return False
        except discord.HTTPException as e:
            logger.warning(f"[EMBED] HTTPException sending embed: {e}")
            # try fallback channel if provided
            try:
                if fallback_channel is not None and bot is not None:
                    fallback_msg = discord.Embed(
                        title="Embed Delivery Failed (HTTPException)",
                        description=f"Failed to deliver embed titled: {title}",
                        color=0xE67E22,
                    )
                    await fallback_channel.send(embed=fallback_msg)
            except Exception:
                logger.exception("[EMBED] Failed to send fallback for HTTPException")
            return False
        except Exception:
            logger.exception("[EMBED] Unexpected error sending embed")
            return False

    # If we reach here, total_chars exceeded total_cap — try to attach largest remaining fields
    # Build list of remaining (name, value, len)
    extra_candidates = []
    for name, sval in remaining_fields:
        try:
            size = len(sval)
        except Exception:
            size = 0
        extra_candidates.append((size, name, sval))
    extra_candidates.sort(reverse=True)

    for _, name, sval in extra_candidates:
        if total_chars <= total_cap:
            break
        try:
            fname = f"{title.replace(' ', '_')}_{name.replace(' ', '_')}.txt"
        except Exception:
            fname = f"{uuid.uuid4().hex[:8]}_field.txt"
        try:
            bio = io.BytesIO(sval.encode("utf-8"))
            files.append(discord.File(bio, filename=fname))
            note = f"(attached as {fname})"
            embed.add_field(name=name, value=note, inline=False)
            total_chars -= len(sval)
        except Exception:
            # If attachment fails, add truncated field
            embed.add_field(name=name, value=(sval[: max_field_length - 3] + "..."), inline=False)
            total_chars -= max_field_length

    # Final send attempt
    try:
        if files:
            await destination.send(content=mention if mention else None, embed=embed, files=files)
        else:
            await destination.send(content=mention if mention else None, embed=embed)
        try:
            await log_embed_to_file(embed)
        except Exception:
            logger.exception("[EMBED] log_embed_to_file failed")
        return True
    except discord.Forbidden as e:
        logger.warning(f"[EMBED] Forbidden sending to destination: {e}")
        if VIEW_PRUNE_ON_FORBIDDEN:
            logger.info("[EMBED] VIEW_PRUNE_ON_FORBIDDEN set: treating Forbidden as prunable.")
            return False
        # try fallback
        try:
            if fallback_channel is not None and bot is not None:
                fallback_msg = discord.Embed(
                    title="Embed Delivery Failed (Forbidden)",
                    description=f"Failed to deliver embed titled: {title}",
                    color=0xE67E22,
                )
                await fallback_channel.send(embed=fallback_msg)
        except Exception:
            logger.exception("[EMBED] Failed to send fallback for Forbidden")
        return False
    except discord.HTTPException as e:
        logger.warning(f"[EMBED] HTTPException sending embed: {e}")
        try:
            if fallback_channel is not None and bot is not None:
                fallback_msg = discord.Embed(
                    title="Embed Delivery Failed (HTTPException)",
                    description=f"Failed to deliver embed titled: {title}",
                    color=0xE67E22,
                )
                await fallback_channel.send(embed=fallback_msg)
        except Exception:
            logger.exception("[EMBED] Failed to send fallback for HTTPException")
        return False
    except Exception:
        logger.exception("[EMBED] Unexpected error sending embed")
        return False


# Keep backward-compatible send_embed wrapper (calls the robust helper)
async def send_embed(
    destination, title, fields: dict, color: int, mention=None, fallback_channel=None, bot=None
):
    # Call send_embed_safe with defaults for truncation thresholds
    return await send_embed_safe(
        destination,
        title,
        fields or {},
        color,
        mention=mention,
        fallback_channel=fallback_channel,
        bot=bot,
    )


async def generate_summary_embed(days=1, summary_log_path="summary_log.csv"):
    start_date = discord.utils.utcnow().date() - timedelta(days=days - 1)
    total = 0
    failures = 0
    durations = []
    rows_to_show = []

    if not os.path.exists(summary_log_path):
        return None

    rows = await read_summary_log_rows(summary_log_path)

    for row in rows:
        timestamp_str = row.get("Timestamp")
        if not timestamp_str:
            continue
        try:
            ts = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue

        if ts.date() >= start_date:
            total += 1
            try:
                duration = float(row.get("Duration (sec)", 0))
                durations.append(duration)
            except Exception:
                duration = 0.0

            excel = "✅" if row.get("Excel Success") == "True" else "❌"
            archive = "✅" if row.get("Archive Success") == "True" else "❌"
            sql = "✅" if row.get("SQL Success") == "True" else "❌"
            export = "✅" if row.get("Export Success") == "True" else "❌"

            if sql != "✅" or export != "✅":
                failures += 1

            rows_to_show.append(
                f"🕒 {ts.strftime('%Y-%m-%d %H:%M')} – **{row.get('Filename', 'N/A')}** – {duration:.0f}s – Excel:{excel} Archive:{archive} SQL:{sql} Export:{export}"
            )

    if total == 0:
        return None

    avg_duration_str = f"{(sum(durations) / len(durations)):.1f} sec" if durations else "N/A"

    embed = discord.Embed(
        title=f"📊 {'Weekly' if days > 1 else 'Daily'} Processing Summary", color=INFO_COLOR
    )
    today = discord.utils.utcnow().date()
    embed.add_field(name="Date Range", value=f"{start_date} to {today}", inline=False)
    embed.add_field(name="Files Processed", value=fmt_short(total), inline=True)
    embed.add_field(name="Failures", value=str(failures), inline=True)
    embed.add_field(name="Average Duration", value=avg_duration_str, inline=True)
    details_text = "\n".join(rows_to_show[-10:]) or "No recent files"
    if len(details_text) > 1024:
        details_text = details_text[:1021] + "…"
    embed.add_field(name="File Details", value=details_text, inline=False)
    embed.timestamp = discord.utils.utcnow()
    return embed


async def send_summary_embed(channel: discord.TextChannel, days: int = 1) -> discord.Message | None:
    """Build and send a summary embed to a Discord channel."""
    try:
        embed = await generate_summary_embed(days=days)
    except Exception as e:
        logger.warning(f"[SUMMARY] Failed to generate summary embed: {e}")
        embed = None

    if not embed:
        await channel.send("No recent processing activity to summarise.")
        return
    await channel.send(embed=embed)


class HistoryView(discord.ui.View):
    def __init__(
        self, interaction, rows, page, total_pages, *, entries_per_page: int = 5, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction  # original interaction (optional fallback)
        self.rows = rows
        self.page = max(1, int(page))
        self.total_pages = max(1, int(total_pages))
        self.entries_per_page = entries_per_page
        self.message: discord.Message | None = None  # set by the command after send
        self._apply_nav_state()

    def _get_nav_buttons(self):
        prev_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "previous" in (c.label or "").lower()
            ),
            None,
        )
        next_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "next" in (c.label or "").lower()
            ),
            None,
        )
        return prev_btn, next_btn

    def _apply_nav_state(self):
        prev_btn, next_btn = self._get_nav_buttons()
        if prev_btn:
            prev_btn.disabled = self.page <= 1
        if next_btn:
            next_btn.disabled = self.page >= self.total_pages

    async def _refresh_message(self, interaction: discord.Interaction):
        self._apply_nav_state()
        try:
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        except discord.InteractionResponded:
            # Fallback if already acked
            try:
                if self.message:
                    await self.message.edit(embed=self.get_embed(), view=self)
                elif self.interaction:
                    msg = await self.interaction.original_response()
                    await msg.edit(embed=self.get_embed(), view=self)
            except Exception:
                pass

    def get_embed(self):
        start = (self.page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        page_rows = self.rows[::-1][start:end]

        embed = discord.Embed(
            title=f"📜 File Processing History (Page {self.page}/{self.total_pages})",
            color=INFO_COLOR,
        )
        for row in page_rows:
            embed.add_field(
                name=f"📄 {row.get('Filename', 'Unknown')}",
                value=(
                    f"👤 Uploaded by: `{row.get('Author', 'Unknown')}`\n"
                    f"🕒 Time: `{row.get('Timestamp', 'Unknown')}`\n"
                    f"#️⃣ Channel: `{row.get('Channel', 'Unknown')}`\n"
                    f"📂 Path: `{row.get('SavedPath', 'Unknown')}`"
                ),
                inline=False,
            )
        embed.timestamp = discord.utils.utcnow()
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page <= 1:
            # Ack silently so Discord doesn't show an error
            await interaction.response.defer()
            return
        self.page -= 1
        await self._refresh_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page >= self.total_pages:
            await interaction.response.defer()
            return
        self.page += 1
        await self._refresh_message(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
            elif self.interaction:
                msg = await self.interaction.original_response()
                await msg.edit(view=self)
        except Exception as e:
            logger.warning(f"[HistoryView] Failed to disable buttons after timeout: {e}")


class FailuresView(discord.ui.View):
    def __init__(
        self, interaction, rows, page, total_pages, *, entries_per_page: int = 5, timeout: int = 60
    ):
        super().__init__(timeout=timeout)
        self.interaction = interaction
        self.rows = rows
        self.page = max(1, int(page))
        self.total_pages = max(1, int(total_pages))
        self.entries_per_page = entries_per_page
        self.message: discord.Message | None = None  # set by the command after send
        self._apply_nav_state()

    def _get_nav_buttons(self):
        prev_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "previous" in (c.label or "").lower()
            ),
            None,
        )
        next_btn = next(
            (
                c
                for c in self.children
                if isinstance(c, discord.ui.Button) and "next" in (c.label or "").lower()
            ),
            None,
        )
        return prev_btn, next_btn

    def _apply_nav_state(self):
        prev_btn, next_btn = self._get_nav_buttons()
        if prev_btn:
            prev_btn.disabled = self.page <= 1
        if next_btn:
            next_btn.disabled = self.page >= self.total_pages

    async def _refresh_message(self, interaction: discord.Interaction):
        self._apply_nav_state()
        try:
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        except discord.InteractionResponded:
            try:
                if self.message:
                    await self.message.edit(embed=self.get_embed(), view=self)
                elif self.interaction:
                    msg = await self.interaction.original_response()
                    await msg.edit(embed=self.get_embed(), view=self)
            except Exception:
                pass

    def get_embed(self):
        start = (self.page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        page_rows = self.rows[::-1][start:end]

        embed = discord.Embed(
            title=f"❌ Failed Jobs (Page {self.page}/{self.total_pages})", color=DANGER_COLOR
        )
        for row in page_rows:
            embed.add_field(
                name=f"📄 {row.get('Filename', 'Unknown')}",
                value=(
                    f"👤 Author: `{row.get('User', 'Unknown')}`\n"
                    f"🕒 Time: `{row.get('Timestamp', 'Unknown')}`\n"
                    f"📊 Rank/Seed: `{row.get('Rank', '?')}` / `{row.get('Seed', '?')}`\n"
                    f"**Excel:** `{row.get('Excel Success', '?')}`, Archive: `{row.get('Archive Success', '?')}`\n"
                    f"🧠 SQL: `{row.get('SQL Success', '?')}` | 📤 Export: `{row.get('Export Success', '?')}`\n"
                    f"⏱ Duration: `{row.get('Duration (sec)', '?')}`"
                ),
                inline=False,
            )
        embed.timestamp = discord.utils.utcnow()
        return embed

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def previous(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page <= 1:
            await interaction.response.defer()
            return
        self.page -= 1
        await self._refresh_message(interaction)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next(self, button: discord.ui.Button, interaction: discord.Interaction):
        if self.page >= self.total_pages:
            await interaction.response.defer()
            return
        self.page += 1
        await self._refresh_message(interaction)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
            elif self.interaction:
                msg = await self.interaction.original_response()
                await msg.edit(view=self)
        except Exception as e:
            logger.warning(f"[FailuresView] Failed to disable buttons after timeout: {e}")


def build_target_embed(data):
    gov_name = md_escape(str(data.get("GovernorName", "Unknown")))
    embed = discord.Embed(title=f"🎯 KVK Targets for {gov_name}", color=INFO_COLOR)
    embed.add_field(name="Governor ID", value=str(data.get("GovernorID", "—")), inline=False)
    embed.add_field(name="Kill Target", value=fmt_short(data.get("KillTarget", 0)), inline=True)
    embed.add_field(name="Dead Target", value=fmt_short(data.get("DeadTarget", 0)), inline=True)
    embed.add_field(name="DKP Target", value=fmt_short(data.get("DKPTarget", 0)), inline=True)
    embed.set_footer(text="K98 Discord bot • KVK Targets")
    embed.timestamp = discord.utils.utcnow()
    return embed


def format_fight_embed(fights):
    embed = discord.Embed(
        title="🔥 Upcoming Fights",
        color=DANGER_COLOR,
    )
    embed.set_thumbnail(url="https://i.ibb.co/FLPsD22x/FIGHTS.jpg")

    for event in fights:
        name = md_escape(event.get("name", "(Unnamed Event)"))
        start = event.get("start_time")
        if not start:
            continue
        countdown = format_countdown(start, short=True)
        value = f"{format_event_time(start)}  ({countdown})"  # UTC
        if len(value) > 1024:
            value = value[:1021] + "…"
        embed.add_field(name=f"⚔️ {name}", value=value, inline=False)

    embed.set_footer(
        text="Times shown in UTC — use the button to view in your local time & switch between 1 or 3 upcoming fights."
    )
    embed.timestamp = discord.utils.utcnow()
    return embed


def format_event_embed(events):
    embed = discord.Embed(
        title="📅 Upcoming Event(s)",
        color=INFO_COLOR,
    )

    for event in events:
        name = md_escape(event.get("name", "(Unnamed Event)"))
        start = event.get("start_time")
        if not start:
            continue
        countdown = format_countdown(start, short=True)
        value = f"{format_event_time(start)}  ({countdown})"  # UTC
        description = event.get("description")
        if description:
            value += f"\n\n📖 {md_escape(description)}"
        if len(value) > 1024:
            value = value[:1021] + "…"
        embed.add_field(name=name, value=value, inline=False)

    embed.set_footer(text="Times shown in UTC — use the local-time button to convert.")
    embed.timestamp = discord.utils.utcnow()
    return embed


async def expire_old_event_embeds(bot: discord.Client):
    try:
        with open(VIEW_TRACKING_FILE, encoding="utf-8") as f:
            views = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("[expire_embeds] View tracker file not found or invalid.")
        return

    now = discord.utils.utcnow()
    today = now.date()
    yesterday = today - timedelta(days=1)

    views_to_update = views.copy()

    for key in ("nextevent", "nextfight"):
        data = views.get(key)
        if not data:
            continue

        created_at_str = data.get("created_at")
        if not created_at_str:
            continue

        try:
            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        except ValueError:
            print(f"[expire_embeds] Invalid timestamp for {key}: {created_at_str}")
            continue

        if created_at.date() != yesterday:
            continue  # Not expired yet

        channel_id = data.get("channel_id")
        message_id = data.get("message_id")

        try:
            channel = await bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            await message.delete()
            print(f"[expire_embeds] Deleted outdated `{key}` embed.")
        except Exception as e:
            print(f"[expire_embeds] Failed to delete `{key}` message: {e}")
            continue  # Skip regeneration if delete failed

        if AUTO_REGENERATE:
            try:
                from command_regenerate import regenerate_embed

                new_embed_data = await regenerate_embed(key, channel)
                if new_embed_data:
                    views_to_update[key] = new_embed_data
                    print(f"[expire_embeds] Regenerated `{key}` embed and updated tracker.")
                else:
                    print(
                        f"[expire_embeds] Regeneration returned no data for `{key}` — keeping old."
                    )
                    continue  # Keep old entry
            except Exception as e:
                print(f"[expire_embeds] Regeneration failed for `{key}`: {e}")
                continue  # Keep old entry
        else:
            del views_to_update[key]  # Only remove if not regenerating

    with open(VIEW_TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(views_to_update, f, indent=2, ensure_ascii=False)
        print("[expire_embeds] View tracker file updated.")


def build_stats_embed(governor_data, discord_user) -> tuple[discord.Embed, discord.File]:
    def clamp(v, lo=0.0, hi=100.0):
        try:
            return max(lo, min(hi, float(v)))
        except Exception:
            return 0.0

    governor_name = md_escape(governor_data.get("GovernorName", "Unknown"))
    KVK_NO = int(governor_data.get("KVK_NO", 0) or 0)
    governor_id = str(governor_data.get("GovernorID", "Unknown"))
    power_int = int(governor_data.get("Power", 0) or 0)
    power = fmt_short(power_int)
    kvk_rank = governor_data.get("KVK_RANK", "—")
    status_raw = str(governor_data.get("STATUS", "") or "").strip().upper()
    is_exempt = status_raw == "EXEMPT"

    # Targets
    kill_target = int(governor_data.get("Kill Target", 0) or 0)
    dead_target = int(governor_data.get("Dead Target", 0) or 0)
    dkp_target = int(governor_data.get("DKPTarget", 0) or 0)
    no_targets_set = kill_target == 0 and dead_target == 0 and dkp_target == 0

    # Stats
    T4_kills = int(governor_data.get("T4_Kills", 0) or 0)
    T5_kills = int(governor_data.get("T5_Kills", 0) or 0)
    Total_kills = int(governor_data.get("T4&T5_Kills", 0) or 0)
    T4_deads = int(governor_data.get("T4_Deads", 0) or 0)
    T5_deads = int(governor_data.get("T5_Deads", 0) or 0)
    deads = int(governor_data.get("Deads", 0) or 0)
    dkp = float(governor_data.get("DKP Score", 0) or 0.0)

    # Percent calculations (only when targets exist)
    if is_exempt:
        # use Nones to hide % text + avoid drawing a progress dial with numbers
        kills_pct_raw = deads_pct_raw = dkp_pct_raw = None
    else:
        # compute RAW (unclamped) values so text can show >100%
        kills_pct_raw = (Total_kills / kill_target * 100.0) if kill_target else None
        deads_pct_raw = (deads / dead_target * 100.0) if dead_target else None
        dkp_pct_raw = (dkp / dkp_target * 100.0) if dkp_target else None
        # (optional) If you want clamped values handy for anything else:
        # kills_pct = clamp(kills_pct_raw or 0.0)
        # deads_pct = clamp(deads_pct_raw or 0.0)
        # dkp_pct   = clamp(dkp_pct_raw or 0.0)

    # Last refresh
    last_refresh = governor_data.get("LAST_REFRESH", "—")

    def _fmt_last_refresh(val):
        if isinstance(val, datetime):
            return val.strftime("%d %B %Y")
        try:
            s = str(val)
            if s.endswith("Z"):
                s = s.replace("Z", "+00:00")
            return datetime.fromisoformat(s).strftime("%d %B %Y")
        except Exception:
            return "—"

    last_refresh_str = _fmt_last_refresh(last_refresh)

    # Build embed
    title = f"🧾 KVK {KVK_NO} • {governor_name} — ID {governor_id}"
    embed = discord.Embed(title=title[:256], color=INFO_COLOR, timestamp=discord.utils.utcnow())
    # Always use the global custom avatar for consistency
    thumb_url = CUSTOM_AVATAR_URL
    try:
        if not thumb_url and getattr(discord_user, "display_avatar", None):
            thumb_url = discord_user.display_avatar.url
    except Exception:
        pass
    if thumb_url:
        embed.set_thumbnail(url=thumb_url)

    embed.add_field(name="🏅 KVK Rank", value=f"**{kvk_rank}**", inline=True)
    embed.add_field(name="MM Power", value=power, inline=True)

    # Targets block with new logic
    if is_exempt:
        targets_text = "📛 This player is **exempt** from all targets."
    else:
        if no_targets_set:
            if power_int < 40_000_000:
                targets_text = "🍼 Power below **40M** — no targets set. Just do what you can!"
            else:
                targets_text = "⏳ Targets not yet assigned. Please check back soon."
        else:
            targets_text = (
                f"🗡 Kills: **{fmt_short(kill_target)}**\n"
                f"💀 Deads: **{fmt_short(dead_target)}**\n"
                f"🧮 DKP: **{fmt_short(dkp_target)}**"
            )
    embed.add_field(name="🎯 Targets", value=targets_text, inline=False)

    # Per-metric % visibility flags
    show_kill_pct = (not is_exempt) and (kill_target > 0) and (kills_pct_raw is not None)
    show_dead_pct = (not is_exempt) and (dead_target > 0) and (deads_pct_raw is not None)
    show_dkp_pct = (not is_exempt) and (dkp_target > 0) and (dkp_pct_raw is not None)

    # Kills
    kills_val = (
        f"T4: **{fmt_short(T4_kills)}**\n"
        f"T5: **{fmt_short(T5_kills)}**\n"
        f"T4&T5: **{fmt_short(Total_kills)}**"
        + (f" **({fmt_pct(kills_pct_raw)})**" if show_kill_pct else "")
    )
    embed.add_field(name="🗡 KILLS", value=kills_val, inline=False)

    # Deads
    deads_val = (
        f"T4: **{fmt_short(T4_deads)}**\n"
        f"T5: **{fmt_short(T5_deads)}**\n"
        f"Total: **{fmt_short(deads)}**"
        + (f" **({fmt_pct(deads_pct_raw)})**" if show_dead_pct else "")
    )
    embed.add_field(name="💀 DEADS", value=deads_val, inline=False)

    # DKP
    dkp_val = (
        "📛 Exempt from DKP target."
        if is_exempt
        else f"**{fmt_short(int(dkp))}**"
        + (f" **({fmt_pct(dkp_pct_raw)})**" if show_dkp_pct else "")
    )
    embed.add_field(name="🧮 DKP", value=dkp_val, inline=False)

    embed.add_field(
        name="🕒 Last Updated",
        value=f"{last_refresh_str} — Requested: {discord_user.mention}",
        inline=False,
    )
    embed.set_footer(text="K98 Stats Bot")

    # Dial image
    if is_exempt:
        img_bytes = generate_exempt_dial()
    else:
        # Dial clamped to [0,100], label shows RAW (can be >100)
        dial_pct = clamp(kills_pct_raw if kills_pct_raw is not None else 0.0)
        img_bytes = generate_progress_dial(dial_pct, display_percent=kills_pct_raw)
    file = discord.File(img_bytes, filename="progress.png")
    embed.set_image(url="attachment://progress.png")

    return embed, file
