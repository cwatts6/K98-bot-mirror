"""A verified absent retry preserves, rather than recreates, its old quarantine."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.source_output_pool_dal import record_export_parts


@pytest.mark.parametrize(
    "existing,delayed,accepted",
    [
        (True, True, True),
        (False, True, False),
        (True, False, False),
    ],
)
def test_absent_retry_requires_original_quarantine_and_no_delayed_effect(
    monkeypatch, existing, delayed, accepted
):
    cursor = Mock()
    pool = dict(PoolID="pool", PoolState="active")
    event = dict(JobID="job", AttemptID="attempt", PartNo=1, FileID="index")
    monkeypatch.setattr(
        "kvk.dal.source_output_pool_dal.one",
        Mock(
            side_effect=[
                pool,
                dict(SequenceNo=1),
                None,
                event if existing else None,
            ]
        ),
    )
    claim = SimpleNamespace(job_id="job", owner_id="owner", fence=4)
    job = dict(AccountKey="account", KVK_NO=1, PoolEpoch=1)
    args = (cursor, job, claim, "attempt", [dict(file_id="index", role="index")])
    proof = dict(
        state="absent", writer_terminated=True, evidence_id="proof", no_delayed_effect=delayed
    )
    if accepted:
        record_export_parts(*args, action="quarantine", damage_proof=proof)
    else:
        with pytest.raises(SourceConflict):
            record_export_parts(*args, action="quarantine", damage_proof=proof)
    assert all(call.args[0].startswith("SELECT") for call in cursor.execute.call_args_list)
