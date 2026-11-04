"""Offline P01.3 cost experiment. No bot startup, SQL, provider or log-file reads.

Run from the repository root with the test environment installed. The baseline
functions come from the explicitly supplied Git revision; all delivery/probe/log
adapters are inert. Raw samples and failures are retained in the output JSON.
"""

import argparse
import ast
import asyncio
from datetime import UTC, datetime, timedelta
import gc
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import threading
import time
import tracemalloc
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["K98_TEST_MODE"] = "1"
os.environ["PYTEST_RUNNING"] = "1"
os.environ["PYTHON_DOTENV_DISABLED"] = "1"

from services import operator_status_service as status
from services.health_observation import Observation
from ui.views.health_view import build_health_embed


def summary(samples):
    values = sorted(samples)
    return dict(
        p50=statistics.median(values),
        p95=values[int((len(values) - 1) * 0.95)],
        p99=values[int((len(values) - 1) * 0.99)],
        maximum=values[-1],
    )


def compile_functions(source, names, namespace):
    tree = ast.parse(source)
    nodes = [n for n in tree.body if getattr(n, "name", None) in names]
    if len(nodes) != len(names):
        raise ValueError("Baseline/candidate function inventory changed")
    exec(
        compile(ast.Module(body=nodes, type_ignores=[]), "inert-health-adapters", "exec"), namespace
    )
    return namespace


def sources(now):
    records = {}
    for state in ("unknown", "success", "failure", "in_progress", "deferred", "stale", "invalid"):
        stamp = (
            None
            if state == "unknown"
            else (now - timedelta(hours=2) if state == "stale" else now).isoformat()
        )
        if state == "invalid":
            stamp = "invalid"
        row = Observation(
            "SQL",
            "observed check",
            stamp,
            "in_progress" if state == "in_progress" else "settled",
            (
                "failure"
                if state == "failure"
                else "success" if state in {"success", "stale"} else "unknown"
            ),
            "check_completed",
            "SQL-1",
        )
        records[state] = (row, row, row if state == "failure" else None)
    return records


