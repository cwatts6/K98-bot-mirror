"""P01.6 qualification: offline by default; explicitly guarded local SQL fixture.

Never loads production configuration. Native mode creates a new uniquely named
database, installs reviewed source definitions and synthetic data, and retains it
with its receipts. It never reuses, drops, or repairs an existing database.
"""

import argparse
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from contextvars import ContextVar
from datetime import UTC, date, datetime, timedelta
import gc
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import tracemalloc
from types import ModuleType
from unittest.mock import patch
from uuid import uuid4
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BASELINE = "7e430a62"


def safe_environment():
    for key, value in {
        "PYTHON_DOTENV_DISABLED": "1",
        "K98_TEST_MODE": "1",
        "PYTEST_RUNNING": "1",
        "OUR_KINGDOM": "98",
        "DISCORD_BOT_TOKEN": "offline",
        "SQL_SERVER": "unused",
        "SQL_DATABASE": "unused",
    }.items():
        os.environ[key] = value


def statistics(values):
    ordered = sorted(values)
    return {
        "n": len(values),
        **{
            name: ordered[min(len(values) - 1, int((len(values) - 1) * p))]
            for name, p in (("p50", 0.5), ("p95", 0.95), ("p99", 0.99), ("max", 1))
        },
    }


def baseline_module(path, name):
    source = subprocess.check_output(["git", "show", f"{BASELINE}:{path}"], cwd=ROOT)
    module = ModuleType(name)
    sys.modules[name] = module
    exec(compile(source, f"{name}.py", "exec"), module.__dict__)
    return module, hashlib.sha256(source).hexdigest()


