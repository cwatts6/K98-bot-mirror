"""Read-only Phase 9 benchmark for the KVK_ALL Full Data workbook path."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import statistics
import sys
import time
from typing import Any, TypeVar

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kvk.dal.kvk_all_import_dal import rows_for_stage
from kvk.services.kvk_all_import_service import (
    attach_source_metadata,
    coerce_full_data_frame,
    prepare_kvk_all_import,
    read_full_data_workbook,
)

T = TypeVar("T")

DEFAULT_SAMPLE = Path("downloads/kvk_all_sample_file/1086045_05_08_2026,_02_21_38_AM.xlsx")


def _time_call(
    fn: Callable[..., T],
    *args: Any,
    repeats: int,
    **kwargs: Any,
) -> tuple[T, list[float]]:
    values: list[float] = []
    result: T | None = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = fn(*args, **kwargs)
        values.append((time.perf_counter() - started) * 1000.0)
    if result is None:
        raise RuntimeError("benchmark function returned no result")
    return result, values


def _stats(values: list[float]) -> dict[str, Any]:
    return {
        "runs_ms": [round(value, 2) for value in values],
        "median_ms": round(statistics.median(values), 2),
        "min_ms": round(min(values), 2),
        "max_ms": round(max(values), 2),
    }


def benchmark_workbook(path: Path, *, repeats: int) -> dict[str, Any]:
    content = path.read_bytes()
    workbook = pd.ExcelFile(path)

    raw_tuple, read_ms = _time_call(
        read_full_data_workbook,
        content,
        path.name,
        repeats=repeats,
    )
    raw_df, sheet_name, schema_metadata = raw_tuple
    coerced, coerce_ms = _time_call(coerce_full_data_frame, raw_df, repeats=repeats)
    _, metadata_ms = _time_call(
        attach_source_metadata,
        coerced,
        sheet_name=sheet_name,
        schema_metadata=schema_metadata,
        repeats=repeats,
    )
    prepared, prepare_ms = _time_call(
        prepare_kvk_all_import,
        content,
        path.name,
        repeats=repeats,
    )
    _, rows_ms = _time_call(
        rows_for_stage,
        "00000000-0000-0000-0000-000000000000",
        prepared.dataframe,
        repeats=repeats,
    )

    return {
        "sample": str(path),
        "file_bytes": len(content),
        "sheets": workbook.sheet_names,
        "full_data_rows": int(raw_df.shape[0]),
        "full_data_columns": int(raw_df.shape[1]),
        "schema": schema_metadata,
        "prepared_columns": len(prepared.dataframe.columns),
        "timings": {
            "read_full_data_workbook": _stats(read_ms),
            "coerce_full_data_frame": _stats(coerce_ms),
            "attach_source_metadata": _stats(metadata_ms),
            "prepare_kvk_all_import_total": _stats(prepare_ms),
            "rows_for_stage": _stats(rows_ms),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark the read-only KVK_ALL Full Data workbook preparation path.",
    )
    parser.add_argument(
        "workbook",
        nargs="?",
        type=Path,
        default=DEFAULT_SAMPLE,
        help="Path to a KVK_ALL workbook sample.",
    )
    parser.add_argument("--repeats", type=int, default=5, help="Number of benchmark repeats.")
    args = parser.parse_args()

    if args.repeats < 1:
        raise SystemExit("--repeats must be at least 1")
    if not args.workbook.exists():
        raise SystemExit(f"Workbook not found: {args.workbook}")

    print(json.dumps(benchmark_workbook(args.workbook, repeats=args.repeats), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
