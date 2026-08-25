#!/usr/bin/env python3
"""Retry one already-published Phase 5.2 fallback stats import."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from constants import DATABASE, SERVER
from file_utils import run_maintenance_with_isolation, run_post_import_stats_update
from player_stats_cache import build_lastkvk_player_stats_cache, build_player_stats_cache
import stats_module

POST_MAINT_TIMEOUT = int(os.getenv("POST_MAINT_TIMEOUT", "300"))
BUILD_CACHE_TIMEOUT = float(os.getenv("BUILD_CACHE_TIMEOUT", "60.0"))
MAINT_WORKER_MODE = os.getenv("MAINT_WORKER_MODE", "thread").lower()
POST_STATS_WORKER_SPEC = (
    "scripts.retry_phase52_stats_import:_run_post_stats_without_argv_credentials"
)


def _run_post_stats_without_argv_credentials() -> None:
    """Run post-stats using the existing protected connection configuration."""
    run_post_import_stats_update(SERVER, DATABASE, "", "")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-filename", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser


def _load_bound_parameters(metadata: dict) -> tuple[float, str]:
    raw_rank = metadata.get("rank")
    raw_seed = metadata.get("seed")
    if isinstance(raw_rank, bool) or raw_rank is None:
        raise ValueError("the durable manifest has no original rank")
    try:
        rank = float(raw_rank)
    except (TypeError, ValueError) as exc:
        raise ValueError("the durable manifest rank is invalid") from exc
    seed = str(raw_seed).strip() if raw_seed is not None else ""
    if not seed:
        raise ValueError("the durable manifest has no original seed")
    return rank, seed


async def _run_required_post_sql_stages(completed_filename: str) -> tuple[bool, str]:
    async def _build_cache(builder) -> None:
        cache_build = builder()
        if BUILD_CACHE_TIMEOUT > 0:
            await asyncio.wait_for(cache_build, timeout=BUILD_CACHE_TIMEOUT)
        else:
            await cache_build

    try:
        await _build_cache(build_player_stats_cache)
        await _build_cache(build_lastkvk_player_stats_cache)
    except Exception as exc:
        return False, f"required cache rebuild failed: {exc}"

    ok, output = await run_maintenance_with_isolation(
        POST_STATS_WORKER_SPEC,
        timeout=POST_MAINT_TIMEOUT,
        name="run_post_import_stats_update",
        meta={"completed_filename": completed_filename, "recovery": True},
        prefer_process=(MAINT_WORKER_MODE == "process"),
    )
    if not ok:
        return False, f"required post_stats maintenance failed: {output}"
    return True, str(output or "post_stats completed")


async def _run(args: argparse.Namespace) -> int:
    metadata = stats_module._load_import_metadata()
    try:
        completed_filename = stats_module._resolve_completed_filename(metadata)
    except Exception as exc:
        print(f"RECOVERY REFUSED: {exc}", file=sys.stderr)
        return 2

    if completed_filename != args.completed_filename:
        print(
            "RECOVERY REFUSED: the durable manifest identifies "
            f"{completed_filename}, not {args.completed_filename}.",
            file=sys.stderr,
        )
        return 2

    try:
        rank, seed = _load_bound_parameters(metadata)
    except ValueError as exc:
        print(f"RECOVERY REFUSED: {exc}", file=sys.stderr)
        return 2

    ready_path = Path(stats_module.READY_DIR) / completed_filename
    if not ready_path.is_file():
        print(f"RECOVERY REFUSED: Ready file is missing: {ready_path}", file=sys.stderr)
        return 2

    print(f"Retrying immutable Ready file: {completed_filename}")
    success, message, _extra = await stats_module.run_sql_procedure(
        rank=rank,
        seed=seed,
        completed_filename=completed_filename,
        timeout_seconds=args.timeout_seconds,
        import_metadata=metadata,
    )
    print(message)
    if not success:
        print(
            "RECOVERY FAILED - preserve the file and return the output to Codex.", file=sys.stderr
        )
        return 1

    post_success, post_message = await _run_required_post_sql_stages(completed_filename)
    print(post_message)
    if not post_success:
        print(
            "RECOVERY INCOMPLETE - SQL succeeded but required post-SQL stages failed.",
            file=sys.stderr,
        )
        return 1

    print("PHASE52_STATS_IMPORT_RECOVERY_COMPLETE")
    return 0


def main() -> int:
    return asyncio.run(_run(_build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
