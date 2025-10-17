# Decoraters.py
from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
import functools
from functools import wraps
import logging
import time
from typing import Any

import discord

from bot_config import (
    ADMIN_USER_ID,
    LEADERSHIP_CHANNEL_ID,
    LEADERSHIP_ROLE_IDS,
    LEADERSHIP_ROLE_NAMES,
    NOTIFY_CHANNEL_ID,
)
from usage_tracker import AsyncUsageTracker

# --- ID normalization (robust if env/config values are strings) ---
ADMIN_USER_ID = int(ADMIN_USER_ID)
ALLOWED_CHANNEL_IDS = {int(NOTIFY_CHANNEL_ID), int(LEADERSHIP_CHANNEL_ID)}
LEADERSHIP_ROLE_IDS = [int(x) for x in (LEADERSHIP_ROLE_IDS or [])]

# --- Helpers -------------------------------------------------------

log = logging.getLogger(__name__)


def _resolve_interaction(arg0) -> discord.Interaction | None:
    """Support callbacks receiving either ctx or interaction."""
    if isinstance(arg0, discord.Interaction):
        return arg0
    return getattr(arg0, "interaction", None)


def _actor_from_ctx(ctx):
    interaction = getattr(ctx, "interaction", None)
    user = (
        getattr(ctx, "user", None)
        or (getattr(interaction, "user", None) if interaction else None)
        or getattr(ctx, "author", None)
    )
    guild = getattr(ctx, "guild", None) or (
        getattr(interaction, "guild", None) if interaction else None
    )
    return user, guild


async def _safe_ephemeral_send(interaction: discord.Interaction, message: str):
    """Send an ephemeral message without throwing on double-response."""
    try:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
    except Exception:
        # Guard rails only: never escalate permission/channel messages
        pass


def _is_allowed_channel(channel: discord.abc.GuildChannel | discord.Thread | None) -> bool:
    """Allow both the channel itself and threads whose parent is allowed."""
    if channel is None:
        return False
    chan_id = getattr(channel, "id", None)
    # be robust across discord.py/pycord/nextcord variants
    parent = getattr(channel, "parent", None)
    parent_id = getattr(channel, "parent_id", getattr(parent, "id", None))
    return (chan_id in ALLOWED_CHANNEL_IDS) or (parent_id in ALLOWED_CHANNEL_IDS)


def _is_admin(user: discord.abc.User | None) -> bool:
    try:
        return user is not None and int(user.id) == ADMIN_USER_ID
    except Exception:
        return False


def _has_leadership_role(member: discord.Member | None) -> bool:
    if not isinstance(member, discord.Member):
        return False
    role_ids = {r.id for r in member.roles}
    role_names = {r.name for r in member.roles}
    if any(rid in role_ids for rid in LEADERSHIP_ROLE_IDS):
        return True
    if any(name in role_names for name in (LEADERSHIP_ROLE_NAMES or [])):
        return True
    return False


# --- Decorators ----------------------------------------------------


def is_admin_and_notify_channel(allow_leadership: bool = False):
    """
    Gate: Admin ONLY (ADMIN_USER_ID) AND channel must be allowed.
    By default this matches your previous behavior (NOTIFY only).
    Set allow_leadership=True to also allow the leadership channel (and their threads).
    """

    def decorator(func):
        @wraps(func)  # ✅ preserve signature & __annotations__ for Pycord
        async def wrapper(arg0, *args, **kwargs):
            inter = _resolve_interaction(arg0)
            if not inter:
                return

            # Build allow list
            allowed = {int(NOTIFY_CHANNEL_ID)}
            if allow_leadership:
                allowed |= ALLOWED_CHANNEL_IDS

            chan_id = getattr(inter.channel, "id", None)
            parent_id = getattr(inter.channel, "parent_id", None)

            # Helper: log a denied attempt (non-blocking, best-effort)
            async def _log_denied(reason: str):
                try:
                    cmd_name = (
                        getattr(getattr(inter, "command", None), "name", None)
                        or (getattr(inter, "data", {}) or {}).get("name")
                        or "unknown"
                    )
                    evt = {
                        "executed_at_utc": datetime.now(UTC).isoformat(),
                        "command_name": cmd_name,
                        "version": None,  # version resolver is in @track_usage
                        "app_context": "slash",  # this decorator guards slash cmds
                        "user_id": getattr(inter.user, "id", None),
                        "user_display": getattr(inter.user, "display_name", None),
                        "guild_id": getattr(getattr(inter, "guild", None), "id", None),
                        "channel_id": chan_id,
                        "success": False,
                        "error_code": reason,
                        "error_text": None,
                        "latency_ms": None,
                        "args_shape": None,
                    }
                    await usage_tracker().log(evt)
                except Exception:
                    pass

            # Channel guard
            if (chan_id not in allowed) and (parent_id not in allowed):
                mentions = " or ".join(f"<#{cid}>" for cid in sorted(allowed))
                await _log_denied("ChannelNotAllowed")
                await _safe_ephemeral_send(
                    inter, f"❌ This command can only be used in {mentions}."
                )
                return

            # Admin guard
            if not _is_admin(getattr(inter, "user", None)):
                await _log_denied("AdminOnly")
                await _safe_ephemeral_send(
                    inter, "❌ This command is restricted to the Admin user."
                )
                return

            return await func(arg0, *args, **kwargs)

        return wrapper

    return decorator


