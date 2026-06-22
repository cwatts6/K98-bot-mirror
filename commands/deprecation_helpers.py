from __future__ import annotations

from dataclasses import dataclass

import discord


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
    await ctx.followup.send(
        build_deprecated_command_message(redirect),
        ephemeral=ephemeral,
    )
