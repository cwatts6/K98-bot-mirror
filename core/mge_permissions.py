from __future__ import annotations

import discord

from decoraters import _has_leadership_role, _is_admin


def is_admin_or_leadership_interaction(interaction: discord.Interaction) -> bool:
    user = interaction.user
    if _is_admin(user):
        return True
    member = user if isinstance(user, discord.Member) else None
    return _has_leadership_role(member)


def is_admin_interaction(interaction: discord.Interaction) -> bool:
    """Return True when the interaction actor is an admin."""
    return _is_admin(interaction.user)
