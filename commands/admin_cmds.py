# commands/admin_cmds.py
# flake8: noqa
# ruff: noqa: F403,F405
from __future__ import annotations

import asyncio
import csv
import io
import json
import os
import re
import signal
import sys
from collections import deque
from datetime import datetime, timedelta, timezone
from math import ceil

import logging

import discord

from discord.ext import commands as ext_commands
from admin_helpers import prompt_admin_inputs, log_processing_result
from file_utils import read_summary_log_rows
from bot_config import ADMIN_USER_ID, GUILD_ID, NOTIFY_CHANNEL_ID, OFFSEASON_STATS_CHANNEL_ID

from commands.telemetry_cmds import (
    _ctx_filter_sql,
    _fetch_rows,
    _pick_log_source,
    _resolve_governor_label,
    _session_claim,
    _session_refresh,
    _session_release,
    _usage_detail_value_ac,
    start_bot_time,
)
from core.interaction_safety import get_operation_lock, safe_command, safe_defer
from embed_utils import FailuresView, HistoryView, generate_summary_embed
from file_utils import append_csv_line, read_json_safe, read_summary_log_rows
from gsheet_module import check_basic_gsheets_access, run_all_exports
from logging_setup import CRASH_LOG_PATH, ERROR_LOG_PATH, FULL_LOG_PATH, flush_logs
from proc_config_import import run_proc_config_import_offload
from stats_alerts.interface import send_stats_update_embed
from stats_alerts.kvk_meta import is_currently_kvk
from stats_module import run_stats_copy_archive
from ui.views.admin_views import ConfirmRestartView, LogTailView
from utils import utcnow
from versioning import versioned

from decoraters import (
    _has_leadership_role,
    _is_admin,
    _is_allowed_channel,
    channel_only,
    is_admin_and_notify_channel,
    is_admin_or_leadership,
    track_usage,
)

from constants import (
    CREDENTIALS_FILE,
    CSV_LOG,
    DATABASE,
    EXIT_CODE_FILE,
    FAILED_LOG,
    PASSWORD,
    RESTART_EXIT_CODE,
    RESTART_FLAG_PATH,
    SERVER,
    SHEET_ID,
    SUMMARY_LOG,
    USAGE_TABLE,
    USERNAME,
)

UTC = getattr(datetime, "UTC", timezone.utc)

logger = logging.getLogger(__name__)


def _format_validate_embed(report) -> discord.Embed:
    embed = discord.Embed(
        title="CrystalTech Validation",
        description=report.summary(),
        color=discord.Color.green() if report.ok else discord.Color.red(),
    )
    shown = 0
    for issue in report.issues:
        if shown >= 10:
            remaining = len(report.issues) - shown
            if remaining > 0:
                embed.add_field(name="…", value=f"+{remaining} more issues not shown", inline=False)
            break
        loc = []
        if issue.path_id:
            loc.append(f"path={issue.path_id}")
        if issue.step_uid:
            loc.append(f"step={issue.step_uid}")
        where = f" ({', ' .join(loc)})" if loc else ""
        embed.add_field(
            name=f"[{issue.level}] {issue.code}{where}",
            value=(issue.message[:512] + ("…" if len(issue.message) > 512 else "")) or "—",
            inline=False,
        )
        shown += 1
    return embed


