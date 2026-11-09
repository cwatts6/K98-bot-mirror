"""Offline matched-control P01.5 cost rehearsal; no provider or live SQL calls.

Uses the baseline service body, equal synthetic SQL latency fixtures, actual JSON
replacement, both P01.4 transports and a blocked read. Native SQL boundaries are
qualified separately by qualify_calendar_ownership.py. Raw adverse runs are kept.
"""

import asyncio
from contextlib import ExitStack
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for key, value in {
    "K98_TEST_MODE": "1",
    "PYTEST_RUNNING": "1",
    "PYTHON_DOTENV_DISABLED": "1",
    "OUR_KINGDOM": "98",
}.items():
    os.environ[key] = value

from event_calendar import audit_dal, service
from event_calendar.audit_dal import AuditResult
from event_calendar.cache_publisher import PublishResult
from event_calendar.event_generator import GenerationResult
from event_calendar.mutation_owner import get_owner
from event_calendar.sheets_sync import SyncResult
from event_calendar.sql_lifecycle import SqlOutcome
from event_calendar.sync_audit import SyncAudit
from file_utils import atomic_json_write
from services import operation_diagnostics as diagnostics
from services.download_log_service import DownloadLogWriter
from services.optional_import_audit_worker import ImportAuditWriter


def statistics(values):
    ordered = sorted(values)

    def percentile(p):
        return ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))]

    return dict(
        n=len(values),
        p50=percentile(0.5),
        p95=percentile(0.95),
        p99=percentile(0.99),
        max=max(values),
    )


class FixtureDal:
    def start_import_audit_batch(self, **values):
        time.sleep(0.001)
        return SimpleNamespace(import_audit_batch_id=17, correlation_id=values["correlation_id"])

    def complete_import_audit_batch(self, **values):
        time.sleep(0.001)


