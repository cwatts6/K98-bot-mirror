#!/usr/bin/env python3
"""Retry one already-published Phase 5.2 fallback stats import."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import stats_module


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-filename", required=True)
    parser.add_argument("--rank", required=True, type=float)
    parser.add_argument("--seed", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    return parser


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

    ready_path = Path(stats_module.READY_DIR) / completed_filename
    if not ready_path.is_file():
        print(f"RECOVERY REFUSED: Ready file is missing: {ready_path}", file=sys.stderr)
        return 2

    print(f"Retrying immutable Ready file: {completed_filename}")
    success, message, _extra = await stats_module.run_sql_procedure(
        rank=args.rank,
        seed=args.seed,
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

    print("PHASE52_STATS_IMPORT_RECOVERY_COMPLETE")
    return 0


def main() -> int:
    return asyncio.run(_run(_build_parser().parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