def register_admin(bot: ext_commands.Bot) -> None:
    @bot.slash_command(
        name="summary", description="View today's file processing summary", guild_ids=[GUILD_ID]
    )
    @versioned("v1.04")
    @safe_command
    @track_usage()
    async def summary_command(ctx):
        logger.info("[COMMAND] /summary invoked")
        # Public by default (no ephemeral=True)
        try:
            await safe_defer(ctx)
        except Exception:
            # If already acknowledged elsewhere, continue gracefully
            pass

        try:
            embed = await generate_summary_embed(days=1)
            if embed:
                await ctx.interaction.edit_original_response(embed=embed)
            else:
                await ctx.interaction.edit_original_response(
                    content="⚠️ No summary log available or no files processed today."
                )
        except Exception as e:
            logger.exception("[COMMAND] /summary failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build summary: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="weeksummary", description="View 7-day file processing summary", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def weeksummary_command(ctx):

        logger.info("[COMMAND] /weeksummary invoked")

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        try:
            embed = await generate_summary_embed(days=7)
            if embed:
                await ctx.interaction.edit_original_response(embed=embed)
            else:
                await ctx.interaction.edit_original_response(
                    content="⚠️ No summary log available or no files processed in the last 7 days."
                )
        except Exception as e:
            logger.exception("[COMMAND] /weeksummary failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build weekly summary: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="history", description="View recently processed files", guild_ids=[GUILD_ID]
    )
    @versioned("v1.02")
    @safe_command
    @track_usage()
    async def history_command(ctx, page: int = 1):

        logger.info("[COMMAND] /history invoked (page=%s) by %s", page, ctx.user)

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        # Admin gate
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        log_file = CSV_LOG
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No download log found.")
            return

        try:
            rows = await read_summary_log_rows(log_file)
        except Exception as e:
            logger.exception("[COMMAND] /history read_summary_log_rows failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )
            return

        if not rows:
            await ctx.interaction.edit_original_response(content="✅ No file history found.")
            return

        if "Timestamp" not in rows[0]:
            await ctx.interaction.edit_original_response(
                content="⚠️ Unexpected format in download log."
            )
            return

        rows = [
            row
            for row in rows
            if all(k in row for k in ("Timestamp", "Channel", "Filename", "Author", "SavedPath"))
        ]
        if not rows:
            await ctx.interaction.edit_original_response(
                content="✅ No valid file history entries found."
            )
            return

        entries_per_page = 5
        total_pages = max(1, ceil(len(rows) / entries_per_page))
        page = max(1, min(page, total_pages))

        view = HistoryView(ctx, rows, page, total_pages)

        # Send the real message as a follow-up and bind it to the view
        msg = await ctx.followup.send(embed=view.get_embed(), view=view)
        view.message = msg

        # Optionally clear the original placeholder to avoid clutter
        try:
            await ctx.interaction.edit_original_response(content="")  # or leave it as-is
        except Exception:
            pass

    @bot.slash_command(
        name="failures", description="View recently failed jobs", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @track_usage()
    async def failures_command(ctx, page: int = 1):

        logger.info("[COMMAND] /failures invoked (page=%s) by %s", page, ctx.user)

        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged

        # Admin gate
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        log_file = FAILED_LOG
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No failure log found.")
            return

        try:
            rows = await read_summary_log_rows(log_file)
        except Exception as e:
            logger.exception("[COMMAND] /failures read_summary_log_rows failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )
            return

        expected_keys = [
            "Timestamp",
            "Filename",
            "User",
            "Rank",
            "Seed",
            "Excel Success",
            "Archive Success",
            "SQL Success",
            "Export Success",
            "Duration (sec)",
        ]
        rows = [row for row in rows if all(k in row for k in expected_keys)]

        if not rows:
            await ctx.interaction.edit_original_response(content="✅ No failed jobs found.")
            return

        entries_per_page = 5
        total_pages = max(1, (len(rows) + entries_per_page - 1) // entries_per_page)
        page = max(1, min(page, total_pages))

        view = FailuresView(ctx, rows, page, total_pages)
        msg = await ctx.followup.send(embed=view.get_embed(), view=view)
        view.message = msg

        # Optional: clear the placeholder message to reduce clutter
        try:
            await ctx.interaction.edit_original_response(content="")
        except Exception:
            pass

    @bot.slash_command(
        name="run_sql_proc",
        description="Manually run the SQL stored procedure",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def run_sql_proc_command(ctx):

        logger.info("[COMMAND] /run_sql_proc invoked by %s", ctx.user)

        # Ack early; keep everything on the original response
        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acknowledged elsewhere

        # Hard admin gate (in addition to decorator)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # Let the user know we’ve started
        try:
            await ctx.interaction.edit_original_response(
                content="⏳ Starting manual SQL run… collecting inputs."
            )
        except Exception:
            pass

        # Collect rank/seed
        try:
            rank, seed = await prompt_admin_inputs(bot, ctx.user, ctx.user.id)
        except Exception as e:
            logger.exception("[COMMAND] /run_sql_proc prompt_admin_inputs failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Could not collect inputs: `{type(e).__name__}: {e}`"
            )
            return

        # Execute the job
        start_time = datetime.utcnow()
        try:
            await ctx.interaction.edit_original_response(
                content=f"🏗️ Running SQL pipeline with rank `{rank}` and seed `{seed}`…"
            )
            success, log, steps = await run_stats_copy_archive(rank, seed)
        except Exception as e:
            logger.exception("[COMMAND] /run_sql_proc run_stats_copy_archive crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 SQL run crashed: `{type(e).__name__}: {e}`"
            )
            return

        # Post-process + audit/embed to notify channel
        try:
            await log_processing_result(
                bot=bot,
                notify_channel_id=NOTIFY_CHANNEL_ID,
                user=ctx.user,
                message=None,
                filename="Manual SQL Run",
                rank=rank,
                seed=seed,
                success_excel=(steps or {}).get("excel"),
                success_archive=(steps or {}).get("archive"),
                success_sql=(steps or {}).get("sql"),
                success_export=None,  # intentionally skipped here
                success_proc_import=None,  # intentionally skipped here
                combined_log=log,
                start_time=start_time,
                summary_log_path=SUMMARY_LOG,
            )
        except Exception:
            logger.exception("[COMMAND] /run_sql_proc log_processing_result failed")
            # Fall through and still inform the invoker below

        # Summarize back to the invoker
        def mark(ok):
            return "✅" if ok else "❌"

        excel_ok = (steps or {}).get("excel", False)
        archive_ok = (steps or {}).get("archive", False)
        sql_ok = (steps or {}).get("sql", False)

        summary = (
            f"**Manual SQL Run Complete**\n"
            f"- Excel: {mark(excel_ok)}\n"
            f"- Archive: {mark(archive_ok)}\n"
            f"- SQL: {mark(sql_ok)}\n"
            f"\nDetailed results have been posted to <#{NOTIFY_CHANNEL_ID}>."
        )

        await ctx.interaction.edit_original_response(
            content=summary if success else f"⚠️ Completed with issues:\n{summary}"
        )

    @bot.slash_command(
        name="run_gsheets_export",
        description="Manually trigger Google Sheets export",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def run_gsheets_export_command(ctx):
        logger.info("[COMMAND] /run_gsheets_export invoked by %s", ctx.user)

        # Acknowledge first
        try:
            await safe_defer(ctx)
        except Exception:
            pass  # already acked

        # Extra admin gate (in addition to decorator)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # Let caller know we're starting
        try:
            await ctx.interaction.edit_original_response(
                content="⏳ Starting Google Sheets export…"
            )
        except Exception:
            pass

        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)

        # Run export in a thread (blocking IO)
        start_ts = datetime.utcnow()
        try:
            success, log = await asyncio.to_thread(
                run_all_exports,
                SERVER,
                DATABASE,
                USERNAME,
                PASSWORD,
                CREDENTIALS_FILE,
                notify_channel=notify_channel,
                bot_loop=bot.loop,
            )
        except Exception as e:
            logger.exception("[COMMAND] /run_gsheets_export crashed")
            await ctx.interaction.edit_original_response(
                content=f"💥 Export failed unexpectedly: `{type(e).__name__}: {e}`"
            )
            return

        # Build result embed
        duration_s = (datetime.utcnow() - start_ts).total_seconds()

        # Normalize log output: accept either list[str] or single string
        if isinstance(log, list):
            # use a descriptive iterator name to avoid E741
            raw_text = "\n".join(str(line) for line in log).strip()
        else:
            raw_text = (log or "").strip()

        # Present logs in a code block if present; mark when truncated
        if raw_text:
            max_len = 3900  # leave room for code fences
            clipped = raw_text[:max_len]
            if len(raw_text) > max_len:
                clipped += "\n…(truncated)"
            desc = f"```{clipped}```"
        else:
            if success:
                desc = (
                    "All configured exports completed successfully.\n\n"
                    f"Details have been posted to {notify_channel.mention}."
                )
            else:
                desc = (
                    "The export appears to have failed, but no log output was captured. "
                    "Please check the bot logs and the notify channel."
                )

        title = "📊 Sheets Export Complete" if success else "❌ Sheets Export Failed"
        color = 0x2ECC71 if success else 0xE74C3C

        embed = discord.Embed(title=title, description=desc, color=color)
        embed.add_field(name="Triggered by", value=f"<@{ctx.user.id}>", inline=True)
        embed.add_field(name="Duration", value=f"{duration_s:.1f}s", inline=True)
        if notify_channel:
            embed.add_field(name="Notify channel", value=notify_channel.mention, inline=True)

        embed.set_footer(text=f"{SERVER} · {DATABASE}")
        embed.timestamp = datetime.utcnow()

        await ctx.interaction.edit_original_response(content=None, embed=embed)

    @bot.slash_command(
        name="restart_bot", description="Forcefully restart the bot", guild_ids=[GUILD_ID]
    )
    @versioned("v1.06")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def restart_bot_command(ctx):
        view = ConfirmRestartView(ctx, bot=bot, notify_channel_id=NOTIFY_CHANNEL_ID)
        await ctx.respond("⚠️ Are you sure you want to restart the bot?", view=view, ephemeral=True)

        # Cache the original ephemeral message so the view can disable itself
        try:
            view.message = await ctx.interaction.original_response()
        except Exception:
            pass

        try:
            await asyncio.wait_for(view.confirmed.wait(), timeout=30)
        except TimeoutError:
            # Use followup after initial respond
            await view._try_disable_ui()
            await ctx.followup.send(
                "⏱️ Restart cancelled – no confirmation received.", ephemeral=True
            )
            return

        if view.cancelled:
            await ctx.followup.send("✅ Restart request cancelled.", ephemeral=True)
            return

        logger.info("[RESTART] Confirmation received – proceeding with restart.")
        await asyncio.sleep(2)

        restart_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": ctx.user.id,
            "reason": "slash_restart",
        }

        try:
            with open(RESTART_FLAG_PATH, "w", encoding="utf-8") as f:
                json.dump(restart_data, f)
                f.flush()
                os.fsync(f.fileno())
            logger.info("[RESTART] Restart flag file written")

            try:
                with open(RESTART_FLAG_PATH, encoding="utf-8") as f:
                    contents = f.read().strip()
                logger.info(f"[RESTART] Restart flag content: {contents}")
            except Exception as e:
                logger.exception(f"[RESTART] Failed to read back restart flag: {e}")

            ws_code, ws_reason, ws_time = "", "", ""
            if os.path.exists(".last_disconnect_reason"):
                try:
                    with open(".last_disconnect_reason", encoding="utf-8") as f:
                        ws_info = json.load(f)
                        ws_code = str(ws_info.get("code", ""))
                        ws_reason = ws_info.get("reason", "")
                        ws_time = ws_info.get("timestamp", "")
                except Exception as e:
                    logger.exception(
                        f"[RESTART] Failed to read .last_disconnect_reason for CSV: {e}"
                    )

            await append_csv_line(
                "restart_log.csv",
                [
                    restart_data["timestamp"],
                    restart_data["reason"],
                    restart_data["user_id"],
                    "success",
                    ws_code,
                    ws_reason,
                    ws_time,
                ],
            )

        except Exception as e:
            logger.exception(f"[RESTART] Failed to write restart flag or log: {e}")

        try:
            logger.info("[RESTART] Restarting bot via slash command.")
            logger.info(f"[RESTART] sys.executable = {sys.executable}")
            logger.info(f"[RESTART] sys.argv = {sys.argv}")

            # Followup (not respond) after the initial message
            await ctx.followup.send(
                "✅ Restarting now... This may take a few seconds.", ephemeral=True
            )
            await asyncio.sleep(3)

            flush_logs()

            with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                f.write(str(RESTART_EXIT_CODE))

            flush_logs()
            await asyncio.sleep(1)
            print("[RESTART] Restart flag written – sleeping before SIGTERM")
            print("[RESTART] Sending SIGTERM to self now.")
            os.kill(os.getpid(), signal.SIGTERM)

        except Exception as e:
            logger.exception(f"[RESTART ERROR] Restart attempt failed: {e}")
            try:
                await ctx.followup.send(
                    embed=discord.Embed(
                        title="❌ Restart Failed",
                        description=f"Bot restart failed: `{type(e).__name__}: {e}`",
                        color=0xE74C3C,
                    ),
                    ephemeral=True,
                )
            except Exception:
                pass

    # Commands.py — replace the whole function body of force_restart with this slimmer flow
    @bot.slash_command(
        name="force_restart",
        description="Force a restart via the watchdog mechanism (admin only).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.07")
    @safe_command
    @is_admin_and_notify_channel()
    @ext_commands.has_permissions(administrator=True)
    @track_usage()
    async def force_restart(ctx):
        logger.info("[COMMAND] /force_restart invoked by %s", ctx.user)

        # 1) Ack ASAP (best-effort)
        try:
            await safe_defer(ctx, ephemeral=True)
        except Exception:
            pass

        # 2) Tell the user ONCE, before we begin teardown racing the gateway
        try:
            await ctx.interaction.edit_original_response(content="🔄 Restarting via watchdog…")
        except Exception:
            pass  # If we already disconnected, it's fine.

        # 3) Schedule the actual restart; DO NOT await long-running work here
        async def _do_restart():
            try:
                # Write restart flag + audit quickly
                restart_flag = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "reason": "slash_force_restart",
                    "user_id": str(ctx.user.id),
                }
                with open(RESTART_FLAG_PATH, "w", encoding="utf-8") as f:
                    json.dump(restart_flag, f)
                    f.flush()
                    os.fsync(f.fileno())
                logger.info("[RESTART] Flag written")

                # Optional CSV audit (best-effort)
                try:
                    await append_csv_line(
                        "restart_log.csv",
                        [
                            restart_flag["timestamp"],
                            restart_flag["reason"],
                            restart_flag["user_id"],
                            "success",
                            "",
                            "",
                            "",
                        ],
                    )
                except Exception:
                    pass

                # Exit code file for watchdog
                try:
                    with open(EXIT_CODE_FILE, "w", encoding="utf-8") as f:
                        f.write(str(RESTART_EXIT_CODE))
                except Exception:
                    pass

                # Small delay to let the response leave the socket
                await asyncio.sleep(0.25)
            finally:
                # Trigger graceful shutdown via SIGTERM (your handler will run)
                logger.info("[RESTART] Sending SIGTERM to self")
                try:
                    os.kill(os.getpid(), signal.SIGTERM)
                except Exception:
                    # Windows can still deliver SIGTERM; if it failed, fall back:
                    os._exit(RESTART_EXIT_CODE)

        asyncio.create_task(_do_restart())
        # IMPORTANT: return immediately so we don’t block the loop
        return

    @bot.slash_command(
        name="resync_commands",
        description="Force resync of slash commands and update command cache",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.09")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def resync_commands(ctx):
        async with get_operation_lock("resync"):
            await safe_defer(ctx, ephemeral=True)

            # === Sync commands with timeout
            try:
                await asyncio.wait_for(bot.sync_commands(guild_ids=[GUILD_ID]), timeout=5.0)
                logger.info("[COMMAND SYNC] Slash commands successfully resynced.")
            except TimeoutError:
                logger.exception("[COMMAND SYNC] Timed out during sync — skipping.")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="⚠️ Sync Timed Out",
                        description="The command sync request took too long and was skipped.",
                        color=0xF39C12,
                    )
                )
                return
            except Exception as e:
                logger.exception("[COMMAND SYNC] Resync failed")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Sync Failed",
                        description=f"```{type(e).__name__}: {e}```",
                        color=0xE74C3C,
                    )
                )
                return

            # === Update command_cache.json (atomically)
            try:
                # Load existing cache (if present)
                try:
                    with open("command_cache.json", encoding="utf-8") as f:
                        old_cache = {cmd["name"]: cmd for cmd in json.load(f)}
                except FileNotFoundError:
                    old_cache = {}
                except Exception as e:
                    logger.warning(
                        "[COMMAND SYNC] Could not read existing command_cache.json: %s", e
                    )
                    old_cache = {}

                new_cache = []
                updated = []

                for command in bot.application_commands:
                    name = command.name
                    version = getattr(command.callback, "__version__", "N/A")
                    description = command.description or ""
                    cached_version = old_cache.get(name, {}).get("version")

                    entry = {
                        "name": name,
                        "version": version,
                        "description": description,
                        "admin_only": True,  # keep as-is; refine later if we introspect decorators
                    }
                    new_cache.append(entry)

                    if cached_version != version:
                        updated.append(f"/{name} → `{cached_version}` ➜ `{version}`")

                # Atomic write helper (scoped here so this block is self-contained)
                def _atomic_json_write(path: str, data):
                    import json
                    import os
                    import tempfile

                    d = os.path.dirname(path) or "."
                    fd, tmp = tempfile.mkstemp(dir=d, prefix=".cmdcache.", suffix=".tmp")
                    try:
                        with os.fdopen(fd, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                            f.flush()
                            os.fsync(f.fileno())
                        os.replace(tmp, path)  # atomic on POSIX + Windows
                    finally:
                        try:
                            if os.path.exists(tmp):
                                os.remove(tmp)
                        except Exception:
                            pass

                # Write atomically
                _atomic_json_write("command_cache.json", new_cache)

                summary = "\n".join(updated) if updated else "✅ No changes to cached versions."
                # Keep under embed description limit
                if len(summary) > 4000:
                    summary = summary[:3990] + "…"

                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="✅ Slash Commands Resynced & Cache Updated",
                        description=summary,
                        color=0x2ECC71,
                    )
                )

            except Exception as e:
                logger.exception("[COMMAND SYNC] Unexpected failure building/writing cache")
                await ctx.interaction.edit_original_response(
                    embed=discord.Embed(
                        title="❌ Cache Update Failed",
                        description=f"```{type(e).__name__}: {e}```",
                        color=0xE74C3C,
                    )
                )

    @bot.slash_command(
        name="show_command_versions",
        description="List all currently loaded slash commands with their versions",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def show_command_versions(ctx):

        await safe_defer(ctx, ephemeral=True)

        try:
            # Sort for stable output
            cmds = sorted(bot.application_commands, key=lambda c: c.name.lower())

            embed = discord.Embed(
                title="📦 Loaded Slash Command Versions",
                description="Showing all commands and their current version tags.",
                color=0x3498DB,
            )

            # Discord embeds allow max 25 fields. If we have more, use a description list.
            if len(cmds) <= 25:
                for command in cmds:
                    version = getattr(command.callback, "__version__", "N/A")
                    embed.add_field(
                        name=f"/{command.name}", value=f"Version: `{version}`", inline=False
                    )
            else:
                lines = []
                for command in cmds:
                    version = getattr(command.callback, "__version__", "N/A")
                    lines.append(f"/{command.name} — `{version}`")
                text = "\n".join(lines)
                # Keep under embed description limits (~4096 chars)
                if len(text) > 3900:
                    text = text[:3890] + "…"
                embed.description = (
                    f"Showing all commands and their current version tags.\n\n{text}"
                )

            await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /show_command_versions failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to build command version list: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="validate_command_cache",
        description="Check for mismatched or missing entries in command_cache.json",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.04")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def validate_command_cache(ctx):

        await safe_defer(ctx, ephemeral=True)

        # Load cache
        try:
            with open("command_cache.json", encoding="utf-8") as f:
                raw = json.load(f)
                cache = {entry["name"]: entry.get("version", "N/A") for entry in raw}
        except Exception as e:
            logger.exception("[COMMAND] /validate_command_cache load failed")
            await ctx.interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Failed to Load Cache",
                    description=f"```{type(e).__name__}: {e}```",
                    color=0xE74C3C,
                )
            )
            return

        # Build checks
        loaded_cmds = sorted(bot.application_commands, key=lambda c: c.name.lower())
        loaded_names = {c.name for c in loaded_cmds}
        cache_names = set(cache.keys())

        issues = []

        # Missing or mismatched
        for command in loaded_cmds:
            name = command.name
            version = getattr(command.callback, "__version__", "N/A")
            cached = cache.get(name)
            if cached is None:
                issues.append(f"➕ `/{name}` is **missing** from cache (code=`{version}`)")
            elif cached != version:
                issues.append(f"🔁 `/{name}` version mismatch: cache=`{cached}`, code=`{version}`")

        # Stale entries (in cache but not loaded anymore)
        stale = sorted(cache_names - loaded_names)
        for name in stale:
            issues.append(f"➖ `/{name}` is in cache but not currently loaded")

        # Build response
        if issues:
            # Keep under embed description limit (~4096)
            full = "\n".join(issues)
            if len(full) > 3900:
                clipped = []
                total = 0
                for line in issues:
                    if total + len(line) + 1 > 3900:
                        break
                    clipped.append(line)
                    total += len(line) + 1
                remaining = len(issues) - len(clipped)
                full = "\n".join(clipped) + (f"\n…and {remaining} more." if remaining > 0 else "")
            embed = discord.Embed(
                title="🧩 Command Cache Validation", description=full, color=0xF1C40F
            )
        else:
            embed = discord.Embed(
                title="🧩 Command Cache Validation",
                description="✅ All commands are correctly versioned and cached.",
                color=0x2ECC71,
            )

        await ctx.interaction.edit_original_response(embed=embed)

    @bot.slash_command(
        name="view_restart_log", description="View recent bot restarts", guild_ids=[GUILD_ID]
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def view_restart_log(ctx, count: int = 5):
        await safe_defer(ctx, ephemeral=True)

        log_file = "restart_log.csv"
        if not os.path.exists(log_file):
            await ctx.interaction.edit_original_response(content="⚠️ No restart log found.")
            return

        # Clamp count to keep the embed manageable
        count = max(1, min(int(count or 5), 20))

        try:
            with open(log_file, encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                await ctx.interaction.edit_original_response(
                    content="✅ No restart events have been recorded yet."
                )
                return

            # Take last N rows (most recent assumed at end of file)
            selected = rows[-count:]

            # Pick color from the most recent selected entry
            last_status = (selected[-1].get("Status", "") or "").lower()
            if "crash" in last_status:
                embed_color = discord.Color.red()
            elif "success" in last_status:
                embed_color = discord.Color.green()
            else:
                embed_color = discord.Color.orange()

            embed = discord.Embed(title="📜 Recent Bot Restarts", color=embed_color)

            # Add fields newest → oldest
            for row in reversed(selected):
                ts = row.get("Timestamp", "—")
                rsn = row.get("Reason", "—")
                uid = row.get("UserId", row.get("user_id", "SYSTEM"))  # support both header styles
                stat = row.get("Status", "—")

                ws_code = row.get("WS Code", row.get("ws_code", "")) or ""
                ws_desc = row.get("WS Reason", row.get("ws_reason", "")) or ""
                ws_time = row.get("WS Time", row.get("ws_time", "")) or ""

                trigger = f"<@{uid}>" if uid and uid != "SYSTEM" else "🛠️ System"
                reason_label = (rsn or "").replace("_", " ").capitalize()

                desc = (
                    f"👤 **Triggered By:** {trigger}\n"
                    f"📄 **Reason:** `{reason_label}`\n"
                    f"📌 **Status:** `{stat}`"
                )
                if ws_code and ws_desc:
                    desc += f"\n🔌 **Last Disconnect:** `{ws_code}` – {ws_desc}"
                    if ws_time:
                        desc += f"\n🕒 {ws_time}"

                embed.add_field(name=f"🕒 {ts}", value=desc, inline=False)

            embed.set_footer(text=f"Showing last {len(selected)} restarts")
            await ctx.interaction.edit_original_response(content=None, embed=embed)

        except Exception as e:
            logger.exception("[RESTART_LOG] Failed to read or parse restart log.")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to load restart log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="import_proc_config",
        description="Manually run the ProcConfig import (admin only)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @ext_commands.has_permissions(administrator=True)
    @track_usage()
    async def import_proc_config(ctx):
        """
        Run ProcConfig import from Discord command.
        Uses run_proc_config_import_offload to perform the heavy work in a subprocess/thread
        so we don't block the bot's event loop.
        """
        start_ts = None
        dur = None
        try:
            # Optionally defer the interaction if long-running
            try:
                await safe_defer(ctx, ephemeral=True)
            except Exception:
                # safe_defer may not be desired in all contexts; proceed if it fails
                logger.debug("safe_defer failed or skipped", exc_info=False)

            start_ts = datetime.utcnow()

            # Let the caller see progress
            try:
                await ctx.interaction.edit_original_response(
                    content="⏳ Starting ProcConfig import…"
                )
            except Exception:
                # If editing the original response fails, continue — we'll still try to send final status
                logger.debug("Could not send start progress message", exc_info=False)

            try:
                # Offload the synchronous import to a process/thread to avoid blocking
                success, report = await run_proc_config_import_offload(
                    dry_run=False, prefer_process=True
                )
            except Exception as e:
                logger.exception("[COMMAND] /import_proc_config crashed")
                # Try to inform the user of the unexpected crash
                try:
                    await ctx.interaction.edit_original_response(
                        content=f"💥 Import failed unexpectedly: `{type(e).__name__}: {e}`"
                    )
                except Exception:
                    logger.debug("Failed to notify user about unexpected crash", exc_info=False)
                return

            dur = (datetime.utcnow() - start_ts).total_seconds() if start_ts else None

            if success:
                logger.info(
                    "[COMMAND] /import_proc_config completed successfully in %.2fs", dur or 0.0
                )
                try:
                    await ctx.interaction.edit_original_response(
                        content=f"✅ ProcConfig import completed successfully in **{(dur or 0.0):.1f}s**."
                    )
                except Exception:
                    logger.debug("Failed to send success response to user", exc_info=False)
            else:
                logger.error(
                    "[COMMAND] /import_proc_config reported failure after %.2fs", dur or 0.0
                )

                # Ensure report is a dict before accessing keys
                report = report or {}
                errors = report.get("errors") or []
                short_err = "; ".join(errors[:3]) or "Unknown error"
                persisted = report.get("persisted_to") or report.get("manifest_path")
                msg = f"❌ ProcConfig import failed: {short_err} in **{(dur or 0.0):.1f}s**"
                if persisted:
                    msg += f" (report: {persisted})"

                try:
                    # edit_original_response typically doesn't accept ephemeral; omit it here
                    await ctx.interaction.edit_original_response(content=msg)
                except Exception:
                    # If editing the original response fails, try sending a followup or log
                    logger.debug(
                        "Failed to send failure response to user via edit_original_response",
                        exc_info=False,
                    )
                    try:
                        await ctx.send(msg, ephemeral=True)
                    except Exception:
                        logger.debug(
                            "Also failed to send failure response via ctx.send", exc_info=False
                        )

        except Exception as e:
            # Make sure we don't crash attempting to reference dur/start_ts
            logger.exception("import_proc_config handler failed: %s", e)
            dur_str = (
                f"{(datetime.utcnow() - start_ts).total_seconds():.1f}s" if start_ts else "unknown"
            )
            try:
                await ctx.interaction.edit_original_response(
                    content=(
                        "❌ Unexpected error starting ProcConfig import. "
                        f"Duration **{dur_str}**. Please check the logs for details."
                    )
                )
            except Exception:
                logger.debug("Failed to send failure response to user", exc_info=False)

    @bot.slash_command(
        name="dl_bot_status",
        description="Check if the bot is running and connected to SQL.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.03")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def status_command(ctx):
        await safe_defer(ctx, ephemeral=True)

        # Belt-and-braces admin gate (decorator already limits usage)
        if ctx.user.id != ADMIN_USER_ID:
            await ctx.interaction.edit_original_response(
                content="❌ This command is restricted to admins."
            )
            return

        # --- Check DB connection
        try:
            conn_str = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                f"SERVER={SERVER};"
                f"DATABASE={DATABASE};"
                f"UID={USERNAME};"
                f"PWD={PASSWORD};"
            )
            import pyodbc

            with pyodbc.connect(conn_str, timeout=5) as conn:
                conn.execute("SELECT 1")
            db_ok = True
            db_status = "🟢 SQL connected"
        except Exception as e:
            db_ok = False
            db_status = f"🔴 SQL ERROR: `{type(e).__name__}: {str(e)[:150]}`"

        # --- Check Google Sheets
        try:
            success, message = check_basic_gsheets_access(CREDENTIALS_FILE, SHEET_ID)
            gsheets_ok = bool(success)
            gsheets_status = f"🟢 {message}" if success else f"🟠 {message}"
        except Exception as e:
            gsheets_ok = False
            gsheets_status = f"🔴 ERROR: {type(e).__name__}: {str(e)[:120]}"

        # --- Uptime + latency
        now = datetime.now(UTC)
        delta = now - start_bot_time
        total_seconds = int(delta.total_seconds())
        days, rem_hours = divmod(total_seconds // 3600, 24)
        minutes = (total_seconds % 3600) // 60
        uptime = f"{int(days)}d {int(rem_hours)}h {int(minutes)}m"

        ws_latency_ms = int(getattr(bot, "latency", 0) * 1000)

        # Overall status colour
        if db_ok and gsheets_ok:
            colour = discord.Color.green()
            headline = "All systems operational ✅"
        elif db_ok or gsheets_ok:
            colour = discord.Color.orange()
            headline = "Degraded performance ⚠️"
        else:
            colour = discord.Color.red()
            headline = "Multiple issues detected ❌"

        embed = discord.Embed(title="📡 DL_Bot Status", description=headline, color=colour)
        embed.add_field(name="DL_Bot", value=f"✅ Online • {ws_latency_ms} ms latency", inline=True)
        embed.add_field(name="Database", value=db_status, inline=True)
        embed.add_field(name="Google Sheets", value=gsheets_status, inline=True)
        embed.add_field(name="Uptime", value=uptime, inline=False)
        embed.set_footer(text=f"Checked by {ctx.user.name} • {SERVER}/{DATABASE}")
        embed.timestamp = now

        await ctx.interaction.edit_original_response(embed=embed)

    @bot.slash_command(
        name="logs",
        description="Tail logs with filters & paging (general/error/crash).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.10")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def logs_command(
        ctx,
        source: str = discord.Option(
            str, "Which log?", choices=["general", "error", "crash"], default="general"
        ),
        level: str = discord.Option(
            str,
            "Filter by level",
            choices=["INFO", "WARNING", "ERROR", "CRITICAL", "(none)"],
            required=False,
        ),
        contains: str = discord.Option(str, "Substring or regex", required=False),
        page: int = discord.Option(int, "Page number", required=False, default=1),
        page_size: int = discord.Option(int, "Lines per page (10-200)", required=False, default=50),
    ):
        await safe_defer(ctx, ephemeral=True)
        lvl = None if (level or "") == "(none)" else level
        path = _pick_log_source(source)

        if not os.path.exists(path):
            await ctx.interaction.edit_original_response(content=f"⚠️ Log file not found: `{path}`")
            return

        title = {
            "general": "📄 General Log",
            "error": "🚨 Error Log",
            "crash": "💥 Crash Log",
        }.get(source, "📄 Log")

        view = LogTailView(
            ctx, path, title, level=lvl, contains=contains, page=page, page_size=page_size
        )
        await view.render(ctx.interaction)
        await ctx.interaction.edit_original_response(view=view)

    @bot.slash_command(
        name="show_logs",
        description="Show recent entries from the general log file.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def show_logs_command(ctx, lines: int = 20):
        await safe_defer(ctx, ephemeral=True)

        # Clamp the number of lines for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(FULL_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Log file not found: `{FULL_LOG_PATH}`"
            )
            return

        try:
            # Tail efficiently without loading the whole file
            dq = deque(maxlen=lines)
            with open(FULL_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip()
            if not message:
                message = "(log is empty)"

            # Neutralize accidental code fence endings inside the log
            safe_text = message.replace("```", "`\u200b``")

            # Embed description budget (Discord ~4096 chars; leave margin for fences)
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET

            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            # Build embed
            mtime = datetime.fromtimestamp(os.path.getmtime(FULL_LOG_PATH))
            embed = discord.Embed(title="📄 Last Log Entries", description=desc, color=0x3498DB)
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(FULL_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")

            if needs_file:
                # Attach full tail as a file to avoid embed limits
                buf = io.BytesIO(message.encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"log_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /show_logs failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="last_errors",
        description="Show recent entries from the error log.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def last_errors_command(ctx, lines: int = 20):

        await safe_defer(ctx, ephemeral=True)

        # Clamp lines for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(ERROR_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Error log not found: `{ERROR_LOG_PATH}`"
            )
            return

        try:
            # Efficient tail
            dq = deque(maxlen=lines)
            with open(ERROR_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip() or "(no errors logged)"

            # Neutralise accidental code-fence closures
            safe_text = message.replace("```", "`\u200b``")

            # Embed budget & attachment fallback
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET
            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            mtime = datetime.fromtimestamp(os.path.getmtime(ERROR_LOG_PATH))
            embed = discord.Embed(title="🚨 Last Error Entries", description=desc, color=0xE74C3C)
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(ERROR_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")
            embed.timestamp = datetime.utcnow()

            if needs_file:
                buf = io.BytesIO("\n".join(dq).encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"error_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /last_errors failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read error log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="crash_log",
        description="Show recent entries from the crash log.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def crash_log_command(ctx, lines: int = 20):

        await safe_defer(ctx, ephemeral=True)

        # Clamp for safety
        lines = max(1, min(int(lines or 20), 200))

        if not os.path.exists(CRASH_LOG_PATH):
            await ctx.interaction.edit_original_response(
                content=f"⚠️ Crash log not found: `{CRASH_LOG_PATH}`"
            )
            return

        try:
            # Efficient tail without loading whole file
            dq = deque(maxlen=lines)
            with open(CRASH_LOG_PATH, encoding="utf-8", errors="replace", newline="") as f:
                for ln in f:
                    dq.append(ln.rstrip("\n"))

            message = "\n".join(dq).strip() or "(no crash logs found)"

            # Neutralize accidental ``` inside the log
            safe_text = message.replace("```", "`\u200b``")

            # Embed budget + optional attachment
            BUDGET = 3800
            needs_file = len(safe_text) > BUDGET

            desc_body = safe_text[:BUDGET]
            if needs_file:
                desc_body += "\n…(truncated)"

            desc = f"```{desc_body}```"

            mtime = datetime.fromtimestamp(os.path.getmtime(CRASH_LOG_PATH))
            embed = discord.Embed(
                title="💥 Last Crash Log Entries",
                description=desc,
                color=0xFF6347,  # tomato; keep your original
            )
            embed.add_field(name="Lines", value=str(min(lines, len(dq))), inline=True)
            embed.add_field(name="File", value=os.path.basename(CRASH_LOG_PATH), inline=True)
            embed.set_footer(text=f"Modified {mtime:%Y-%m-%d %H:%M:%S}")
            embed.timestamp = datetime.utcnow()

            if needs_file:
                buf = io.BytesIO("\n".join(dq).encode("utf-8", "replace"))
                buf.seek(0)
                file = discord.File(buf, filename=f"crash_tail_{lines}.txt")
                await ctx.interaction.edit_original_response(embed=embed, attachments=[file])
            else:
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[COMMAND] /crash_log failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to read crash log: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="test_embed",
        description="🧪 Manually trigger the stats update embed",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.07")
    @safe_command
    @is_admin_and_notify_channel()
    @track_usage()
    async def test_embed_command(ctx):
        from datetime import datetime

        from bot_config import NOTIFY_CHANNEL_ID

        await safe_defer(ctx, ephemeral=True)
        start_ts = datetime.now(UTC)

        # Where the embed will land (for the admin’s confirmation)
        notify_channel = bot.get_channel(NOTIFY_CHANNEL_ID)

        try:
            # Determine if KVK fighting is open (blocking) — run off the loop
            is_kvk = await asyncio.to_thread(is_currently_kvk)

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

            # Send the test embed (async interface accepts (bot, timestamp, is_kvk, is_test=...))
            await send_stats_update_embed(bot, timestamp, is_kvk, is_test=True)

            dur = (datetime.now(UTC) - start_ts).total_seconds()
            where = notify_channel.mention if notify_channel else f"<#{OFFSEASON_STATS_CHANNEL_ID}>"
            await ctx.interaction.edit_original_response(
                content=(
                    "✅ **Test stats embed sent.**\n"
                    f"- KVK active: **{is_kvk}**\n"
                    f"- Timestamp: `{timestamp}`\n"
                    f"- Posted to: {where}\n"
                    f"- Duration: **{dur:.1f}s**"
                )
            )
            logger.info("[/test_embed] success (kvk=%s, dur=%.2fs)", is_kvk, dur)

        except Exception as e:
            logger.exception("[/test_embed] failed")
            await ctx.interaction.edit_original_response(
                content=f"❌ Failed to send embed:\n```{type(e).__name__}: {e}```"
            )

    @bot.slash_command(
        name="usage",
        description="View bot usage summary (admin/leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def usage_command(
        ctx: discord.ApplicationContext,
        period: str = discord.Option(str, "Time window", choices=["day", "week"], default="day"),
        by: str = discord.Option(
            str, "Group by", choices=["command", "user", "reliability"], default="command"
        ),
        context_filter: str = discord.Option(
            str,
            "Filter by context",
            choices=["slash", "component", "autocomplete", "all"],
            default="slash",
        ),
        limit: int = discord.Option(int, "Max rows", default=10),
    ):
        await safe_defer(ctx, ephemeral=True)
        limit = max(1, min(int(limit or 10), 50))
        since = utcnow() - (timedelta(days=7) if period == "week" else timedelta(days=1))

        # context WHERE clause
        ctx_sql, ctx_params = _ctx_filter_sql(context_filter)

        try:
            if by == "user":
                sql = f"""
                    SELECT TOP {limit} UserId,
                           MAX(UserDisplay) AS UserDisplay,
                           COUNT(*) AS Uses,
                           COUNT(DISTINCT CommandName) AS UniqueCommands
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY UserId
                    ORDER BY Uses DESC, UserId ASC;
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                lines = [
                    f"<@{r['UserId']}> · uses **{r['Uses']}** · cmds **{r['UniqueCommands']}**"
                    for r in rows
                ]
                title = f"Usage by user (last {period})"

            elif by == "reliability":
                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Total,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY CommandName
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                # compute success % in python and sort by worst
                stats = []
                for r in rows:
                    total = int(r["Total"] or 0)
                    ok = int(r["Successes"] or 0)
                    rate = (ok / total * 100.0) if total else 0.0
                    stats.append((r["CommandName"], total, ok, rate))
                stats.sort(key=lambda t: (100.0 - t[3], -t[1]))
                stats = stats[:limit]
                lines = [
                    f"`/{n}` · **{rate:.1f}%** success ({ok}/{tot})" for n, tot, ok, rate in stats
                ]
                title = f"Reliability by command (last {period})"

            else:
                # by == command
                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Uses,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
                           AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ?{ctx_sql}
                    GROUP BY CommandName
                    ORDER BY Uses DESC, CommandName ASC;
                """
                rows = await _fetch_rows(sql, (since, *ctx_params))
                rows = rows[:limit]
                lines = [
                    f"`/{r['CommandName']}` · uses **{r['Uses']}** · ok **{r['Successes']}** · avg {int(r['AvgLatencyMs'] or 0)}ms"
                    for r in rows
                ]
                title = f"Usage by command (last {period})"

            embed = discord.Embed(
                title=title,
                description=("\n".join(lines) or "_No data_"),
                colour=discord.Colour.blurple(),
            )
            await ctx.interaction.edit_original_response(embed=embed)
        except Exception as e:
            logger.exception("[/usage] failed")
            await ctx.interaction.edit_original_response(
                content=f"Sorry, I couldn't load usage stats: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="usage_detail",
        description="Drill down into a specific command or user (admin/leadership)",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @safe_command
    @is_admin_or_leadership()
    @track_usage()
    async def usage_detail_command(
        ctx: discord.ApplicationContext,
        # ✅ REQUIRED FIRST
        dimension: str = discord.Option(str, "Filter by", choices=["command", "user"]),
        value: str = discord.Option(
            str, "Command name or user mention/ID", autocomplete=_usage_detail_value_ac
        ),
        # ✅ OPTIONALS AFTER
        period: str = discord.Option(str, "Time window", choices=["day", "week"], default="day"),
        context_filter: str = discord.Option(
            str,
            "Filter by context",
            choices=["slash", "component", "autocomplete", "all"],
            default="slash",
        ),
    ):
        await safe_defer(ctx, ephemeral=True)
        since = utcnow() - (timedelta(days=7) if period == "week" else timedelta(days=1))
        ctx_sql, ctx_params = _ctx_filter_sql(context_filter)

        try:
            if dimension == "command":
                cmd = value.lstrip("/").strip()
                sql_pct = f"""
                    WITH s AS (
                      SELECT LatencyMs, Success
                      FROM {USAGE_TABLE}
                      WHERE ExecutedAtUtc >= ? AND CommandName = ?{ctx_sql}
                    )
                    SELECT
                      (SELECT COUNT(*) FROM s) AS Total,
                      (SELECT SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) FROM s) AS Successes,
                      (SELECT SUM(CASE WHEN Success=0 THEN 1 ELSE 0 END) FROM s) AS Failures,
                      (SELECT TOP 1 CAST(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                         FROM s WHERE LatencyMs IS NOT NULL) AS P50,
                      (SELECT TOP 1 CAST(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY CAST(LatencyMs AS float)) OVER () AS int)
                         FROM s WHERE LatencyMs IS NOT NULL) AS P95;
                """
                rows = await _fetch_rows(sql_pct, (since, cmd, *ctx_params))
                row = rows[0] if rows else {}
                total = int(row.get("Total") or 0)
                successes = int(row.get("Successes") or 0)
                failures = int(row.get("Failures") or 0)
                p50 = row.get("P50")
                p95 = row.get("P95")

                sql_errs = f"""
                    SELECT TOP 10 ErrorCode, COUNT(*) AS Cnt
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ? AND CommandName = ? AND Success = 0{ctx_sql}
                    GROUP BY ErrorCode
                    ORDER BY Cnt DESC, ErrorCode ASC;
                """
                errs = await _fetch_rows(sql_errs, (since, cmd, *ctx_params))
                err_lines = [f"`{e['ErrorCode']}` · {e['Cnt']}" for e in errs] or ["_No failures_"]

                desc = (
                    f"**/{cmd}** · last **{period}**\n"
                    f"Total **{total}** · Successes **{successes}** · Failures **{failures}**\n"
                    f"P50 **{(str(int(p50))+'ms') if p50 is not None else '–'}** · "
                    f"P95 **{(str(int(p95))+'ms') if p95 is not None else '–'}**\n\n"
                    f"**Top failure reasons:**\n" + "\n".join(err_lines)
                )
                embed = discord.Embed(
                    title="Usage detail — command",
                    description=desc,
                    colour=discord.Colour.blurple(),
                )
                await ctx.interaction.edit_original_response(embed=embed)

            else:
                # dimension == user
                # accept mention or raw ID
                m = re.search(r"\d{15,22}", value or "")
                uid = int(m.group(0)) if m else int(value)

                sql = f"""
                    SELECT CommandName,
                           COUNT(*) AS Uses,
                           SUM(CASE WHEN Success=1 THEN 1 ELSE 0 END) AS Successes,
                           AVG(CAST(LatencyMs AS float)) AS AvgLatencyMs
                    FROM {USAGE_TABLE}
                    WHERE ExecutedAtUtc >= ? AND UserId = ?{ctx_sql}
                    GROUP BY CommandName
                    ORDER BY Uses DESC, CommandName ASC;
                """
                rows = await _fetch_rows(sql, (since, uid, *ctx_params))
                lines = [
                    f"`/{r['CommandName']}` · uses **{r['Uses']}** · ok **{r['Successes']}** · avg {int(r['AvgLatencyMs'] or 0)}ms"
                    for r in rows
                ] or ["_No data_"]
                embed = discord.Embed(
                    title=f"Usage detail — user <@{uid}>",
                    description="\n".join(lines),
                    colour=discord.Colour.blurple(),
                )
                await ctx.interaction.edit_original_response(embed=embed)

        except Exception as e:
            logger.exception("[/usage_detail] failed")
            await ctx.interaction.edit_original_response(
                content=f"Sorry, I couldn't load usage detail: `{type(e).__name__}: {e}`"
            )

    @bot.slash_command(
        name="crystaltech_validate",
        description="Validate CrystalTech config & assets.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_validate(ctx: discord.ApplicationContext):
        await ctx.defer(ephemeral=True)
        try:
            service = get_crystaltech_service()
        except Exception as e:
            await ctx.respond(f"❌ Service not initialized: `{e}`", ephemeral=True)
            return

        report = service.report()
        if report is None:
            # If not yet loaded for any reason, trigger a fresh load here
            report = await service.reload(fail_on_warn=False)

        embed = _format_validate_embed(report)
        await ctx.respond(embed=embed, ephemeral=True)

    @bot.slash_command(
        name="crystaltech_reload",
        description="Reload CrystalTech config (hot).",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.00")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_reload(ctx: discord.ApplicationContext, fail_on_warn: bool = False):
        await ctx.defer(ephemeral=True)
        try:
            service = get_crystaltech_service()
        except Exception as e:
            await ctx.respond(f"❌ Service not initialized: `{e}`", ephemeral=True)
            return

        report = await service.reload(fail_on_warn=fail_on_warn)
        embed = _format_validate_embed(report)
        await ctx.respond(embed=embed, ephemeral=True)

    # ---------- CrystalTech runner using the generic picker ----------
    async def run_crystaltech_flow(
        interaction: discord.Interaction, governor_id: str, ephemeral: bool
    ):
        from crystaltech_di import get_crystaltech_service

        # 0) Claim the governor for this user (one session at a time)
        claimed, why = _session_claim(governor_id, interaction.user.id)
        if not claimed:
            msg = f"🔒 {why}"
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
            return

        # release helper (used by views on timeout/reset, and by error paths here)
        async def _release():
            _session_release(governor_id, interaction.user.id)

        try:
            try:
                service = get_crystaltech_service()
            except Exception as e:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"❌ CrystalTech is unavailable: `{e}`", ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"❌ CrystalTech is unavailable: `{e}`", ephemeral=True
                    )
                await _release()
                return

            rep = service.report()
            if not service.is_ready:
                msg = rep.summary() if rep else "Service not initialized."
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ {msg}", ephemeral=True)
                await _release()
                return

            entry = service.get_user_entry(governor_id)
            if entry:
                # Existing user → open progress panel as a fresh ephemeral message
                path_id = entry.get("selected_path_id")
                troop = entry.get("selected_troop_type", "unknown")

                view = ProgressView(
                    author_id=interaction.user.id,
                    governor_id=governor_id,
                    path_id=path_id,
                    troop=troop,
                    timeout=300,
                    on_release=_release,  # <-- important
                )
                embed, files = await view.render_embed()

                # Ack the picker (no files on edit), then send panel
                try:
                    await interaction.response.edit_message(
                        content="Opening progress…", embed=None, view=None, attachments=[]
                    )
                except Exception:
                    pass

                sent = await interaction.followup.send(
                    embed=embed, files=files, ephemeral=ephemeral, view=view
                )
                view.message = sent
                _session_refresh(governor_id, interaction.user.id)
                return

            # ---------- FIRST-TIME SETUP ----------
            label = await _resolve_governor_label(interaction.user.id, governor_id)
            accounts = [(governor_id, label)]
            view = SetupView(
                author_id=interaction.user.id,
                accounts=accounts,
                timeout=300,
                on_release=_release,  # <-- important
            )
            embed = view.make_embed()

            # 1) Ack the picker message (no components or files)
            try:
                await interaction.response.edit_message(
                    content="Opening setup…", embed=None, view=None, attachments=[]
                )
            except Exception:
                pass

            # 2) Send a NEW ephemeral message with the Setup view (so components render reliably)
            sent = await interaction.followup.send(embed=embed, ephemeral=ephemeral, view=view)
            view.message = sent
            _session_refresh(governor_id, interaction.user.id)

        except Exception as e:
            logger.exception("[CrystalTech] run_crystaltech_flow unhandled: %s", e, exc_info=True)
            # best-effort notify and release
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"❌ Unexpected error: `{type(e).__name__}: {e}`", ephemeral=True
                )
            await _release()

    @bot.slash_command(
        name="crystaltech_admin_reset",
        description="Archive CrystalTech progress and reset for the next KVK.",
        guild_ids=[GUILD_ID],
    )
    @versioned("v1.01")
    @is_admin_and_notify_channel()
    @safe_command
    @track_usage()
    async def crystaltech_admin_reset(
        ctx: discord.ApplicationContext,
        next_kvk_no: int = discord.Option(
            int,
            name="next_kvk_no",
            description="Optional: set the KVK number for the new season (e.g., 14).",
            required=False,
            default=None,
        ),
        only_me: bool = discord.Option(
            bool,
            name="only_me",
            description="Show only to me (ephemeral).",
            required=False,
            default=True,
        ),
    ):
        await safe_defer(ctx, ephemeral=only_me)
        from crystaltech_di import get_crystaltech_service

        try:
            service = get_crystaltech_service()
            if not service.is_ready:
                rep = service.report()
                msg = rep.summary() if rep else "Service not initialized."
                await ctx.followup.send(f"❌ {msg}", ephemeral=only_me)
                return

            # archive + reset
            archive_path = await service.archive_and_reset_all(next_kvk_no=next_kvk_no)
            await ctx.followup.send(
                f"✅ Archived current progress and reset for the next KVK."
                f"\n• Archive file: `{archive_path}`"
                f"\n• Next KVK: `{next_kvk_no if next_kvk_no is not None else 'unchanged'}`",
                ephemeral=only_me,
            )
        except Exception as e:
            logger.exception("[/crystaltech_admin_reset] failed")
            await ctx.followup.send(f"❌ Failed: `{type(e).__name__}: {e}`", ephemeral=only_me)
