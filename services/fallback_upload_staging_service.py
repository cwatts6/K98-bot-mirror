"""Private staging ownership for fallback stats upload processing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

STAGING_DIRECTORY_NAME = ".fallback_upload_staging"


@dataclass(frozen=True, slots=True)
class FallbackStagedUpload:
    """One upload's private staging path and preserved public filename."""

    filename: str
    path: Path
    directory: Path


def create_fallback_staged_upload(
    download_folder: str | os.PathLike[str],
    raw_filename: str,
) -> FallbackStagedUpload:
    """Allocate a unique directory while preserving the sanitized basename."""
    filename = os.path.basename(str(raw_filename))
    if not filename or filename in {".", ".."}:
        raise ValueError("Fallback upload filename must contain a valid basename")

    staging_root = Path(download_folder) / STAGING_DIRECTORY_NAME
    directory = staging_root / uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    return FallbackStagedUpload(
        filename=filename,
        path=directory / filename,
        directory=directory,
    )


def cleanup_fallback_staged_upload(staged_upload: FallbackStagedUpload) -> None:
    """Best-effort cleanup without recursively deleting an unresolved path."""
    try:
        staged_upload.path.unlink(missing_ok=True)
    except OSError:
        logger.warning(
            "[FALLBACK_UPLOAD] Failed to remove staged file %s",
            staged_upload.path,
            exc_info=True,
        )

    try:
        staged_upload.directory.rmdir()
    except FileNotFoundError:
        return
    except OSError:
        logger.warning(
            "[FALLBACK_UPLOAD] Failed to remove staging directory %s",
            staged_upload.directory,
            exc_info=True,
        )


async def stage_and_process_fallback_attachment(
    attachment: Any,
    *,
    download_folder: str | os.PathLike[str],
    processing_lock: Any,
    download_attachment: Callable[..., Awaitable[bool]],
    process_attachment: Callable[[str, str], Awaitable[Any]],
    channel_name: str | None = None,
    user: object | None = None,
) -> bool:
    """Download privately, then retain exclusive ownership through processing.

    Network download remains concurrent across channel workers. Publication of
    canonical import files and all downstream processing remain serialized by
    ``processing_lock``.
    """
    staged_upload = create_fallback_staged_upload(
        download_folder,
        getattr(attachment, "filename", "unknown"),
    )
    try:
        downloaded = await download_attachment(
            attachment,
            str(staged_upload.path),
            channel_name=channel_name,
            user=user,
        )
        if not downloaded:
            return False

        async with processing_lock:
            await process_attachment(staged_upload.filename, str(staged_upload.path))
        return True
    finally:
        cleanup_fallback_staged_upload(staged_upload)
