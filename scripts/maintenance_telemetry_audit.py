#!/usr/bin/env python3
"""
maintenance_telemetry_audit.py

Lightweight parser to aggregate maintenance_spec_* telemetry events.

Purpose:
- Count occurrences of maintenance_spec_allowed / maintenance_spec_denied / maintenance_spec_evaluated
- Show first_seen / last_seen timestamps and a sample payload for each spec
- Filter by --since timestamp (ISO8601) and limit output to top N specs

Usage:
    python scripts/maintenance_telemetry_audit.py --path logs/telemetry_log.jsonl --top 50
    python scripts/maintenance_telemetry_audit.py --since 2025-12-01T00:00:00Z

If the project exposes logging_setup.TELEMETRY_LOG_PATH, the script will use that by default.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import UTC, datetime
import gzip
import io
import json
import os
import sys
from typing import Any

# Try to pick up central telemetry path if available
try:
    from logging_setup import TELEMETRY_LOG_PATH  # type: ignore
except Exception:
    TELEMETRY_LOG_PATH = None  # type: ignore


def parse_iso(s: str) -> datetime | None:
    if not s:
        return None
    try:
        # Accept trailing Z
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        # best-effort parse common ISO formats
        fmts = ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S")
        for fmt in fmts:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.replace(tzinfo=UTC)
            except Exception:
                continue
    return None


def open_maybe_gz(path: str):
    # Support .gz compressed logs
    if path.endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8")
    return open(path, encoding="utf-8")


def summarize_telemetry(
    path: str, since: datetime | None, top: int, include_events: list[str] | None
):
    stats: dict[str, dict[str, Any]] = {}
    counts_total = defaultdict(int)
    lines_processed = 0
    lines_skipped = 0

    if not os.path.exists(path):
        raise FileNotFoundError(f"Telemetry path not found: {path}")

    with open_maybe_gz(path) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            lines_processed += 1
            try:
                payload = json.loads(raw)
            except Exception:
                lines_skipped += 1
                continue

            # payload may be nested depending on logging pipe; we expect a dict with event
            event = payload.get("event")
            if event not in include_events:
                # Some processes emit a wrapped payload under different layout; try nested check
                # e.g., telemetry lines previously included event directly; continue if not present
                lines_skipped += 1
                continue

            spec = payload.get("spec") or payload.get("command") or "<unknown>"
            ts = (
                payload.get("timestamp")
                or payload.get("time")
                or payload.get("ts")
                or payload.get("created_at")
            )
            # fallback: use current time for ordering if no timestamp present
            parsed_ts = parse_iso(str(ts)) if ts else None

            if since and parsed_ts and parsed_ts < since:
                continue
            # If parsed_ts is None but 'since' filter is set, conservatively skip (we don't know)
            if since and parsed_ts is None:
                continue

            entry = stats.setdefault(
                spec,
                {
                    "spec": spec,
                    "first_seen": None,
                    "last_seen": None,
                    "counts": defaultdict(int),
                    "sample": None,
                },
            )
            entry["counts"][event] += 1
            counts_total[event] += 1
            # update first/last seen using parsed_ts (fallback to line number time ordering)
            if parsed_ts:
                if entry["first_seen"] is None or parsed_ts < entry["first_seen"]:
                    entry["first_seen"] = parsed_ts
                if entry["last_seen"] is None or parsed_ts > entry["last_seen"]:
                    entry["last_seen"] = parsed_ts
            else:
                # use an incremental fallback timestamp if parsing unavailable
                now = datetime.now(UTC)
                if entry["first_seen"] is None:
                    entry["first_seen"] = now
                entry["last_seen"] = now

            if entry["sample"] is None:
                entry["sample"] = payload

    # Build sorted list by allowed count desc then total events
    def sort_key(e):
        counts = e["counts"]
        primary = counts.get("maintenance_spec_allowed", 0)
        secondary = sum(counts.values())
        return (-primary, -secondary)

    sorted_entries = sorted(stats.values(), key=sort_key)
    if top and top > 0:
        sorted_entries = sorted_entries[:top]

    return {
        "lines_processed": lines_processed,
        "lines_skipped": lines_skipped,
        "per_spec": sorted_entries,
        "totals": counts_total,
    }


def fmt_dt(dt: datetime | None) -> str:
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def print_summary(summary: dict):
    print("Telemetry summary")
    print("=================")
    print(f"Lines processed: {summary['lines_processed']}")
    print(f"Lines skipped (non-json/irrelevant): {summary['lines_skipped']}")
    print("Totals by event:")
    for k, v in summary["totals"].items():
        print(f"  {k}: {v}")
    print()
    print(f"Top specs (showing {len(summary['per_spec'])}):")
    print(f"{'count_allowed':>13} {'count_total':>12} {'first_seen':>25} {'last_seen':>25}  spec")
    print("-" * 100)
    for e in summary["per_spec"]:
        allowed = e["counts"].get("maintenance_spec_allowed", 0)
        total = sum(e["counts"].values())
        print(
            f"{allowed:13d} {total:12d} {fmt_dt(e['first_seen']):25s} {fmt_dt(e['last_seen']):25s}  {e['spec']}"
        )
        sample = e.get("sample")
        if sample:
            # show a short sample line
            s = json.dumps(sample, default=str)
            if len(s) > 200:
                s = s[:200] + "...(truncated)"
            print(f"    sample: {s}")
    print()


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(description="Aggregate maintenance_spec telemetry events")
    default_path = TELEMETRY_LOG_PATH or os.path.join("logs", "telemetry_log.jsonl")
    p.add_argument(
        "--path", "-p", default=default_path, help=f"Telemetry log path (default: {default_path})"
    )
    p.add_argument(
        "--since",
        "-s",
        default=None,
        help="ISO timestamp (e.g., 2025-12-01T00:00:00Z) to filter from",
    )
    p.add_argument("--top", "-n", type=int, default=50, help="Top N specs to show (default 50)")
    p.add_argument(
        "--events",
        "-e",
        default="maintenance_spec_allowed,maintenance_spec_denied,maintenance_spec_evaluated",
        help="Comma-separated events to include",
    )
    args = p.parse_args(argv)

    since = parse_iso(args.since) if args.since else None
    include_events = [x.strip() for x in args.events.split(",") if x.strip()]
    try:
        summary = summarize_telemetry(args.path, since, args.top, include_events)
    except Exception as exc:
        print(f"Error reading telemetry path: {exc}", file=sys.stderr)
        sys.exit(2)
    print_summary(summary)


if __name__ == "__main__":
    main()
