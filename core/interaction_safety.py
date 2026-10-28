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
import inspect
import logging
from typing import Any

import discord
from discord import HTTPException, NotFound

logger = logging.getLogger(__name__)
_private_children = set()
_private_admission_closed = False


def close_private_operations():
    global _private_admission_closed
    _private_admission_closed = True


async def drain_private_operations():
    from core.owned_work import drain_awaitable

    close_private_operations()
    while _private_children:
        await drain_awaitable(asyncio.gather(*tuple(_private_children), return_exceptions=True))


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
        kwargs.pop("ephemeral", None)  # this helper always owns private visibility
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


def member_role_ids(interaction) -> set[int]:
    member = interaction.user if isinstance(interaction.user, discord.Member) else None
    if member is None and interaction.guild:
        member = interaction.guild.get_member(interaction.user.id)
    return {int(role.id) for role in getattr(member, "roles", []) if getattr(role, "id", None)}


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


async def defer_result(
    ctx, *, ephemeral: bool = True, invisible: bool | None = None
) -> DeferResult:
    """One defer with allowlisted diagnostics; never retain exception text/token."""
    try:
        ir = getattr(ctx, "interaction", None) or ctx
        if ir and hasattr(ir, "response") and not ir.response.is_done():
            kwargs = {} if invisible is None else {"invisible": invisible}
            await ir.response.defer(ephemeral=ephemeral, **kwargs)
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


async def acknowledge_private(interaction) -> bool:
    """Explicit private thinking response for components/modal submits, never modal openers."""
    if response_is_done(interaction):
        return True
    result = await defer_result(interaction, ephemeral=True, invisible=False)
    if not result.acknowledged:
        logger.warning(
            "interaction_admission_stopped disposition=%s error_type=%s code=%s",
            result.disposition,
            result.error_type,
            result.code,
        )
    return result.acknowledged


def private_operation(function):
    """Own one callback through cancellation; reject overlapping same-view clicks.

    Durable deduplication and authorization remain the service/DAL's responsibility.
    Apply only to callbacks that never open a modal as their initial response.
    """
    from time import perf_counter

    from core.owned_work import drain_awaitable

    signature = inspect.signature(function)
    interaction_parameter = next(
        name
        for name in signature.parameters
        if name == "interaction" or name.endswith("_interaction")
    )

    @functools.wraps(function)
    async def run(self, *args, **kwargs):
        interaction = signature.bind(self, *args, **kwargs).arguments[interaction_parameter]
        started = perf_counter()
        if not await acknowledge_private(interaction):
            return None
        if _private_admission_closed:
            await send_ephemeral(
                interaction, "The bot is shutting down. No new action was started."
            )
            return None
        pending = getattr(self, "_private_operations", None)
        if pending is None:
            pending = self._private_operations = set()
        key = (function.__name__, None if hasattr(self, "_completed") else interaction.user.id)
        if key in pending:
            await send_ephemeral(interaction, "This action is still processing. Please wait.")
            return None
        pending.add(key)
        acknowledged = perf_counter()
        child = asyncio.create_task(function(self, *args, **kwargs))
        _private_children.add(child)
        try:
            return await drain_awaitable(child)
        finally:
            _private_children.discard(child)
            pending.discard(key)
            logger.info(
                "interaction_operation callback=%s ack_ms=%.3f total_ms=%.3f",
                function.__qualname__,
                (acknowledged - started) * 1000,
                (perf_counter() - started) * 1000,
            )

    return run


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
