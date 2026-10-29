#!/usr/bin/env python3
"""
CLI admin tooling to interact with the offload registry.

Usage:
  - List offloads:
      python scripts/offload_admin.py list
  - Cancel by offload id:
      python scripts/offload_admin.py cancel --id <offload_id> [--actor "admin:42"]
  - Cancel by pid:
      python scripts/offload_admin.py cancel --pid <pid> [--actor "admin:42"]

This script uses file_utils.* helpers and emits basic stdout output. It is intended
as an admin convenience for operators on the host.
"""

from __future__ import annotations

import argparse
import json
import sys

from file_utils import cancel_offload, list_offloads


def cmd_list():
    offs = list_offloads()
    if not offs:
        print("No offloads recorded.")
        return 0
    for o in sorted(offs, key=lambda x: x.get("start_time") or ""):
        print(json.dumps(o, indent=2, default=str))
        print("-" * 60)
    return 0


def cmd_cancel(offload_id=None, pid=None, actor=None):
    if not offload_id and not pid:
        print("Provide either --id or --pid to cancel.")
        return 2
    res = cancel_offload(offload_id=offload_id, pid=pid, actor=actor)
    print("Result:", json.dumps(res, indent=2, default=str))
    return 0 if res.get("ok") else 1


def main(argv=None):
    parser = argparse.ArgumentParser(prog="offload_admin")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List offloads")

    p_cancel = sub.add_parser("cancel", help="Cancel an offload by id or pid")
    p_cancel.add_argument("--id", dest="offload_id")
    p_cancel.add_argument("--pid", dest="pid", type=int)
    p_cancel.add_argument("--actor", dest="actor", default=None)

    args = parser.parse_args(argv)
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "cancel":
        return cmd_cancel(offload_id=args.offload_id, pid=args.pid, actor=args.actor)
    return 2


if __name__ == "__main__":
    sys.exit(main())
