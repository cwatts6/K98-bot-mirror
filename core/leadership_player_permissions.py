"""Dedicated fail-closed permission matrix for private leadership player review."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Literal

import discord

from bot_config import (
    ADMIN_USER_ID,
    GUILD_ID,
    LEADERSHIP_CHANNEL_ID,
    LEADERSHIP_ROLE_IDS,
    NOTIFY_CHANNEL_ID,
)

AuthorizationBasis = Literal["ADMIN_USER_ID", "LEADERSHIP_ROLE_ID", "NONE"]


@dataclass(frozen=True, slots=True)
class LeadershipPlayerAuthorization:
    allowed: bool
    basis: AuthorizationBasis = "NONE"
    role_id: int | None = None
    error_code: str | None = None


def _channel_and_parent_ids(channel: Any) -> tuple[int | None, int | None]:
    channel_id = getattr(channel, "id", None)
    parent = getattr(channel, "parent", None)
    parent_id = getattr(channel, "parent_id", getattr(parent, "id", None))
    try:
        channel_id = int(channel_id) if channel_id is not None else None
    except (TypeError, ValueError):
        channel_id = None
    try:
        parent_id = int(parent_id) if parent_id is not None else None
    except (TypeError, ValueError):
        parent_id = None
    return channel_id, parent_id


def _is_channel_or_child(channel: Any, configured_id: int | None) -> bool:
    if not configured_id:
        return False
    channel_id, parent_id = _channel_and_parent_ids(channel)
    expected = int(configured_id)
    return channel_id == expected or parent_id == expected


def authorize_leadership_player_interaction(
    interaction: discord.Interaction | Any,
) -> LeadershipPlayerAuthorization:
    """Apply the command-specific role/channel matrix without role-name fallback."""
    if interaction is None:
        return LeadershipPlayerAuthorization(False, error_code="NO_INTERACTION")
    guild = getattr(interaction, "guild", None)
    if guild is None:
        return LeadershipPlayerAuthorization(False, error_code="DM_NOT_ALLOWED")
    if GUILD_ID and int(getattr(guild, "id", 0) or 0) != int(GUILD_ID):
        return LeadershipPlayerAuthorization(False, error_code="GUILD_NOT_ALLOWED")

    user = getattr(interaction, "user", None)
    try:
        actor_id = int(getattr(user, "id", 0) or 0)
    except (TypeError, ValueError):
        actor_id = 0
    in_leadership = _is_channel_or_child(
        getattr(interaction, "channel", None), LEADERSHIP_CHANNEL_ID
    )
    in_notify = _is_channel_or_child(getattr(interaction, "channel", None), NOTIFY_CHANNEL_ID)

    if ADMIN_USER_ID and actor_id == int(ADMIN_USER_ID):
        if in_leadership or in_notify:
            return LeadershipPlayerAuthorization(True, basis="ADMIN_USER_ID")
        return LeadershipPlayerAuthorization(False, error_code="ADMIN_CHANNEL_NOT_ALLOWED")

    if not in_leadership:
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_CHANNEL_REQUIRED")
    if not isinstance(user, discord.Member):
        return LeadershipPlayerAuthorization(False, error_code="MEMBER_REQUIRED")

    configured_roles = {int(value) for value in (LEADERSHIP_ROLE_IDS or []) if int(value) > 0}
    if not configured_roles:
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLES_UNCONFIGURED")
    actor_roles = {int(role.id) for role in getattr(user, "roles", ())}
    matching = sorted(actor_roles & configured_roles)
    if not matching:
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLE_REQUIRED")
    return LeadershipPlayerAuthorization(
        True,
        basis="LEADERSHIP_ROLE_ID",
        role_id=matching[0],
    )


async def reauthorize_leadership_player_interaction(
    interaction: discord.Interaction | Any,
) -> LeadershipPlayerAuthorization:
    """Recheck current Discord membership and roles at a protected action boundary."""
    entry = authorize_leadership_player_interaction(interaction)
    if not entry.allowed:
        return entry

    guild = getattr(interaction, "guild", None)
    user = getattr(interaction, "user", None)
    actor_id = int(getattr(user, "id", 0) or 0)
    fetch_member = getattr(guild, "fetch_member", None)
    if actor_id <= 0 or not callable(fetch_member):
        return LeadershipPlayerAuthorization(
            False,
            error_code="MEMBER_REVALIDATION_UNAVAILABLE",
        )
    try:
        current_member = await fetch_member(actor_id)
    except Exception:
        return LeadershipPlayerAuthorization(
            False,
            error_code="MEMBER_REVALIDATION_FAILED",
        )
    if current_member is None or int(getattr(current_member, "id", 0) or 0) != actor_id:
        return LeadershipPlayerAuthorization(
            False,
            error_code="MEMBER_NO_LONGER_PRESENT",
        )

    current = SimpleNamespace(
        guild=guild,
        channel=getattr(interaction, "channel", None),
        user=current_member,
    )
    return authorize_leadership_player_interaction(current)


def actor_guild_channel_ids(interaction: Any) -> tuple[int, int, int]:
    """Return validated audit identifiers or raise for an unusable interaction."""
    actor_id = int(getattr(getattr(interaction, "user", None), "id", 0) or 0)
    guild_id = int(getattr(getattr(interaction, "guild", None), "id", 0) or 0)
    channel_id = int(getattr(getattr(interaction, "channel", None), "id", 0) or 0)
    if min(actor_id, guild_id, channel_id) <= 0:
        raise ValueError("interaction does not contain auditable actor/guild/channel IDs")
    return actor_id, guild_id, channel_id
