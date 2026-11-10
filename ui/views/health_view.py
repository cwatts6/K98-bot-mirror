"""Shared passive health rendering and the persistent pinned-card entry point."""

import asyncio
import logging

import discord

from core.interaction_safety import defer_result, send_ephemeral_result

logger = logging.getLogger(__name__)

_LABELS = {
    "sql": "Database",
    "sheets": "Google Sheets",
    "profiles": "Profiles",
    "recovery": "Recovery monitor",
    "events": "Event delivery",
    "startup": "Startup activity",
    "personal_stats": "Personal Stats",
}
_REASONS = {
    "not_observed": "No observation yet",
    "source_unavailable": "Observation unavailable",
    "scope_mismatch": "No observation for the configured target",
    "owned_operation": "Existing check in progress",
    "admission_deferred": "Check deferred",
    "check_completed": "Check completed",
    "check_failed": "Check failed",
    "access_denied": "Access denied; verify the configured access permissions",
    "refreshed": "Cache refreshed",
    "disk_loaded": "Cache loaded from disk",
    "memory_reused": "Cache reused",
    "retained_last_known_good": "Previous cache retained",
    "unavailable": "Cache unavailable",
    "cache_invalidated": "Cache changed; previous refresh no longer verifies this snapshot",
    "journal_observed": "Last journal observation",
    "changed_since_observation": "Delivery state changed; previous observation only",
    "monitor_stalled": "Monitoring stalled; investigate retained work",
    "monitor_failed": "Monitoring check failed; recovery state unestablished",
    "monitor_progressing": "Monitoring progressing; completed results may be older",
    "monitor_active": "Monitoring active; this does not mean there are no incidents",
    "monitor_unestablished": "Monitoring results stale or not yet established",
    "startup_activity": "Historical startup activity",
}


def _line(row):
    reason = _REASONS.get(row.get("reason"), "Observation unavailable")
    outcome = row.get("outcome")
    prefix = (
        "Last observed failure"
        if outcome == "failure"
        else "Last observed success" if outcome == "success" else "Current condition unknown"
    )
    if row.get("execution") == "in_progress":
        prefix = "In progress"
    elif outcome == "partial":
        prefix = "Partial outcome"
    age = row.get("age_seconds")
    when = f"{int(age // 60)}m ago" if type(age) in (int, float) and age >= 0 else "age unknown"
    stale = "; stale — current condition unknown" if row.get("freshness") == "stale" else ""
    stamp = row.get("observed_utc")
    # Produced by the bounded projection; never emit arbitrary exception payloads.
    stamp = stamp if type(stamp) is str and len(stamp) <= 40 else "not observed"
    text = f"{prefix}: {reason}\nObserved: {stamp} ({when}){stale}"
    elapsed = row.get("elapsed_seconds")
    if type(elapsed) in (int, float) and elapsed >= 0:
        text += f"\nExisting check elapsed: {int(elapsed)}s; original work remains owned"
    count = row.get("count")
    if type(count) is int and 0 <= count <= 10**12:
        text += f"\nCount at observation: {count}"
    source_time = row.get("source_utc")
    if type(source_time) is str and len(source_time) <= 40:
        text += f"\nData as of: {source_time}"
    counts = row.get("counts", {})
    if counts:
        text += "\n" + ", ".join(
            f"{label}={counts.get(key, 0)}"
            for key, label in (
                ("acknowledged", "acknowledged"),
                ("entered", "unconfirmed"),
                ("refused", "refused"),
                ("not_found", "confirmed absent"),
            )
        )
    if row.get("notifications_need_attention"):
        text += "\nIncident notifications need attention; use the recovery centre."
    prior = row.get("last_failure")
    if type(prior) is dict and outcome != "failure" and prior.get("observed_utc"):
        text += f"\nEarlier failure: {prior['observed_utc']}"
    if row.get("last_success_utc"):
        text += f"\nLast completed monitor success: {row['last_success_utc']}"
    return text[:1024]


