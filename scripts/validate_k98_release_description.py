"""Check committed combined-release metadata; no SQL or installed-state access."""

import argparse
from pathlib import Path
import sys

if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.prepare_k98_update import validate_combined_description


def validate(path):
    path = Path(path)
    if not path.exists():
        return "No combined release descriptor: source-only target."
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
        raise ValueError("Bounded ordinary release descriptor required.")
    value = validate_combined_description(path.read_bytes())
    return f"Combined release metadata valid: {len(value['migrations'])} explicit SQL profile(s)."


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descriptor", default="deploy/k98-release.json")
    args = parser.parse_args(argv)
    try:
        print(validate(args.descriptor))
    except (ValueError, TypeError, OSError) as exc:
        print(f"Invalid combined release descriptor: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
