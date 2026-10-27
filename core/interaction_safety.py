# core/interaction_safety.py
"""Shared interaction safety helpers.

This module centralizes command reliability utilities that were previously
defined in ``Commands.py`` so other modules can reuse them without importing
the full command registration monolith.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import functools
import logging
from typing import Any

import discord
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


async def send_ephemeral(
    interaction: discord.Interaction,
    content: str,
    **kwargs: Any,
) -> None:
    """
    Safely send an ephemeral response for both initial and followup phases.
    """
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=True, **kwargs)
        else:
            await interaction.response.send_message(content, ephemeral=True, **kwargs)
    except asyncio.CancelledError:
        # Preserve cooperative cancellation semantics
        raise
    except Exception:
        logger.exception("interaction_send_ephemeral_failed")


def response_is_done(interaction: discord.Interaction) -> bool:
    """Return whether an interaction has already received its first response."""
    try:
        responder = getattr(interaction, "response", None)
        return bool(responder and responder.is_done())
    except Exception:
        return False


async def send_or_followup(
    interaction: discord.Interaction,
    content: str | None = None,
    *,
    ephemeral: bool = True,
    **kwargs: Any,
) -> Any:
    """Send the first response when possible, otherwise send a followup."""
    if response_is_done(interaction):
        return await interaction.followup.send(content, ephemeral=ephemeral, **kwargs)
    return await interaction.response.send_message(content, ephemeral=ephemeral, **kwargs)


async def edit_or_followup(
    interaction: discord.Interaction,
    content: str | None = None,
    *,
    ephemeral: bool = True,
    **kwargs: Any,
) -> Any:
    """Edit the original response when possible, otherwise fall back to a followup."""
    try:
        return await interaction.edit_original_response(content=content, **kwargs)
    except Exception:
        logger.debug("interaction_edit_original_failed_falling_back", exc_info=True)
        return await interaction.followup.send(content, ephemeral=ephemeral, **kwargs)


@dataclass(frozen=True)
class DeferResult:
    acknowledged: bool
    disposition: str
    error_type: str | None = None
    status: int | None = None
    code: int | None = None


async def defer_result(ctx, *, ephemeral: bool = True) -> DeferResult:
    """One defer with allowlisted diagnostics; never retain exception text/token."""
    try:
        ir = getattr(ctx, "interaction", None) or ctx
        if ir and hasattr(ir, "response") and not ir.response.is_done():
            await ir.response.defer(ephemeral=ephemeral)
            return DeferResult(True, "acknowledged")
        # discord.py variants also expose ctx.defer()
        if hasattr(ctx, "defer"):
            await ctx.defer(ephemeral=ephemeral)
            return DeferResult(True, "acknowledged")
    except (NotFound, HTTPException) as exc:
        return DeferResult(
            False,
            "unconfirmed",
            type(exc).__name__,
            exc.status if type(exc.status) is int else None,
            exc.code if type(exc.code) is int else None,
        )
    except Exception as exc:
        return DeferResult(False, "unconfirmed", type(exc).__name__[:64])
    return DeferResult(False, "unavailable")


async def safe_defer(ctx, *, ephemeral: bool = True) -> bool:
    """Compatible Boolean wrapper for callers that do not consume diagnostics."""
    return (await defer_result(ctx, ephemeral=ephemeral)).acknowledged


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
