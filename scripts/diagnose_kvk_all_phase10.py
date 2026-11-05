"""Read-only Phase 10 diagnostics for KVK_ALL Full Data v2 window correctness."""

from __future__ import annotations

import argparse
from itertools import pairwise
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kvk.services.kvk_all_import_service import prepare_kvk_all_import

DEFAULT_SAMPLE_DIR = Path("downloads/kvk_all_sample_file")
DEFAULT_PATTERN = "1086045_05_*.xlsx"

METRICS: tuple[tuple[str, str, str], ...] = (
    ("kp_gain", "max_kill_points", "kill_points_diff"),
    ("t4_kills", "max_kills_iv", "kills_iv_diff"),
    ("t5_kills", "max_kills_v", "kills_v_diff"),
    ("deads", "max_dead", "dead_diff"),
    ("healed_troops", "max_units_healed", "healed_troops"),
    ("max_contribute_gain", "max_max_contribute", "max_contribute_diff"),
    ("cur_contribute_gain", "max_cur_contribute", "cur_contribute_diff"),
)


def _int_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([0] * len(df), index=df.index, dtype="Int64")
    return pd.to_numeric(df[column], errors="coerce").fillna(0).astype("Int64")


def _single_row_int(df: pd.DataFrame, column: str) -> int:
    value = _int_series(df, column).iloc[0]
    if pd.isna(value):
        return 0
    return int(value)


def _single_row_str(df: pd.DataFrame, column: str) -> str:
    if column not in df.columns:
        return ""
    value = df[column].iloc[0]
    if pd.isna(value):
        return ""
    return str(value)


def _window_delta(end_df: pd.DataFrame, start_df: pd.DataFrame, column: str) -> int:
    return _single_row_int(end_df, column) - _single_row_int(start_df, column)


def _load_prepared_samples(paths: list[Path]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for scan_id, path in enumerate(paths, start=1):
        prepared = prepare_kvk_all_import(path.read_bytes(), source_filename=path.name)
        df = prepared.dataframe.copy()
        df["ScanID"] = scan_id
        df["source_file"] = path.name
        frames.append(df)
    if not frames:
        raise ValueError("No workbook samples were provided")
    return pd.concat(frames, ignore_index=True)


def _pair_summary(all_scans: pd.DataFrame, start_scan: int, end_scan: int) -> dict[str, Any]:
    start = all_scans[all_scans["ScanID"] == start_scan].set_index("governor_id")
    end = all_scans[all_scans["ScanID"] == end_scan].set_index("governor_id")
    common = start.index.intersection(end.index)

    metrics: dict[str, Any] = {}
    for name, endpoint_col, diff_col in METRICS:
        endpoint_delta = _int_series(end.loc[common], endpoint_col) - _int_series(
            start.loc[common], endpoint_col
        )
        diff_delta = _int_series(end.loc[common], diff_col) - _int_series(
            start.loc[common], diff_col
        )
        metrics[name] = {
            "endpoint_delta_sum": int(endpoint_delta.sum()),
            "diff_delta_sum": int(diff_delta.sum()),
            "masked_nonzero_endpoint_zero_diff_rows": int(
                ((endpoint_delta != 0) & (diff_delta == 0)).sum()
            ),
            "endpoint_diff_mismatch_rows": int((endpoint_delta != diff_delta).sum()),
        }

    return {
        "start_scan": start_scan,
        "end_scan": end_scan,
        "common_governors": int(len(common)),
        "start_only_governors": int(len(start.index.difference(end.index))),
        "end_only_governors": int(len(end.index.difference(start.index))),
        "metrics": metrics,
    }


def _governor_window(
    all_scans: pd.DataFrame,
    governor_id: int,
    start_scan: int,
    end_scan: int,
) -> dict[str, Any]:
    rows = all_scans[all_scans["governor_id"] == governor_id].set_index("ScanID")
    if start_scan not in rows.index or end_scan not in rows.index:
        return {
            "governor_id": governor_id,
            "start_scan": start_scan,
            "end_scan": end_scan,
            "error": "Governor missing from start or end scan",
        }

    start = rows.loc[[start_scan]]
    end = rows.loc[[end_scan]]
    expected: dict[str, int] = {}
    legacy_diff_delta: dict[str, int] = {}
    for name, endpoint_col, diff_col in METRICS:
        expected[name] = _window_delta(end, start, endpoint_col)
        legacy_diff_delta[name] = _window_delta(end, start, diff_col)

    return {
        "governor_id": governor_id,
        "name": _single_row_str(end, "name"),
        "kingdom": _single_row_int(end, "kingdom"),
        "start_scan": start_scan,
        "end_scan": end_scan,
        "expected_endpoint_delta": expected,
        "legacy_diff_delta": legacy_diff_delta,
    }


def diagnose(
    paths: list[Path],
    *,
    known_governor_id: int,
    known_start_scan: int,
    known_end_scan: int,
) -> dict[str, Any]:
    all_scans = _load_prepared_samples(paths)
    scan_ids = sorted(int(value) for value in all_scans["ScanID"].unique())

    return {
        "workbooks": [
            {
                "scan_id": index,
                "path": str(path),
                "file_bytes": path.stat().st_size,
            }
            for index, path in enumerate(paths, start=1)
        ],
        "rows_by_scan": {
            str(scan_id): int((all_scans["ScanID"] == scan_id).sum()) for scan_id in scan_ids
        },
        "pair_summaries": [
            _pair_summary(all_scans, start_scan, end_scan)
            for start_scan, end_scan in pairwise(scan_ids)
        ],
        "full_span_summary": _pair_summary(all_scans, scan_ids[0], scan_ids[-1]),
        "known_governor": _governor_window(
            all_scans,
            known_governor_id,
            known_start_scan,
            known_end_scan,
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive expected KVK_ALL Full Data v2 endpoint deltas from consecutive workbook "
            "samples without mutating SQL or posting Google Sheets output."
        )
    )
    parser.add_argument(
        "--sample-dir",
        type=Path,
        default=DEFAULT_SAMPLE_DIR,
        help="Directory containing the consecutive KVK_ALL sample workbooks.",
    )
    parser.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Glob pattern used inside --sample-dir.",
    )
    parser.add_argument(
        "--known-governor-id",
        type=int,
        default=45227155,
        help="Governor ID to include as a representative regression case.",
    )
    parser.add_argument("--known-start-scan", type=int, default=2)
    parser.add_argument("--known-end-scan", type=int, default=3)
    args = parser.parse_args()

    paths = sorted(args.sample_dir.glob(args.pattern))
    if not paths:
        raise SystemExit(f"No workbooks matched {args.sample_dir / args.pattern}")

    print(
        json.dumps(
            diagnose(
                paths,
                known_governor_id=args.known_governor_id,
                known_start_scan=args.known_start_scan,
                known_end_scan=args.known_end_scan,
            ),
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
