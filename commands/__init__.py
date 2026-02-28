# commands/__init__.py
from __future__ import annotations

from discord.ext import commands as ext_commands

from .admin_cmds import register_admin
from .ark_cmds import register_ark
from .events_cmds import register_events
from .location_cmds import register_location
from .registry_cmds import register_registry
from .stats_cmds import register_stats
from .subscriptions_cmds import register_subscriptions
from .telemetry_cmds import register_telemetry


def register_all(bot: ext_commands.Bot) -> None:
    register_admin(bot)
    register_events(bot)
    register_location(bot)
    register_registry(bot)
    register_stats(bot)
    register_subscriptions(bot)
    register_telemetry(bot)
    register_ark(bot)
