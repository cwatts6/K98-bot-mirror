"""Inspect/resolve local notification evidence. Never imports SQL or provider clients.

Run on the Bot host as its authorized local operator. All mutations require the
exact preview token and an audit reason; no uncertain notification can be replayed.
"""

import argparse
import getpass
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.processing_notification_store import notification_store


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--action", choices=["status", "preview", "retry", "dismiss", "close"], default="status"
    )
    parser.add_argument("--component")
    parser.add_argument("--confirmation")
    parser.add_argument("--reason")
    parser.add_argument("--channel-id", type=int)
    args = parser.parse_args(argv)
    store = notification_store()
    row = store.get(args.run_id)
    if args.action not in {"status", "preview"}:
        if not args.confirmation or not args.reason:
            parser.error("Mutation requires --confirmation from preview and --reason.")
        row = store.resolve(
            args.run_id,
            action=args.action,
            token=args.confirmation,
            reason=args.reason,
            actor="local:" + getpass.getuser(),
            component=args.component,
            channel_id=args.channel_id,
        )
    print(json.dumps(row, indent=2))
    print(
        "Next actions: failed = correct channel/permissions then preview+retry; "
        "sending/held = inspect Discord and logs, then preview+dismiss after manual resolution; "
        "close = acknowledge all remaining notification issues and stop this notification watch. "
        "These commands never rerun SQL or Google exports."
    )
    if args.action == "preview":
        print("Confirmation token: " + store.token(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
