"""Attempt history is independent of SQL admission and cannot authorize replay."""

import json
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from services import configuration_attempt_recovery as module
from services.producer_recovery_intent import configuration_import_intent


@pytest.fixture
def setup_attempt(tmp_path, monkeypatch):
    from services import legacy_export_snapshot_service as snapshots

    runtime = SimpleNamespace(account="account", store=SimpleNamespace(storage_owner="store"))
    monkeypatch.setattr(snapshots, "_writer_runtime", lambda: runtime)
    journal = module.AttemptJournal(module.journal_root(tmp_path, runtime))
    sink = Mock()

    def decorate(function):
        return configuration_import_intent(
            module.record_configuration_attempt(data_dir=lambda: tmp_path, report_sink=sink)(
                function
            )
        )

    return journal, decorate, sink


def test_failure_saved_before_input_and_survives_restart_and_later_success(setup_attempt):
    journal, decorate, sink = setup_attempt

    @decorate
    def fail(dry_run):
        assert len(journal.pending()) == 1  # durable before business callback
        return False, {"errors": ["private SQL prose must not enter receipt"]}

    ok, failed = fail()

    @decorate
    def succeed(dry_run):
        module.attempt_phase("reading_inputs")
        module.attempt_phase("writes_may_start")
        return True, {"errors": []}

    assert succeed()[0]
    restarted = module.ConfigurationAttemptRecovery(module.AttemptJournal(journal.root))
    evidence, _, resolved = restarted.inspect(failed["attempt_id"])
    assert not ok and not resolved
    assert evidence["outcome"] == "failed_before_inputs"
    assert "previous configuration" in evidence["explanation"]
    assert not evidence["actions"]
    assert "private SQL" not in json.dumps(evidence)
    assert len(restarted.pending_recovery()) == 2
    assert failed["attempt_recording"] == "recorded"


def test_missing_or_corrupt_receipt_does_not_resolve(setup_attempt):
    journal, decorate, sink = setup_attempt
    _, result = decorate(lambda dry: (False, {}))()
    adapter = module.ConfigurationAttemptRecovery(journal)
    path = journal.path(result["attempt_id"])
    path.write_text("{}")
    with pytest.raises(module.SourceConflict):
        adapter.inspect(result["attempt_id"])
    path.unlink()
    with pytest.raises(FileNotFoundError):
        adapter.inspect(result["attempt_id"])


@pytest.mark.parametrize("phase", ["reading_inputs", "writes_may_start"])
def test_late_failure_never_claims_previous_configuration_retained(setup_attempt, phase):
    journal, decorate, _ = setup_attempt

    @decorate
    def fail(dry):
        module.attempt_phase(phase)
        return False, {}

    _, report = fail()
    evidence, _, resolved = module.ConfigurationAttemptRecovery(journal).inspect(
        report["attempt_id"]
    )
    assert not resolved
    assert evidence["outcome"] == "failed_after_inputs"
    assert "previous configuration" not in evidence["explanation"]


@pytest.mark.parametrize("which", ["begin", "finish", "phase"])
def test_recording_failure_is_explicit_and_never_claims_completion(
    setup_attempt, monkeypatch, which
):
    journal, decorate, sink = setup_attempt
    original = module.AttemptJournal.save
    writes = []
    calls = []

    def save(self, value):
        writes.append(value["phase"])
        if len(writes) == (1 if which == "begin" else 2):
            raise OSError("private filesystem details")
        return original(self, value)

    monkeypatch.setattr(module.AttemptJournal, "save", save)

    @decorate
    def work(dry):
        calls.append("called")
        if which == "phase":
            module.attempt_phase("reading_inputs")
        return True, {}

    if which == "phase":
        with pytest.raises(OSError):
            work()
    else:
        ok, report = work()
        assert not ok and report["attempt_recording"] == "unrecorded"
        if which == "begin":
            assert not calls
        else:
            assert report["import_reported_success"]
    if which != "begin":
        retained = journal.read(journal.pending()[0])
        assert retained["outcome"] == "unconfirmed"


def test_cancellation_retains_unconfirmed_without_retry(setup_attempt):
    journal, decorate, _ = setup_attempt
    calls = []

    @decorate
    def work(dry):
        calls.append(1)
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        work()
    assert calls == [1]
    assert journal.read(journal.pending()[0])["outcome"] == "unconfirmed"


def test_dry_run_creates_no_incident(setup_attempt):
    journal, decorate, _ = setup_attempt
    assert decorate(lambda dry: (True, {}))(dry_run=True)[0]
    assert not journal.pending()


def test_scope_isolation_and_bounded_rotating_discovery(tmp_path):
    runtime = lambda owner: SimpleNamespace(account="a", store=SimpleNamespace(storage_owner=owner))
    journal = module.AttemptJournal(module.journal_root(tmp_path, runtime("one")))
    journal.root.mkdir(parents=True)
    ids = sorted(str(uuid4()) for _ in range(121))
    for item in ids:
        journal.path(item).write_text("{}")
    assert journal.pending() == ids[:100]
    page = journal.pending(ids[99])
    assert page[:21] == ids[100:]
    assert not module.AttemptJournal(module.journal_root(tmp_path, runtime("two"))).pending()
    with pytest.raises(ValueError):
        journal.path("../outside")


@pytest.mark.asyncio
async def test_startup_false_is_failed_not_completed():
    from core import startup_diagnostics

    async def failed():
        return False

    await startup_diagnostics.run(
        failed(), 1, "proc_config_import", completion_check=module.verify_startup_import
    )
    assert (
        next(r for r in startup_diagnostics.report() if r["step"] == "proc_config_import")["state"]
        == "failed"
    )


def test_real_import_refusal_records_safe_failure_without_inputs(tmp_path, monkeypatch):
    import proc_config_import as pci
    from services import legacy_export_snapshot_service as snapshots
    from tests.test_export_contention import refusal

    monkeypatch.setattr(pci, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(pci, "_validate_import_config", lambda: (True, []))
    error = refusal()
    error.transaction_released = True
    monkeypatch.setattr(snapshots, "read_configuration", Mock(side_effect=error))
    provider, sql = Mock(), Mock()
    monkeypatch.setattr(pci, "_get_sheet_service", provider)
    monkeypatch.setattr(pci, "_get_import_connection_with_retry", sql)
    # Keep producer identity and receipt wrapper, omit only runtime composition.
    ok, report = pci.run_proc_config_import.__wrapped__()
    assert not ok
    assert report["attempt_outcome"] == "failed_before_inputs"
    assert report["admission_failure"]["transaction_released"]
    assert report["attempt_recording"] == "recorded"
    provider.assert_not_called()
    sql.assert_not_called()