async def main(args):
    import discord

    baseline = subprocess.check_output(
        ["git", "show", f"{args.base}:bot_instance.py"], cwd=ROOT
    ).decode("utf-8")
    candidate = (ROOT / "bot_instance.py").read_text(encoding="utf-8")
    profile_source = subprocess.check_output(
        ["git", "show", f"{args.base}:services/profile_cache_service.py"], cwd=ROOT
    ).decode("utf-8")
    profile_ns = {"__name__": "inert_profile_baseline"}
    exec(compile(profile_source, "baseline-profile-service", "exec"), profile_ns)
    from services.profile_cache_service import ProfileCacheService

    caches = {"baseline": profile_ns["ProfileCacheService"](), "candidate": ProfileCacheService()}
    for cache in caches.values():
        cache._players = {"1": {"GovernorID": 1}}
        cache._loaded_at = time.time()

    def forbidden(*a, **k):
        raise AssertionError("Synthetic cache workload entered an external dependency")

    now = datetime.now(UTC)
    records = sources(now)
    original_loaded = status._loaded
    selected = [records["success"]]

    def loaded(module, method):
        if method in {"sql_snapshot", "health_snapshot"} and module in {
            status.__name__,
            "services.gsheets_health_service",
        }:
            return selected[0]
        if module == "services.recovery_health":
            return (
                Observation("recovery", "monitor", now.isoformat()),
                now.isoformat(),
                None,
                None,
                False,
                False,
            )
        if module == "core.startup_diagnostics":
            return tuple(
                Observation("startup", label, now.isoformat(), "settled", "success")
                for label in (
                    "warm_profile_cache",
                    "warm_name_cache",
                    "proc_config_import",
                    "build_player_stats_cache",
                )
            )
        return Observation(
            "local", "retained state", now.isoformat(), "settled", "success", count=2449
        )

    status._loaded = loaded
    result = {
        "base": args.base,
        "baseline_bot_sha256": hashlib.sha256(baseline.encode()).hexdigest(),
        "candidate_bot_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
        "limitations": [
            "Synthetic fake-Discord and fake business work; no installed/production timing claim.",
            "Existing command telemetry is unchanged and excluded from pure render measurements.",
            "Business workload models 2ms asynchronous external latency with fixed CPU work; raw absolute timings retained.",
        ],
        "states": {},
        "runs": [],
        "timer_resolution_ms": args.timer_resolution_ms,
        "failures": [],
    }
    try:
        max_bytes = 0
        for label, rows in records.items():
            selected[0] = rows
            samples = []
            for _ in range(1000):
                start = time.perf_counter()
                projection = status.snapshot(now, time.monotonic())
                embed = build_health_embed(projection)
                samples.append((time.perf_counter() - start) * 1000)
                if len(embed) > 6000:
                    result["failures"].append("embed byte/character limit")
            max_bytes = max(max_bytes, len(json.dumps(projection).encode()))
            result["states"][label] = {"samples_ms": samples, "summary_ms": summary(samples)}
        # Cold source availability is separate and never initialized by the reader.
        status._loaded = lambda *a: None
        samples = []
        for _ in range(1000):
            start = time.perf_counter()
            build_health_embed(status.snapshot(now, 0))
            samples.append((time.perf_counter() - start) * 1000)
        result["states"]["sources_absent"] = {"samples_ms": samples, "summary_ms": summary(samples)}
        status._loaded = loaded
        selected[0] = records["success"]

        counters = {"sql": 0, "sheets": 0, "log_scans": 0, "edits": 0, "business": 0}

        async def noop(*a, **k):
            pass

        async def probe(name):
            counters[name] += 1
            await asyncio.sleep(0)
            return True, "OK"

        async def logs(*a):
            counters["log_scans"] += 1
            await asyncio.sleep(0)
            return 0

        async def edit(**k):
            counters["edits"] += 1

        message = SimpleNamespace(edit=edit)

        class Channel:
            guild = SimpleNamespace(id=1)

            async def fetch_message(self, *a):
                return message

        channel = Channel()

        async def ensure(*a):
            return 3

        common = dict(
            bot=SimpleNamespace(get_channel=lambda _: channel, latency=0),
            discord=SimpleNamespace(
                TextChannel=Channel, Thread=Channel, VoiceChannel=Channel, Embed=discord.Embed
            ),
            STATUS_CHANNEL_ID=2,
            GUILD_ID=1,
            ADMIN_USER_ID=4,
            logger=Mock(),
            _ensure_pinned_health_message=ensure,
            _aware=lambda x: x,
            utcnow=lambda: now,
            _last_health_embed_update_ts=None,
            _last_health_alert_ts=None,
            is_pytest_logging_mode=lambda: True,
        )
        old = compile_functions(
            baseline,
            {"_update_health_embed"},
            dict(
                common,
                _uptime_hms=lambda: (0, 0, 1, 0),
                _check_sql_health=lambda **k: probe("sql"),
                _check_gsheets_health=lambda **k: probe("sheets"),
                _count_errors_last_minutes=logs,
                _get_queue_depth_safe=lambda: 0,
                get_cache_stats=lambda: {},
                _summarize_tasks=lambda: "idle",
                LAST_DISCONNECT_UTC=None,
                LAST_RESUME_UTC=None,
                HealthView=lambda: None,
                ERROR_SPIKE_THRESHOLD=5,
                STALENESS_THRESHOLD_MIN=15,
            ),
        )
        new = compile_functions(
            candidate,
            {"_update_health_embed"},
            dict(
                common,
                _shutdown_once=asyncio.Event(),
                _health_projection=lambda: status.snapshot(now, time.monotonic()),
                _health_card=lambda p: build_health_embed(p),
                _bind_health_view=lambda _: None,
                _health_alerts=noop,
            ),
        )

        async def workload(update, cache):
            before = dict(counters)
            lag = []

            async def observer():
                for _ in range(5):
                    await update()
                    await asyncio.sleep(0)

            async def business():
                for _ in range(25):
                    start = time.perf_counter()
                    # asyncio timers may wake early on Windows. A simulated
                    # external operation must not complete before its deadline.
                    deadline = start + 0.002
                    while (remaining := deadline - time.perf_counter()) > 0:
                        await asyncio.sleep(remaining)
                    lag.append(max(0, (time.perf_counter() - start - 0.002) * 1000))
                    outcome = cache.refresh(
                        path="unused",
                        ttl=3600,
                        parse_time=forbidden,
                        build=forbidden,
                        save=forbidden,
                    )
                    assert outcome.execution == "succeeded" and outcome.count == 1
                    # Stable useful work with identical invocation/result assertions.
                    assert sum(range(1000)) == 499500
                    counters["business"] += 1

            start = time.perf_counter()
            await asyncio.gather(business(), *(observer() for _ in range(20)))
            return {
                "elapsed_ms": (time.perf_counter() - start) * 1000,
                "lag_ms": lag,
                "counts": {k: counters[k] - before[k] for k in counters},
            }

        for n in range(30):
            pair = {}
            for label in (("baseline", "candidate") if n % 2 == 0 else ("candidate", "baseline")):
                pair[label] = await workload(
                    (old if label == "baseline" else new)["_update_health_embed"], caches[label]
                )
            result["runs"].append(pair)
        elapsed = {
            k: summary([r[k]["elapsed_ms"] for r in result["runs"]])
            for k in ("baseline", "candidate")
        }
        lag = {k: summary([v for r in result["runs"] for v in r[k]["lag_ms"]]) for k in elapsed}
        result.update(elapsed_ms=elapsed, loop_lag_ms=lag, max_projection_bytes=max_bytes)
        before_threads = threading.active_count()
        before_tasks = len(asyncio.all_tasks())
        gc.collect()
        tracemalloc.start()
        for _ in range(100):
            build_health_embed(status.snapshot(now, 0))
        gc.collect()
        before = tracemalloc.get_traced_memory()[0]
        for _ in range(2000):
            build_health_embed(status.snapshot(now, 0))
        gc.collect()
        retained, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["allocation"] = {
            "retained_growth_bytes": retained - before,
            "peak_bytes": peak,
            "new_threads": threading.active_count() - before_threads,
            "new_tasks": len(asyncio.all_tasks()) - before_tasks,
        }
        if result["allocation"]["new_threads"] or result["allocation"]["new_tasks"]:
            result["failures"].append("new persistent workers")
        if result["allocation"]["retained_growth_bytes"] > 16384:
            result["failures"].append("retained state growth")
        for label, data in result["states"].items():
            if data["summary_ms"]["p95"] > 5 or data["summary_ms"]["p99"] > 10:
                result["failures"].append(f"render limit: {label}")
        if max_bytes > 16384:
            result["failures"].append("projection retention limit")
        for metric, limit in (("p50", 1.02), ("p95", 1.05)):
            if elapsed["candidate"][metric] > elapsed["baseline"][metric] * limit:
                result["failures"].append(f"business elapsed {metric} regression")
        if lag["candidate"]["p95"] - lag["baseline"]["p95"] > 5:
            result["failures"].append("event loop lag regression")
        for r in result["runs"]:
            if r["candidate"]["counts"] != {
                "sql": 0,
                "sheets": 0,
                "log_scans": 0,
                "edits": 100,
                "business": 25,
            }:
                result["failures"].append("candidate unexpected work counts")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(
            json.dumps({k: v for k, v in result.items() if k not in {"states", "runs"}}, indent=2)
        )
        return bool(result["failures"])
    finally:
        status._loaded = original_loaded


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--timer-resolution-ms",
        type=int,
        choices=[1],
        default=None,
        help="Windows-only controlled timer resolution; always released on exit",
    )
    args = parser.parse_args()
    timer = None
    try:
        if args.timer_resolution_ms is not None:
            if sys.platform != "win32":
                raise ValueError("Timer-resolution control is Windows-only")
            import ctypes

            timer = ctypes.WinDLL("winmm")
            if timer.timeBeginPeriod(args.timer_resolution_ms) != 0:
                timer = None
                raise RuntimeError("Timer-resolution request failed")
        raise SystemExit(asyncio.run(main(args)))
    finally:
        if timer is not None:
            timer.timeEndPeriod(args.timer_resolution_ms)
