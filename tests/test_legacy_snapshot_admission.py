"""Original refusal facts survive without producer replay or guessed holders."""

from unittest.mock import Mock

import pytest

from services.export_contention import sql_error_facts
from services.legacy_snapshot_admission import SnapshotAdmissionRefused, acquire_snapshot_guard


@pytest.mark.parametrize("result", [-1, -2, -3, -999])
def test_exact_native_refusal_is_attributed_once_and_redacted(result):
    original = Exception(
        "42000",
        f"private K98_SNAPSHOT_ADMISSION result={result} session=73 xact=0 count=0 (51421) (SQLExecDirectW)",
    )
    cursor = Mock()
    cursor.execute.side_effect = original
    with pytest.raises(SnapshotAdmissionRefused) as caught:
        acquire_snapshot_guard(cursor)
    assert caught.value.__cause__ is original
    facts = sql_error_facts(caught.value)
    assert facts["applock_result"] == result
    assert facts["sql_session_id"] == 73
    assert facts["holder_identity"] == "unknown"
    assert "private" not in str(facts)
    assert "transaction_released" not in facts
    cursor.execute.assert_called_once()


@pytest.mark.parametrize(
    "error",
    [
        Exception("42000", "Legacy snapshot busy (51421)"),
        Exception("08S01", "K98_SNAPSHOT_ADMISSION result=-1 session=73 xact=0 count=0 (51421)"),
        OSError("lost reply"),
    ],
)
def test_unknown_or_transport_failure_preserves_original_without_retry(error):
    cursor = Mock()
    cursor.execute.side_effect = error
    with pytest.raises(type(error)) as caught:
        acquire_snapshot_guard(cursor)
    assert caught.value is error
    cursor.execute.assert_called_once()
