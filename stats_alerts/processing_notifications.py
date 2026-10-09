"""Discord adapter for independently verified stats and Sheets outcomes."""

import asyncio
from datetime import UTC, datetime
import time

import discord

from services.legacy_export_snapshot_service import drain_thread
from services.processing_notification_service import (
    TERMINAL_EXPORTS,
    NotificationTransitionFailed,
    _current_cache_generation,
    cache_generation,
    event,
    observe_export,
    patch_run,
    validate_runtime_scope,
)
from services.processing_notification_store import NotificationHeld, notification_store
from stats_alerts.processing_delivery import DurableStatsTracker

_last_observed_key = ""


async def bot_data_ready(bot, run_id, output):
    """Called before any Sheets dependency. A preserved old cache is not readiness."""
    if not run_id:
        return
    generation = cache_generation(output)
    if generation is None:
        await patch_run(run_id, stats="unavailable", stats_delivery="held")
        event(run_id, "bot_data", "unavailable", "repair_cache_refresh_then_upload_a_new_scan")
        return
    ready_recorded = False
    try:
        from stats_alerts.kvk_meta import is_currently_kvk

        is_kvk = await drain_thread(is_currently_kvk)
        row = await patch_run(
            run_id,
            stats="ready",
            cache_generation=generation,
            ready_at=time.time(),
            is_kvk=bool(is_kvk),
            stats_delivery="retry_pending",
            stats_timestamp=datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        )
        if row:
            ready_recorded = True
            event(run_id, "bot_data", "ready", "publish_existing_stats_route")
            await publish_stats(bot, row)
    except asyncio.CancelledError:
        raise
    except NotificationTransitionFailed:
        # Do not replace verified readiness with a fabricated unavailable result.
        # The pipeline reports the intervention and stops dependent work.
        raise
    except Exception as exc:
        if not ready_recorded:
            await patch_run(run_id, stats="unavailable", stats_delivery="held")
        event(run_id, "stats_notification", "held", "inspect_notification_status", error=exc)


async def publish_stats(bot, row):
    from stats_alerts.delivery_outcomes import log_delivery
    from stats_alerts.interface import send_stats_update_embed

    if row.get("stats") != "ready" or row.get("stats_delivery") != "retry_pending":
        return
    store, run_id = notification_store(), row["run_id"]
    if row["stats_tries"] >= 3 or time.time() - row["ready_at"] > 300:
        await patch_run(run_id, stats_delivery="held")
        event(run_id, "stats_notification", "held", "inspect_status_and_publish_manually_if_needed")
        return
    if await drain_thread(_current_cache_generation) != row["cache_generation"]:
        await patch_run(run_id, stats_delivery="superseded")
        event(run_id, "stats_notification", "superseded", "use_newer_stats_run")
        return
    await drain_thread(store.patch, run_id, stats_tries=row["stats_tries"] + 1)
    tracker = DurableStatsTracker(store, run_id)
    try:
        await send_stats_update_embed(
            bot,
            row["stats_timestamp"],
            row["is_kvk"],
            _delivery=tracker,
        )
    finally:
        log_delivery(
            tracker.result(),
            caller="processing_outcomes",
            source_message_id=row.get("source_message_id"),
        )
        await tracker.finish()
    event(run_id, "stats_notification", "observed", "inspect_component_receipts")


def outcome_embed(row, *, sheets=False):
    state = row["sheets"]
    ready = row["stats"] == "ready"
    if sheets:
        title = (
            "Google Sheets ready for analysis"
            if state == "confirmed"
            else "Google Sheets update needs attention"
        )
        text = (
            "The export is confirmed."
            if state == "confirmed"
            else (
                "The export outcome is uncertain; an admin must inspect the exact job before any recovery."
                if state == "uncertain"
                else "This export did not complete. An admin should inspect its job and error logs."
            )
        )
        text += (
            " Bot stats are available independently."
            if ready
            else " Bot stats readiness was not confirmed."
        )
    else:
        title = "Processing results" if state in TERMINAL_EXPORTS else "Processing: Sheets pending"
        text = f"Bot stats: {'available' if ready else row['stats']}.\nGoogle Sheets: {state}."
    embed = discord.Embed(
        title=title, description=text, color=0x2ECC71 if state == "confirmed" else 0xF1C40F
    )
    if state == "confirmed" and sheets and row.get("links"):
        lines, length = [], 0
        for i, url in enumerate(row["links"], 1):
            line = f"[Spreadsheet {i}]({url})"
            if length + len(line) + 1 > 1024:
                embed.add_field(name="Analysis", value="\n".join(lines), inline=False)
                lines, length = [], 0
            lines.append(line)
            length += len(line) + 1
        if lines:
            embed.add_field(name="Analysis", value="\n".join(lines), inline=False)
        if row.get("additional_links"):
            embed.add_field(
                name="Additional outputs",
                value=f"{row['additional_links']} more public spreadsheets are recorded in this export job.",
                inline=False,
            )
    if row.get("job_id"):
        embed.add_field(name="Export job", value=row["job_id"], inline=False)
    if row.get("duration_seconds") is not None:
        embed.add_field(name="Total duration", value=f"{row['duration_seconds']:.1f} seconds")
    embed.set_footer(text="Processing run " + row["run_id"])
    return embed


