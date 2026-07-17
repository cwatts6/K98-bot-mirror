"""Service orchestration for private all-linked Account Data downloads."""

from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import UTC, datetime
import logging
from pathlib import Path
import shutil
import tempfile
from time import monotonic
from typing import Callable

import pandas as pd

from player_self_service import accounts_export, accounts_service
from player_self_service.account_data_export_contract import (
    AccountDataExportFile,
    AccountDataExportMetadata,
    AccountDataExportOutcome,
    AccountDataOutputKind,
    AuthorisedAccountDataContext,
    HistoryWindowResult,
    ensure_child_path,
    filter_history_window,
    normalise_utc,
    safe_filename_part,
    validate_history_days,
    validate_output_kind,
)
from services import governor_account_service
from stats.dal import stats_export_dal
from stats_exporter import build_account_data_workbook
from stats_exporter_csv import build_account_data_history_csv

logger = logging.getLogger(__name__)


def cleanup_export_file(export_file: AccountDataExportFile | None) -> None:
    """Idempotently remove an Account Data file and its owned temporary directory."""
    if export_file is None:
        return
    try:
        export_file.file_path.unlink(missing_ok=True)
    except Exception:
        logger.warning("account_data_export_file_cleanup_failed", exc_info=True)
    try:
        if export_file.temp_dir.exists():
            shutil.rmtree(export_file.temp_dir)
    except Exception:
        logger.warning("account_data_export_dir_cleanup_failed", exc_info=True)


def telemetry_payload(
    export_file: AccountDataExportFile, *, discord_user_id: int, duration_ms: int
) -> dict[str, object]:
    metadata = export_file.metadata
    return {
        "event": "account_data_export",
        "user_id": int(discord_user_id),
        "output_kind": metadata.output_kind.value,
        "requested_days": metadata.requested_days,
        "authorised_governors": metadata.authorised_governor_count,
        "snapshot_rows": metadata.snapshot_row_count,
        "history_rows": metadata.history_row_count,
        "window_start": metadata.window_start.isoformat() if metadata.window_start else None,
        "window_end": metadata.window_end.isoformat() if metadata.window_end else None,
        "duration_ms": max(0, int(duration_ms)),
        "outcome": "ok",
    }


