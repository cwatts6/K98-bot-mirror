"""Offline startup/update ordering; no SQL, provider, VM or host operations."""

import ast
import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
from pathlib import Path
import re
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from scripts import prepare_k98_update as updater, verify_k98_update_pair as verifier
from scripts.package_k98_update_tool import package
from services import (
    export_runtime_composition as runtime,
    runtime_admission_diagnostics as diagnostic,
)
from services.application_maintenance_contract import RESOURCE
from services.application_maintenance_dal import schema_observation

ADMISSION_POLICY = {"source_hashes": {"services/runtime_admission_diagnostics.py": "a" * 64}}


@pytest.fixture
def admission(tmp_path, monkeypatch, caplog):
    manifest = tmp_path / "bot.json"
    manifest.write_text(
        json.dumps({"authority": {"process_bindings": {"bot": {"created_filetime": 123}}}})
    )
    monkeypatch.setenv("K98_EXPORT_RUNTIME_MANIFEST", str(manifest))
    monkeypatch.setattr(diagnostic.os, "getpid", lambda: 42)
    caplog.set_level(logging.INFO, logger=diagnostic.__name__)
    root = tmp_path / "app"
    (root / "logs").mkdir(parents=True)
    log = root / "logs/log.txt"
    log.write_bytes(b"")
    config = {"root": str(root), "release_id": "release"}
    journal = {
        "bindings": {"bot": {"pid": 42, "created_filetime": 123}},
        "publication": {"manifests": {"bot": hashlib.sha256(manifest.read_bytes()).hexdigest()}},
    }
    start = dict(
        release_id="release",
        requested_utc=(datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
        log_offset=0,
    )

    def publish():
        messages = [
            r.getMessage() for r in caplog.records if r.getMessage().startswith(diagnostic.MARKER)
        ]
        log.write_text("\n".join(messages) + "\n", encoding="utf-8")
        return json.loads(messages[-1].removeprefix(diagnostic.MARKER))

    return config, journal, start, log, publish


def installed_result(monkeypatch, admission):
    monkeypatch.setattr(runtime, "install_configured_runtime", lambda: object())
    diagnostic.install_startup_runtime()
    return admission[-1]()


def test_scheduled_and_deployment_use_same_settled_observation(monkeypatch, admission):
    result = installed_result(monkeypatch, admission)
    config, journal, start, _, _ = admission
    assert verifier.startup_admission_result(config, journal, start) == result
    assert result["outcome"] == "installed"
    # The scheduled bot needs no updater/start-request file to emit its result.
    assert result["created_filetime"] == journal["bindings"]["bot"]["created_filetime"]


@pytest.mark.asyncio
@pytest.mark.parametrize("fails", [False, True])
async def test_actual_ready_callback_waits_for_observation_before_registering_workers(
    monkeypatch, admission, caplog, fails
):
    # Compile the actual callback without importing/running the Discord application.
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "bot_instance.py").read_text(encoding="utf-8"))
    callback = next(
        n
        for n in tree.body
        if isinstance(n, ast.AsyncFunctionDef) and n.name == "_run_ready_runtime_services"
    )
    entered, release = threading.Event(), threading.Event()
    registrations = []

    def install():
        entered.set()
        assert release.wait(5)
        if fails:
            raise SourceConflict("original refusal")
        return object()

    def register(*_):
        observations = [
            r.getMessage() for r in caplog.records if diagnostic.MARKER in r.getMessage()
        ]
        assert len(observations) == 1
        assert json.loads(observations[0].removeprefix(diagnostic.MARKER))["outcome"] == (
            "failed" if fails else "installed"
        )
        registrations.append(True)

    monkeypatch.setattr(runtime, "install_configured_runtime", install)
    for path in (
        "kvk.services.new_source_recovery_service.register_recovery",
        "services.export_coordination_service.register_exports",
        "services.processing_outcome_worker.register_processing_outcomes",
        "core.recovery_lifecycle.register_recovery_monitor",
    ):
        monkeypatch.setattr(path, register)
    from PIL import Image

    monkeypatch.setattr(Image, "show", Mock(), raising=False)  # Restore/delete after the callback.
    names = {
        name: Mock()
        for name in (
            "logger",
            "task_monitor",
            "bot",
            "_shutdown_once",
            "health_dashboard_task",
            "heartbeat_loop",
            "clean_old_lock_files",
            "start_usage_tracker",
            "usage_jsonl_prune_loop",
            "daily_summary",
        )
    }
    names.update(
        os=SimpleNamespace(makedirs=Mock(), getenv=lambda _, default: default),
        LOG_DIR="unused",
        monitor_loop_coro=None,
        ACTIVITY_TRACKING_ENABLED=False,
        SERVER_STATUS_ENABLED=False,
    )
    if fails:
        names["logger"].warning.side_effect = OSError("optional warning unavailable")
    exec(compile(ast.Module(body=[callback], type_ignores=[]), "bot_instance.py", "exec"), names)
    task = asyncio.create_task(names["_run_ready_runtime_services"]())
    try:
        assert await asyncio.to_thread(entered.wait, 5)
        assert not registrations
    finally:
        release.set()
    await task
    assert len(registrations) == 4


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "partial",
        "pid",
        "creation",
        "manifest",
        "stale",
        "future",
        "failed",
        "disabled",
        "duplicate",
        "failed_then_success",
        "request",
        "offset",
        "rotated",
        "oversize",
        "malformed",
    ],
)
def test_missing_failed_stale_or_ambiguous_evidence_never_reaches_sql(
    monkeypatch, admission, damage
):
    record = installed_result(monkeypatch, admission)
    config, journal, start, log, _ = admission
    pending = damage in {"missing", "partial", "pid", "creation", "manifest"}
    if damage == "pid":
        record["pid"] += 1
    if damage == "creation":
        record["created_filetime"] += 1
    if damage == "manifest":
        record["manifest_sha256"] = "0" * 64
    if damage == "stale":
        record["observed_utc"] = "2020-01-01T00:00:00+00:00"
    if damage == "future":
        record["observed_utc"] = "2999-01-01T00:00:00+00:00"
    if damage in {"failed", "disabled"}:
        record["outcome"] = damage
    raw = diagnostic.MARKER + json.dumps(record) + "\n"
    if damage == "missing":
        raw = "Logged in as bot\n[BOOT] full_startup_sequence completed successfully\n"
    if damage == "partial":
        raw = raw[:-1]
    if damage == "duplicate":
        raw *= 2
    if damage == "failed_then_success":
        raw = diagnostic.MARKER + json.dumps(dict(record, outcome="failed")) + "\n" + raw
    if damage == "request":
        start["release_id"] = "other"
    if damage == "offset":
        start["log_offset"] = True
    if damage == "rotated":
        start["log_offset"] = 999999
    if damage == "oversize":
        raw = "x" * (8 * 1024 * 1024 + 1)
    if damage == "malformed":
        raw = diagnostic.MARKER + "{bad\n"
    log.write_text(raw, encoding="utf-8")
    monkeypatch.setattr(
        verifier,
        "verify_successor_admission",
        lambda c, j: verifier.startup_admission_result(c, j, start),
    )
    sql = Mock()
    monkeypatch.setattr(verifier, "verify_sql_contracts", sql)
    with pytest.raises(verifier.PairPublicationPending if pending else ValueError):
        verifier.verify_successor_contracts(config, ADMISSION_POLICY, journal)
    sql.assert_not_called()


