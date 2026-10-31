"""Guided shared-workbook recovery against temporary SQL and recorded reads."""

from copy import deepcopy
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.schemas.new_source_schema import SOURCE_KEY
from services.export_configuration_preflight_dal import ConfigurationPreflightDAL
from services.export_execution_protocol import ProviderRequest
from services.export_replacement_configuration import CONFIGURATION_TABS
from services.export_replacement_verification_service import ReplacementVerificationService
from services.legacy_export_snapshot_service import LegacyExportRuntime
from tests import test_export_target_containment as authority_fixture
from tests.configuration_preflight_sql_fixture import install_preflight_tables
from tests.test_export_enrollment_service import FakeChild
from tests.test_export_replacement_configuration import (
    COMPLETE_CONFIGURATION,
    configuration_responses,
)
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
    install_preflight_tables(monkeypatch, r.f)
    r.failure_tab = None
    r.configuration_rows = deepcopy(COMPLETE_CONFIGURATION)

    class Child(FakeChild):
        def execute(self, message):
            typed = ProviderRequest.parse(message, enrollment=True)
            r.runtime.sent.append(typed)
            metadata, responses = configuration_responses(
                r.runtime.plan, typed.target, rows_by_tab=r.configuration_rows
            )
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


def test_invalid_configuration_is_guided_discarded_fixed_and_checked(shared):
    r = shared
    r.configuration_rows["KVK_CampMap"][0][2] = 9
    row = apply(r, "verify_replacements")
    assert "CampID" in row["evidence"]["explanation"]
    assert "activate_replacements" not in row["evidence"]["actions"]
    apply(r, "discard_replacement_check")
    r.configuration_rows["KVK_CampMap"][0][2] = 8
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    assert apply(r, "activate_replacements")["evidence"]["outcome"] == "publication_required"


def test_official_target_conflict_guides_copy_correction_and_new_check(shared):
    r = shared
    r.f.sql.execute("INSERT #KingdomScanData4 VALUES (103)")
    r.f.sql.execute("INSERT #KVK_Target_Publication VALUES (42,'OFFICIAL',103,103,1)")
    r.f.sql.commit()
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "configuration_attention"
    assert "scan 103" in row["evidence"]["explanation"]
    assert "activate_replacements" not in row["evidence"]["actions"]
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 0
    r.configuration_rows["ProcConfig"][0][2] = 103
    page = r.recovery.input_page(ACTOR, row["IncidentID"], "choose_replacements")
    r.recovery.save_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        page["draft_version"],
        0,
        {"owner_email": "owner@example.com", "old-file": "fresh-file"},
    )
    preview = r.recovery.input_confirmation(ACTOR, row["IncidentID"], "choose_replacements")
    r.recovery.execute_input(
        ACTOR,
        row["IncidentID"],
        row["Revision"],
        row["EvidenceHash"],
        "choose_replacements",
        preview["draft_version"],
    )
    row = apply(r, "verify_replacements")
    assert row["evidence"]["outcome"] == "activation_required"
    assert apply(r, "activate_replacements")["evidence"]["outcome"] == "publication_required"


def test_activation_rechecks_sql_after_the_admin_review(shared):
    r = shared
    apply(r, "verify_replacements")
    state = r.workflow._state(r.f.job)
    r.f.sql.execute("INSERT #KVK_Target_Publication VALUES (42,'OFFICIAL',103,103,1)")
    r.f.sql.commit()
    with pytest.raises(SourceConflict, match="official targets"):
        r.workflow.activation.apply(
            state["proposal"]["replacement_id"],
            state["check"]["verification_id"],
            token=state["check"]["token"],
            actor="recovery:" + str(uuid4()),
            reason="Admin reviewed prior state",
        )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 0


