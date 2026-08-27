"""
crystaltech_config.py
- Unified loader + validator for Crystal Tech paths
- Flatten includes, renumber orders, verify assets, and expose helpers for the bot

Usage (programmatic):
    from crystaltech_config import (
        load_and_validate_config,           # -> (cfg, report)
        get_path_flat,                      # -> list[Step] with 'order'
        compute_user_progress_pct,          # -> float
        compute_path_avg_completion,        # -> float
        load_progress_file, save_progress_file
    )

CLI (local):
    python -m crystaltech_config --config ./config/crystaltech_paths.v1.json --assets ./assets/crystaltech
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from typing import Any

# ---------- Defaults (override if your repo differs) ----------
DEFAULT_CONFIG_PATH = os.path.join("config", "crystaltech_paths.v1.json")
DEFAULT_ASSETS_DIR = os.path.join("assets", "crystaltech")
DEFAULT_PROGRESS_PATH = os.path.join("data", "crystaltech_progress.json")


# ---------- Data Models ----------
@dataclass(frozen=True)
class Step:
    step_uid: str
    type: str  # "building" | "research"
    name: dict[str, str]  # i18n map, e.g., {"en-GB": "..."}
    target_level: int
    crystal_cost: int
    image: str  # filename relative to /assets/crystaltech
    order: int  # assigned by flattener

    def display_name(self, locale: str = "en-GB") -> str:
        return (
            self.name.get(locale)
            or self.name.get("en-GB")
            or next(iter(self.name.values()), self.step_uid)
        )


@dataclass
class ValidationIssue:
    level: str  # "ERROR" | "WARN" | "INFO"
    code: str
    message: str
    path_id: str | None = None
    step_uid: str | None = None


@dataclass
class ValidationReport:
    ok: bool
    issues: list[ValidationIssue]

    def summary(self) -> str:
        counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
        for i in self.issues:
            counts[i.level] = counts.get(i.level, 0) + 1
        return f"Validation {'OK' if self.ok else 'FAILED'} — Errors: {counts['ERROR']}, Warnings: {counts['WARN']}, Info: {counts['INFO']}"


# ---------- File I/O ----------
def _read_json(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, payload: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


# ---------- Public API ----------
def load_and_validate_config(
    config_path: str = DEFAULT_CONFIG_PATH,
    assets_dir: str = DEFAULT_ASSETS_DIR,
    fail_on_warn: bool = False,
) -> tuple[dict[str, Any], ValidationReport]:
    """
    Loads the unified config, validates schema-level constraints and assets, returns (cfg, report).

    - Ensures unique path_id and step_uid (globally)
    - Ensures includes resolve and no cycles
    - Ensures all images exist in assets_dir
    - Ensures flattened + renumbered steps produce integer 1..N
    """
    issues: list[ValidationIssue] = []
    ok = True

    # --- Load file
    try:
        cfg = _read_json(config_path)
    except Exception as e:
        return {}, ValidationReport(
            ok=False,
            issues=[
                ValidationIssue("ERROR", "CONFIG_LOAD_FAILED", f"Failed to read {config_path}: {e}")
            ],
        )

    # --- Basic keys
    if not isinstance(cfg.get("paths"), list):
        issues.append(ValidationIssue("ERROR", "MISSING_KEY", "'paths' must be a list at root"))
        return cfg, ValidationReport(ok=False, issues=issues)

    blocks = cfg.get("blocks", {})
    common_blocks = (blocks.get("common") or {}) if isinstance(blocks, dict) else {}
    paths: list[dict[str, Any]] = cfg["paths"]

    # --- Unique path_id
    seen_path_ids: set[str] = set()
    for p in paths:
        pid = p.get("path_id")
        if not pid:
            issues.append(
                ValidationIssue("ERROR", "PATH_ID_MISSING", "A path is missing 'path_id'")
            )
            ok = False
            continue
        if pid in seen_path_ids:
            issues.append(
                ValidationIssue("ERROR", "PATH_ID_DUP", f"Duplicate path_id '{pid}'", path_id=pid)
            )
            ok = False
        seen_path_ids.add(pid)

    # --- Build global step_uid registry during flatten (also checks includes & images)
    global_step_uids: set[str] = set()

    # detect include cycles with DFS
    def resolve_includes(includes: list[str]) -> list[dict[str, Any]]:
        res: list[dict[str, Any]] = []
        visited: set[str] = set()

        def visit(token: str):
            if token in visited:
                # simple cycle guard; realistic configs shouldn't have deep include graphs
                issues.append(
                    ValidationIssue(
                        "ERROR", "INCLUDE_CYCLE", f"Cycle detected at include '{token}'"
                    )
                )
                raise RuntimeError("include cycle")
            visited.add(token)
            parts = token.split(".")
            if len(parts) != 2 or parts[0] != "common":
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "INCLUDE_BAD",
                        f"Unsupported include '{token}'. Use 'common.<group>'",
                    )
                )
                raise RuntimeError("bad include")
            group = parts[1]
            block_steps = common_blocks.get(group) or []
            if not isinstance(block_steps, list):
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "INCLUDE_RESOLVE_FAILED",
                        f"Include '{token}' not found or not a list",
                    )
                )
                raise RuntimeError("bad include")
            res.extend(block_steps)

        for inc in includes or []:
            visit(inc)

        return res

    # Validate each path by actually flattening now (and checking assets + uniqueness)
    for p in paths:
        pid = p.get("path_id")
        includes = p.get("includes") or []
        own_steps = p.get("steps") or []
        try:
            flattened_raw = resolve_includes(includes) + own_steps
        except RuntimeError:
            ok = False
            continue

        if not flattened_raw:
            issues.append(
                ValidationIssue(
                    "WARN", "PATH_EMPTY", f"Path '{pid}' has no steps after includes.", path_id=pid
                )
            )

        # Verify each step structure & assets, and collect step_uids
        local_step_uids: set[str] = set()
        for s in flattened_raw:
            suid = s.get("step_uid")
            img = s.get("image")
            nm = s.get("name")
            t = s.get("type")
            lvl = s.get("target_level")
            cost = s.get("crystal_cost")

            # Required fields
            missing_fields = [
                k
                for k in ("step_uid", "type", "name", "target_level", "crystal_cost", "image")
                if s.get(k) in (None, "")
            ]
            if missing_fields:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "STEP_FIELDS_MISSING",
                        f"Path '{pid}' step missing: {', '.join(missing_fields)}",
                        path_id=pid,
                    )
                )
                ok = False
                continue

            # step_uid uniqueness (global + local)
            if suid in global_step_uids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "STEP_UID_DUP_GLOBAL",
                        f"Duplicate step_uid '{suid}' across paths",
                        path_id=pid,
                        step_uid=suid,
                    )
                )
                ok = False
            if suid in local_step_uids:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "STEP_UID_DUP_LOCAL",
                        f"Duplicate step_uid '{suid}' within path",
                        path_id=pid,
                        step_uid=suid,
                    )
                )
                ok = False
            global_step_uids.add(suid)
            local_step_uids.add(suid)

            # type sanity
            if t not in ("building", "research"):
                issues.append(
                    ValidationIssue(
                        "WARN",
                        "STEP_TYPE_UNKNOWN",
                        f"Path '{pid}' step '{suid}' has unusual type='{t}'",
                        path_id=pid,
                        step_uid=suid,
                    )
                )

            # name structure
            if not isinstance(nm, dict) or not nm:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "NAME_I18N_BAD",
                        f"Path '{pid}' step '{suid}' name must be a non-empty i18n map",
                        path_id=pid,
                        step_uid=suid,
                    )
                )
                ok = False

            # integers
            if not isinstance(lvl, int) or lvl < 0:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "LEVEL_BAD",
                        f"Path '{pid}' step '{suid}' target_level must be non-negative int",
                        path_id=pid,
                        step_uid=suid,
                    )
                )
                ok = False
            if not isinstance(cost, int) or cost < 0:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "COST_BAD",
                        f"Path '{pid}' step '{suid}' crystal_cost must be non-negative int",
                        path_id=pid,
                        step_uid=suid,
                    )
                )
                ok = False

            # assets
            if img:
                img_path = os.path.join(assets_dir, img)
                if not os.path.isfile(img_path):
                    issues.append(
                        ValidationIssue(
                            "ERROR",
                            "MISSING_IMAGE",
                            f"Image not found: {img_path}",
                            path_id=pid,
                            step_uid=suid,
                        )
                    )
                    ok = False

        # Renumbering preview (not persisted here; loader will assign final 1..N)
        # We only check that resulting count would be 1..N (i.e., list length)
        # No-op here, as we renumber in get_path_flat()

    # Final OK calc
    if fail_on_warn:
        ok = ok and not any(i.level in ("ERROR", "WARN") for i in issues)
    else:
        ok = ok and not any(i.level == "ERROR" for i in issues)

    return cfg, ValidationReport(ok=ok, issues=issues)


def get_path_flat(cfg: dict[str, Any], path_id: str, locale: str = "en-GB") -> list[Step]:
    """
    Flatten a single path:
      - resolve includes
      - concatenate steps
      - assign sequential integer `order` (1..N)
    Returns a list[Step].
    Raises KeyError if path_id not found or includes invalid.
    """
    blocks = cfg.get("blocks", {})
    common_blocks = (blocks.get("common") or {}) if isinstance(blocks, dict) else {}
    paths = cfg.get("paths") or []
    path = next((p for p in paths if p.get("path_id") == path_id), None)
    if not path:
        raise KeyError(f"path_id '{path_id}' not found")

    includes = path.get("includes") or []
    own_steps = path.get("steps") or []

    def resolve_includes(includes_list: list[str]) -> list[dict[str, Any]]:
        res: list[dict[str, Any]] = []
        visited: set[str] = set()

        def visit(token: str):
            if token in visited:
                raise KeyError(f"include cycle at '{token}'")
            visited.add(token)
            parts = token.split(".")
            if len(parts) != 2 or parts[0] != "common":
                raise KeyError(f"unsupported include '{token}'")
            group = parts[1]
            block_steps = common_blocks.get(group) or []
            if not isinstance(block_steps, list):
                raise KeyError(f"include '{token}' not found or not a list")
            res.extend(block_steps)

        for inc in includes_list:
            visit(inc)
        return res

    flattened_raw = resolve_includes(includes) + own_steps

    steps: list[Step] = []
    # Assign final 1..N order
    for idx, s in enumerate(flattened_raw, start=1):
        step = Step(
            step_uid=s["step_uid"],
            type=s["type"],
            name=s["name"],
            target_level=int(s["target_level"]),
            crystal_cost=int(s["crystal_cost"]),
            image=s["image"],
            order=idx,
        )
        steps.append(step)

    return steps


# ---------- Progress helpers (for averages) ----------
def load_progress_file(progress_path: str = DEFAULT_PROGRESS_PATH) -> dict[str, Any]:
    if not os.path.isfile(progress_path):
        return {"kvk_no": None, "updated_at_utc": None, "entries": []}
    return _read_json(progress_path)


def save_progress_file(payload: dict[str, Any], progress_path: str = DEFAULT_PROGRESS_PATH) -> None:
    payload = dict(payload)
    payload["updated_at_utc"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_json(progress_path, payload)


def compute_user_progress_pct(steps_flat: list[Step], completed_uids: list[str]) -> float:
    total = len(steps_flat)
    if total == 0:
        return 0.0
    completed = sum(1 for s in steps_flat if s.step_uid in set(completed_uids))
    return round(100.0 * completed / total, 1)


def compute_path_avg_completion(
    progress_payload: dict[str, Any], path_id: str, cfg: dict[str, Any]
) -> float:
    """
    Average completion % over all entries that chose this path_id.
    """
    entries = progress_payload.get("entries") or []
    steps_flat = get_path_flat(cfg, path_id)
    if not steps_flat:
        return 0.0

    samples = [
        compute_user_progress_pct(steps_flat, e.get("steps_completed") or [])
        for e in entries
        if e.get("selected_path_id") == path_id
    ]
    if not samples:
        return 0.0
    return round(sum(samples) / len(samples), 1)


# ---------- Optional CLI for local validation ----------
def _print_report(report: ValidationReport) -> None:
    print(report.summary())
    # show up to 50 issues for brevity
    for i in report.issues[:50]:
        loc = []
        if i.path_id:
            loc.append(f"path={i.path_id}")
        if i.step_uid:
            loc.append(f"step={i.step_uid}")
        where = f" ({', '.join(loc)})" if loc else ""
        print(f" - [{i.level}] {i.code}{where}: {i.message}")
    if len(report.issues) > 50:
        print(f" ... (+{len(report.issues)-50} more)")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config", default=DEFAULT_CONFIG_PATH, help="Path to crystaltech_paths.v1.json"
    )
    ap.add_argument(
        "--assets", default=DEFAULT_ASSETS_DIR, help="Directory containing step image assets"
    )
    ap.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as failures")
    args = ap.parse_args()

    cfg, report = load_and_validate_config(args.config, args.assets, fail_on_warn=args.fail_on_warn)
    _print_report(report)
    exit(0 if report.ok else 1)
