"""Read the updater's exact inventory with a restricted disposable SQL login."""

import os
from pathlib import Path
import re

import pytest
from test_export_target_containment_sql import contained_job  # noqa: F401
from test_legacy_export_closeout_sql import installed  # noqa: F401

pytestmark = pytest.mark.skipif(
    os.getenv("K98_LEGACY_CLOSEOUT_SQL") != "1", reason="Explicit disposable SQL opt-in"
)


def test_updater_reads_contained_history_without_releasing_it(installed):  # noqa: F811
    f = installed
    # Only fixture owner writes: reproduce terminal history with a closed session.
    f.owner.execute("UPDATE dbo.ExportExecutionStream SET State='target_contained'")
    f.owner.execute(
        "UPDATE dbo.ExportExecutionSession SET State='closed',ClosedUTC=SYSUTCDATETIME()"
    )
    source = (Path(__file__).parents[1] / "scripts/K98-SourceUpdate.ps1").read_text()
    query = re.search(r'\$observed=Rows \("(SELECT TOP \(129\).*?)"\)', source)[1]
    query = query.replace("'\"+$c.account+\"'", "?")
    before = tuple(f.app.execute("SELECT * FROM dbo.ExportExecutionStream").fetchone())
    cursor = f.app.execute(query, "test-account")
    rows = [
        dict(zip((c[0] for c in cursor.description), row, strict=True)) for row in cursor.fetchall()
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["State"] == "target_contained"
    assert row["SessionState"] == "closed"
    assert row["ActiveAccountKey"] is None
    assert row["SessionClosedUTC"] >= row["ClosedUTC"] >= row["CreatedUTC"]
    assert len(row["ClosureHash"]) == len(row["EventDigest"]) == 32
    assert row["ClosureReference"] is not None
    assert tuple(f.app.execute("SELECT * FROM dbo.ExportExecutionStream").fetchone()) == before
    assert f.app.execute(query, "other-account").fetchall() == []
