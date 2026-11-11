"""Check committed combined-release metadata; no SQL or installed-state access."""

import argparse
from pathlib import Path
import re
import subprocess
import sys

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.prepare_k98_update import validate_combined_description


def validate(path, base_revision=None):
    path = Path(path)
    if base_revision:
        if not re.fullmatch(r"[a-f0-9]{40}", base_revision):
            raise ValueError("Exact PR base commit required.")
        if path.as_posix() != "deploy/k98-release.json":
            raise ValueError("PR transition check requires the repository descriptor path.")
        previous = subprocess.run(
            ["git", "ls-tree", "--name-only", base_revision, "--", path.as_posix()],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        if previous and not path.exists():
            raise ValueError("Removing a committed combined release descriptor is unsupported.")
    if not path.exists():
        return "No combined release descriptor: source-only target."
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise ValueError("Bounded ordinary release descriptor required.")
    value = validate_combined_description(path.read_bytes())
    return f"Combined release metadata valid: {len(value['migrations'])} explicit SQL profile(s)."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", default="deploy/k98-release.json")
    parser.add_argument("--base-revision", help="Exact PR base commit for transition validation")
    args = parser.parse_args(argv)
    try:
        print(validate(args.descriptor, args.base_revision))
    except (ValueError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Invalid combined release descriptor: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