@pytest.mark.parametrize("sql_contracts", [False, True])
@pytest.mark.parametrize("sql_refused", [False, True])
def test_historical_successor_keeps_sql_checks_without_new_protocol(
    monkeypatch, sql_contracts, sql_refused
):
    policy = {"source_hashes": {"bot_instance.py": "b" * 64}}
    config, journal = {}, {}
    admission_check = Mock(side_effect=AssertionError("Legacy successor emits no marker"))
    error = SourceConflict("schema observation refused")
    sql = Mock(side_effect=error if sql_refused else None)
    monkeypatch.setattr(verifier, "verify_successor_admission", admission_check)
    monkeypatch.setattr(verifier, "verify_sql_contracts", sql)
    if sql_contracts and sql_refused:
        with pytest.raises(SourceConflict) as caught:
            verifier.verify_successor_contracts(config, policy, journal)
        assert caught.value is error
    else:
        verifier.verify_successor_contracts(config, policy, journal, sql_contracts=sql_contracts)
    admission_check.assert_not_called()
    if sql_contracts:
        sql.assert_called_once_with(config, policy)
    else:
        sql.assert_not_called()


def test_new_protocol_requires_settlement_even_without_sql_flag(monkeypatch):
    pending = verifier.PairPublicationPending("Admission has not settled")
    admission_check = Mock(side_effect=pending)
    sql = Mock()
    monkeypatch.setattr(verifier, "verify_successor_admission", admission_check)
    monkeypatch.setattr(verifier, "verify_sql_contracts", sql)
    with pytest.raises(verifier.PairPublicationPending) as caught:
        verifier.verify_successor_contracts({}, ADMISSION_POLICY, {}, sql_contracts=False)
    assert caught.value is pending
    admission_check.assert_called_once()
    sql.assert_not_called()


