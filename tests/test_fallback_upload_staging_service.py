from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.fallback_upload_staging_service import (
    stage_and_process_fallback_attachment,
)


@pytest.mark.asyncio
async def test_same_filename_downloads_keep_private_bytes_until_each_processing_turn(
    tmp_path: Path,
) -> None:
    processing_lock = asyncio.Lock()
    first_processing_started = asyncio.Event()
    second_downloaded = asyncio.Event()
    processed: list[tuple[str, bytes, Path]] = []

    first = SimpleNamespace(filename="stats.csv", payload=b"first-upload")
    second = SimpleNamespace(filename="stats.csv", payload=b"second-upload")

    async def download(attachment, save_path, **_kwargs):
        Path(save_path).write_bytes(attachment.payload)
        if attachment is second:
            second_downloaded.set()
        return True

    async def process(filename: str, staged_path: str) -> None:
        path = Path(staged_path)
        if path.read_bytes() == first.payload:
            first_processing_started.set()
            await asyncio.wait_for(second_downloaded.wait(), timeout=1)
        processed.append((filename, path.read_bytes(), path))

    first_task = asyncio.create_task(
        stage_and_process_fallback_attachment(
            first,
            download_folder=tmp_path,
            processing_lock=processing_lock,
            download_attachment=download,
            process_attachment=process,
            channel_name="first-channel",
            user="first-user",
        )
    )
    await asyncio.wait_for(first_processing_started.wait(), timeout=1)
    second_task = asyncio.create_task(
        stage_and_process_fallback_attachment(
            second,
            download_folder=tmp_path,
            processing_lock=processing_lock,
            download_attachment=download,
            process_attachment=process,
            channel_name="second-channel",
            user="second-user",
        )
    )

    assert await first_task is True
    assert await second_task is True
    assert [(name, data) for name, data, _path in processed] == [
        ("stats.csv", first.payload),
        ("stats.csv", second.payload),
    ]
    assert processed[0][2] != processed[1][2]
    assert all(path.name == "stats.csv" for _name, _data, path in processed)
    assert all(not path.exists() for _name, _data, path in processed)


@pytest.mark.asyncio
async def test_failed_download_is_cleaned_and_never_processed(tmp_path: Path) -> None:
    attempted_paths: list[Path] = []
    processed = False

    async def download(_attachment, save_path, **_kwargs):
        path = Path(save_path)
        attempted_paths.append(path)
        path.write_bytes(b"partial")
        return False

    async def process(_filename: str, _staged_path: str) -> None:
        nonlocal processed
        processed = True

    result = await stage_and_process_fallback_attachment(
        SimpleNamespace(filename="../stats.csv"),
        download_folder=tmp_path,
        processing_lock=asyncio.Lock(),
        download_attachment=download,
        process_attachment=process,
        channel_name="uploads",
        user="uploader",
    )

    assert result is False
    assert processed is False
    assert len(attempted_paths) == 1
    assert attempted_paths[0].name == "stats.csv"
    assert not attempted_paths[0].exists()