def build_health_embed(projection, *, local=None):
    local = local or {}
    components = projection.get("components", {})
    failed = any(row.get("outcome") == "failure" for row in components.values())
    embed = discord.Embed(
        title="Bot Health",
        description="Shutting down" if local.get("shutting_down") else "Retained observations",
        color=0xE74C3C if failed else 0xF39C12,
    )
    connected = local.get("connected")
    embed.add_field(
        name="Discord",
        value=(
            "Connected" if connected is True else "Not ready" if connected is False else "Unknown"
        ),
        inline=True,
    )
    uptime = local.get("uptime_seconds")
    embed.add_field(
        name="Uptime",
        value=(
            f"{int(uptime // 60)} minutes"
            if type(uptime) in (int, float) and uptime >= 0
            else "Unknown"
        ),
        inline=True,
    )
    embed.add_field(name="Queue depth", value="Unknown", inline=True)
    for key, label in _LABELS.items():
        row = components.get(key, {})
        if key == "startup":
            steps = row.get("steps", [])
            value = (
                "\n".join(f"{item['scope_label']}: {_line(item)}" for item in steps)[:1024]
                or "No retained startup observations"
            )
        else:
            value = _line(row)
        if key == "personal_stats":
            value = {
                "stats_cleanup_uncertain": "Cleanup uncertain; new Stats requests unavailable. Inspect the diagnostic report.",
                "stats_shutdown": "Shutting down; new Stats requests unavailable.",
                "stats_busy": "Busy; new Stats requests may be refused.",
                "stats_available": "Capacity available; this is not a SQL health check.",
            }.get(row.get("reason"), "Not yet observed; no check was started.")
            if row.get("reason", "").startswith("stats_"):
                value += f"\nSQL owned: {row['sql_owned']}/8 · Rendering: {row['render_owned']}/2 · Requests: {row['observers']}/32"
                value += f"\nLocal snapshot: {row.get('observed_utc', 'unknown')}"
        if key == "recovery":
            channel_id = local.get("notify_channel_id")
            route = f" in <#{channel_id}>" if type(channel_id) is int and channel_id > 0 else ""
            value = value[:850] + f"\nRecovery centre: `/ops dl_bot_status`{route}."
        embed.add_field(name=label, value=value, inline=False)
    tasks = local.get("tasks")
    if type(tasks) is tuple and len(tasks) == 3 and all(type(n) is int and n >= 0 for n in tasks):
        embed.add_field(
            name="Tasks",
            value=f"Running {tasks[0]} · crashed {tasks[1]} · restarts {tasks[2]}",
            inline=False,
        )
    embed.set_footer(
        text=f"Rendered at {projection['captured_utc']} · Auto-updates every 5 minutes; no provider checks. Explicit logs: /ops logs"
    )
    return embed


class HealthView(discord.ui.View):
    def __init__(self, *, guild_id, channel_id, render):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = None
        self.render = render
        self._editing = False
        self._active = None
        self._closed = False

    def close_admission(self):
        self._closed = True

    async def shutdown(self):
        from core.owned_work import drain_awaitable

        self.close_admission()
        task = self._active
        if task is not None and task is not asyncio.current_task():
            await drain_awaitable(asyncio.gather(task, return_exceptions=True))

    @discord.ui.button(
        label="Refresh", style=discord.ButtonStyle.primary, custom_id="k98:health:refresh:v1"
    )
    async def do_refresh(self, _button, interaction):
        if (
            interaction.guild_id != self.guild_id
            or interaction.channel_id != self.channel_id
            or getattr(interaction.message, "id", None) != self.message_id
            or self.message_id is None
        ):
            await send_ephemeral_result(
                interaction, "Use the current health card in the status channel."
            )
            return
        if not (await defer_result(interaction, ephemeral=False, invisible=True)).acknowledged:
            return
        if self._editing or self._closed:
            return
        self._editing = True
        self._active = asyncio.current_task()
        try:
            embed = self.render()
            await interaction.message.edit(embed=embed, view=self)
        except Exception as exc:
            logger.warning("health_refresh_unavailable error_type=%s", type(exc).__name__)
        finally:
            self._editing = False
            self._active = None
