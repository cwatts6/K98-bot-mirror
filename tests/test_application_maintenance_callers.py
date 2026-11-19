"""Exercise lost schema ownership acknowledgements through actual resource owners."""

from contextlib import nullcontext
from inspect import unwrap
from types import SimpleNamespace
from unittest.mock import Mock

import pandas as pd
import pytest

from core import sql_connection_custody as custody
from kvk.dal.new_source_import_dal import transaction
import kvk_all_importer
import player_stats_cache
import proc_config_import
from services import (
    application_maintenance_dal as lifecycle,
    legacy_export_snapshot_service as legacy,
)
from tests.test_application_maintenance_contract import Cursor


class OwnedCursor(Cursor):
    def __init__(self, failure):
        super().__init__([], failure=failure)
        self.close = Mock()
        self.connection.cursor = Mock(return_value=self)
        self.connection.commit = Mock()
        self.connection.rollback = Mock()
        self.connection.close = Mock()
        self.connection.timeout = 15

    def execute(self, sql, *args):
        if sql == "SET XACT_ABORT ON; SET NOCOUNT ON;":
            self.calls.append((sql, args))
            return self
        return super().execute(sql, *args)


@pytest.mark.parametrize("failure", ["acquire", "release"])
@pytest.mark.parametrize("owner", ["configuration", "all_kvk", "source_transaction", "player"])
def test_lost_schema_acknowledgement_retains_every_producer_owner(monkeypatch, failure, owner):
    cursor = OwnedCursor(failure)
    connection = cursor.connection
    first_failure = []

    def verify(actual, **kwargs):
        try:
            with lifecycle.schema_observation(actual):
                pass
        except custody.SqlCleanupUnknown as error:
            first_failure.append(error)
            raise

    monkeypatch.setattr(legacy, "verify_producer_cursor", verify)
    business = Mock(side_effect=AssertionError("business work must not start"))
    monkeypatch.setattr(legacy, "begin_writer_transaction", business)

    if owner == "configuration":
        monkeypatch.setattr(proc_config_import, "_validate_import_config", lambda: (True, []))
        monkeypatch.setattr(
            proc_config_import, "_get_import_connection_with_retry", lambda: connection
        )
        monkeypatch.setattr(proc_config_import, "_set_last_import_report", Mock())
        monkeypatch.setattr(proc_config_import, "preflight_or_raise", business)
        monkeypatch.setattr(
            legacy, "read_configuration", lambda *a, **kw: (pd.DataFrame({"KVK_NO": [16]}), {})
        )
        monkeypatch.setattr(legacy, "writer_scope", lambda *a: nullcontext())
        success, report = unwrap(proc_config_import.run_proc_config_import)()
        assert not success and report["errors"]
    else:
        with pytest.raises(custody.SqlCleanupUnknown) as caught:
            if owner == "all_kvk":
                monkeypatch.setattr(
                    kvk_all_importer.kvk_all_import_dal,
                    "connect_sql_server",
                    lambda **kw: connection,
                )
                monkeypatch.setattr(
                    kvk_all_importer.kvk_all_import_dal,
                    "ingest_prepared_import",
                    unwrap(kvk_all_importer.kvk_all_import_dal.ingest_prepared_import),
                )
                unwrap(kvk_all_importer._ingest_validated_workbook)(
                    prepared=SimpleNamespace(
                        dataframe=None, staged_rows=1, sheet_name="Full Data", schema_metadata={}
                    ),
                    content=b"",
                    source_filename="test.xlsx",
                    uploader_id=1,
                    scan_ts_utc=None,
                    server="test",
                    database="test",
                    username="test",
                    password="test",
                )
            elif owner == "source_transaction":
                with transaction(lambda: connection) as actual:
                    verify(actual)
            else:
                monkeypatch.setattr(player_stats_cache, "current_owner", lambda: None)
                monkeypatch.setattr(player_stats_cache.time, "sleep", business)
                unwrap(player_stats_cache._execute_sp_with_retries)(connection, retries=3)
        assert caught.value is first_failure[0]

    assert len(first_failure) == 1
    assert custody.connection_retained(connection)
    assert custody.custody_snapshot() == {"admission": "closed", "unconfirmed": 1}
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()
    connection.close.assert_not_called()
    cursor.close.assert_not_called()
    business.assert_not_called()
    assert sum("sp_getapplock" in sql for sql, _ in cursor.calls) == 1
    assert sum("sp_releaseapplock" in sql for sql, _ in cursor.calls) == (failure == "release")