def test_old_interval_cannot_certify_new_admission(monkeypatch, admission):
    installed_result(monkeypatch, admission)
    config, journal, start, log, _ = admission
    start["log_offset"] = log.stat().st_size
    with pytest.raises(verifier.PairPublicationPending):
        verifier.startup_admission_result(config, journal, start)


@pytest.mark.parametrize("broken", ["identity", "formatter", "logger"])
@pytest.mark.parametrize("fails", [False, True])
def test_optional_observation_failure_preserves_original_outcome(
    monkeypatch, admission, broken, fails
):
    error = SourceConflict("original password=private-secret")
    result = object()
    install = Mock(side_effect=error) if fails else Mock(return_value=result)
    monkeypatch.setattr(runtime, "install_configured_runtime", install)
    if broken == "identity":
        monkeypatch.setattr(diagnostic, "_identity", Mock(side_effect=OSError("denied")))
    if broken == "formatter":
        monkeypatch.setattr(
            "services.recovery_health.failure_detail", Mock(side_effect=RuntimeError("format"))
        )
    if broken == "logger":
        monkeypatch.setattr(diagnostic.logger, "info", Mock(side_effect=OSError("log")))
    if fails:
        with pytest.raises(SourceConflict) as caught:
            diagnostic.install_startup_runtime()
        assert caught.value is error
    else:
        assert diagnostic.install_startup_runtime() is result
    assert install.call_count == 1
    assert diagnostic._attempt.get() is None


def test_failure_stage_chain_codes_and_no_secret_prose(monkeypatch, admission):
    driver_error = type("Error", (Exception,), {"__module__": "pyodbc"})

    def install():
        diagnostic.stage("application_sql_contract")
        try:
            raise driver_error("HYT00", "password=private-secret; token=private-secret (1222)")
        except Exception as original:
            raise SourceConflict(
                "Application schema observation retained for cleanup review."
            ) from original

    monkeypatch.setattr(runtime, "install_configured_runtime", install)
    with pytest.raises(SourceConflict):
        diagnostic.install_startup_runtime()
    record = admission[-1]()
    assert record["outcome"] == "failed" and record["stage"] == "application_sql_contract"
    assert record["diagnostic"]["exception_types"] == ["SourceConflict", "Error"]
    assert record["diagnostic"]["sql_numbers"] == [1222]
    assert record["diagnostic"]["sqlstates"] == ["HYT00"]
    assert record["diagnostic"]["frames"]
    assert record["diagnostic"]["chain_frames"]
    assert "private-secret" not in json.dumps(record)


