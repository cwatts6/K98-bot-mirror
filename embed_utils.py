# embed_utils.py
from __future__ import annotations  # 🔒 avoid runtime eval of type hints

from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)
from collections.abc import Awaitable, Callable
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
from file_utils import (
    cursor_row_to_dict,
    emit_telemetry_event,
    get_conn_with_retries,
    read_summary_log_rows,
)
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


def _get_int_from_variants(d: dict, candidates: list[str], default: int = 0) -> int:
    """
    Try several possible keys in `d` and coerce the first non-empty value
    to an integer (handles int/float/str). Returns `default` on failure.
    """
    for k in candidates:
        try:
            if k in d and d[k] is not None and str(d[k]).strip() != "":
                # Accept ints, floats or numeric strings
                val = d[k]
                # convert booleans and weird values defensively
                if isinstance(val, bool):
                    return int(val)
                try:
                    return int(float(val))
                except Exception:
                    # fallback to int() for numeric-like strings
                    try:
                        return int(val)
                    except Exception:
                        continue
        except Exception:
            continue
    return default


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


def _truncate_embed_title(title: str | None, max_len: int = 256) -> str:
    text = title or ""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return text[:max_len]
    return f"{text[: max_len - 1]}…"


class LocalTimeToggleView(View):
    def __init__(self, events, prefix="default", timeout=None):
        """
        LocalTimeToggleView builds a single-button view that, when clicked,
        shows the same event(s) in the user's local time.
        """
        super().__init__(timeout=timeout)
        self.events = events
        self.prefix = prefix

        safe_prefix = sanitize_view_prefix(self.prefix, max_len=64)
        custom_id = f"{safe_prefix}_local_time_toggle"
        if len(custom_id) > 100:
            custom_id = custom_id[:100]

        self.add_item(LocalTimeButton(custom_id=custom_id))

    async def build_local_time_embed(self):
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
            embed_title = (
                f"📅 {self.events[0].get('name') or self.events[0].get('title')} – Local Time View"
            )
        else:
            types = {(e.get("type") or "").lower() for e in self.events}
            embed_title = (
                "⚔️ Upcoming Fights – Local Time View"
                if types and types.issubset({"altar", "altars"})
                else "📊 Upcoming Events – Local Time View"
            )

        embed = discord.Embed(
            title=_truncate_embed_title(embed_title),
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
    def __init__(
        self,
        matches: list[dict],
        on_lookup: Callable[[discord.Interaction, str], Awaitable[None]],
        timeout: float = 60,
    ):
        super().__init__(timeout=timeout)
        self.matches = matches
        self.on_lookup = on_lookup

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

            # Delegate lookup behavior via injected callback to avoid UI -> command imports.
            try:
                await self.on_lookup(interaction, governor_id)
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


def _load_last_kvk_for_governor(governor_id: str) -> dict | None:
    """
    Try to load the separate last-KVK cache and return the record for governor_id (if present).
    Uses PLAYER_STATS_LAST_CACHE from constants if available; otherwise derives a sibling file name.
    This is intentionally lightweight and returns None on any failure.
    """
    try:
        from constants import PLAYER_STATS_LAST_CACHE

        last_path = PLAYER_STATS_LAST_CACHE
    except Exception:
        try:
            from constants import PLAYER_STATS_CACHE

            base, ext = os.path.splitext(PLAYER_STATS_CACHE)
            if ext:
                last_path = f"{base}.lastkvk{ext}"
            else:
                last_path = f"{PLAYER_STATS_CACHE}.lastkvk"
        except Exception:
            return None

    try:
        with open(last_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    # data format: { "_meta": {...}, "<GovernorID>": { ... }, ... }
    try:
        return data.get(str(governor_id))
    except Exception:
        return


# Helpers to fetch per-governor Pre-KVK phase deltas and latest honor list
def _fetch_prekvk_phase_list(kvk_no: int, phase: int) -> list[dict[str, Any]]:
    """
    Return list of dicts with keys GovernorID, Name, Points for the given KVK and phase.
    Uses the same delta computation logic as stats_alerts/prekvk_stats._phase_top but returns all rows.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                WITH W AS (
                  SELECT StartUTC, EndUTC
                  FROM dbo.PreKvk_Phases
                  WHERE KVK_NO = ? AND Phase = ?
                ),
                B AS (
                  SELECT sc.GovernorID,
                         MAX(sc.Points) AS Baseline
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  CROSS JOIN W
                  WHERE sc.KVK_NO = ? AND s.ScanTimestampUTC < W.StartUTC
                  GROUP BY sc.GovernorID
                ),
                P AS (
                  SELECT sc.GovernorID,
                         MAX(sc.Points) AS InWindow
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  CROSS JOIN W
                  WHERE sc.KVK_NO = ? AND s.ScanTimestampUTC BETWEEN W.StartUTC AND W.EndUTC
                  GROUP BY sc.GovernorID
                ),
                Names AS (
                  SELECT sc.GovernorID, MAX(sc.GovernorName) AS GovernorName
                  FROM dbo.PreKvk_Scores sc
                  JOIN dbo.PreKvk_Scan s ON s.KVK_NO = sc.KVK_NO AND s.ScanID = sc.ScanID
                  WHERE sc.KVK_NO = ?
                  GROUP BY sc.GovernorID
                )
                SELECT COALESCE(p.GovernorID, b.GovernorID) AS GovernorID,
                       COALESCE(n.GovernorName, CONVERT(varchar(20), COALESCE(p.GovernorID, b.GovernorID))) AS Name,
                       MAX(COALESCE(p.InWindow, b.Baseline, 0)) - MAX(COALESCE(b.Baseline, 0)) AS Points
                FROM B b
                FULL JOIN P p ON p.GovernorID = b.GovernorID
                LEFT JOIN Names n ON n.GovernorID = COALESCE(p.GovernorID, b.GovernorID)
                GROUP BY COALESCE(p.GovernorID, b.GovernorID), COALESCE(n.GovernorName, CONVERT(varchar(20), COALESCE(p.GovernorID, b.GovernorID)))
                ORDER BY Points DESC, Name;
                """,
                (kvk_no, phase, kvk_no, kvk_no, kvk_no),
            )
            rows = cur.fetchall()
            if not rows:
                return []
            return [cursor_row_to_dict(cur, r) for r in rows]
    except Exception:
        logger.exception("[PREKVK] Failed to fetch phase list for KVK %s phase %s", kvk_no, phase)
        return []


def _fetch_latest_honor_list() -> list[dict[str, Any]]:
    """
    Return the full latest honor list (GovernorName, GovernorID, HonorPoints) ordered desc.
    """
    try:
        conn = get_conn_with_retries()
        with conn:
            cur = conn.cursor()
            sql = """
            ;WITH latest_kvk AS (
                SELECT MAX(KVK_NO) AS KVK_NO
                FROM dbo.KVK_Honor_Scan
            ),
            last_scan AS (
                SELECT s.KVK_NO, MAX(s.ScanID) AS ScanID
                FROM dbo.KVK_Honor_Scan s
                JOIN latest_kvk k ON k.KVK_NO = s.KVK_NO
                GROUP BY s.KVK_NO
            )
            SELECT a.GovernorName, a.GovernorID, a.HonorPoints
            FROM dbo.KVK_Honor_AllPlayers_Raw a
            JOIN last_scan l ON l.KVK_NO = a.KVK_NO AND l.ScanID = a.ScanID
            ORDER BY a.HonorPoints DESC, a.GovernorID ASC;
            """
            cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                return []
            return [cursor_row_to_dict(cur, r) for r in rows]
    except Exception:
        logger.exception("[HONOR] Failed to fetch latest honor list")
        return []


def build_target_embed(data):
    gov_name = md_escape(str(data.get("GovernorName", "Unknown")))
    embed = discord.Embed(title=f"🎯 KVK Targets for {gov_name}", color=INFO_COLOR)
    embed.add_field(name="Governor ID", value=str(data.get("GovernorID", "—")), inline=False)
    embed.add_field(name="Kill Target", value=fmt_short(data.get("KillTarget", 0)), inline=True)
    embed.add_field(name="Dead Target", value=fmt_short(data.get("DeadTarget", 0)), inline=True)
    embed.add_field(name="DKP Target", value=fmt_short(data.get("DKPTarget", 0)), inline=True)
    last_kvk = data.get("last_kvk") or _load_last_kvk_for_governor(str(data.get("GovernorID", "")))
    if last_kvk:
        try:
            lk_kvk_no = last_kvk.get("KVK_NO", None)
            lk_total_kills = int(last_kvk.get("T4&T5_Kills", 0) or 0)
            lk_kill_target = int(last_kvk.get("Kill Target", 0) or 0)
            lk_kill_pct = None
            if lk_kill_target:
                lk_kill_pct = (lk_total_kills / lk_kill_target) * 100.0
            lk_dkp = float(last_kvk.get("DKP_Score", 0) or 0.0)
            lk_line = (
                f"KVK {lk_kvk_no}: Kills {fmt_short(lk_total_kills)} / {fmt_short(lk_kill_target)} "
                + (f"({fmt_pct(lk_kill_pct)}) " if lk_kill_pct is not None else "")
                + f"• DKP {fmt_short(int(lk_dkp))}"
            )
            embed.add_field(name="Last KVK Summary", value=lk_line, inline=False)
        except Exception:
            logger.exception("[EMBED] Failed to render last_kvk summary for target embed")

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


def build_stats_embed(governor_data, discord_user) -> tuple[list[discord.Embed], discord.File]:
    """
    Return three embeds + the dial image file in this order:
      1) embed_summary: primary stats (targets, rank, kills, deads, dkp, healed delta, acclaim) — condensed (blue)
      2) embed_dial: dial image + Last Updated footer (visual) — red
      3) embed_history: Historic KVK Data — history, Last KVK summary, MatchMaking snapshot — condensed (green)

    Caller should send like:
      embeds, file = build_stats_embed(data, user)
      await channel.send(embeds=embeds, files=[file])
    """

    def clamp(v, lo=0.0, hi=100.0):
        try:
            return max(lo, min(hi, float(v)))
        except Exception:
            return 0.0

    governor_name = md_escape(governor_data.get("GovernorName", "Unknown"))
    KVK_NO = int(governor_data.get("KVK_NO", 0) or 0)
    governor_id = str(governor_data.get("GovernorID", "Unknown"))

    # Updated: prefer Starting Power / Starting_Power variants (cache uses "Starting Power")
    power_int = _get_int_from_variants(
        governor_data, ["Starting Power", "Starting_Power", "StartingPower", "Power"], default=0
    )
    power = fmt_short(power_int)

    kvk_rank = governor_data.get("KVK_RANK", "—")
    status_raw = str(governor_data.get("STATUS", "") or "").strip().upper()
    is_exempt = status_raw == "EXEMPT"

    # Targets
    kill_target = _get_int_from_variants(
        governor_data, ["Kill Target", "Kill_Target", "KillTarget"], default=0
    )
    dead_target = _get_int_from_variants(
        governor_data, ["Dead_Target", "Dead Target", "DeadTarget"], default=0
    )
    # DKP target may appear as DKP_Target or DKP Target or DKP_Target in cache
    dkp_target = _get_int_from_variants(
        governor_data, ["DKP_Target", "DKP Target", "DKP_Target"], default=0
    )
    no_targets_set = kill_target == 0 and dead_target == 0 and dkp_target == 0

    # Stats
    T4_kills = _get_int_from_variants(
        governor_data, ["T4_KILLS", "T4_Kills", "T4 KILLS"], default=0
    )
    T5_kills = _get_int_from_variants(
        governor_data, ["T5_KILLS", "T5_Kills", "T5 KILLS"], default=0
    )
    Total_kills = _get_int_from_variants(
        governor_data, ["T4&T5_Kills", "T4&T5_Kills", "T4&T5 Kills"], default=0
    )
    T4_deads = _get_int_from_variants(governor_data, ["T4_Deads", "T4 Deads"], default=0)
    T5_deads = _get_int_from_variants(governor_data, ["T5_Deads", "T5 Deads"], default=0)

    # Updated: use Deads_Delta per new cache layout (user requested)
    deads = _get_int_from_variants(
        governor_data, ["Deads_Delta", "Deads Delta", "Deads"], default=0
    )

    # DKP score/key - tolerantly parse common variants (DKP_SCORE, DKP Score, DKP_Score)
    dkp_raw = None
    for k in ("DKP_SCORE", "DKP Score", "DKP_Score", "DKP_SCORE"):
        if k in governor_data and governor_data[k] is not None:
            dkp_raw = governor_data[k]
            break
    try:
        dkp = float(dkp_raw or 0.0)
    except Exception:
        try:
            dkp = float(str(dkp_raw or "0").strip())
        except Exception:
            dkp = 0.0

    # KillPoints (use delta as primary KP shown)
    kp = _get_int_from_variants(
        governor_data,
        ["KillPointsDelta", "Kill Points Delta", "KillPoints_Delta", "KillPoints"],
        default=0,
    )

    # Healed Troops (total + delta)
    healed_total = _get_int_from_variants(
        governor_data,
        [
            "Starting_HealedTroops",
            "Starting HealedTroops",
            "Starting_Healed_Troops",
            "Starting Healed Troops",
        ],
        default=0,
    )
    healed_delta = _get_int_from_variants(
        governor_data,
        ["HealedTroopsDelta", "Healed Troops Delta", "Healed_Troops_Delta"],
        default=0,
    )

    # KVK lifetime / historic bests (from player_stats_cache)
    kvk_played = _get_int_from_variants(
        governor_data, ["KvKPlayed", "KVK Played", "KVK_Played"], default=0
    )
    highest_acclaim = _get_int_from_variants(
        governor_data, ["HighestAcclaim", "Highest_Acclaim", "Highest Acclaim"], default=0
    )
    autarch_times = _get_int_from_variants(
        governor_data, ["AutarchTimes", "Autarch Times", "Autarch_Times", "AUTARCHTIMES"], default=0
    )
    most_kill = _get_int_from_variants(
        governor_data, ["MostKvKKill", "MostKvK_Kill", "Most KvK Kill"], default=0
    )
    most_dead = _get_int_from_variants(
        governor_data, ["MostKvKDead", "MostKvK_Dead", "Most KvK Dead"], default=0
    )
    most_heal = _get_int_from_variants(
        governor_data, ["MostKvKHeal", "MostKvK_Heal", "Most KvK Heal"], default=0
    )

    # Acclaim (current / lifetime display)
    acclaim = _get_int_from_variants(governor_data, ["Acclaim", "AcclaimScore"], default=0)

    # Starting/MM snapshot fields (new in enhanced STATS_FOR_UPLOAD)
    starting_kp = _get_int_from_variants(
        governor_data,
        ["Starting_KillPoints", "Starting KillPoints", "StartingKillPoints"],
        default=0,
    )
    starting_kills = _get_int_from_variants(
        governor_data,
        ["Starting_T4&T5_KILLS", "Starting T4&T5 Kills", "Starting_T4&T5_KILLS"],
        default=0,
    )
    starting_deads = _get_int_from_variants(
        governor_data, ["Starting_Deads", "Starting Deads"], default=0
    )

    # New: Pre-KVK and Honor fields
    prek_vk = _get_int_from_variants(
        governor_data, ["Max_PreKvk_Points", "Max PreKvk Points", "Max_PreKvk_Points"], default=0
    )
    prek_vk_rank = _get_int_from_variants(
        governor_data, ["PreKvk_Rank", "PreKvk Rank", "PreKvk_Rank"], default=0
    )
    honor = _get_int_from_variants(
        governor_data, ["Max_HonorPoints", "Max Honor Points", "Max_HonorPoints"], default=0
    )
    honor_rank = _get_int_from_variants(
        governor_data, ["Honor_Rank", "Honor Rank", "Honor_Rank"], default=0
    )

    # Pass counters (show if > 0)
    pass_keys = [
        "Pass 4 Kills",
        "Pass 6 Kills",
        "Pass 7 Kills",
        "Pass 8 Kills",
        "Pass 4 Deads",
        "Pass 6 Deads",
        "Pass 7 Deads",
        "Pass 8 Deads",
    ]
    pass_values = []
    for pk in pass_keys:
        v = _get_int_from_variants(governor_data, [pk, pk.replace(" ", "_")], default=0)
        if v and v > 0:
            # shorten label for display
            label = pk.replace("Pass ", "P").replace(" Kills", "K").replace(" Deads", "D")
            pass_values.append(f"{label}: {fmt_short(v)}")

    # Percent calculations (only when targets exist)
    if is_exempt:
        kills_pct_raw = deads_pct_raw = dkp_pct_raw = None
    else:
        kills_pct_raw = (Total_kills / kill_target * 100.0) if kill_target else None
        deads_pct_raw = (deads / dead_target * 100.0) if dead_target else None
        dkp_pct_raw = (dkp / dkp_target * 100.0) if dkp_target else None

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

    # -----------------------
    # Embed 1: Primary summary (now includes targets + primary stats) - Blue
    # -----------------------
    title = f"🧾 KVK {KVK_NO} • {governor_name} — ID {governor_id}"
    embed_summary = discord.Embed(
        title=title[:256], color=INFO_COLOR, timestamp=discord.utils.utcnow()
    )

    # Targets line (compact) — MM Power moved to its own line (factory emoji)
    if is_exempt:
        targets_text = "📛 Exempt from targets"
    else:
        if no_targets_set:
            if power_int < 40_000_000:
                targets_text = "🍼 Power < 40M — no targets set"
            else:
                targets_text = "⏳ Targets not yet assigned"
        else:
            targets_text = f"🗡 {fmt_short(kill_target)} • 💀 {fmt_short(dead_target)} • 🧮 {fmt_short(dkp_target)}"
    embed_summary.add_field(name="🎯 Targets", value=targets_text, inline=False)

    # MM Power as its own line with factory emoji
    try:
        embed_summary.add_field(name="🏭 MM Power", value=f"{power}", inline=False)
    except Exception:
        pass

    # KVK Rank as separate field
    embed_summary.add_field(name="🏅 KVK Rank", value=f"**{kvk_rank}**", inline=False)

    # KILLS condensed
    kills_parts = [
        f"T4: {fmt_short(T4_kills)}",
        f"T5: {fmt_short(T5_kills)}",
        f"T4&T5: {fmt_short(Total_kills)}",
    ]
    kills_pct_piece = ""
    if not is_exempt and kill_target and kills_pct_raw is not None:
        kills_pct_piece = f"({fmt_pct(kills_pct_raw)})"
    kills_main = " • ".join(kills_parts) + (f" • {kills_pct_piece}" if kills_pct_piece else "")
    embed_summary.add_field(
        name="🗡 KILLS", value=f"{kills_main}\nKP: {fmt_short(kp)}", inline=False
    )

    # DEADS condensed
    deads_parts = [
        f"T4: {fmt_short(T4_deads)}",
        f"T5: {fmt_short(T5_deads)}",
        f"Delta: {fmt_short(deads)}",
    ]
    deads_pct_piece = ""
    if not is_exempt and dead_target and deads_pct_raw is not None:
        deads_pct_piece = f"({fmt_pct(deads_pct_raw)})"
    deads_main = " • ".join(deads_parts) + (f" • {deads_pct_piece}" if deads_pct_piece else "")
    embed_summary.add_field(name="💀 DEADS", value=deads_main, inline=False)

    # DKP
    dkp_text = "📛 Exempt" if is_exempt else f"{fmt_short(int(dkp))}"
    if not is_exempt and dkp_target and dkp_pct_raw is not None:
        dkp_text += f" ({fmt_pct(dkp_pct_raw)})"
    embed_summary.add_field(name="🧮 DKP", value=dkp_text, inline=False)

    # Passes (if any non-zero)
    if pass_values:
        embed_summary.add_field(name="📈 Passes", value=" • ".join(pass_values), inline=False)

    # HEALED Δ (only delta shown)
    try:
        if healed_delta:
            sign = "+" if healed_delta > 0 else ""
            embed_summary.add_field(
                name="🏥 HEALED Δ", value=f"{sign}{fmt_short(healed_delta)}", inline=False
            )
    except Exception:
        pass

    # ACCLAIM
    embed_summary.add_field(name="🏆 ACCLAIM", value=f"{fmt_short(acclaim)}", inline=False)

    # Pre-KVK (separate field) — show only if > 0
    if prek_vk and prek_vk > 0:
        try:
            embed_summary.add_field(
                name="🎖️ Pre KVK",
                value=f"Rank: {prek_vk_rank}. Points: {fmt_short(prek_vk)}",
                inline=False,
            )
        except Exception:
            pass

    # Honor (separate field) — show only if > 0
    if honor and honor > 0:
        try:
            embed_summary.add_field(
                name="🛡️ Honor",
                value=f"Rank: {honor_rank}. Points: {fmt_short(honor)}",
                inline=False,
            )
        except Exception:
            pass

    # Optional thumbnail
    thumb_url = CUSTOM_AVATAR_URL
    try:
        if not thumb_url and getattr(discord_user, "display_avatar", None):
            thumb_url = discord_user.display_avatar.url
    except Exception:
        pass
    if thumb_url:
        embed_summary.set_thumbnail(url=thumb_url)

    # -----------------------
    # Embed 2: Dial image + Last Updated (visual) - Red
    # -----------------------
    if is_exempt:
        img_bytes = generate_exempt_dial()
    else:
        dial_pct = clamp(kills_pct_raw if kills_pct_raw is not None else 0.0)
        img_bytes = generate_progress_dial(dial_pct, display_percent=kills_pct_raw)
    file = discord.File(img_bytes, filename="progress.png")

    embed_dial = discord.Embed(color=DANGER_COLOR)
    embed_dial.set_image(url="attachment://progress.png")
    embed_dial.add_field(
        name="🕒 Last Updated",
        value=f"{last_refresh_str} — Requested: {discord_user.mention}",
        inline=False,
    )
    embed_dial.set_footer(text="K98 Stats Bot")

    # -----------------------
    # Embed 3: Historic KVK Data (condensed) - Green
    # -----------------------
    embed_history = discord.Embed(title="📜 Historic KVK Data", color=SUCCESS_COLOR)

    try:
        hist = f"Autarch: {fmt_short(autarch_times)} • KvK Played: {fmt_short(kvk_played)} • Highest Acclaim: {fmt_short(highest_acclaim)}"  # MODIFY THIS LINE
        bests = f"Most Kills: {fmt_short(most_kill)} • Most Deads: {fmt_short(most_dead)} • Most Heal: {fmt_short(most_heal)}"
        # Remove blank field; use a named summary field instead
        embed_history.add_field(name="Summary", value=f"{hist}\n{bests}", inline=False)
    except Exception:
        pass

    # Last KVK summary condensed with the requested section title format
    last_kvk = governor_data.get("last_kvk") or _load_last_kvk_for_governor(str(governor_id))
    if last_kvk:
        try:
            lk_kvk_no = last_kvk.get("KVK_NO", None)
            lk_total_kills = int(last_kvk.get("T4&T5_Kills", 0) or 0)
            lk_kill_target = int(last_kvk.get("Kill Target", 0) or 0)
            lk_dkp = float(last_kvk.get("DKP_SCORE", 0) or 0.0)
            try:
                lk_dkp_target = int(
                    last_kvk.get("DKP Target")
                    or last_kvk.get("DKP_Target")
                    or last_kvk.get("DKPTarget")
                    or 0
                )
            except Exception:
                lk_dkp_target = 0
            lk_kill_pct = (lk_total_kills / lk_kill_target * 100.0) if lk_kill_target else None
            lk_dkp_pct = (lk_dkp / lk_dkp_target * 100.0) if lk_dkp_target else None

            try:
                lk_kp_delta = int(last_kvk.get("KillPointsDelta", 0) or 0)
            except Exception:
                lk_kp_delta = 0

            try:
                lk_deads_delta = int(last_kvk.get("Deads_Delta", 0) or 0)
            except Exception:
                lk_deads_delta = 0

            try:
                lk_dead_target = int(last_kvk.get("Dead_Target", 0) or 0)
            except Exception:
                lk_dead_target = 0

            lk_healed = _get_int_from_variants(
                last_kvk, ["HealedTroops", "Healed_Troops", "Healed Troops", "Healed"], default=0
            )
            lk_healed_delta = _get_int_from_variants(
                last_kvk,
                [
                    "HealedTroopsDelta",
                    "Healed Troops Delta",
                    "Healed_Troops_Delta",
                    "HealedTroops_Delta",
                ],
                default=0,
            )

            parts = []
            parts.append(
                f"⚔️ {fmt_short(lk_total_kills)}/{fmt_short(lk_kill_target)}{(' ' + fmt_pct(lk_kill_pct)) if lk_kill_pct is not None else ''}"
            )
            if lk_deads_delta and lk_dead_target:
                lk_deads_pct = (lk_deads_delta / lk_dead_target * 100.0) if lk_dead_target else None
                deads_piece = f"💀 {fmt_short(lk_deads_delta)}/{fmt_short(lk_dead_target)}"
                if lk_deads_pct is not None:
                    deads_piece += f" {fmt_pct(lk_deads_pct)}"
                parts.append(deads_piece)
            elif lk_deads_delta:
                parts.append(f"💀 {fmt_short(lk_deads_delta)}")

            if lk_dkp_target:
                parts.append(
                    f"🧮 {fmt_short(int(lk_dkp))}/{fmt_short(int(lk_dkp_target))} ({fmt_pct(lk_dkp_pct)})"
                )
            else:
                parts.append(f"🎯 {fmt_short(int(lk_dkp))}")
            if lk_kp_delta:
                parts.append(f"KP: {fmt_short(lk_kp_delta)}")
            if lk_healed:
                healed_piece = f"🏥 {fmt_short(lk_healed)}"
                if lk_healed_delta:
                    healed_piece += f" (/ {fmt_short(lk_healed_delta)})"
                parts.append(healed_piece)
            if lk_acclaim := _get_int_from_variants(
                last_kvk, ["Acclaim", "AcclaimScore", "ACCLAIM", "HighestAcclaim"], default=0
            ):
                parts.append(f"🏆 {fmt_short(lk_acclaim)}")

            # Use the combined section title requested
            section_title = f"Last KVK Summary • KVK {lk_kvk_no}"
            embed_history.add_field(name=section_title, value=" • ".join(parts), inline=False)
        except Exception:
            logger.exception("[EMBED] Failed to render last_kvk summary for history embed")

    # MM Snapshot condensed (single-line)
    mm_parts = [
        f"MM KP: {fmt_short(starting_kp)}",
        f"MM Kills: {fmt_short(starting_kills)}",
        f"MM Deads: {fmt_short(starting_deads)}",
        f"MM Healed: {fmt_short(healed_total)}",
    ]
    embed_history.add_field(name="MatchMaking Snapshot", value=" • ".join(mm_parts), inline=False)

    return [embed_summary, embed_dial, embed_history], file
