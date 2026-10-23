"""Exercise the paged request/event join against disposable local SQL tables."""

import os
from uuid import uuid4

import pytest

from services.export_execution_dal import ExportExecutionDAL
from tests.test_import_capture_recovery_sql import recovery as recovery

pytestmark = [
    pytest.mark.skipif(
        os.getenv("K98_RECOVERY_SQL_TEMP_TESTS") != "1", reason="Disposable SQL opt-in required"
    ),
    pytest.mark.parametrize("recovery", ["configuration_continuation"], indirect=True),
]


def test_sql_pages_match_individual_reads_and_exclude_other_stream(recovery):
    streams = [str(uuid4()), str(uuid4())]
    connection = recovery.connect()
    try:
        cursor = connection.cursor()
        for stream, count in zip(streams, [65, 1], strict=True):
            for sequence in range(1, count + 1):
                request = str(uuid4())
                cursor.execute(
                    "INSERT dbo.ExportProviderRequest "
                    "(RequestID,StreamID,Sequence,Operation,RequestKind,TargetID,PayloadHash,PayloadReference,CreatedUTC) "
                    "VALUES (?,?,?,'drive.files.get','read','file-a',?,?,SYSUTCDATETIME())",
                    request,
                    stream,
                    sequence,
                    b"p" * 32,
                    str(uuid4()),
                )
                for number, state in enumerate(["prepared", "dispatch_intent", "succeeded"], 1):
                    cursor.execute(
                        "INSERT dbo.ExportProviderRequestEvent "
                        "(EventID,RequestID,EventSequence,State,EvidenceHash,EvidenceReference,CreatedUTC) "
                        "VALUES (?,?,?,?,?,?,SYSUTCDATETIME())",
                        str(uuid4()),
                        request,
                        number,
                        state,
                        b"e" * 32,
                        str(uuid4()),
                    )
        connection.commit()
    finally:
        connection.close()
    dal = ExportExecutionDAL(recovery.connect)
    records = list(dal.request_records(streams[0]))
    assert len(records) == 65
    assert [identifier for identifier, _, _ in records] == list(dal.request_ids(streams[0]))
    for identifier, request, events in records:
        assert (request, events) == dal.read_request(identifier)
        assert str(request["StreamID"]).lower() == streams[0]
        assert len(events) == 3