class LockModel:
    owner = None


class Cursor:
    def __init__(self, model):
        self.model, self.acquisitions, self.releases = model, 0, 0

    def execute(self, sql, *params):
        assert set(params) == {RESOURCE}
        if sql.startswith("DECLARE @transaction_mode"):
            self.row = ("Exclusive" if self.model.owner is self else "NoLock", "NoLock", 2)
        elif "sys.sp_getapplock" in sql:
            assert "@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0" in sql
            self.acquisitions += 1
            if self.model.owner is None:
                self.model.owner, self.row = self, (0,)
            else:
                self.row = (-1,)
        elif "sys.sp_releaseapplock" in sql:
            assert self.model.owner is self
            self.model.owner, self.row = None, (0, "NoLock")
            self.releases += 1
        else:
            raise AssertionError("Unexpected SQL")

    def fetchone(self):
        return self.row


@pytest.mark.parametrize("first", ["updater", "bot"])
def test_actual_observer_both_arrival_orders_are_sequenced(monkeypatch, admission, first):
    config, journal, start, _, publish = admission
    model = LockModel()
    bot, updater = Cursor(model), Cursor(model)
    entered, release = threading.Event(), threading.Event()

    def install():
        diagnostic.stage("application_sql_contract")
        with schema_observation(bot):
            entered.set()
            assert release.wait(5)
        return object()

    def verify_sql(*_):
        with schema_observation(updater):
            pass

    monkeypatch.setattr(runtime, "install_configured_runtime", install)
    monkeypatch.setattr(
        verifier,
        "verify_successor_admission",
        lambda c, j: verifier.startup_admission_result(c, j, start),
    )
    monkeypatch.setattr(verifier, "verify_sql_contracts", verify_sql)
    if first == "updater":
        with pytest.raises(verifier.PairPublicationPending):
            verifier.verify_successor_contracts(config, ADMISSION_POLICY, journal)
    with ThreadPoolExecutor(max_workers=1) as pool:
        task = pool.submit(diagnostic.install_startup_runtime)
        assert entered.wait(5)
        try:
            with pytest.raises(verifier.PairPublicationPending):
                verifier.verify_successor_contracts(config, ADMISSION_POLICY, journal)
            assert updater.acquisitions == 0 and model.owner is bot
        finally:
            release.set()
        task.result(timeout=5)
    publish()
    verifier.verify_successor_contracts(config, ADMISSION_POLICY, journal)
    assert model.owner is None
    assert bot.acquisitions == bot.releases == updater.acquisitions == updater.releases == 1


def test_post_admission_worker_contention_is_one_failure_no_retry(monkeypatch, admission):
    installed_result(monkeypatch, admission)
    config, journal, start, _, _ = admission
    model = LockModel()
    worker, updater = Cursor(model), Cursor(model)
    monkeypatch.setattr(
        verifier,
        "verify_successor_admission",
        lambda c, j: verifier.startup_admission_result(c, j, start),
    )

    def verify_sql(*_):
        with schema_observation(updater):
            pass

    monkeypatch.setattr(verifier, "verify_sql_contracts", verify_sql)
    with schema_observation(worker):
        with pytest.raises(SourceConflict, match="busy or refused"):
            verifier.verify_successor_contracts(config, ADMISSION_POLICY, journal)
        assert updater.acquisitions == 1 and updater.releases == 0 and model.owner is worker
    assert model.owner is None


@pytest.fixture(scope="module")
def packaged_tools(tmp_path_factory):
    root = tmp_path_factory.mktemp("admission-tools")
    result = package(root / "package")
    installer = Path(result["installer"]).read_text()
    encoded = re.search(r"\$encoded='([A-Za-z0-9+/=]+)'", installer)[1]
    payload = json.loads(base64.b64decode(encoded))
    tools = root / "tools"
    tools.mkdir()
    for name, data in payload.items():
        (tools / name).write_bytes(base64.b64decode(data))
    manifest = json.loads((tools / "update-tool.json").read_bytes())
    for name, expected in manifest["files"].items():
        assert hashlib.sha256((tools / name).read_bytes()).hexdigest() == expected
    return tools


