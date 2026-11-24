"""Authenticate the real refused publisher and preserve committed observer work."""

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path

import pytest
from test_poststate_capture_packet import qualification as qualification


@pytest.fixture
def installed(qualification):
    return importlib.import_module("poststate_installed")


@pytest.fixture
def stop():
    directory = os.environ.get("K98_P02_INSTALLED_RECEIPTS")
    if not directory:
        pytest.skip("Explicit retained installed-fixture receipts are required")
    root = Path(directory)
    return [
        json.loads((root / name).read_bytes())
        for name in (
            "integration/receipt.json",
            "integration.launch.json",
            "chain-workload/receipt.json",
            "chain-initial-contracts.json",
        )
    ]


def test_real_permission_failure_keeps_committed_observer(installed, stop):
    installed.require_stop(*stop)


@pytest.mark.parametrize(
    "damage",
    [
        "unsettled",
        "custody",
        "cleanup",
        "names",
        "apply",
        "verify",
        "child",
        "acknowledged",
        "captures",
        "generation",
        "permission",
        "connections",
        "digest",
    ],
)
def test_advanced_or_uncertain_failure_cannot_continue(installed, stop, damage):
    record, launch, worker, initial = deepcopy(stop)
    if damage == "unsettled":
        launch["settled"] = False
    elif damage == "custody":
        worker["physical_custody_retained"] = True
    elif damage == "cleanup":
        record["cleanup_failures"] = [dict(error_type="OSError")]
    elif damage == "names":
        record["original_name_restored"] = False
    elif damage == "apply":
        record["coordinator"][2]["acknowledged"] = False
    elif damage == "verify":
        record["coordinator"][-1]["result"]["deployment_id"] = "changed"
    elif damage == "child":
        record["children"].append(dict(role="consumer"))
    elif damage == "acknowledged":
        worker["publisher_response_acknowledged"] = True
    elif damage == "captures":
        worker["cases"] = []
    elif damage == "generation":
        initial["contract_result"]["application_observation"]["generation"] = 2
    elif damage == "permission":
        initial["contract_result"]["application"]["object_permissions"].append(
            dict(ObjectName="dbo.sp_ExcelOutput_ByKVK", PermissionName="EXECUTE")
        )
    elif damage == "connections":
        worker["application_cleanup"]["all_closed_by_callers"] = False
    elif damage == "digest":
        launch["receipt_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        installed.require_stop(record, launch, worker, initial)


def test_installed_continuation_binds_original_fixture(qualification):
    assert (
        qualification.chain.fixture_stamp(
            dict(
                continuation="installed-publisher-refused-20261123160455336",
                guest_directory="Q:/P02Observer/20261123170000000",
            )
        )
        == "20261123150616134"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        (0, "S11_ExportApplication_P02Qual"),
        (1, 0),
        (2, 18),
        (3, "K98_P02CaptureChain_other"),
        (4, "9DC35927-02A8-4C11-BC05-210381ECA28D"),
    ],
)
def test_operational_publisher_rejects_wrong_actor_or_database(qualification, field, value):
    module = importlib.import_module("poststate_publisher")
    row = [r"MINI_AMD\K98LabAdmin", 1, 27, "ROK_TRACKER", "6A0068DA-C67F-4A8C-A934-C2FEB49EDF2E"]
    module.require_identity(row)
    row[field] = value
    with pytest.raises(ValueError):
        module.require_identity(row)


def test_installed_migration_history_uses_original_commit(qualification, stop):
    from cost_resume import require_history

    result = stop[0]["coordinator"][-1]["result"]
    history = [
        dict(
            MigrationId=result["migration_id"],
            ChecksumSha256=result["profile_sha256"],
            GitCommit=result["sql_commit"],
            DeploymentId=result["deployment_id"],
            Status="Applied",
        )
    ]
    require_history(history, [], "ON", stop[0])
    history[0]["DeploymentId"] = "changed"
    with pytest.raises(ValueError):
        require_history(history, [], "ON", stop[0])