async def publish_status(bot, row, component):
    store, run_id = notification_store(), row["run_id"]
    current = row["components"].get(component, {})
    if current.get("state") in {"sending", "held", "acknowledged", "skipped"}:
        return
    tries = current.get("tries", 0)
    if tries >= 3:
        return
    sheets = component.startswith("sheets_")
    channel_id = row["sheets_channel_id"] if sheets else row["summary_channel_id"]
    entered = False
    message = None
    try:
        channel = bot.get_channel(channel_id) if channel_id else None
        if channel is None:
            raise NotificationHeld("Configured notification channel unavailable.")
        message = None
        if component.startswith("summary_final_"):
            prior = row["components"].get("summary_pending", {})
            previous = [
                v
                for k, v in row["components"].items()
                if k.startswith("summary_final_") and v.get("state") == "acknowledged"
            ]
            if previous:
                prior = max(previous, key=lambda v: v["acknowledged"])
            if prior.get("state") in {"sending", "held"}:
                raise NotificationHeld(
                    "Pending summary acknowledgment is ambiguous; inspect first."
                )
            if prior.get("state") == "acknowledged":
                try:
                    message = await channel.fetch_message(prior["message_id"])
                except discord.NotFound:
                    message = None  # Proven deleted: a replacement cannot duplicate it.
                if message and (
                    message.author.id != bot.user.id or message.channel.id != channel_id
                ):
                    raise NotificationHeld("Summary author or channel differs.")
        await drain_thread(
            store.enter,
            run_id,
            component,
            channel_id=channel_id,
            operation="edit" if message else "send",
            message_id=message.id if message else None,
        )
        embed = outcome_embed(row, sheets=sheets)
        entered = True
        if message:
            await message.edit(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        else:
            message = await channel.send(
                embed=embed, allowed_mentions=discord.AllowedMentions.none()
            )
        await drain_thread(
            store.acknowledge,
            run_id,
            component,
            message_id=message.id,
            channel_id=message.channel.id,
        )
        event(
            run_id,
            component,
            "acknowledged",
            "none",
            job_id=row.get("job_id"),
            channel_id=channel_id,
            message_id=message.id,
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        error_type = type(exc).__name__

        def failure(latest):
            item = latest["components"].get(component, {})
            if item.get("state") in {"acknowledged", "skipped", "held"} or (
                item.get("state") == "sending" and not entered
            ):
                return
            item.update(
                state="held" if item.get("state") == "sending" else "failed",
                reason=error_type,
                tries=tries + 1,
            )
            latest["components"][component] = item

        failed_row = await drain_thread(store.update, run_id, failure)
        event(
            run_id,
            component,
            failed_row["components"][component]["state"],
            "inspect_notification_status_and_channel_permissions",
            error=exc,
            job_id=row.get("job_id"),
            channel_id=channel_id,
            message_id=getattr(message, "id", None),
        )


async def update_queue(bot, row):
    from utils import live_queue, live_queue_lock, update_live_queue_embed

    changed = False
    async with live_queue_lock:
        for job in live_queue["jobs"]:
            if job.get("processing_run_id") == row["run_id"]:
                status = f"Stats: {row['stats']}; Sheets: {row['sheets']}"
                if job["status"] != status:
                    job["status"] = status
                    changed = True
    if changed:
        await update_live_queue_embed(bot, row["summary_channel_id"])


async def observe_notifications(bot):
    global _last_observed_key
    store = notification_store()
    active = sorted(
        (r for r in await drain_thread(store.all) if not r.get("closed")), key=lambda r: r["run_id"]
    )
    selected = [r for r in active if r["run_id"] > _last_observed_key] + [
        r for r in active if r["run_id"] <= _last_observed_key
    ]
    sql_unavailable = False
    for row in selected[:16]:
        _last_observed_key = row["run_id"]
        try:
            # Each Discord operation has its own durable compare-and-set boundary.
            await drain_thread(validate_runtime_scope, row)
            try:
                await publish_stats(bot, row)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                event(
                    row["run_id"],
                    "stats_notification",
                    "held",
                    "inspect_stats_component_receipts",
                    error=exc,
                )
            if not sql_unavailable:
                try:
                    row = await drain_thread(observe_export, row)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    sql_unavailable = type(exc).__name__ in {
                        "OperationalError",
                        "InterfaceError",
                        "TimeoutError",
                    }
                    event(
                        row["run_id"],
                        "export_observation",
                        "held",
                        "inspect_SQL_connectivity_and_exact_job_receipt",
                        error=exc,
                    )
            if row.get("handoff"):
                terminal = row["sheets"] in TERMINAL_EXPORTS
                summary_component = (
                    "summary_final_" + row["sheets"] if terminal else "summary_pending"
                )
                sheets_component = "sheets_" + row["sheets"]
                await publish_status(bot, row, summary_component)
                if terminal:
                    await publish_status(bot, row, sheets_component)
                    await update_queue(bot, row)
                    latest = await drain_thread(store.get, row["run_id"])
                    if (
                        row["sheets"] != "uncertain"
                        and latest.get("stats_delivery") in {"complete", "superseded"}
                        and all(
                            latest["components"].get(key, {}).get("state")
                            in {"acknowledged", "skipped"}
                            for key in (summary_component, sheets_component)
                        )
                    ):
                        await drain_thread(store.patch, row["run_id"], closed=True)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            event(row["run_id"], "observer", "held", "inspect_exact_run_status", error=exc)
