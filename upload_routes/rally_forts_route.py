"""Rally Forts workbook upload route for the legacy Discord message listener."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
import re
from typing import Any

from upload_routes.common import resolve_notify_channel, schedule_best_effort

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RallyFortsRouteDeps:
    fort_rally_channel_id: int
    log_dir: str
    get_notify_channel: Callable[[], Awaitable[Any | None]]
    send_embed: Callable[..., Awaitable[None]]
    ensure_sql_headroom_or_notify: Callable[[Any], Awaitable[bool]]
    offload_callable: Callable[..., Awaitable[Any]]
    trigger_log_backup_background: Callable[[], Awaitable[Any]]
    create_task: Callable[[Awaitable[Any]], Any] = asyncio.create_task
    importer_loader: Callable[[], tuple[Callable[..., Any], Callable[..., Any]]] | None = None


def is_rally_daily(filename: str) -> bool:
    return re.search(r"^Rally_data_\d{2}-\d{2}-\d{4}\.xlsx$", filename, re.I) is not None


def is_rally_alltime(filename: str) -> bool:
    return re.search(r"Rally[_\s]?data.*all[\s_]?time.*\.xlsx$", filename, re.I) is not None


def _load_importers() -> tuple[Callable[..., Any], Callable[..., Any]]:
    from forts_ingest import import_rally_alltime_xlsx, import_rally_daily_xlsx

    return import_rally_alltime_xlsx, import_rally_daily_xlsx


def _safe_attachment_filename(filename: str) -> str | None:
    safe_name = os.path.basename(filename)
    if (
        not safe_name
        or safe_name in {".", ".."}
        or safe_name != filename
        or "/" in filename
        or "\\" in filename
    ):
        return None
    return safe_name


async def handle_rally_forts_upload(message: Any, deps: RallyFortsRouteDeps) -> bool:
    """Handle Rally Forts XLSX imports from the configured Fort Rally channel."""
    if message.channel.id != deps.fort_rally_channel_id or not message.attachments:
        return False

    notify_ch = await resolve_notify_channel(
        deps.get_notify_channel,
        message.channel,
        logger,
        "rally_forts_upload",
    )

    try:
        importer_loader = deps.importer_loader or _load_importers
        import_rally_alltime_xlsx, import_rally_daily_xlsx = importer_loader()
    except Exception as e:
        await deps.send_embed(
            notify_ch,
            "Rally Forts Import \u274c",
            {
                "Error": f"Import failure: {type(e).__name__}: {e}",
                "Hint": "Ensure forts_ingest.py and its dependencies (pandas, pyodbc) are installed in the venv.",
            },
            0xE74C3C,
        )
        return True

    downloads_dir = os.path.join(deps.log_dir, "downloads")
    try:
        os.makedirs(downloads_dir, exist_ok=True)
    except Exception:
        pass

    results: list[tuple[str, str, Any]] = []
    matched_any = False
    for attachment in message.attachments:
        if not attachment.filename.lower().endswith(".xlsx"):
            continue

        filename = attachment.filename
        safe_filename = _safe_attachment_filename(filename)
        if safe_filename is None:
            logger.warning("[RALLY] Rejected unsafe attachment filename: %r", filename)
            results.append(("err", filename, "Unsafe attachment filename"))
            continue

        local_path = os.path.join(downloads_dir, safe_filename)
        try:
            await attachment.save(local_path)
            logger.info("[RALLY] Saved %s to %s", filename, local_path)

            if is_rally_alltime(filename):
                matched_any = True
                logger.info("[RALLY] Detected ALL-TIME file: %s", filename)
                ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
                if not ok:
                    results.append(("err", filename, "Aborted: SQL log headroom insufficient"))
                    continue

                result = await deps.offload_callable(
                    import_rally_alltime_xlsx,
                    local_path,
                    name="import_rally_alltime_xlsx",
                    prefer_process=True,
                    meta={"path": local_path},
                )
                results.append(("ok", filename, result))
                schedule_best_effort(
                    deps.create_task,
                    deps.trigger_log_backup_background(),
                    logger,
                    "Failed to schedule background log-backup trigger",
                )
            elif is_rally_daily(filename):
                matched_any = True
                logger.info("[RALLY] Detected DAILY file: %s", filename)
                ok = await deps.ensure_sql_headroom_or_notify(notify_ch)
                if not ok:
                    results.append(("err", filename, "Aborted: SQL log headroom insufficient"))
                    continue

                result = await deps.offload_callable(
                    import_rally_daily_xlsx,
                    local_path,
                    name="import_rally_daily_xlsx",
                    prefer_process=True,
                    meta={"path": local_path},
                )
                results.append(("ok", filename, result))
                schedule_best_effort(
                    deps.create_task,
                    deps.trigger_log_backup_background(),
                    logger,
                    "Failed to schedule background log-backup trigger",
                )
            else:
                results.append(("skip", filename, "Unrecognized rally filename"))
        except Exception as e:
            logger.exception("[RALLY] Error processing attachment %s", attachment.filename)
            results.append(("err", attachment.filename, f"{type(e).__name__}: {e}"))

    if not matched_any and not results:
        await deps.send_embed(
            notify_ch,
            "Rally Forts Import \u26a0\ufe0f",
            {
                "Info": "No rally .xlsx attachments matched expected patterns.",
                "Expected Daily": "Rally_data_DD-MM-YYYY.xlsx",
                "Expected All-Time": "Rally_data_All_Time*.xlsx",
            },
            0xE67E22,
        )
        return True

    fields = {
        "Source Channel": f"#{message.channel.name} ({message.channel.id})",
        "Uploaded By": f"{message.author} ({message.author.id})",
    }
    oks = [result for result in results if result[0] == "ok"]
    errs = [result for result in results if result[0] == "err"]
    skips = [result for result in results if result[0] == "skip"]

    for _, filename, result in oks[:5]:
        if isinstance(result, dict):
            rows = result.get("rows")
            as_of = result.get("as_of")
            extra = f"rows={rows}" + (f"; as_of={as_of}" if as_of else "")
        else:
            extra = str(result)
        fields[f"\u2705 {filename}"] = extra or "ok"

    for _, filename, why in skips[:5]:
        fields[f"\u23ed\ufe0f {filename}"] = why

    for _, filename, err in errs[:5]:
        fields[f"\u274c {filename}"] = err

    color = 0x2ECC71 if oks and not errs else (0xE67E22 if oks and errs else 0xE74C3C)
    title = "Rally Forts Import" + (
        " \u2705" if oks and not errs else " \u26a0\ufe0f" if oks and errs else " \u274c"
    )

    try:
        await deps.send_embed(notify_ch, title, fields, color)
    except Exception:
        logger.exception("Failed to send Rally Forts import embed")

    return True
