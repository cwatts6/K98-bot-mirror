"""Real caller cleanup separates deferred observation from uncertain publication."""

from inspect import unwrap
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from core import sql_connection_custody as custody
import kvk_all_importer
import player_stats_cache
import proc_config_import
from services import legacy_export_snapshot_service as service
from services.catalogue_observation_dal import ObservationDeferred
from tests.test_legacy_export_snapshot import producer_runtime


@pytest.mark.parametrize(
    "actor,fault",
    [
        ("player", None),
        ("player", "rollback"),
        ("player", "cursor_close"),
        ("all_kvk", None),
        ("all_kvk", "connection_close"),
        ("configuration", None),
        ("configuration", "cursor_close"),
        ("configuration", "connection_close"),
        ("admin", None),
        ("admin", "rollback"),
        ("admin", "connection_close"),
    ],
)
def test_actual_entry_deferral_settles_only_after_confirmed_cleanup(
    tmp_path, monkeypatch, actor, fault
):
    kind = "scan_data" if actor in {"player", "configuration"} else "all_kvk"
    runtime, dal = producer_runtime(
        tmp_path,
        configuration={
            kind: dict(consumer=kind, kvk_no=7, destinations=["file-a"]),
        },
    )
    error = ObservationDeferred("generation_changed")
    dal.verify_producer_cursor.side_effect = error
    connection = Mock(autocommit=False, timeout=15)
    cursor = connection.cursor.return_value
    cursor.connection = connection
    if fault == "rollback":
        connection.rollback.side_effect = OSError("rollback acknowledgement lost")
    elif fault == "cursor_close":
        cursor.close.side_effect = OSError("cursor close acknowledgement lost")
    elif fault == "connection_close":
        connection.close.side_effect = OSError("connection close acknowledgement lost")

    business = Mock(side_effect=AssertionError("Business work must not enter"))
    dal.begin_producer_transaction = business
    monkeypatch.setattr(
        kvk_all_importer.kvk_all_import_dal, "connect_sql_server", lambda **kw: connection
    )
    if actor == "configuration":
        monkeypatch.setattr(proc_config_import, "_validate_import_config", lambda: (True, []))
        monkeypatch.setattr(
            proc_config_import, "_get_import_connection_with_retry", lambda: connection
        )
        monkeypatch.setattr(proc_config_import, "_set_last_import_report", Mock())
        phase = Mock()
        monkeypatch.setattr(proc_config_import, "attempt_phase", phase)
        inputs = Mock(return_value=(pd.DataFrame({"KVK_NO": [7]}), {}))
        monkeypatch.setattr(service, "read_configuration", inputs)
        monkeypatch.setattr(proc_config_import, "write_df_to_staging_and_upsert", business)
    if actor == "admin":
        from kvk.dal import kvk_admin_dal

        monkeypatch.setattr(kvk_admin_dal, "get_conn_with_retries", lambda: connection)

    def run():
        if actor == "configuration":
            return unwrap(proc_config_import.run_proc_config_import)()
        if actor == "all_kvk":
            return kvk_all_importer._ingest_validated_workbook(
                prepared=SimpleNamespace(
                    dataframe=None, staged_rows=1, sheet_name="Full Data", schema_metadata={}
                ),
                content=b"",
                source_filename="new-test.xlsx",
                uploader_id=1,
                scan_ts_utc=None,
                server="fixture",
                database="fixture",
                username="fixture",
                password="fixture",
            )
        if actor == "admin":
            return kvk_admin_dal.recompute_windows(7)
        with service.writer_scope("scan_data"):
            return unwrap(player_stats_cache._execute_sp_with_retries)(connection, retries=1)

    with service.use_runtime(runtime):
        if actor == "configuration" and not fault:
            ok, report = run()
            assert not ok and report["recovery_status"] == "configuration_observation_deferred"
            inputs.assert_called_once()
            assert all(c.args != ("writes_may_start",) for c in phase.call_args_list)
        else:
            with pytest.raises(
                custody.SqlCleanupUnknown if fault else ObservationDeferred
            ) as caught:
                run()
            if not fault:
                assert caught.value is error

    unavailable = [
        c for c in dal.transition.call_args_list if c.kwargs.get("state") == "unavailable"
    ]
    if fault:
        assert not unavailable
        assert custody.connection_retained(connection)
        assert not any(
            c.kwargs.get("release") and c.kwargs.get("expected") != "preflight"
            for c in dal.transition.call_args_list
        )
    else:
        assert len(unavailable) == 1 and unavailable[0].kwargs["release"] is True
        dal.uncertain.assert_not_called()
        if actor == "player":
            connection.rollback.assert_called_once()
            cursor.close.assert_called_once()
        else:
            connection.close.assert_called_once()
    dal.request.assert_called_once()
    dal.verify_producer_cursor.assert_called_once()
    business.assert_not_called()
    runtime.capture.assert_not_called()
    dal.captured.assert_not_called()
    connection.commit.assert_not_called()
    assert not any("sp_" in str(call.args[0]) for call in cursor.execute.call_args_list)