async def offline(receipt, artifact):
    from player_self_service import stats_runtime, stats_service
    from player_self_service.stats_models import (
        PersonalStatsDailyRow,
        PersonalStatsDataSet,
        PersonalStatsHeader,
    )
    from services.governor_account_service import summarize_accounts

    baseline, digest = baseline_module(
        "player_self_service/stats_service.py", "p016_baseline_stats"
    )
    receipt["baseline"] = BASELINE
    receipt["baseline_source_sha256"] = digest
    summary = summarize_accounts({"Main": {"GovernorID": "111", "GovernorName": "Fixture"}})
    dataset = PersonalStatsDataSet(
        PersonalStatsHeader(
            date(2026, 11, 5),
            datetime(2026, 11, 5, 23, 59, tzinfo=UTC),
            date(2026, 5, 10),
            date(2026, 11, 5),
            1,
        ),
        tuple(
            PersonalStatsDailyRow(
                governor_id=111,
                as_of_date=date(2026, 5, 10) + timedelta(days=i),
                has_stats=True,
                previous_stats_date=date(2026, 5, 9) + timedelta(days=i),
                power_value=1000 + i,
                troop_power_value=500 + i,
                power_delta=1,
                troop_power_delta=1,
                kill_points_delta=1,
                rss_gathered_delta=1,
                rss_assist_delta=1,
                helps_delta=1,
                t4_kills_delta=1,
                t5_kills_delta=1,
                deads_delta=1,
                healed_troops_delta=1,
                has_alliance_activity=True,
                previous_activity_date=date(2026, 5, 9) + timedelta(days=i),
                build_activity_delta=1,
                tech_donations_delta=1,
                has_forts=True,
                forts_total=1,
                forts_launched=1,
                forts_joined=0,
            )
            for i in range(180)
        ),
    )

    async def accounts(user):
        return summary

    def data(ids, **kwargs):
        return dataset

    samples = {"baseline": [], "candidate": []}
    cpu = {"baseline": [], "candidate": []}
    lag = {"baseline": [], "candidate": []}
    runtime = stats_runtime.get_runtime()
    # Match a fully warmed eight-worker fixture on both sides. Lazy executor
    # thread creation is startup allocation, not residual per-cycle growth.
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=8))
    warm_barrier = threading.Barrier(8)
    await asyncio.gather(*(loop.run_in_executor(None, warm_barrier.wait) for _ in range(8)))
    with (
        patch.object(stats_service, "_emit", lambda *a: None),
        patch.object(baseline, "_emit", lambda *a: None),
    ):
        for cycle in range(3):
            order = [("baseline", baseline), ("candidate", stats_service)]
            if cycle % 2:
                order.reverse()
            for label, module in order:
                await module.clear_personal_stats_cache()
                for _ in range(100):
                    await module.build_personal_stats_payload(
                        42, account_loader=accounts, data_loader=data
                    )
                running = True

                async def heartbeat():
                    while running:
                        started = time.perf_counter()
                        await asyncio.sleep(0.001)
                        lag[label].append(max(0, (time.perf_counter() - started - 0.001) * 1000))

                monitor = asyncio.create_task(heartbeat())
                cpu_start = time.process_time()
                for index in range(3000):
                    if index % 10 == 0:
                        await module.clear_personal_stats_cache()
                    started = time.perf_counter()
                    await module.build_personal_stats_payload(
                        42, account_loader=accounts, data_loader=data
                    )
                    samples[label].append((time.perf_counter() - started) * 1000)
                    await asyncio.sleep(0)
                cpu[label].append(time.process_time() - cpu_start)
                running = False
                await monitor
    # Snapshot cost at maximum physical records; no submitted work or SQL.
    fixture = stats_runtime.StatsRuntime()
    for i in range(10):
        run = stats_runtime.ReadRun("dataset" if i < 8 else "render")
        fixture.jobs[id(run)] = run
    for _ in range(32):
        fixture.terminal.append(run.snapshot())
    copies = []
    for _ in range(1000):
        began = time.perf_counter()
        snapshot = fixture.snapshot()
        copies.append((time.perf_counter() - began) * 1000)

    async def stalled_deadline():
        began = time.perf_counter()
        try:
            async with asyncio.timeout(0.01):
                time.sleep(0.12)
                await asyncio.sleep(0.02)
        except TimeoutError:
            return (time.perf_counter() - began) * 1000
        raise AssertionError("Stall calibration did not expire")

    calibrated_stall = await stalled_deadline()
    receipt["stall_calibration_ms"] = calibrated_stall
    receipt["samples_ms"] = samples
    receipt["latency_ms"] = {k: statistics(v) for k, v in samples.items()}
    receipt["loop_lag_ms"] = {k: statistics(v) for k, v in lag.items()}
    receipt["cpu_seconds"] = cpu
    retention = {}
    for label, module in (("baseline", baseline), ("candidate", stats_service)):
        await module.clear_personal_stats_cache()
        tracemalloc.start()
        gc.collect()
        start_bytes = tracemalloc.get_traced_memory()[0]
        cycles = []
        for cycle in range(10):
            for user in range(cycle * 100, (cycle + 1) * 100):
                await module.build_personal_stats_payload(
                    user, account_loader=accounts, data_loader=data
                )
            cycles.append(
                dict(
                    tasks=len(asyncio.all_tasks()),
                    threads=threading.active_count(),
                    cache=len(runtime.cache if label == "candidate" else baseline._CACHE),
                )
            )
        gc.collect()
        retention[label] = dict(
            bytes=tracemalloc.get_traced_memory()[0] - start_bytes, cycles=cycles
        )
        tracemalloc.stop()
    receipt["matched_retention"] = retention
    receipt["snapshot_ms"] = statistics(copies)
    receipt["snapshot_bytes"] = len(json.dumps(snapshot).encode())
    base, candidate = receipt["latency_ms"]["baseline"], receipt["latency_ms"]["candidate"]
    base_lag, candidate_lag = (
        receipt["loop_lag_ms"]["baseline"],
        receipt["loop_lag_ms"]["candidate"],
    )
    receipt["gates"] = dict(
        service_p95=candidate["p95"] - base["p95"] <= 5,
        loop_p99=candidate_lag["p99"] - base_lag["p99"] <= 5,
        loop_max=candidate_lag["max"] - base_lag["max"] <= 25,
        snapshot_bound=receipt["snapshot_bytes"] <= 8192,
        snapshot_cost=receipt["snapshot_ms"]["p99"] <= 2,
        stall_calibration=calibrated_stall > 100,
        settled=not runtime.jobs and runtime.observers == 0,
        cpu=sum(cpu["candidate"]) <= sum(cpu["baseline"]) * 1.1,
        retention=retention["candidate"]["bytes"] - retention["baseline"]["bytes"]
        <= 8 * 1024 * 1024,
        retention_counts=all(
            row == retention["candidate"]["cycles"][0] for row in retention["candidate"]["cycles"]
        ),
    )
    receipt["cost_limits"] = (
        "Synthetic orchestration; native SQL, full payload, CPU and retention gates reported separately"
    )
    assert all(receipt["gates"].values()), receipt["gates"]


