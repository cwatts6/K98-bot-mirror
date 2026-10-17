"""Prepare a conservative S11 source scope offline; never read installed SQL.

All reviewed modules/types, KVK objects, fixed coordination objects and direct
grant targets are roots. Retain every canonical object named in those sources,
including comments and dynamic SQL strings, recursively. This is deliberately
an over-approximation, not a SQL parser or permission/shape approval. Runtime
contracts still require independently reviewed metadata and dynamic outputs.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from services.export_execution_dal import INSTALLATION_OBJECTS


def prepare(sql_root, revision, sources, grants):
    by_name = {s["name"]: s for s in sources}
    roots = (
        {s["name"] for s in sources if s["type"] != "U" or s["name"].startswith("KVK.")}
        | set(INSTALLATION_OBJECTS)
        | {g["object"] for g in grants["grants"] if not g["object"].startswith("sys.")}
    )
    if not roots <= by_name.keys():
        raise ValueError("Required S11 roots are absent from reviewed source")
    patterns = {}
    for name in by_name:
        schema, object_name = name.split(".", 1)
        patterns[name] = re.compile(
            r"(?<![\w])(?:\[?"
            + re.escape(schema)
            + r"\]?\s*\.\s*)?\[?"
            + re.escape(object_name)
            + r"\]?(?![\w])",
            re.IGNORECASE,
        )
    pending = sorted(roots)
    edges = {}
    while pending:
        name = pending.pop(0)
        if name in edges:
            continue
        source = by_name[name]
        raw = subprocess.check_output(
            ["git", "-C", str(sql_root), "show", revision + ":" + source["path"]],
            timeout=15,
        )
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError("Source pin mismatch: " + source["path"])
        text = raw.decode("utf-8-sig")
        references = sorted(
            n for n, pattern in patterns.items() if n != name and pattern.search(text)
        )
        edges[name] = references
        pending.extend(n for n in references if n not in edges)
    return dict(
        version=1,
        sql_revision=revision,
        roots=sorted(roots),
        objects=sorted(edges),
        references={n: edges[n] for n in sorted(edges)},
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    scope = prepare(
        args.sql_root,
        args.revision,
        json.loads((root / "deploy/export_application_schema_source.json").read_bytes()),
        json.loads((root / "deploy/s11_application_grants.json").read_bytes()),
    )
    args.out.write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