@pytest.mark.parametrize("damage", ["connection", "error", "late_authority", "no_ack"])
def test_refusal_cannot_borrow_other_cleanup_proof(tmp_path, damage):
    runtime, dal = producer_runtime(tmp_path)
    connection = Mock()
    cursor = Mock(connection=connection)
    error = ObservationDeferred("active_writer")
    dal.verify_producer_cursor.side_effect = error
    with service.use_runtime(runtime), pytest.raises(ObservationDeferred):
        with service.writer_scope("all_kvk") as owner:
            try:
                service.verify_producer_cursor(cursor, before_side_effects=True)
            except ObservationDeferred:
                if damage == "late_authority":
                    owner.producer_authorized = True
                if damage != "no_ack":
                    service.acknowledge_observation_cleanup(
                        object() if damage == "connection" else connection,
                        ObservationDeferred("active_writer") if damage == "error" else error,
                    )
                raise
    assert not any(
        c.kwargs.get("release") and c.kwargs.get("expected") != "preflight"
        for c in dal.transition.call_args_list
    )
    dal.uncertain.assert_called_once()


def test_committed_kvk_result_survives_lost_connection_close(tmp_path, monkeypatch):
    from services.upload_outcome_service import CommittedKvkResult

    runtime, dal = producer_runtime(tmp_path)
    connection = Mock()
    connection.close.side_effect = OSError("lost close")
    result = CommittedKvkResult(success=True, committed=True, scan_id=123)
    monkeypatch.setattr(
        kvk_all_importer.kvk_all_import_dal, "connect_sql_server", lambda **kw: connection
    )
    ingest = Mock(return_value=result)
    monkeypatch.setattr(kvk_all_importer.kvk_all_import_dal, "ingest_prepared_import", ingest)
    with service.use_runtime(runtime):
        actual = kvk_all_importer._ingest_validated_workbook(
            prepared=object(),
            content=b"",
            source_filename="new-test.xlsx",
            uploader_id=1,
            scan_ts_utc=None,
            server="fixture",
            database="fixture",
            username="fixture",
            password="fixture",
        )
    assert actual is result
    assert result["success"] and result["committed"] and result["scan_id"] == 123
    assert result["capture_outcome"] == "unconfirmed"
    assert "export_preparation_id" not in result
    assert custody.connection_retained(connection)
    ingest.assert_called_once()
    runtime.capture.assert_not_called()
    dal.captured.assert_not_called()


def test_configuration_cancellation_cannot_enter_successful_capture(tmp_path, monkeypatch):
    runtime, dal = producer_runtime(
        tmp_path,
        configuration={
            "scan_data": dict(consumer="scan_data", kvk_no=7, destinations=["file-a"]),
        },
    )
    connection = Mock(autocommit=False)
    connection.cursor.side_effect = KeyboardInterrupt("cancelled before business cursor")
    monkeypatch.setattr(proc_config_import, "_validate_import_config", lambda: (True, []))
    monkeypatch.setattr(proc_config_import, "_get_import_connection_with_retry", lambda: connection)
    monkeypatch.setattr(proc_config_import, "_set_last_import_report", Mock())
    monkeypatch.setattr(
        service, "read_configuration", lambda *a, **kw: (pd.DataFrame({"KVK_NO": [7]}), {})
    )
    with service.use_runtime(runtime), pytest.raises(KeyboardInterrupt):
        unwrap(proc_config_import.run_proc_config_import)()
    connection.close.assert_called_once()
    dal.uncertain.assert_called_once()
    runtime.capture.assert_not_called()
    dal.captured.assert_not_called()
