"""Print a review-only MGE descriptor from committed SQL and explicit Bot predecessors.

No live inventory, package staging, drain or deployment. Commit the SQL profile
first; supply only predecessor identities established by approved observation.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess

from scripts.prepare_k98_update import (
    combined_payload,
    sha256,
    validate_combined_description,
)


def describe(sql_commit, predecessors, read_blob):
    migration = "20261029_001_mge_board_finalisation"
    raw = read_blob("migrations/" + migration + ".release.json")
    if not raw:
        raise ValueError("Committed, environment-bound MGE SQL profile required")
    result = dict(
        version=1,
        profile="mge_finalisation_v1",
        bot_predecessors=predecessors,
        sql_commit=sql_commit,
        migrations=[dict(id=migration, sha256=sha256(raw))],
    )
    validate_combined_description(json.dumps(result).encode())
    combined_payload(result, read_blob)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--sql-commit", required=True)
    parser.add_argument("--bot-predecessor", action="append", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.sql_commit):
        raise ValueError("Exact reviewed SQL commit required")
    root = Path(args.sql_root).resolve()

    def read(path):
        return subprocess.check_output(
            [
                "git",
                "--no-optional-locks",
                "-C",
                str(root),
                "show",
                args.sql_commit + ":" + path,
            ],
            timeout=30,
        )

    print(json.dumps(describe(args.sql_commit, args.bot_predecessor, read), indent=2))


if __name__ == "__main__":
    main()
