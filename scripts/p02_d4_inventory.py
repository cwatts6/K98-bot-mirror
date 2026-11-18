"""Offline D4 source census. Never import application code or connect to SQL."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOTS = (
    "UPDATE_ALL",
    "UPDATE_ALL2",
    "UPDATE_RALLY_DATA",
    "TEST",
    "sp_Import_Rally_Daily",
    "sp_Import_Rally_AllTime",
    "IngestionLog",
    "CLAIM_KS4_IMPORT_FILE",
    "IMPORT_STAGING_PROC_CORE",
    "ARCHIVE_IMPORT_STAGING_FILE",
    "KS4_UNO_SEQ",
    "KingdomScanData4",
    "SUMMARY_PROC",
    "SP_Stats_for_Upload",
    "sp_TARGETS_MASTER",
    "CREATE_DELTA_TABLES",
    "sp_ExcelOutput_ByKVK",
    "usp_S11CompleteStatsReportsCore",
    "usp_S11ValidateStatsReportStage",
    "MaintenanceWork",
    "MaintenanceConfigurationWork",
    "MaintenanceKvkWork",
    "MaintenanceBackupWork",
    "usp_update_stats",
    "usp_RunMaintenance",
    "usp_MaintenanceDue",
    "usp_MaintenanceConfigurationDue",
    "usp_MaintenanceKvkDue",
    "usp_MaintenanceImport",
    "usp_MaintenanceConfiguration",
    "usp_MaintenancePlayerReport",
    "usp_MaintenanceKvkOutput",
    "usp_MaintenanceFinalStats",
    "usp_MaintenancePostImport",
    "usp_MaintenanceBackupClaim",
    "usp_MaintenanceBackupAcknowledge",
    "LogBackupTriggerQueue",
    "usp_GetPendingLogBackupTriggers",
    "usp_MarkLogBackupTriggerProcessed",
    "usp_CleanupLogBackupTriggerQueue",
    "usp_start_rok_tracker_log_backup",
)
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_FILES = 8192
MAX_TOTAL_BYTES = 128 * 1024 * 1024


def tracked_sources(root, suffix):
    """Git filenames are data; no shell, working-tree import or recursive walk."""
    root = Path(root).resolve(strict=True)
    raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"], timeout=30)
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("Source inventory exceeds byte bound")
    paths = [p for p in raw.decode("utf-8").split("\0") if p.endswith(suffix)]
    if len(paths) > MAX_FILES:
        raise ValueError("Source inventory exceeds file bound")
    result = {}
    total_bytes = 0
    for name in sorted(paths):
        path = root / name
        if not path.exists():
            raise ValueError("Tracked source is missing: " + name)
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(root) or path.is_symlink():
            raise ValueError("Source escapes its repository: " + name)
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("Source exceeds file bound: " + name)
        data = path.read_bytes()
        if len(data) > MAX_FILE_BYTES:
            raise ValueError("Source exceeds file bound: " + name)
        total_bytes += len(data)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Source inventory exceeds total byte bound")
        result[name] = data
    return result


def source_census(bot, sql):
    """Lexical references are candidates, not proof of execution or installed use."""
    definitions = {}
    for path in sql:
        match = re.fullmatch(r"sql_schema/([^/]+)\.([^.]+)\.[^.]+\.sql", path)
        if match:
            definitions.setdefault(match[2].casefold(), []).append(path)
    pattern = re.compile(r"(?<![\w])(" + "|".join(re.escape(s) for s in ROOTS) + r")(?![\w])", re.I)
    canonical = {s.casefold(): s for s in ROOTS}
    references = {s: [] for s in ROOTS}
    for repository, files in (("bot", bot), ("sql", sql)):
        for path, raw in sorted(files.items()):
            text = raw.decode("utf-8-sig")
            digest = hashlib.sha256(raw).hexdigest()
            lines = {}
            for number, line in enumerate(text.splitlines(), 1):
                for match in pattern.finditer(line):
                    lines.setdefault(canonical[match[1].casefold()], []).append(number)
            for name, numbers in lines.items():
                references[name].append(
                    {
                        "repository": repository,
                        "path": path,
                        "sha256": digest,
                        "lines": sorted(set(numbers)),
                        "classification": "lexical_candidate_requires_review",
                    }
                )
    return {
        "version": 1,
        "kind": "p02_d4_source_census",
        "installed_use": "unknown",
        "source_inventory": {
            name: {
                "files": len(files),
                "bytes": sum(len(raw) for raw in files.values()),
                "manifest_sha256": hashlib.sha256(
                    json.dumps(
                        {path: hashlib.sha256(raw).hexdigest() for path, raw in files.items()},
                        sort_keys=True,
                    ).encode("utf-8")
                ).hexdigest(),
            }
            for name, files in (("bot", bot), ("sql", sql))
        },
        "limitations": [
            "Comments, fixtures and dynamic strings can match; inspect each candidate.",
            "No reference does not prove no installed, dynamic or external consumer.",
            "Root census does not replace transitive installed dependency review.",
            "No source text, data rows, credentials or application imports are collected.",
        ],
        "objects": [
            {
                "name": name,
                "definitions": definitions.get(name.casefold(), []),
                "source_status": "present" if name.casefold() in definitions else "missing",
                "installed_use": "unknown",
                "disposition": "qualify_or_explicit_retirement",
                "references": references[name],
            }
            for name in ROOTS
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot-root", type=Path, required=True)
    parser.add_argument("--sql-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = source_census(
        tracked_sources(args.bot_root, ".py"), tracked_sources(args.sql_root, ".sql")
    )
    for name, root in (("bot", args.bot_root), ("sql", args.sql_root)):
        result[name + "_head"] = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], timeout=30, text=True
        ).strip()
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("D4 source census saved; installed use remains unknown.")


if __name__ == "__main__":
    main()
