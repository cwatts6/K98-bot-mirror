"""Recovery activation drains exports without draining its own admin call."""

from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_runtime_composition import RuntimeLifetime


def test_two_owned_recoveries_serialize_without_waiting_for_each_other():
    runtime = RuntimeLifetime(object())
    ready = threading.Barrier(2)
    results = []

    def recover(key):
        with runtime.owned():
            ready.wait(timeout=5)
            with runtime.reconfigure(recovery=True):
                assert not runtime._calls
                results.append(key)
            assert len(runtime._calls) >= 1

    with ThreadPoolExecutor(2) as executor:
        futures = [executor.submit(recover, key) for key in (1, 2)]
        for future in futures:
            future.result(timeout=5)
    assert sorted(results) == [1, 2]
    assert not runtime._calls and not runtime._reconfiguration_calls


def test_recovery_waits_for_export_and_shutdown_waits_for_recovery():
    runtime = RuntimeLifetime(object())
    exporting, release_export = threading.Event(), threading.Event()
    activating, release_activation = threading.Event(), threading.Event()
    stopped, drained = threading.Event(), threading.Event()

    def export():
        with runtime.owned():
            exporting.set()
            assert release_export.wait(5)

    def recover():
        with runtime.owned():
            with runtime.reconfigure(recovery=True):
                activating.set()
                assert release_activation.wait(5)

    def shutdown():
        runtime.stop()
        stopped.set()
        runtime.drain()
        drained.set()

    with ThreadPoolExecutor(3) as executor:
        export_future = executor.submit(export)
        assert exporting.wait(5)
        recovery_future = executor.submit(recover)
        with runtime._condition:
            assert runtime._condition.wait_for(lambda: runtime._reconfiguration_calls, timeout=5)
        assert not activating.is_set()
        release_export.set()
        assert activating.wait(5)
        shutdown_future = executor.submit(shutdown)
        assert stopped.wait(5)
        assert not drained.is_set()
        release_activation.set()
        for future in (export_future, recovery_future, shutdown_future):
            future.result(timeout=5)
    assert drained.is_set()


def test_recovery_cannot_suspend_shared_provider_work_and_failure_restores_caller():
    runtime = RuntimeLifetime(object())
    with runtime.owned():
        with runtime.owned():
            with pytest.raises(SourceConflict, match="sole"):
                with runtime.reconfigure(recovery=True):
                    pytest.fail("shared caller was suspended")
        with pytest.raises(RuntimeError, match="activation failed"):
            with runtime.reconfigure(recovery=True):
                raise RuntimeError("activation failed")
        with runtime.owned():
            pass
    assert not runtime._calls and not runtime._reconfiguration_calls
