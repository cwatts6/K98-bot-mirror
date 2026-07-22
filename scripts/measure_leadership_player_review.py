"""Bounded sequential Phase 8.1 leadership performance evidence harness."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict, replace
from datetime import UTC, datetime
import json
from pathlib import Path
import sys
import time

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from leadership_player_review import renderer, service

_CASE_LABELS = frozenset({"recent_dense", "long_tenure", "sparse", "high_history"})
_PAGES = ("overview", "activity", "kvk", "record")
_PRIVATE_OUTPUT_ROOT = (_REPO_ROOT / ".codex_artifacts" / "phase81_private").resolve()
_DEFAULT_OUTPUT = _PRIVATE_OUTPUT_ROOT / "phase81-app-timing.json"


def _case(value: str) -> tuple[str, int]:
    try:
        label, raw_governor_id = value.split("=", 1)
        governor_id = int(raw_governor_id)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("case must be label=GovernorID") from exc
    if label not in _CASE_LABELS:
        raise argparse.ArgumentTypeError(
            "case label must be one of: high_history, long_tenure, recent_dense, sparse"
        )
    if not 0 < governor_id <= 9_223_372_036_854_775_807:
        raise argparse.ArgumentTypeError("Governor ID must be a positive 64-bit integer")
    return label, governor_id


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Measure sequential cold-application-cache and warm leadership reads. "
            "This does not clear SQL Server caches and is not a load test."
        )
    )
    parser.add_argument(
        "--case",
        action="append",
        type=_case,
        required=True,
        help=(
            "Representative case as fixed_anonymous_label=GovernorID; provide each of "
            "recent_dense, long_tenure, sparse and high_history exactly once."
        ),
    )
    parser.add_argument(
        "--confirm-read-only",
        action="store_true",
        help="Required acknowledgement that the approved SQL measurement window is active.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_DEFAULT_OUTPUT,
        help=(
            "Private JSON output beneath .codex_artifacts/phase81_private only. "
            "The default is phase81-app-timing.json in that ignored directory."
        ),
    )
    return parser


def _resolve_output_path(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.suffix.lower() != ".json":
        raise SystemExit("--output must name a .json file")
    try:
        resolved.relative_to(_PRIVATE_OUTPUT_ROOT)
    except ValueError as exc:
        raise SystemExit(
            "--output must stay beneath .codex_artifacts/phase81_private"
        ) from exc
    return resolved


def _diagnostics(payload) -> dict[str, object] | None:
    return asdict(payload.diagnostics) if payload.diagnostics is not None else None


async def _measure_case(label: str, governor_id: int) -> dict[str, object]:
    periods: list[dict[str, object]] = []
    for period in service.SUPPORTED_PERIODS:
        cold_started = time.perf_counter()
        cold_payload = await service.load_payload(
            governor_id, period, page="overview", refresh=True
        )
        cold_elapsed_ms = (time.perf_counter() - cold_started) * 1000.0

        render_rows: list[dict[str, object]] = []
        for page in _PAGES:
            render_started = time.perf_counter()
            rendered = renderer.render_leadership_player(
                replace(cold_payload, page=page, record_page=0)
            )
            render_rows.append(
                {
                    "page": page,
                    "render_ms": round((time.perf_counter() - render_started) * 1000.0, 3),
                    "png_bytes": len(rendered.image_bytes),
                }
            )

        warm_started = time.perf_counter()
        warm_payload = await service.load_payload(
            governor_id, period, page="overview", refresh=False
        )
        warm_elapsed_ms = (time.perf_counter() - warm_started) * 1000.0
        periods.append(
            {
                "period_days": period,
                "cold_application_cache_elapsed_ms": round(cold_elapsed_ms, 3),
                "cold_diagnostics": _diagnostics(cold_payload),
                "warm_application_cache_elapsed_ms": round(warm_elapsed_ms, 3),
                "warm_diagnostics": _diagnostics(warm_payload),
                "renders": render_rows,
                "kvk_rows": len(cold_payload.kvk_rows),
                "alias_rows": len(cold_payload.aliases),
                "alliance_rows": len(cold_payload.alliance_episodes),
                "linked_rows": len(cold_payload.linked_governors),
            }
        )
    return {"case": label, "periods": periods}


async def _run(cases: list[tuple[str, int]]) -> dict[str, object]:
    results = []
    for label, governor_id in cases:
        results.append(await _measure_case(label, governor_id))
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "measurement_kind": "bounded_sequential_read_only",
        "artifact_classification": "restricted_leadership_performance_evidence",
        "shareable_without_sanitization": False,
        "sql_cache_cleared": False,
        "case_concurrency": 1,
        "sql_reads_per_load_max_concurrent": 3,
        "governor_ids_redacted": True,
        "notes": (
            "Raw labels and row cardinalities remain restricted even though Governor IDs are "
            "omitted. Authorization and Discord attachment timing must be joined from the "
            "bounded leadership_player_*_performance runtime logs for the same manual run."
        ),
        "cases": results,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cases = list(args.case)
    if not args.confirm_read_only:
        raise SystemExit("--confirm-read-only is required")
    if len(cases) != len(_CASE_LABELS):
        raise SystemExit("provide all four representative cases exactly once")
    labels = [label for label, _governor_id in cases]
    governor_ids = [governor_id for _label, governor_id in cases]
    if set(labels) != _CASE_LABELS or len(set(governor_ids)) != len(governor_ids):
        raise SystemExit("case labels must be complete and Governor IDs must be distinct")

    artifact = asyncio.run(_run(cases))
    rendered = json.dumps(artifact, indent=2, sort_keys=True)
    output = _resolve_output_path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
