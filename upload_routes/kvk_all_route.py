"""KVK all-kingdom workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
from typing import Any

from kvk_all_importer import ingest_kvk_all_excel

logger = logging.getLogger(__name__)

ACCEPTED_KVK_ALL_EXTENSIONS = (".xlsx", ".xls", ".csv")


@dataclass(frozen=True)
class KvkAllRouteDeps:
    prokingdom_channel_id: int
    bot: Any
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    auto_export_enabled: bool
    auto_export_scheduler: Callable[[int, Any, Any], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    get_sheet_id: Callable[[], str | None] | None = None
    embed_factory: Callable[..., Any] | None = None
    view_factory: Callable[[], Any] | None = None
    button_factory: Callable[..., Any] | None = None
    button_style_link: Any | None = None
    custom_avatar_url: str | None = None


def _default_embed_factory(**kwargs: Any) -> Any:
    import discord

    return discord.Embed(**kwargs)


def _default_view_factory() -> Any:
    import discord

    return discord.ui.View()


def _default_button_factory(**kwargs: Any) -> Any:
    import discord

    return discord.ui.Button(**kwargs)


def _default_button_style_link() -> Any:
    import discord

    return discord.ButtonStyle.link


def _resolve_custom_avatar_url(deps: KvkAllRouteDeps) -> str | None:
    if deps.custom_avatar_url is not None:
        return deps.custom_avatar_url
    try:
        from constants import CUSTOM_AVATAR_URL

        return CUSTOM_AVATAR_URL
    except Exception:
        return None


def _resolve_sheet_id(deps: KvkAllRouteDeps) -> str | None:
    if deps.get_sheet_id is not None:
        return deps.get_sheet_id()
    return os.environ.get("KVK_SHEET_ID") or os.environ.get("ALL_KVK_SHEET_ID")


def _build_result_embed(deps: KvkAllRouteDeps, title: str, color: int, fields: dict[str, str]) -> Any:
    embed_factory = deps.embed_factory or _default_embed_factory
    embed = embed_factory(title=title, color=color)
    for key, value in fields.items():
        embed.add_field(name=key, value=str(value), inline=True)

    avatar_url = _resolve_custom_avatar_url(deps)
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    return embed


def _build_sheet_view(deps: KvkAllRouteDeps) -> Any | None:
    try:
        sheet_id = _resolve_sheet_id(deps)
        if not sheet_id:
            return None
        view_factory = deps.view_factory or _default_view_factory
        button_factory = deps.button_factory or _default_button_factory
        button_style_link = (
            deps.button_style_link if deps.button_style_link is not None else _default_button_style_link()
        )
        view = view_factory()
        view.add_item(
            button_factory(
                label="\U0001f4c4 Open KVK_ALLPLAYER_OUTPUT",
                url=f"https://docs.google.com/spreadsheets/d/{sheet_id}",
                style=button_style_link,
            )
        )
        return view
    except Exception:
        logger.info("[KVK EXPORT] ALL KVK SHEET ID INVALID")
        return None


async def handle_kvk_all_upload(message: Any, deps: KvkAllRouteDeps) -> bool:
    """Handle KVK all-kingdom uploads from the configured Pro Kingdom channel."""
    if message.channel.id != deps.prokingdom_channel_id or not message.attachments:
        return False

    notify_ch = await deps.get_notify_channel() or message.channel

    try:
        logger.info(
            "[KVK] msg=%s attachments=%s",
            message.id,
            [attachment.filename for attachment in message.attachments],
        )
    except Exception:
        pass

    excel_attachments = [
        attachment
        for attachment in message.attachments
        if attachment.filename.lower().strip().endswith(ACCEPTED_KVK_ALL_EXTENSIONS)
    ]

    if not excel_attachments:
        await deps.send_embed(
            notify_ch,
            "KVK All-Kingdom Import \u26a0\ufe0f",
            {
                "Info": "No .xlsx/.xls/.csv attachment found.",
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            },
            0xE67E22,
        )
        return True

    for attachment in excel_attachments:
        try:
            logger.info(
                "[KVK] Reading attachment: %s (%s bytes)",
                attachment.filename,
                getattr(attachment, "size", None),
            )
            file_bytes = await attachment.read()

            ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
            if not ok:
                await deps.send_embed(
                    notify_ch,
                    "KVK All-Kingdom Import Aborted \u274c",
                    {"File": attachment.filename, "Reason": "SQL log headroom insufficient"},
                    0xE74C3C,
                )
                continue

            result = await deps.offload_callable(
                ingest_kvk_all_excel,
                content=file_bytes,
                source_filename=attachment.filename,
                uploader_id=message.author.id,
                scan_ts_utc=message.created_at,
                server=os.environ.get("SQL_SERVER"),
                database=os.environ.get("SQL_DATABASE"),
                username=os.environ.get("SQL_USERNAME"),
                password=os.environ.get("SQL_PASSWORD"),
                name="ingest_kvk_all_excel",
                prefer_process=True,
                meta={"filename": attachment.filename},
            )

            if isinstance(result, dict) and not result.get("success", True):
                logger.info("[KVK] Import failed for %s: %s", attachment.filename, result.get("error"))
                await deps.send_embed(
                    notify_ch,
                    "KVK All-Kingdom Import \u274c",
                    {
                        "Filename": attachment.filename,
                        "Channel": f"#{message.channel.name} ({message.channel.id})",
                        "Uploader": f"{message.author} ({message.author.id})",
                        "Error": result.get("error"),
                        "Sheet": result.get("sheet", "unknown"),
                    },
                    0xE74C3C,
                )
                continue

            kvk_no = int(result["kvk_no"])
            scan_id = int(result["scan_id"])
            rows = int(result["row_count"])
            neg = int(result["negatives"])
            dur_s = float(result["duration_s"])
            staged = int(result.get("staged_rows", rows))
            proc_ms = float(result.get("proc_ms", max(0.0, dur_s * 1000.0)))
            io_ms = max(0.0, dur_s * 1000.0 - proc_ms)
            recompute_ms = float(result.get("recompute_ms", 0.0))
            sheet_used = result.get("sheet", "unknown")

            neg_badge = "0" if neg == 0 else f"{neg} \u26a0\ufe0f"
            color = 0x2ECC71 if neg == 0 else 0xE67E22
            title = (
                "KVK All-Kingdom Import \u2705"
                if neg == 0
                else "KVK All-Kingdom Import \u26a0\ufe0f"
            )

            fields = {
                "KVK": str(kvk_no),
                "ScanID": str(scan_id),
                "Rows": str(rows),
                "Staged": str(staged),
                "Negative Corrections": neg_badge,
                "Duration": f"{dur_s:.2f}s",
                "Health": (
                    f"proc `{proc_ms:.0f}ms` \u2022 I/O `{io_ms:.0f}ms`"
                    + (f" \u2022 recompute `{recompute_ms:.0f}ms`" if recompute_ms > 0 else "")
                ),
                "File": attachment.filename,
                "Sheet": sheet_used,
                "Channel": f"#{message.channel.name} ({message.channel.id})",
                "Uploader": f"{message.author} ({message.author.id})",
            }

            embed = _build_result_embed(deps, title, color, fields)
            view = _build_sheet_view(deps)
            await notify_ch.send(embed=embed, view=view)

            if deps.auto_export_enabled:
                logger.info(
                    "[KVK_EXPORT] Scheduling auto-export for KVK %s (Scan %s)",
                    kvk_no,
                    scan_id,
                )
                deps.create_task(
                    deps.auto_export_scheduler(
                        kvk_no,
                        notify_ch,
                        deps.bot.loop,
                    )
                )
        except Exception as exc:
            logger.exception("[KVK] Import failed for %s: %s", attachment.filename, exc)
            await deps.send_embed(
                notify_ch,
                "KVK All-Kingdom Import \u274c",
                {
                    "Error": f"{type(exc).__name__}: {exc}",
                    "File": attachment.filename,
                    "Channel": f"#{message.channel.name} ({message.channel.id})",
                    "Uploader": f"{message.author} ({message.author.id})",
                },
                0xE74C3C,
            )
    return True