async def build_account_data_export(
    *,
    discord_user_id: int,
    display_name: str,
    requested_kind: AccountDataOutputKind | str,
    requested_days: int | None,
    generated_at_utc: datetime | None = None,
) -> AccountDataExportOutcome:
    started = monotonic()
    try:
        output_kind = validate_output_kind(requested_kind)
        days = validate_history_days(output_kind, requested_days)
    except (TypeError, ValueError) as exc:
        return AccountDataExportOutcome(status="invalid_request", message=str(exc))

    generated = normalise_utc(generated_at_utc or datetime.now(UTC))
    user_id = int(discord_user_id)
    resolution = await governor_account_service.get_account_summary_for_user(user_id)
    if not resolution.ok:
        logger.warning("account_data_export_registry_unavailable user_id=%s", user_id)
        return AccountDataExportOutcome(
            status="registry_error",
            message="The account registry is temporarily unavailable. Please try again.",
        )
    if not resolution.governor_ids:
        return AccountDataExportOutcome(
            status="no_accounts",
            message="No linked governors are available. Open `/me accounts` to manage your account links.",
        )

    portfolio = await accounts_service.build_accounts_portfolio_from_resolution(
        user_id,
        resolution,
        refreshed_at_utc=generated,
    )
    context = AuthorisedAccountDataContext(
        discord_user_id=user_id,
        display_name=str(display_name or ""),
        portfolio=portfolio,
        governor_ids=tuple(int(value) for value in resolution.governor_ids),
        generated_at_utc=generated,
    )

    window: HistoryWindowResult | None = None
    if output_kind is not AccountDataOutputKind.CURRENT_SNAPSHOT:
        assert days is not None
        try:
            fetched = await asyncio.to_thread(
                stats_export_dal.fetch_daily_player_export,
                context.governor_ids,
            )
            authorised = _authorise_history_rows(fetched, context.governor_ids)
            window = filter_history_window(authorised, days)
        except ValueError:
            logger.error(
                "account_data_export_history_contract_failed user_id=%s kind=%s",
                user_id,
                output_kind.value,
                exc_info=True,
            )
            return AccountDataExportOutcome(
                status="data_error",
                message="Stats history did not meet the export contract. No file was created.",
            )
        except Exception:
            logger.exception(
                "account_data_export_history_read_failed user_id=%s kind=%s",
                user_id,
                output_kind.value,
            )
            return AccountDataExportOutcome(
                status="data_error",
                message="Stats history is temporarily unavailable. Please try again.",
            )
        if window.invalid_date_rows:
            logger.warning(
                "account_data_export_invalid_dates_excluded user_id=%s rows=%s",
                user_id,
                window.invalid_date_rows,
            )

    metadata = _build_metadata(context, output_kind=output_kind, days=days, window=window)
    temp_dir = Path(tempfile.mkdtemp(prefix="k98_account_data_"))
    export_file: AccountDataExportFile | None = None
    try:
        filename, target = _export_target(
            context,
            output_kind=output_kind,
            temp_dir=temp_dir,
        )
        export_file = AccountDataExportFile(
            file_path=target,
            temp_dir=temp_dir,
            filename=filename,
            metadata=metadata,
        )
        await _run_export_builder(
            lambda: _write_export_file(
                output_kind=output_kind,
                filename=filename,
                target=target,
                portfolio=portfolio,
                context=context,
                metadata=metadata,
                window=window,
            ),
            export_file=export_file,
        )
        if not target.is_file() or target.stat().st_size <= 0:
            raise ValueError("Export builder did not create a non-empty file.")
    except Exception:
        logger.exception(
            "account_data_export_build_failed user_id=%s kind=%s",
            user_id,
            output_kind.value,
        )
        cleanup_export_file(export_file or _cleanup_placeholder(temp_dir, metadata))
        return AccountDataExportOutcome(
            status="generation_error",
            message="The download could not be generated. Please try again.",
        )

    elapsed_ms = int((monotonic() - started) * 1000)
    logger.info(
        "account_data_export_ready user_id=%s kind=%s governors=%s snapshot_rows=%s history_rows=%s duration_ms=%s",
        user_id,
        output_kind.value,
        metadata.authorised_governor_count,
        metadata.snapshot_row_count,
        metadata.history_row_count,
        elapsed_ms,
    )
    return AccountDataExportOutcome(status="ok", export_file=export_file)


async def _run_export_builder(
    builder: Callable[[], None], *, export_file: AccountDataExportFile
) -> None:
    """Run a writer without letting task cancellation race its owned-file cleanup."""
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="k98-account-data")
    try:
        work = executor.submit(builder)
        try:
            await asyncio.shield(asyncio.wrap_future(work))
        except asyncio.CancelledError:
            work.add_done_callback(
                lambda completed: _cleanup_cancelled_builder(completed, export_file)
            )
            raise
    finally:
        executor.shutdown(wait=False, cancel_futures=False)


def _cleanup_cancelled_builder(
    completed: Future[None], export_file: AccountDataExportFile
) -> None:
    """Clean only after the underlying writer has released its file handles."""
    try:
        completed.result()
    except BaseException:
        pass
    cleanup_export_file(export_file)


def _write_export_file(
    *,
    output_kind: AccountDataOutputKind,
    filename: str,
    target: Path,
    portfolio: accounts_service.AccountsPortfolioPayload,
    context: AuthorisedAccountDataContext,
    metadata: AccountDataExportMetadata,
    window: HistoryWindowResult | None,
) -> None:
    if output_kind is AccountDataOutputKind.CURRENT_SNAPSHOT:
        snapshot = accounts_export.build_accounts_csv(portfolio)
        if snapshot.filename != filename:
            raise ValueError("Snapshot filename contract mismatch.")
        target.write_bytes(snapshot.data)
        return
    if output_kind is AccountDataOutputKind.RAW_HISTORY:
        assert window is not None
        build_account_data_history_csv(window.frame, out_path=target)
        return
    assert window is not None
    build_account_data_workbook(
        window.frame,
        portfolio=portfolio,
        governor_ids=context.governor_ids,
        metadata=metadata,
        out_path=target,
    )