def native(database, receipt, artifact):
    import pyodbc

    from event_calendar.sql_lifecycle import SqlOutcome
    from registry.dal import registry_dal
    from stats.dal import personal_stats_dal as dal

    pyodbc.pooling = False
    prefix = (
        "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:localhost\\K98DEV;"
        "Trusted_Connection=yes;TrustServerCertificate=yes;DATABASE="
    )
    master = pyodbc.connect(prefix + "master", timeout=3, autocommit=True)
    receipt["server"] = master.execute(
        "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))"
    ).fetchval()
    if receipt["server"] != r"9SX2VF4\K98DEV":
        raise RuntimeError("Unexpected local development instance")
    if master.execute("SELECT DB_ID(?)", database).fetchval() is not None:
        raise RuntimeError("Target exists; no writes authorized")
    receipt["database"] = database
    created_id = None
    setup = None
    try:
        master.execute(f"CREATE DATABASE [{database}]")
        created_id = master.execute("SELECT DB_ID(?)", database).fetchval()
        receipt["database_id"] = created_id
        files = [
            r[0]
            for r in master.execute(
                "SELECT physical_name FROM sys.master_files WHERE database_id=?", created_id
            )
        ]
        if not files or any(not Path(p).name.startswith(database) for p in files):
            raise RuntimeError("Unexpected new fixture file paths")
        receipt["new_files"] = files
        master.execute(f"ALTER DATABASE [{database}] SET DISABLE_BROKER")

        def connect(*, reader=True):
            connection = pyodbc.connect(prefix + database, timeout=3, autocommit=False)
            try:
                actual = connection.execute(
                    "SELECT DB_ID(), DB_NAME(), CONVERT(nvarchar(128),SERVERPROPERTY('ServerName'))"
                ).fetchone()
                if tuple(actual) != (created_id, database, r"9SX2VF4\K98DEV"):
                    raise RuntimeError("Fixture identity changed")
                if reader:
                    connection.execute("EXECUTE AS USER = 'P016Reader'")
                return connection
            except BaseException:
                connection.close()
                raise

        setup = connect(reader=False)
        setup.autocommit = True
        # The SQL export references this sequence but supplies no CREATE script.
        # This is an explicit synthetic fixture dependency, not a schema assertion.
        setup.execute("CREATE SEQUENCE dbo.KS4_UNO_SEQ AS int START WITH 1 INCREMENT BY 1")
        receipt["synthetic_prerequisite"] = (
            "KS4_UNO_SEQ int sequence; definition missing from source export; inserts bind SCAN_UNO explicitly"
        )
        names = [
            "dbo.IntList.UserDefinedTableType",
            "dbo.KingdomScanData4.Table",
            "dbo.AllianceActivitySnapshotHeader.Table",
            "dbo.AllianceActivitySnapshotRow.Table",
            "dbo.cur_RallyDaily.Table",
            "dbo.DiscordGovernorRegistry.Table",
            "dbo.usp_GetPersonalStatsDaily.StoredProcedure",
            "dbo.sp_Registry_GetByDiscordID.StoredProcedure",
        ]
        receipt["schema_hashes"] = {}
        for name in names:
            raw = (Path(r"C:\K98-bot-SQL-Server\sql_schema") / (name + ".sql")).read_bytes()
            receipt["schema_hashes"][name] = hashlib.sha256(raw).hexdigest()
            text = raw.decode("utf-8-sig")
            # ALTER PROCEDURE must begin its own batch; preserve exact definitions.
            for batch in re.split(r"(?m)^GO\s*$|(?=^ALTER PROCEDURE)", text):
                if batch.strip():
                    setup.execute(batch)
        setup.execute("CREATE USER P016Reader WITHOUT LOGIN")
        setup.execute("GRANT EXECUTE ON dbo.usp_GetPersonalStatsDaily TO P016Reader")
        setup.execute("GRANT EXECUTE ON dbo.sp_Registry_GetByDiscordID TO P016Reader")
        setup.execute("GRANT EXECUTE, REFERENCES ON TYPE::dbo.IntList TO P016Reader")
        setup.execute("CREATE USER P016Denied WITHOUT LOGIN")
        ids = tuple(range(1001, 1027))
        slots = ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 21)]
        cursor = setup.cursor()
        cursor.executemany(
            "INSERT dbo.DiscordGovernorRegistry (DiscordUserID,GovernorID,GovernorName,AccountType,RegistrationStatus) VALUES (42,?,?,?,'Active')",
            [(gid, f"Synthetic {gid}", slot) for gid, slot in zip(ids, slots, strict=True)],
        )
        other_ids = tuple(range(2001, 2005))
        cursor.executemany(
            "INSERT dbo.DiscordGovernorRegistry (DiscordUserID,GovernorID,GovernorName,AccountType,RegistrationStatus) VALUES (?,?,?,'Main','Active')",
            [
                (user, gid, f"Synthetic {gid}")
                for user, gid in zip(range(43, 47), other_ids, strict=True)
            ],
        )
        rows = []
        for day in range(181):
            for index, gid in enumerate(ids + other_ids):
                rows.append(
                    (
                        gid,
                        day + 100,
                        datetime(2026, 5, 9) + timedelta(days=day),
                        day + 1,
                        day * 30 + index + 1,
                    )
                )
        cursor.executemany(
            """INSERT dbo.KingdomScanData4
            (GovernorID,Power,ScanDate,SCANORDER,SCAN_UNO,PowerRank,KillPoints,Deads,
             T1_Kills,T2_Kills,T3_Kills,T4_Kills,T5_Kills,RSSAssistance,Helps)
             VALUES (?,?,?,?,?,1,1,1,1,1,1,1,1,1,1)""",
            rows,
        )
        cursor.close()
        receipt["cases"] = {}
        with (
            patch.object(dal, "get_conn_with_retries", connect),
            patch.object(registry_dal, "_get_conn", connect),
        ):
            for requested in ((ids[0],), ids):
                outcome = SqlOutcome()
                result = dal.fetch_personal_stats_daily(requested, sql_outcome=outcome)
                assert len(result.rows) == 180 * len(requested)
                assert outcome.cleanup == "settled" and outcome.rollback == "confirmed"
            accounts_outcome = SqlOutcome()
            assert len(registry_dal.get_by_discord_id(42, sql_outcome=accounts_outcome)) == 26
            assert accounts_outcome.cleanup == "settled"
            receipt["cases"]["restricted_principal_1_and_26_ids_180_days_registry"] = "passed"
            blocker = connect(reader=False)
            try:
                blocker.execute(
                    "UPDATE dbo.KingdomScanData4 WITH (TABLOCKX) SET Power=Power WHERE GovernorID=?",
                    ids[0],
                )
                outcome = SqlOutcome()
                began = time.monotonic()
                with ThreadPoolExecutor(max_workers=1) as observer:
                    pending = observer.submit(
                        dal.fetch_personal_stats_daily, (ids[0],), sql_outcome=outcome
                    )
                    deadline = time.monotonic() + 5
                    requests = []
                    while not requests and time.monotonic() < deadline:
                        requests = master.execute(
                            "SELECT session_id, blocking_session_id, wait_type FROM sys.dm_exec_requests WHERE database_id=? AND blocking_session_id<>0",
                            created_id,
                        ).fetchall()
                        if not requests:
                            time.sleep(0.02)
                    assert requests, "No fixture-bound blocked request observed"
                    receipt["blocked_request_evidence"] = [list(row) for row in requests]
                    try:
                        pending.result()
                    except pyodbc.Error as error:
                        receipt["query_timeout_sqlstate"] = error.args[0]
                    else:
                        raise AssertionError("Blocked native query did not time out")
                elapsed = time.monotonic() - began
                assert 8 <= elapsed <= 13, elapsed
                assert outcome.cleanup == "settled"
                receipt["cases"]["real_connection_query_timeout_and_close"] = dict(
                    seconds=elapsed, outcome=outcome.public()
                )
            finally:
                blocker.rollback()
                blocker.close()

        def denied():
            connection = connect(reader=False)
            connection.execute("EXECUTE AS USER = 'P016Denied'")
            return connection

        with patch.object(dal, "get_conn_with_retries", denied):
            outcome = SqlOutcome()
            try:
                dal.fetch_personal_stats_daily((ids[0],), sql_outcome=outcome)
            except pyodbc.Error:
                assert outcome.cleanup == "settled"
                receipt["cases"]["denied_principal"] = "passed"
            else:
                raise AssertionError("Denied principal read data")
        # Reverse overlap order: an existing read transaction blocks a writer;
        # both connections are confined to the uniquely created fixture.
        reader, writer = connect(reader=False), connect(reader=False)
        try:
            reader.execute(
                "SELECT GovernorID FROM dbo.KingdomScanData4 WITH (TABLOCK,HOLDLOCK) WHERE GovernorID=?",
                ids[0],
            ).fetchall()
            writer.timeout = 1
            try:
                writer.execute(
                    "UPDATE dbo.KingdomScanData4 SET Power=Power WHERE GovernorID=?", ids[0]
                )
            except pyodbc.Error as error:
                assert error.args[0] == "HYT00"
                receipt["cases"]["read_before_writer_lock_order"] = "passed"
            else:
                raise AssertionError("Read transaction did not retain its lock")
        finally:
            writer.rollback()
            writer.close()
            reader.rollback()
            reader.close()
        invalid_login = "P016_Qualification_NoSuchLogin"
        assert master.execute("SELECT SUSER_ID(?)", invalid_login).fetchval() is None
        try:
            pyodbc.connect(
                prefix.replace(
                    "Trusted_Connection=yes;", f"UID={invalid_login};PWD=not-a-credential;"
                )
                + database,
                timeout=1,
            )
        except pyodbc.Error as error:
            receipt["cases"]["native_login_failure"] = dict(sqlstate=error.args[0])
        else:
            raise AssertionError("Nonexistent fixture login connected")
        # Representative full service calls, including the candidate's additional
        # final access check; all SQL goes to this same restricted fixture user.
        from player_self_service import stats_service

        baseline, source_hash = baseline_module(
            "player_self_service/stats_service.py", "p016_native_baseline"
        )
        baseline_dal, dal_hash = baseline_module(
            "stats/dal/personal_stats_dal.py", "p016_native_baseline_dal"
        )
        receipt["native_baseline_hashes"] = [source_hash, dal_hash]
        assert baseline_dal.PERSONAL_STATS_SQL == dal.PERSONAL_STATS_SQL
        # SHOWPLAN is local fixture-only evidence permission, not an application
        # grant claim. Execute unchanged parameterized batches under the same user.
        setup.execute("GRANT SHOWPLAN TO P016Reader")
        plan_samples = []
        for size in (1, 26):
            for label, source in (("baseline", baseline_dal), ("candidate", dal)):
                connection = connect()
                connection.timeout = 9
                messages, rowsets, plan_hashes = [], [], []
                try:
                    cursor = connection.cursor()
                    cursor.execute("SET STATISTICS IO ON; SET STATISTICS XML ON")
                    cursor.execute(
                        source.PERSONAL_STATS_SQL,
                        (*ids[:size], *(None for _ in range(26 - size)), 180),
                    )
                    while True:
                        messages.extend(str(message[1]) for message in cursor.messages)
                        if cursor.description:
                            rows = cursor.fetchall()
                            if (
                                rows
                                and len(rows[0]) == 1
                                and isinstance(rows[0][0], str)
                                and "<ShowPlanXML" in rows[0][0]
                            ):
                                xml = rows[0][0]
                                (
                                    artifact / f"{label}-{size}-plan-{len(plan_hashes)}.xml"
                                ).write_text(xml, encoding="utf-8")
                                plan_hashes.extend(
                                    (node.attrib.get("QueryHash"), node.attrib.get("QueryPlanHash"))
                                    for node in ET.fromstring(xml).iter()
                                    if "QueryPlanHash" in node.attrib
                                )
                            else:
                                rowsets.append([list(row) for row in rows])
                        if not cursor.nextset():
                            messages.extend(str(message[1]) for message in cursor.messages)
                            break
                    logical_reads = sum(
                        int(value)
                        for message in messages
                        for value in re.findall(r"(?<!lob )logical reads (\d+)", message)
                    )
                    assert logical_reads > 0 and plan_hashes
                    sample = dict(
                        label=label,
                        governors=size,
                        logical_reads=logical_reads,
                        plan_hashes=plan_hashes,
                        row_sha256=hashlib.sha256(
                            json.dumps(rowsets, default=str).encode()
                        ).hexdigest(),
                    )
                    plan_samples.append(sample)
                    (artifact / f"{label}-{size}-io.json").write_text(
                        json.dumps(messages), encoding="utf-8"
                    )
                finally:
                    connection.rollback()
                    connection.close()
            before, after = plan_samples[-2:]
            assert after["logical_reads"] <= before["logical_reads"] * 1.05
            assert after["row_sha256"] == before["row_sha256"]
            assert after["plan_hashes"] == before["plan_hashes"]
        receipt["logical_reads_and_plan_identity"] = plan_samples
        print("Native permission, timeout, overlap, login and SQL cost checks passed", flush=True)

        async def compare():
            times = {"baseline": [], "candidate": []}
            counts = {"registry": 0, "dataset": 0}
            maximum_payload = {"baseline": [], "candidate": []}
            # Save partial samples on failure as well as successful completion.
            receipt["native_partial_samples_ms"] = times
            receipt["maximum_26_x_180_payload_ms"] = maximum_payload

            def counted(kind):
                def factory():
                    counts[kind] += 1
                    return connect()

                return factory

            with ExitStack() as patches:
                patches.enter_context(
                    patch.object(dal, "get_conn_with_retries", counted("dataset"))
                )
                patches.enter_context(
                    patch.object(baseline_dal, "get_conn_with_retries", counted("dataset"))
                )
                patches.enter_context(patch.object(registry_dal, "_get_conn", counted("registry")))
                # Qualify maximum 26 x 180 payloads separately. The sustained
                # mixed workload uses the default selected governor, equally
                # for control/candidate; neither side gets a warm-cache advantage.
                for label, module, loader in (
                    ("baseline", baseline, baseline_dal.fetch_personal_stats_daily),
                    ("candidate", stats_service, dal.fetch_personal_stats_daily),
                ):
                    for _ in range(3):
                        await module.clear_personal_stats_cache()
                        began = time.perf_counter()
                        payload = await module.build_personal_stats_payload(
                            42, all_linked=True, data_loader=loader
                        )
                        if label == "candidate":
                            await stats_service.assert_personal_stats_access(payload)
                        maximum_payload[label].append((time.perf_counter() - began) * 1000)
                for cycle in range(3):
                    order = [
                        ("baseline", baseline, baseline_dal.fetch_personal_stats_daily),
                        ("candidate", stats_service, dal.fetch_personal_stats_daily),
                    ]
                    if cycle % 2:
                        order.reverse()
                    for label, module, loader in order:
                        for i in range(1100):
                            if i % 5 == 0:
                                await module.clear_personal_stats_cache()
                            began = time.perf_counter()
                            receipt["native_current_request"] = dict(
                                cycle=cycle + 1, variant=label, index=i, cold=i % 5 == 0
                            )
                            payload = await module.build_personal_stats_payload(
                                42, data_loader=loader
                            )
                            if label == "candidate":
                                await stats_service.assert_personal_stats_access(payload)
                            if i >= 100:
                                times[label].append((time.perf_counter() - began) * 1000)
                        print(f"Native comparison cycle {cycle + 1}: {label} complete", flush=True)
                await stats_service.clear_personal_stats_cache()
                counts.update(registry=0, dataset=0)
                payload = await stats_service.build_personal_stats_payload(42)
                await stats_service.assert_personal_stats_access(payload)
                assert counts == {"registry": 3, "dataset": 1}, counts
                normal_counts = dict(counts)
                completed, refused = Counter(), Counter()
                stages = ContextVar("qualification_registry_stage", default=0)
                original_registry = stats_service._load_registry

                async def classified_registry(*args, **kwargs):
                    index = stages.get()
                    stages.set(index + 1)
                    try:
                        return await original_registry(*args, **kwargs)
                    except Exception:
                        refused[("pre", "post", "final")[min(index, 2)]] += 1
                        raise

                patches.enter_context(
                    patch.object(stats_service, "_load_registry", classified_registry)
                )

                async def mixed_request(user):
                    stages.set(0)
                    try:
                        payload = await stats_service.build_personal_stats_payload(user)
                        await stats_service.assert_personal_stats_access(payload)
                    except Exception:
                        return
                    completed[user] += 1

                for wave in range(10):
                    if wave % 3 == 0:
                        await stats_service.clear_personal_stats_cache()
                    await asyncio.gather(
                        *(
                            mixed_request(user)
                            for user in ([42] * 4 + list(range(43, 47)) + [42] * 4)
                        )
                    )
                receipt["native_mixed_progress"] = dict(
                    completed=dict(completed), registry_refused=dict(refused), arrivals=120
                )
                assert all(completed[user] > 0 for user in range(42, 47)), receipt[
                    "native_mixed_progress"
                ]
            base, candidate = statistics(times["baseline"]), statistics(times["candidate"])
            passed = candidate["p95"] - base["p95"] <= max(250, base["p95"] * 0.2)
            receipt["native_latency_ms"] = dict(
                baseline=base, candidate=candidate, samples=times, passed=passed
            )
            receipt["normal_delivery_statements"] = normal_counts
            receipt["maximum_26_x_180_payload_ms"] = maximum_payload
            receipt["native_workload"] = (
                "3 alternating pairs; 100 warmup + 1000 measured default-governor requests each; 20% explicit cache misses; maximum payloads separate"
            )
            assert passed

        asyncio.run(compare())
        receipt["retained"] = True
    finally:
        if setup is not None:
            setup.close()
        master.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.database and (
        not args.execute
        or not re.fullmatch(r"K98_P016_Disposable_\d{8}_[a-f0-9]{8}", args.database)
    ):
        parser.error(
            "Native mode requires --execute and a new K98_P016_Disposable_YYYYMMDD_nonce target"
        )
    safe_environment()
    artifact = (
        ROOT
        / ".codex_artifacts"
        / "p016-qualification-20261105"
        / (args.database or "offline-" + uuid4().hex[:8])
    )
    artifact.mkdir(parents=True, exist_ok=False)
    receipt = dict(started_utc=datetime.now(UTC).isoformat(), status="running")
    from scripts.prepare_k98_update import P016_PERSONAL_STATS_PATHS

    receipt["candidate_source_sha256"] = {
        path: hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for path in sorted(P016_PERSONAL_STATS_PATHS | {"scripts/qualify_p016_personal_stats.py"})
    }
    try:
        if args.database:
            native(args.database, receipt, artifact)
        else:
            asyncio.run(offline(receipt, artifact))
        receipt["status"] = "passed"
    except BaseException as error:
        receipt["status"] = "failed"
        receipt["error_type"] = type(error).__name__
        raise
    finally:
        (artifact / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(str(artifact / "receipt.json"))


if __name__ == "__main__":
    main()
