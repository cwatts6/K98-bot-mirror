from __future__ import annotations

from dataclasses import dataclass

import discord

from core.interaction_safety import send_or_followup


@dataclass(frozen=True)
class CommandRedirect:
    old_path: str
    new_path: str
    detail: str | None = None


def build_deprecated_command_message(redirect: CommandRedirect) -> str:
    message = (
        f"`{redirect.old_path}` is deprecated and no longer returns the old output.\n"
        f"Please use `{redirect.new_path}` instead."
    )
    if redirect.detail:
        message += f"\n{redirect.detail}"
    return message


async def send_deprecated_command_redirect(
    ctx: discord.ApplicationContext,
    redirect: CommandRedirect,
    *,
    ephemeral: bool,
) -> None:
    message = build_deprecated_command_message(redirect)
    interaction = getattr(ctx, "interaction", None)
    if (
        interaction is not None
        and hasattr(interaction, "response")
        and hasattr(interaction, "followup")
    ):
        await send_or_followup(interaction, message, ephemeral=ephemeral)
        return

    responder = getattr(ctx, "respond", None)
    if responder is not None:
        await responder(message, ephemeral=ephemeral)
        return

    await ctx.followup.send(message, ephemeral=ephemeral)
