#!/usr/bin/env python3
"""
CLI entrypoint for offload monitor.

This script provides a simple one-shot mode and a loop mode. The in-process loop
is compatible with being run standalone (it will use asyncio) or you can schedule
the monitor_loop_coro inside the bot process via TaskMonitor.

Examples:
  # one-shot check & rotate (suitable for cron)
  python scripts/offload_monitor.py --once --rotate-days 30 --max-entries 2000

  # run as a looping process (simple daemon)
  python scripts/offload_monitor.py --interval 300
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from offload_monitor_lib import monitor_loop_coro, monitor_once_coro


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="Run one iteration and exit")
    p.add_argument("--interval", type=int, default=300, help="Loop interval seconds")
    p.add_argument("--rotate-days", type=int, default=30)
    p.add_argument("--max-entries", type=int, default=2000)
    p.add_argument("--alert-stale-threshold", type=int, default=5)
    args = p.parse_args(argv)

    if args.once:
        try:
            res = asyncio.run(
                monitor_once_coro(rotate_days=args.rotate_days, max_entries=args.max_entries)
            )
            print("Monitor result:", res)
            return 0
        except Exception as e:
            print("Monitor failed:", e, file=sys.stderr)
            return 2

    # Long-running loop
    try:
        asyncio.run(
            monitor_loop_coro(
                interval_seconds=args.interval,
                rotate_days=args.rotate_days,
                max_entries=args.max_entries,
                alert_stale_threshold=args.alert_stale_threshold,
            )
        )
    except KeyboardInterrupt:
        print("Interrupted")
        return 0
    except Exception as e:
        print("Monitor loop failed:", e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