def _authorise_history_rows(frame: pd.DataFrame, governor_ids: tuple[int, ...]) -> pd.DataFrame:
    if frame.empty:
        return frame.copy(deep=True)
    if "GovernorID" not in frame.columns:
        raise ValueError("Stats history is missing GovernorID.")
    numeric_ids = pd.to_numeric(frame["GovernorID"], errors="coerce")
    if numeric_ids.isna().any():
        raise ValueError("Stats history contains invalid GovernorID values.")
    allowed = frozenset(int(value) for value in governor_ids)
    returned = frozenset(int(value) for value in numeric_ids.tolist())
    if not returned.issubset(allowed):
        raise ValueError("Stats history returned an unauthorised GovernorID.")
    authorised = frame.copy(deep=True)
    authorised["GovernorID"] = numeric_ids.astype("int64")
    return authorised


def _build_metadata(
    context: AuthorisedAccountDataContext,
    *,
    output_kind: AccountDataOutputKind,
    days: int | None,
    window: HistoryWindowResult | None,
) -> AccountDataExportMetadata:
    inventory_dates = tuple(
        row.inventory_as_of for row in context.portfolio.rows if row.inventory_as_of is not None
    )
    includes_snapshot = output_kind in {
        AccountDataOutputKind.FULL_WORKBOOK,
        AccountDataOutputKind.CURRENT_SNAPSHOT,
    }
    includes_history = output_kind in {
        AccountDataOutputKind.FULL_WORKBOOK,
        AccountDataOutputKind.RAW_HISTORY,
    }
    return AccountDataExportMetadata(
        output_kind=output_kind,
        generated_at_utc=context.generated_at_utc,
        authorised_governor_count=len(context.governor_ids),
        snapshot_row_count=len(context.portfolio.rows) if includes_snapshot else None,
        history_row_count=window.row_count if includes_history and window is not None else None,
        requested_days=days if includes_history else None,
        window_start=window.window_start if window is not None else None,
        window_end=window.window_end if window is not None else None,
        written_start=window.written_start if window is not None else None,
        written_end=window.written_end if window is not None else None,
        stats_freshness=window.window_end if window is not None else None,
        governor_scan_freshness=(context.portfolio.latest_scan_date if includes_snapshot else None),
        inventory_oldest=min(inventory_dates) if includes_snapshot and inventory_dates else None,
        inventory_latest=max(inventory_dates) if includes_snapshot and inventory_dates else None,
        inventory_reporting_count=(len(inventory_dates) if includes_snapshot else None),
        inventory_expected_count=(len(context.portfolio.rows) if includes_snapshot else None),
    )


def _export_target(
    context: AuthorisedAccountDataContext,
    *,
    output_kind: AccountDataOutputKind,
    temp_dir: Path,
) -> tuple[str, Path]:
    timestamp = context.generated_at_utc.strftime("%Y%m%d_%H%M%S")
    if output_kind is AccountDataOutputKind.CURRENT_SNAPSHOT:
        filename = f"me_account_summary_{context.discord_user_id}_{timestamp}.csv"
    else:
        extension = ".xlsx" if output_kind is AccountDataOutputKind.FULL_WORKBOOK else ".csv"
        filename = f"stats_{safe_filename_part(context.display_name)}_{timestamp}{extension}"
    return filename, ensure_child_path(temp_dir, temp_dir / filename)


def _cleanup_placeholder(
    temp_dir: Path, metadata: AccountDataExportMetadata
) -> AccountDataExportFile:
    return AccountDataExportFile(
        file_path=temp_dir / "partial-export",
        temp_dir=temp_dir,
        filename="partial-export",
        metadata=metadata,
    )