@pytest.mark.parametrize(
    "fault", ["no_fight", "null_symmetry", "timestamps", "ambiguous", "closed"]
)
def test_source_prerequisites_are_checked_without_creating_requests(shared, fault):
    from services.export_replacement_configuration import CONFIGURATION_COLUMNS

    r = shared
    tables = {
        tab: [dict(zip(CONFIGURATION_COLUMNS[tab], row, strict=True)) for row in records]
        for tab, records in COMPLETE_CONFIGURATION.items()
    }
    period, config = str(uuid4()), str(uuid4())
    r.f.sql.execute(
        "INSERT #SeasonSource (KVK_NO,SourceKey,SeasonState,ChoiceID,ChosenBy,ChosenUTC,"
        "Reason,ProvenanceJson,SeasonVersion) "
        "VALUES (42,?,?,NEWID(),'test',SYSUTCDATETIME(),'temporary fixture','{}',1)",
        SOURCE_KEY,
        "closed" if fault == "closed" else "open",
    )
    r.f.sql.execute(
        "INSERT #SourcePeriod VALUES (?,?,42,'pass4',?)",
        period,
        SOURCE_KEY,
        "no_fight" if fault in {"no_fight", "null_symmetry"} else "fight",
    )
    r.f.sql.execute("INSERT #SourceConfigVersion VALUES (?,?,42,1)", config, SOURCE_KEY)
    r.f.sql.execute(
        "INSERT #SourceWindowConfig VALUES (?,?,42,'pass4','Pass 4',102,103)", config, SOURCE_KEY
    )
    if fault == "null_symmetry":
        tables["KVK_Windows"][0]["StartScanID"] = None
    elif fault == "ambiguous":
        r.f.sql.execute(
            "INSERT #SourcePeriod VALUES (?,?,42,'pass4','fight')", str(uuid4()), SOURCE_KEY
        )
    elif fault == "timestamps":
        for scan, stamp in [(102, "2026-10-15"), (103, "2026-10-14")]:
            observation = str(uuid4())
            r.f.sql.execute("INSERT #SourceObservation VALUES (?,?)", observation, stamp)
            r.f.sql.execute(
                "INSERT #SourceLogicalScan VALUES (?,42,?,?)", SOURCE_KEY, scan, observation
            )
    r.f.sql.commit()
    with pytest.raises(SourceConflict):
        ConfigurationPreflightDAL(r.f.connect).inspect(
            tables, source_recovery=True, source_intake=False
        )
    assert r.f.sql.execute("SELECT COUNT(*) FROM #SourceConfigRequest").fetchval() == 0


@pytest.mark.parametrize("mode", ["windows", "weights", "unchanged_closed_weights"])
def test_valid_source_preflight_does_not_create_configuration_requests(shared, mode):
    from services.export_replacement_configuration import CONFIGURATION_COLUMNS

    r = shared
    tables = {
        tab: [dict(zip(CONFIGURATION_COLUMNS[tab], row, strict=True)) for row in records]
        for tab, records in COMPLETE_CONFIGURATION.items()
    }
    period, config = str(uuid4()), str(uuid4())
    state = "closed" if mode == "unchanged_closed_weights" else "open"
    r.f.sql.execute(
        "INSERT #SeasonSource (KVK_NO,SourceKey,SeasonState,ChoiceID,ChosenBy,ChosenUTC,"
        "Reason,ProvenanceJson,SeasonVersion) "
        "VALUES (42,?,?,NEWID(),'test',SYSUTCDATETIME(),'temporary fixture','{}',1)",
        SOURCE_KEY,
        state,
    )
    r.f.sql.execute("INSERT #SourcePeriod VALUES (?,?,42,'pass4','fight')", period, SOURCE_KEY)
    r.f.sql.execute("INSERT #SourceConfigVersion VALUES (?,?,42,1)", config, SOURCE_KEY)
    r.f.sql.execute(
        "INSERT #SourceWindowConfig VALUES (?,?,42,'pass4','Pass 4',102,103)", config, SOURCE_KEY
    )
    if mode == "unchanged_closed_weights":
        r.f.sql.execute("INSERT #SourceWeightConfig VALUES (?,0.125,2,3)", config)
    r.f.sql.commit()
    result = ConfigurationPreflightDAL(r.f.connect).inspect(
        tables, source_recovery=mode == "windows", source_intake=mode != "windows"
    )
    assert result["source_periods_checked"] == 1
    assert r.f.sql.execute("SELECT COUNT(*) FROM #SourceConfigRequest").fetchval() == 0


def test_empty_details_and_blank_procconfig_cells_use_retained_sql(shared):
    from services.export_replacement_configuration import CONFIGURATION_COLUMNS

    r = shared
    tables = {name: [] for name in CONFIGURATION_COLUMNS}
    tables["ProcConfig"] = [dict(KVK_NO="42", MATCHMAKING_SCAN=None, DRAFTSCAN=None)]
    r.f.sql.execute("INSERT #KVK_Details VALUES (43)")
    r.f.sql.execute("INSERT #ProcConfig VALUES (43,'MATCHMAKING_SCAN',101)")
    r.f.sql.execute("INSERT #KVK_Target_Publication VALUES (43,'OFFICIAL',101,101,1)")
    r.f.sql.commit()
    result = ConfigurationPreflightDAL(r.f.connect).inspect(
        tables, source_recovery=False, source_intake=False
    )
    assert result["season"] == 43 and result["selected_scan"] == 101
    assert "KVK_Details" in result["empty_tabs_retain_sql"]


@pytest.mark.parametrize("token", ["42", "+42", " 42 ", "0042", "2147483647"])
def test_accepted_procconfig_text_round_trips_through_sql_integer_staging(shared, token):
    from services.export_configuration_values import numeric_value

    expected = numeric_value("ProcConfig", "KVK_NO", token)
    shared.f.sql.execute("CREATE TABLE #ConfigurationIntegerCheck (Value int NOT NULL)")
    shared.f.sql.execute("INSERT #ConfigurationIntegerCheck VALUES (?)", token)
    assert (
        shared.f.sql.execute("SELECT Value FROM #ConfigurationIntegerCheck").fetchval() == expected
    )