async def main():
    target = ROOT / ".codex_artifacts" / "p015-qualification-20261105" / ("cost-" + uuid4().hex[:8])
    target.mkdir(parents=True)
    baseline = ModuleType("calendar_baseline")
    sys.modules[baseline.__name__] = baseline
    source = subprocess.check_output(
        ["git", "show", "8806f7e96bfb32624e10029668c992a5c04651e1:event_calendar/service.py"],
        cwd=ROOT,
    )
    exec(compile(source, "baseline_calendar_service.py", "exec"), baseline.__dict__)
    receipt: dict[str, Any] = dict(
        baseline="8806f7e96bfb32624e10029668c992a5c04651e1",
        sql="offline matched 1 ms boundary fixture",
        raw={},
        gates={},
    )
    sink = diagnostics.DiagnosticSink(target / "diagnostics").start()
    upload_file = DownloadLogWriter(target / "upload.csv").start()
    upload_sql = ImportAuditWriter(lambda: None, dal=FixtureDal()).start()
    release_read = threading.Event()
    blocked_read = asyncio.create_task(asyncio.to_thread(release_read.wait))
    audit_release = threading.Event()
    audit_release.set()
    size = 0
    events = []

    def sync(*args):
        time.sleep(0.001)
        return SyncResult(True, "success", rows_upserted_oneoff=size)

    def generate(**kwargs):
        time.sleep(0.001)
        return GenerationResult(True, "success", instances_generated=size, instances_written=size)

    def publish(**kwargs):
        atomic_json_write(
            str(target / "calendar.json"),
            {"events": events},
            ensure_ascii=True,
            sort_keys=False,
            default=None,
            replace_retries=1,
        )
        atomic_json_write(
            str(target / "index.json"),
            {"war": [str(i) for i in range(size)]},
            ensure_ascii=True,
            sort_keys=False,
            default=None,
            replace_retries=1,
        )
        return PublishResult(True, "success", events_written=size)

    def audit_start(*args):
        assert audit_release.wait(30)
        time.sleep(0.002)
        return AuditResult(1, SqlOutcome(effect="committed", cleanup="settled"))

    def audit_finish(*args):
        time.sleep(0.002)
        return AuditResult(1, SqlOutcome(effect="committed", cleanup="settled"))

    async def run(mode):
        owner = get_owner()
        owner.audit.closed = mode == "off"
        svc = baseline.CalendarService() if mode == "baseline" else service.CalendarService()
        started = time.perf_counter()
        result = await svc.refresh_pipeline(sheet_id="offline")
        elapsed = (time.perf_counter() - started) * 1000
        assert result["ok"] and result["events_written"] == size, (mode, size, result)
        if mode == "on":
            await owner.audit.drain()
        return elapsed

    async def uploads():
        while True:
            upload_file.offer_row(["fixture"] * 5)
            handle = upload_sql.start_batch(import_kind="honor")
            if handle:
                upload_sql.action(handle, "complete", {"rows_written": 1})
            await asyncio.sleep(0.05)

    uploader = asyncio.create_task(uploads())
    try:
        with ExitStack() as patches:
            patches.enter_context(patch.object(diagnostics, "_sink", sink))
            for module in (baseline, service):
                for name, function in (
                    ("sync_sheets_to_sql", sync),
                    ("generate_calendar_instances", generate),
                    ("publish_event_calendar_cache", publish),
                ):
                    patches.enter_context(patch.object(module, name, function))
                patches.enter_context(patch.object(module, "emit_telemetry_event", lambda e: None))
            patches.enter_context(patch.object(audit_dal, "start", audit_start))
            patches.enter_context(patch.object(audit_dal, "finish", audit_finish))
            for size in (0, 1000, 10000):
                events = [
                    dict(
                        instance_id=i,
                        title="Synthetic calendar",
                        type="war",
                        start_utc="2099-01-01T00:00:00Z",
                    )
                    for i in range(size)
                ]
                rows = {mode: [] for mode in ("baseline", "off", "on", "blocked")}
                for mode in ("baseline", "off", "on"):
                    await run(mode)
                # Alternating comparisons avoid a single warm/cold ordering advantage.
                for sample in range(30):
                    for mode in (
                        ("baseline", "off", "on", "blocked")
                        if sample % 2 == 0
                        else ("blocked", "on", "off", "baseline")
                    ):
                        if mode == "blocked":
                            audit_release.clear()
                        rows[mode].append(await run(mode))
                        audit_release.set()
                        await get_owner().audit.drain()
                receipt["raw"][str(size)] = rows
                control = statistics(rows["baseline"])["p95"]
                receipt["gates"][str(size)] = {
                    mode: dict(
                        added_p95_ms=statistics(values)["p95"] - control,
                        limit_ms=max(20, control * 0.05),
                        passed=statistics(values)["p95"] - control <= max(20, control * 0.05),
                    )
                    for mode, values in rows.items()
                    if mode != "baseline"
                }
                print("business size", size, receipt["gates"][str(size)], flush=True)
            size = 0
            events = []
            offers = []
            audit = SyncAudit()
            audit_release.clear()
            ticket = audit.offer("fixture", datetime.now(UTC))
            for _ in range(10000):
                started = time.perf_counter()
                audit.offer("refused", datetime.now(UTC))
                offers.append((time.perf_counter() - started) * 1000)
            audit.finish(ticket, {"status": "success"}, datetime.now(UTC))
            audit_release.set()
            await audit.drain()
            receipt["raw"]["offers_ms"] = offers
            stat = statistics(offers)
            receipt["gates"]["offer"] = dict(**stat, passed=stat["p95"] <= 1 and stat["max"] <= 5)
            windows = []
            # Five alternating 10-second controls/treatments with a 10 ms heartbeat.
            for pair in range(5):
                for mode in (("baseline", "on") if pair % 2 == 0 else ("on", "baseline")):
                    stop = asyncio.Event()

                    async def workload():
                        while not stop.is_set():
                            await run(mode)
                            await asyncio.sleep(0.02)

                    work = asyncio.create_task(workload())
                    lag = []
                    finished = asyncio.Event()
                    loop = asyncio.get_running_loop()

                    def deliver(expected):
                        lag.append(max(0, (time.perf_counter() - expected) * 1000))

                    def timer():
                        due = time.perf_counter() + 0.01
                        for _ in range(1000):
                            time.sleep(max(0, due - time.perf_counter()))
                            loop.call_soon_threadsafe(deliver, due)
                            due += 0.01
                        loop.call_soon_threadsafe(finished.set)

                    timer_thread = threading.Thread(target=timer, name="qualification-heartbeat")
                    timer_thread.start()
                    await finished.wait()
                    timer_thread.join()
                    stop.set()
                    await work
                    windows.append(
                        dict(pair=pair, mode=mode, lag_ms=lag, statistics=statistics(lag))
                    )
                    print("window", pair, mode, statistics(lag), flush=True)
            receipt["raw"]["windows"] = windows
            controls = [v for w in windows if w["mode"] == "baseline" for v in w["lag_ms"]]
            treatments = [v for w in windows if w["mode"] == "on" for v in w["lag_ms"]]
            control, treatment = statistics(controls), statistics(treatments)
            receipt["gates"]["heartbeat"] = dict(
                control=control,
                treatment=treatment,
                passed=treatment["p99"] - control["p99"] <= 5
                and treatment["max"] - control["max"] <= 20,
            )
            expected = time.perf_counter() + 0.01
            loop = asyncio.get_running_loop()
            calibration_done = asyncio.Event()
            calibration = threading.Timer(
                0.01, lambda: loop.call_soon_threadsafe(calibration_done.set)
            )
            calibration.start()
            time.sleep(0.05)
            await calibration_done.wait()
            calibration.join()
            detected = (time.perf_counter() - expected) * 1000
            receipt["gates"]["stall_calibration"] = dict(lag_ms=detected, passed=detected >= 40)
            from event_calendar.mutation_owner import MutationOwner

            owner = MutationOwner()
            bookkeeping = []

            async def no_work(run):
                return {"ok": True}

            for _ in range(500):
                began = time.perf_counter()
                await owner.execute("generate", no_work)
                bookkeeping.append((time.perf_counter() - began) * 1000)
            receipt["raw"]["bookkeeping_ms"] = bookkeeping
            receipt["gates"]["bookkeeping"] = dict(
                **statistics(bookkeeping), passed=statistics(bookkeeping)["p95"] <= 5
            )
            drains = []
            for _ in range(30):
                gate = threading.Event()
                admitted = asyncio.Event()
                owner = MutationOwner()

                async def blocked(run):
                    admitted.set()
                    await asyncio.to_thread(gate.wait)
                    return {"ok": True}

                accepted = asyncio.create_task(owner.execute("generate", blocked))
                await admitted.wait()
                owner.close_admission()
                began = time.perf_counter()
                gate.set()
                assert (await owner.drain())["ok"]
                await accepted
                drains.append((time.perf_counter() - began) * 1000)
            receipt["raw"]["drain_ms"] = drains
            stat = statistics(drains)
            receipt["gates"]["drain"] = dict(
                **stat, passed=stat["p95"] <= 100 and stat["max"] <= 500
            )
            receipt["workers"] = dict(
                file=dict(
                    entered=upload_file.entered,
                    settled=upload_file.settled,
                    high_water=upload_file.high_water,
                ),
                sql=dict(
                    entered=upload_sql.entered,
                    settled=upload_sql.settled,
                    high_water=upload_sql.high_water,
                ),
            )
    finally:
        audit_release.set()
        release_read.set()
        uploader.cancel()
        await asyncio.gather(uploader, return_exceptions=True)
        await blocked_read
        await get_owner().audit.drain()
        upload_file.close()
        upload_sql.close()
        sink.close()
        (target / "cost-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("receipt", target / "cost-receipt.json", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