@pytest.mark.parametrize("damage", ["none", "active", "blocked", "account", "preparation"])
def test_existing_idle_global_resource_is_retained(qualification, damage):
    from poststate_continue import require_unstarted_capture

    resources = [
        dict(
            ResourceKey="sql_snapshot:legacy_outputs",
            blocked=0,
            ActiveJobID=None,
            ActivePreparationID=None,
            ActiveOutputOperationID=None,
            OwnerID=None,
            Fence=30,
            Version=80,
        )
    ]
    preparations = []
    if damage == "active":
        resources[0]["ActivePreparationID"] = "held"
    elif damage == "blocked":
        resources[0]["blocked"] = 1
    elif damage == "account":
        resources.append(dict(ResourceKey="account:already-started"))
    elif damage == "preparation":
        preparations.append(dict(State="captured"))
    if damage == "none":
        require_unstarted_capture(preparations, resources)
    else:
        with pytest.raises(ValueError):
            require_unstarted_capture(preparations, resources)


@pytest.mark.parametrize("fault", ["none", "cursor_close", "sql_and_progress"])
def test_publisher_keeps_original_custody_and_failure(qualification, monkeypatch, tmp_path, fault):
    from contextlib import contextmanager
    from types import SimpleNamespace

    module = importlib.import_module("poststate_publisher")
    state = importlib.import_module("publisher_state")
    worker = importlib.import_module("publisher_worker")
    owner = importlib.import_module("poststate_owner")
    from core import sql_connection_custody as custody

    events, retained = [], []
    original = RuntimeError("original publisher SQL failure")
    close_error = OSError("unconfirmed cursor close")
    row = (r"MINI_AMD\K98LabAdmin", 1, 27, "ROK_TRACKER", "6A0068DA-C67F-4A8C-A934-C2FEB49EDF2E")

    class Cursor:
        fetched = False

        def execute(self, sql):
            assert sql == module.IDENTITY
            events.append("identity")

        def fetchone(self):
            if self.fetched:
                return None
            self.fetched = True
            return row

        def nextset(self):
            return False

        def close(self):
            events.append("cursor-close")
            if fault == "cursor_close":
                raise close_error

    class Connection:
        closed = False

        def cursor(self):
            return Cursor()

        def close(self):
            events.append("connection-close")
            self.closed = True

    class Factory:
        def __init__(self):
            self.items = []

        def __call__(self):
            connection = Connection()
            self.items.append(connection)
            return connection

        def finish(self):
            return dict(
                safe_to_exit=not retained, all_closed_by_callers=all(c.closed for c in self.items)
            )

    factory = Factory()
    monkeypatch.setattr(module, "operational_connections", lambda: factory)
    monkeypatch.setattr(
        custody, "retain_connection", lambda value, **kwargs: retained.append(value)
    )

    @contextmanager
    def owned(*args, **kwargs):
        events.append("readback")
        yield SimpleNamespace()

    monkeypatch.setattr(owner, "owned", owned)
    monkeypatch.setattr(state, "read", lambda owner: dict(generation=1))
    monkeypatch.setattr(state, "require_delta", lambda before, after, index: events.append("delta"))

    def publish(connect, operation, record, save):
        connection = connect()
        events.append("publish")
        connection.close()
        if fault == "sql_and_progress":
            raise original
        return dict(response_acknowledged=True)

    monkeypatch.setattr(worker, "run", publish)
    record = dict(cleanup_failures=[])

    def save():
        if fault == "sql_and_progress" and "publish" in events:
            raise OSError("evidence unavailable")

    if fault == "none":
        assert module.run(tmp_path, dict(publisher_operation="fresh"), record, save)[
            "response_acknowledged"
        ]
        assert events == [
            "readback",
            "identity",
            "cursor-close",
            "publish",
            "connection-close",
            "readback",
            "delta",
        ]
    else:
        with pytest.raises(type(close_error if fault == "cursor_close" else original)) as caught:
            module.run(tmp_path, dict(publisher_operation="fresh"), record, save)
        assert caught.value is (close_error if fault == "cursor_close" else original)
        if fault == "cursor_close":
            assert events == ["readback", "identity", "cursor-close"]
            assert retained and qualification.physical.HELD == [factory]
        else:
            assert not qualification.physical.HELD
            assert (tmp_path / "publisher-after.json").exists()