@pytest.mark.parametrize(
    "case,code,verifications,starts",
    [
        ("success", 0, 1, 1),
        ("pending_success", 0, 2, 1),
        ("timeout", 1, 2, 1),
        ("hard_failure", 1, 1, 1),
        ("verify_fresh", 10, 0, 0),
        ("verify_pending", 11, 1, 0),
        ("verify_success", 0, 1, 0),
    ],
)
def test_packaged_start_actions_bound_wait_and_never_restart(
    packaged_tools, tmp_path, case, code, verifications, starts
):
    trace = tmp_path / "trace.txt"
    trace.write_text("")
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(Path(__file__).with_name("p02_admission_update_offline.ps1")),
            str(packaged_tools / "K98-SourceUpdate.ps1"),
            case,
            str(trace),
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    events = trace.read_text().splitlines()
    assert result.returncode == code, result.stdout + result.stderr + repr(events)
    assert events.count("verify") == verifications
    assert events.count("start") == events.count("start_request") == starts
    if code != 0:
        assert "session" not in events
    if case == "hard_failure":
        assert events.count("wait") == 1


def test_packaged_verifier_correlation_imports_without_app_or_sql(
    packaged_tools, tmp_path, monkeypatch, admission
):
    record = installed_result(monkeypatch, admission)
    config, journal, start, _, _ = admission
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps([config, journal, start, record]))
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import json,runpy,sys;v=runpy.run_path(sys.argv[1]);c,j,s,r=json.load(open(sys.argv[2]));assert v['startup_admission_result'](c,j,s)==r;assert 'pyodbc' not in sys.modules;assert 'bot_config' not in sys.modules",
            str(packaged_tools / "verify_k98_update_pair.py"),
            str(fixture),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr


def test_exact_source_transition_preserves_history_and_rejects_partial_or_unknown(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    transitions = updater.reviewed_transitions()
    assert (
        hashlib.sha256(json.dumps(transitions[:92], sort_keys=True).encode()).hexdigest()
        == "dd43727c31772fae5c4945cb1e1520a219641a934d073f3b85c114bb872eaaff"
    )
    transition = transitions[-1]
    assert transition["id"] == updater.P02_ADMISSION_TRANSITION
    assert {m["path"] for m in transition["members"]} == updater.P02_ADMISSION_PATHS
    for member in transition["members"]:
        assert (
            hashlib.sha256((root / member["path"]).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            == member["after_sha256"]
        )
    raw = {
        m["path"]: (root / m["path"]).read_bytes().replace(b"\r\n", b"\n")
        for m in transition["members"]
    }
    # Mirror CI must not require a private production commit. As in the existing
    # release fixtures, use inert authenticated preimages for family selection.
    # The offline release rehearsal separately reads the actual predecessor Git blobs.
    marker = b"test-only-pinned-sha256:"
    real_hash = updater.sha256
    monkeypatch.setattr(
        updater,
        "sha256",
        lambda value: (
            value[len(marker) :].decode() if value.startswith(marker) else real_hash(value)
        ),
    )
    before = {
        member["path"]: marker + member["before_sha256"].encode()
        if member["before_sha256"] is not None
        else None
        for member in transition["members"]
    }
    read = lambda rev, p: (before if rev == "before" else raw).get(p)
    assert updater.matches_protocol_transition(transition, read, "before", "after")
    for path in raw:
        with pytest.raises(ValueError):
            updater.check_transition_inventory(
                [p for p in raw if p != path], read, "before", "after"
            )
        original = raw[path]
        raw[path] += b"\n# unknown\n"
        assert not updater.matches_protocol_transition(transition, read, "before", "after")
        raw[path] = original
