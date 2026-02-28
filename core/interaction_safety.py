# core/interaction_safety.py
"""Shared interaction safety helpers.

This module centralizes command reliability utilities that were previously
defined in ``Commands.py`` so other modules can reuse them without importing
the full command registration monolith.
"""

from __future__ import annotations

import asyncio
import functools
import logging

from discord import HTTPException, NotFound

logger = logging.getLogger(__name__)


# --- Operation locks (serialize sensitive ops) -----------------------------
_op_locks = {
    "resync": asyncio.Lock(),
    "restart": asyncio.Lock(),
    "import_regs": asyncio.Lock(),
}


def get_operation_lock(key: str) -> asyncio.Lock:
    """Return a shared operation lock by key."""
    if key not in _op_locks:
        _op_locks[key] = asyncio.Lock()
    return _op_locks[key]


def safe_command(fn):
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        try:
            return await fn(*args, **kwargs)
        except Exception:
            logger.exception("[CMD ERROR] %s", getattr(fn, "__name__", "unknown"))
            # best-effort user feedback (ephemeral) without double-acking
            ctx = args[0] if args else None
            try:
                inter = getattr(ctx, "interaction", None) or ctx
                if hasattr(ctx, "respond") and not inter.response.is_done():
                    await ctx.respond(
                        "⚠️ Something went wrong. The team has been notified.", ephemeral=True
                    )
                else:
                    await inter.followup.send(
                        "⚠️ Something went wrong. The team has been notified.", ephemeral=True
                    )
            except Exception:
                pass
            return None

    return wrapper


async def safe_defer(ctx, *, ephemeral: bool = True) -> bool:
    """Best-effort defer that won't crash on unknown/expired interaction."""
    try:
        ir = getattr(ctx, "interaction", None)
        if ir and hasattr(ir, "response") and not ir.response.is_done():
            await ir.response.defer(ephemeral=ephemeral)
            return True
        # discord.py variants also expose ctx.defer()
        if hasattr(ctx, "defer"):
            await ctx.defer(ephemeral=ephemeral)
            return True
    except (NotFound, HTTPException):
        # Interaction expired or the bot disconnected mid-flight
        pass
    except Exception:
        pass
    return False


async def global_cmd_error_handler(ctx, error):
    """Global app command error handler used by command registration."""
    logger.exception(
        "[CMD ERROR] %s",
        getattr(getattr(ctx, "command", None), "qualified_name", "unknown"),
        exc_info=error,
    )
    try:
        inter = getattr(ctx, "interaction", None) or ctx
        if not inter.response.is_done():
            responder = getattr(ctx, "respond", None)
            if responder is not None:
                await responder(
                    "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
                )
            else:
                await inter.response.send_message(
                    "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
                )
        else:
            await inter.followup.send(
                "⚠️ Sorry, something went wrong. The team has been notified.", ephemeral=True
            )
    except Exception:
        pass
