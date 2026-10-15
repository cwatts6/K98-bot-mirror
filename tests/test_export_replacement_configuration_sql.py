"""Guided shared-workbook recovery against temporary SQL and recorded reads."""

from copy import deepcopy
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from services.export_execution_protocol import ProviderRequest
from services.export_replacement_configuration import CONFIGURATION_TABS
from services.export_replacement_verification_service import ReplacementVerificationService
from services.legacy_export_snapshot_service import LegacyExportRuntime
from tests import test_export_target_containment as authority_fixture
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_replacement_configuration import configuration_responses
from tests.test_export_replacement_guided_sql import (
    apply,
    contained_job as contained_job,
    guided as guided,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    store as store,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR


@pytest.fixture
def shared(monkeypatch, request):
    original = authority_fixture.registration_fixture

    def registration():
        value = original()
        value["legacy_configuration"]["config"]["destinations"] = ["old-file"]
        return value

    monkeypatch.setattr(authority_fixture, "registration_fixture", registration)
    r = request.getfixturevalue("guided")
    r.failure_tab = None

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message, enrollment=True)
            r.runtime.sent.append(typed)
            metadata, responses = configuration_responses(r.runtime.plan, typed.target)
            if typed.operation == "drive.files.get":
                return responses[0]
            if typed.operation == "drive.permissions.list":
                return responses[1]
            if typed.arguments.get("includeGridData") is False:
                return metadata
            title = typed.arguments["ranges"][0].split("!")[0].strip("'")
            if title == r.failure_tab:
                raise TimeoutError("Injected lost configuration read")
            index = (*CONFIGURATION_TABS, "Sheet1").index(title)
            return responses[2 + index * 2 + (typed.operation == "sheets.values.batchGet")]

    r.service.authority.host = SimpleNamespace(create_suspended=lambda key: Child(key, r.runtime))
    return r


def test_guided_configuration_copy_activation_publication_and_future_read(shared, monkeypatch):
    r = shared
    page = r.recovery.input_page(ACTOR, r.row["IncidentID"], "choose_replacements")
    assert "Configuration" in page["fields"][1]["label"]
    assert all(tab in page["fields"][1]["help"] for tab in CONFIGURATION_TABS)
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    assert "season and scan IDs" in row["evidence"]["actions"]["activate_replacements"]["check"]
    assert len(row["evidence"]["configuration_checks"]["fresh-file"]) == 7
    assert len(r.runtime.sent) == 19 and all(not req.mutation for req in r.runtime.sent)
    restarted = ReplacementVerificationService(
        dal=r.dal, authority=r.service.authority, proposals=r.service.proposals
    )
    checked = r.workflow._state(r.f.job)["check"]
    assert restarted.inspect(checked["verification_id"])["files"] == checked["files"]
    apply(r, "activate_replacements")
    row = apply(r, "publish_replacement")
    assert row["evidence"]["outcome"] == "replacement_queued"
    r.activated = r.workflow._state(r.f.job)["activation"]
    r.delivery = r.workflow.continuation
    from tests.test_export_replacement_end_to_end import prepare_publication

    prepare_publication(r)
    # Provider starts with the copied input tabs. Report execution must leave
    # their identities intact and must never target their contents.
    r.provider.grids = {
        g["sheet_id"]: dict(
            sheetId=g["sheet_id"],
            title=g["title"],
            gridProperties=dict(rowCount=g["rows"], columnCount=g["columns"]),
        )
        for g in r.activated["files"][0]["configuration_grids"]
    }
    before = deepcopy(r.provider.grids)
    r.publish()
    assert all(r.provider.grids[key] == grid for key, grid in before.items())
    assert r.recovery.review(ACTOR, row["IncidentID"])["State"] == "resolved"
    assert r.provider.rows == dict(values=[["ID", "Value"], [1, "retained"]])
    for req in r.provider.sent:
        if req.mutation:
            assert not any(tab in str(req.arguments) for tab in CONFIGURATION_TABS)
    runtime = LegacyExportRuntime.__new__(LegacyExportRuntime)
    runtime.configuration = json.dumps(r.activated["registration"]["legacy_configuration"])
    import gsheet_module
    import proc_config_import
    from services import (
        export_provider_adapter as provider,
        legacy_export_snapshot_service as legacy,
    )

    monkeypatch.setattr(legacy, "_writer_runtime", lambda: runtime)
    monkeypatch.setattr(provider, "current_provider", lambda: SimpleNamespace(execution=object()))
    reads = []

    def read(file, range, **kwargs):
        reads.append(file)
        return [["KVK_NO"], [42]]

    monkeypatch.setattr(gsheet_module, "get_sheet_values", read)
    frame = proc_config_import._read_sheet_to_df(None, "old-file", "ProcConfig!A1:J")
    assert reads == ["fresh-file"] and frame.iloc[0, 0] == 42
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportContainedTarget WHERE FileID='old-file'"
        ).fetchval()
        == 1
    )
    r.http.request.assert_not_called()


@pytest.mark.parametrize("damage", ["missing", "unknown", "padded", "numeric", "extra"])
def test_sql_rejects_unbounded_or_ambiguous_configuration_roles(shared, damage):
    import pyodbc

    r = shared
    proposal = r.workflow._state(r.f.job)["proposal"]
    value = r.workflow.plan_factory(proposal, str(uuid4())).value()
    policy = value["files"][0]
    if damage == "missing":
        del policy["kind"]
    elif damage == "extra":
        policy["unchecked"] = True
    else:
        policy["kind"] = {"unknown": "arbitrary", "padded": "configuration_output ", "numeric": 5}[
            damage
        ]
    forged = SimpleNamespace(value=lambda: value, sql_json=json.dumps(value))
    with pytest.raises(pyodbc.Error, match="role required"):
        r.begin(forged)


def test_incomplete_copy_read_is_guided_discarded_then_rechecked(shared):
    r = shared
    r.failure_tab = "ProcConfig"
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "checking_replacements"
    assert "activate_replacements" not in row["evidence"]["actions"]
    assert "discard_replacement_check" in row["evidence"]["actions"]
    row = apply(r, "discard_replacement_check")
    assert "verify_replacements" in row["evidence"]["actions"]
    r.failure_tab = None
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    assert (
        r.f.sql.execute(
            "SELECT COUNT(*) FROM #ExportReplacementVerification WHERE State='discarded'"
        ).fetchval()
        == 1
    )