def is_admin_or_leadership():
    """
    Gate: (Admin by ADMIN_USER_ID) OR (has Leadership role),
    AND channel must be one of ALLOWED_CHANNEL_IDS (or their threads).
    """

    def deco(func):
        @wraps(func)  # ✅ preserve signature & __annotations__ for Pycord
        async def wrapper(arg0, *args, **kwargs):
            inter = _resolve_interaction(arg0)
            if not inter:
                return

            # Channel guard
            if not _is_allowed_channel(inter.channel):
                mentions = " or ".join(f"<#{cid}>" for cid in sorted(ALLOWED_CHANNEL_IDS))
                await _safe_ephemeral_send(
                    inter, f"❌ This command can only be used in {mentions}."
                )
                return

            # Permission guard
            user = getattr(inter, "user", None)
            member = user if isinstance(user, discord.Member) else None
            if not (_is_admin(user) or _has_leadership_role(member)):
                await _safe_ephemeral_send(
                    inter, "❌ You don't have permission to use this command."
                )
                return

            return await func(arg0, *args, **kwargs)

        return wrapper

    return deco


# lazy singleton to avoid circular imports
_tracker: AsyncUsageTracker | None = None


def usage_tracker() -> AsyncUsageTracker:
    global _tracker
    if _tracker is None:
        # Flush every 5s or every 20 events while testing
        _tracker = AsyncUsageTracker(flush_interval_sec=5, batch_size=20)
        _tracker.start()
    return _tracker


# add near _safe_args_shape
SENSITIVE_KEYS = {
    "password",
    "token",
    "apikey",
    "key",
    "secret",
    "authorization",
    "auth",
    "cookie",
    "session",
}


def _safe_args_preview(kwargs: dict[str, Any] | None, *, max_len: int = 32):
    if not kwargs:
        return None
    out = {}
    for k, v in kwargs.items():
        kn = str(k).lower()
        if kn in SENSITIVE_KEYS:
            out[k] = "***"
            continue
        if isinstance(v, (str, int, float, bool)):
            s = str(v)
            out[k] = s if len(s) <= max_len else s[:max_len] + "…"
        else:
            out[k] = type(v).__name__
    return out


def _safe_args_shape(kwargs: dict[str, Any] | None) -> dict[str, str] | None:
    if not kwargs:
        return None
    try:
        return {k: type(v).__name__ for k, v in kwargs.items()}
    except Exception:
        return None


# --- keep the rest of Decoraters.py as-is ---


def track_usage(command_name: str | None = None, app_context: str = "slash"):
    def _clip(s: str | None, n: int) -> str | None:
        if s is None:
            return None
        s = str(s)
        return s if len(s) <= n else s[:n]

    def _unwrap(obj, depth=3):
        while depth > 0 and hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            depth -= 1
        return object

    def _resolve_version(ctx, func, wrapper) -> str | None:
        candidates = [
            wrapper,
            func,
            getattr(getattr(ctx, "command", None), "callback", None),
        ]
        for obj in candidates:
            if not obj:
                continue
            # try the object
            v = getattr(obj, "__version__", None)
            if v:
                return str(v)
            # try its unwrapped chain a couple of levels
            uw = _unwrap(obj)
            if uw is not obj:
                v = getattr(uw, "__version__", None)
                if v:
                    return str(v)
        return None

    def deco(func: Callable[..., Any]):
        @functools.wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            t0 = time.perf_counter()
            success = True
            error_code = None
            error_text = None
            try:
                return await func(ctx, *args, **kwargs)
            except Exception as e:
                success = False
                error_code = type(e).__name__
                error_text = _clip(str(e), 4000)  # NVARCHAR(MAX; safe to clip)
                raise
            finally:
                latency_ms = int((time.perf_counter() - t0) * 1000)

                # ✅ robust version lookup
                version = _resolve_version(ctx, func, wrapper)
                cmd_name = (
                    command_name
                    or getattr(getattr(ctx, "command", None), "name", None)
                    or func.__name__
                )

                evt = {
                    "executed_at_utc": datetime.now(UTC).isoformat(),
                    "command_name": _clip(cmd_name, 64),
                    "version": _clip(version, 16),
                    "app_context": _clip(app_context, 16),
                    "user_id": getattr(ctx.user, "id", None),
                    "user_display": _clip(getattr(ctx.user, "display_name", None), 128),
                    "guild_id": getattr(getattr(ctx, "guild", None), "id", None),
                    "channel_id": getattr(getattr(ctx, "channel", None), "id", None),
                    "success": success,
                    "error_code": _clip(error_code, 64),
                    "error_text": error_text,
                    "latency_ms": latency_ms,
                    "args_shape": {
                        "shape": _safe_args_shape(kwargs),
                        "preview": _safe_args_preview(kwargs),  # optional small value peek
                    },
                }

                log.debug(
                    "[USAGE]+ cmd=%s v=%s ok=%s ms=%s",
                    evt.get("command_name"),
                    evt.get("version"),
                    evt.get("success", True),
                    evt.get("latency_ms"),
                )

                try:
                    await usage_tracker().log(evt)
                except Exception:
                    log.warning("[USAGE] queue log failed", exc_info=False)

        return wrapper

    return deco
