"""Derive a narrow observer source plan offline; never approve installed metadata.

Unchanged D4 source records remain byte-for-byte equivalent as JSON values,
including historical sources that differ from today's SQL checkout. Only the
three reviewed mutation roots and three new procedures enter the amendment.
Sequence/trigger definitions are recorded separately from application objects.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from kvk.dal.new_source_import_dal import digest
from services.catalogue_observation_dal import MODULES, canonical_module
from services.export_d4_contract import (
    ACTIVATION_SCOPE_SHA256,
    APPLICATION_SOURCE_SHA256,
    LEGACY_SOURCE_SHA256,
)

BASE = "b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba"
AMENDED = frozenset(
    {"dbo.sp_ExcelOutput_ByKVK", "dbo.usp_RunMaintenance", "dbo.usp_S11ValidateStatsReportStage"}
)
ADDED = frozenset("dbo." + n for n in MODULES if n.startswith("usp_"))
LIFECYCLE = ("dbo.KVKFinalReportHeader", "dbo.MaintenanceKvkWork", "dbo.MaintenanceWork")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _definition(raw, kind):
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    start = re.search(r"(?im)^(?:CREATE\s+OR\s+ALTER|ALTER|CREATE)\s+" + kind + r"\s+", text)
    if start is None:
        raise ValueError("Complete module definition required")
    batches = re.split(r"(?im)^GO\s*$", text[start.start() :])
    if any(batch.strip() for batch in batches[1:]):
        raise ValueError("Unexpected additional module batch")
    return batches[0]  # Preserve the entire body and trailing whitespace.


def prepare(sql_root, output):
    sql_root, output = Path(sql_root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Source-plan output must be a new directory")
    documents = {}
    for name, expected in (
        ("application_sources", APPLICATION_SOURCE_SHA256),
        ("legacy_source", LEGACY_SOURCE_SHA256),
        ("activation_scope", ACTIVATION_SCOPE_SHA256),
    ):
        value = json.loads((ROOT / "deploy" / ("p02_d4_" + name + ".json")).read_bytes())
        if digest(value).hex() != expected:
            raise ValueError("Pinned D4 source predecessor differs: " + name)
        documents[name] = value
    before_application = documents["application_sources"]
    application, legacy, scope = (
        deepcopy(documents[key])
        for key in ("application_sources", "legacy_source", "activation_scope")
    )
    before_rows = {row["name"]: row for row in before_application}
    rows = {row["name"]: row for row in application}
    module_rows = {row["name"]: row for row in legacy["modules"]}
    sources, custody, bodies = {}, [], {}
    for name in sorted(AMENDED | ADDED):
        path = "sql_schema/" + name + ".StoredProcedure.sql"
        raw = (sql_root / path).read_bytes()
        normalized = raw.replace(b"\r\n", b"\n")
        if name in AMENDED:
            base = subprocess.check_output(
                [
                    "git",
                    "-c",
                    "safe.directory=" + str(sql_root),
                    "-C",
                    str(sql_root),
                    "show",
                    BASE + ":" + path,
                ],
                timeout=15,
            )
            if _sha(base) != before_rows[name]["sha256"] or module_rows[name][
                "source_sha256"
            ] != _sha(base):
                raise ValueError(
                    "Amended root does not match the independently pinned predecessor: " + name
                )
            if normalized == base:
                raise ValueError("Expected mutation-root amendment absent: " + name)
        elif name in rows or name in module_rows:
            raise ValueError("New procedure overlaps predecessor")
        body = _definition(normalized, "PROCEDURE")
        bodies[name] = body
        sources[name] = normalized.decode("utf-8-sig")
        rows[name] = dict(name=name, path=path, type="P", sha256=_sha(normalized))
        row = (
            deepcopy(module_rows[name])
            if name in AMENDED
            else dict(name=name, object_type="P", execute_as=None)
        )
        row.pop("compatible_definition_sha256", None)
        calls = set(row.get("calls", []))
        calls.update(
            n
            for n in ADDED
            if n != name and re.search(r"\bEXEC\s+" + re.escape(n) + r"\b", body, re.I)
        )
        calls.update(
            n
            for n in ("sys.sp_getapplock", "sys.sp_releaseapplock")
            if re.search(r"\bEXEC\s+@\w+\s*=\s*" + re.escape(n) + r"\b", body, re.I)
        )
        row.update(
            path=path,
            source_sha256=_sha(normalized),
            definition_format="module_header_lf_body_exact_v1",
            definition_sha256=_sha(canonical_module(body).encode("utf-16-le")),
            calls=sorted(calls),
        )
        module_rows[name] = row
        custody.append(
            dict(
                name=name,
                path=path,
                raw_sha256=_sha(raw),
                git_text_sha256=_sha(normalized),
                predecessor_sha256=before_rows.get(name, {}).get("sha256"),
            )
        )
    application = [rows[name] for name in sorted(rows)]
    legacy["modules"] = [module_rows[name] for name in sorted(module_rows)]
    legacy["roots"] = sorted(set(legacy["roots"]) | ADDED)
    for name in sorted(ADDED):
        legacy["grants"].append(
            dict(
                database="ROK_TRACKER",
                principal="ExportLegacyEntryReader",
                securable_class="OBJECT",
                target=name,
                permission="EXECUTE",
            )
        )
    for name in LIFECYCLE:
        legacy["grants"].append(
            dict(
                database="ROK_TRACKER",
                principal="ExportLegacyEntryReader",
                securable_class="OBJECT",
                target=name,
                permission="ALTER",
                state="D",
            )
        )
    legacy["status"] = "candidate_observer_source_not_installed_acceptance"
    patterns = {}
    for name in rows:
        schema, obj = name.split(".", 1)
        patterns[name] = re.compile(
            r"(?<!\w)(?:\[?"
            + re.escape(schema)
            + r"\]?\s*\.\s*)?\[?"
            + re.escape(obj)
            + r"\]?(?!\w)",
            re.I,
        )
    for name, source in sources.items():
        scope["references"][name] = sorted(
            set(scope["references"].get(name, []))
            | {n for n, pattern in patterns.items() if n != name and pattern.search(source)}
        )
    scope["roots"] = sorted(set(scope["roots"]) | ADDED)
    scope["objects"] = sorted(
        set(scope["objects"])
        | ADDED
        | {n for values in scope["references"].values() for n in values if n in rows}
    )
    external = {n for values in scope["references"].values() for n in values if n not in rows}
    predecessor_external = {
        n
        for values in documents["activation_scope"]["references"].values()
        for n in values
        if n not in before_rows
    }
    if external != predecessor_external:
        raise ValueError("Unreviewed external/dynamic reference appeared")
    if not set(scope["objects"]) <= rows.keys():
        raise ValueError("Source closure escaped the source inventory")
    scope["observer_predecessor_scope_sha256"] = ACTIVATION_SCOPE_SHA256
    scope["sql_revision"] = "candidate_sources_sha256:" + digest(application).hex()
    protocol = dict(
        version=1,
        policy="catalogue_generation_v1",
        bootstrap_value=1,
        source_line_endings="LF",
        modules=[],
        sequence={},
    )
    for name in sorted(MODULES):
        kind = (
            "StoredProcedure"
            if name.startswith("usp_")
            else ("DatabaseTrigger" if name == "tr_P02CatalogueObservation" else "Trigger")
        )
        prefix = "" if kind == "DatabaseTrigger" else "dbo."
        path = "sql_schema/" + prefix + name + "." + kind + ".sql"
        raw = (sql_root / path).read_bytes()
        protocol["modules"].append(
            dict(
                name=name,
                path=path,
                raw_source_sha256=_sha(raw),
                definition=_definition(
                    raw, "PROCEDURE" if kind == "StoredProcedure" else "TRIGGER"
                ),
            )
        )
    path = "sql_schema/dbo.P02ObservationGeneration.Sequence.sql"
    raw = (sql_root / path).read_bytes()
    protocol["sequence"] = dict(
        path=path, raw_source_sha256=_sha(raw), source=raw.decode("utf-8-sig").replace("\r\n", "\n")
    )
    assert all(rows[name] == row for name, row in before_rows.items() if name not in AMENDED)
    assert len(application) == len(before_application) + 3
    outputs = dict(
        application_sources=application,
        legacy_source=legacy,
        activation_scope=scope,
        protocol=protocol,
    )
    output.mkdir(parents=True)
    hashes = {}
    for name, value in outputs.items():
        filename = "p02_observer_" + name + ".json"
        raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
        (output / filename).write_bytes(raw)
        hashes[filename] = dict(file_sha256=_sha(raw), canonical_sha256=digest(value).hex())
    summary = dict(
        schema="p02-observer-source-plan/1",
        status="candidate_not_release_authority",
        sql_base=BASE,
        files=hashes,
        changed_sources=custody,
        application_sources=len(application),
        legacy_modules=len(legacy["modules"]),
        scope_objects=len(scope["objects"]),
        retained_dynamic_references=sorted(external),
        limits="No installed hashes, sequence incarnation, migration acceptance or runtime enablement is inferred. Unchanged historical source records remain intact.",
    )
    (output / "source-plan.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.sql_root, args.output), indent=2))
