"""Exercise the observer seed CLI's ownership and restart sequence.

SQL transport, Windows custody and the three-contract comparator are controlled
boundaries here. Native all-contract evidence is recorded separately; these
tests establish the actual main/receipt/binder/write ordering and retained state.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from core import sql_connection_custody as custody
from kvk.dal.new_source_import_dal import SourceConflict
from scripts import recovery_release_seed as seed
from tests.test_observer_contract_selection import approved  # noqa: F401
from tests.test_observer_release_issuance import issuance  # noqa: F401


@pytest.fixture
def owner(monkeypatch, tmp_path, issuance):  # noqa: F811
    from core import export_startup_windows as windows
    from kvk.dal import new_source_admin_dal
    from scripts import prepare_k98_update as preparer

    release, bot, receipt = deepcopy(issuance)
    policy = dict(
        source_hashes={},
        flags={},
        state_directory=str(tmp_path / "state"),
        predecessor={},
        seed_plan={"path": str(tmp_path / "plan.json")},
    )
    candidate = {
        "bot-template.json": seed.encode(bot),
        "AutomaticStartupPolicy.json": seed.encode(policy),
    }
    config = dict(
        **release,
        root=str(tmp_path),
        sid="test-boundary",
        new_policy=policy,
        recovery_seed="live_sql_observation_v1",
        seed_members=[
            {"name": n, "sha256": hashlib.sha256(b).hexdigest()} for n, b in candidate.items()
        ],
    )
    for name, raw in candidate.items():
        (tmp_path / name).write_bytes(raw)
    bindings = tmp_path / "bindings.json"
    bindings.write_bytes(seed.encode(config))
    args = ["seed", "--bindings", str(bindings), "--sha256", seed.checksum(config), "--create"]
    state = SimpleNamespace(
        receipt=receipt,
        events=[],
        connections=[],
        failure=None,
        observation={"collection": 1},
        args=args,
        root=tmp_path,
        candidate=candidate,
        config=config,
    )

    class Cursor:
        def __init__(self, connection):
            self.connection = connection
            self.description = [(key,) for key in receipt]

        def execute(self, statement, *parameters):
            state.events.append("receipt_read")
            assert parameters
            self.value = deepcopy(state.receipt)
            for field in ("sequence_created", "sequence_modified"):
                self.value[field] = datetime.fromisoformat(self.value[field])
            self.value["deployment_id"] = self.value["deployment_id"].upper()
            return self

        def fetchall(self):
            return [tuple(self.value.values())]

        def close(self):
            state.events.append("cursor_closed")

    class Connection:
        def __init__(self):
            self.autocommit = False
            self.timeout = 0
            self.closed = False

        def cursor(self):
            return Cursor(self)

        def close(self):
            state.events.append("connection_close")
            if state.failure == "close":
                raise OSError("physical connection closure unconfirmed")
            self.closed = True

    def connect(*, sql_profile):
        assert sql_profile == "application"
        state.events.append("connect")
        connection = Connection()
        state.connections.append(connection)
        return connection

    def verify(bound):
        state.events.append("three_contracts")
        assert state.connections[-1].closed
        assert (
            bound["application_sql_contract"]["observation_installation"]["sequence_object_id"]
            == receipt["sequence_object_id"]
        )
        if state.failure == "comparison":
            raise SourceConflict("controlled full-comparison refusal")
        return deepcopy(state.observation)

    def derive(bound_files, collected):
        state.events.append("derive")
        bound = json.loads(bound_files["bot-template.json"])
        assert "observation_installation" in bound["application_sql_contract"]
        assert collected["collection"] == 1
        return bound_files

    monkeypatch.setattr(seed.sys, "argv", args)
    monkeypatch.setattr(seed, "sys", SimpleNamespace(flags=SimpleNamespace(isolated=1)))
    monkeypatch.setattr(windows, "administrative_path", lambda path, **_: Path(path))
    monkeypatch.setattr(new_source_admin_dal, "configured_connection", connect)
    monkeypatch.setattr(
        seed, "load_release_verifier", lambda _: {"verify_bot_sql_contracts": verify}
    )
    # Only comparator/derivation contents are controlled; the observer DAL,
    # physical owner, strict binder, retained-proof checks and file loop are real.
    monkeypatch.setattr(seed, "verified_seed", derive)
    writers = preparer.output_writers
    monkeypatch.setattr(
        preparer, "output_writers", lambda sid, **_: writers(sid, secure_output=False)
    )
    return state


def test_observer_cli_closes_receipt_before_comparison_and_retains_proof(owner):
    assert seed.main() == 0
    assert owner.events[:5] == [
        "connect",
        "receipt_read",
        "cursor_closed",
        "connection_close",
        "three_contracts",
    ]
    proof_path = owner.root / "verified-seed/sql-evidence.json"
    retained = proof_path.read_bytes()
    proof = json.loads(retained)
    assert proof["observer_release"] == owner.receipt
    assert proof["collected"] == owner.observation
    owner.observation = {"collection": 2}
    owner.args.remove("--create")
    assert seed.main() == 0
    assert proof_path.read_bytes() == retained
    assert all(connection.closed for connection in owner.connections)
    assert (owner.root / "bot-template.json").read_bytes() == owner.candidate["bot-template.json"]


@pytest.mark.parametrize("failure", ["close", "comparison", "receipt"])
def test_observer_cli_failure_cannot_publish_seed(owner, failure):
    owner.failure = failure
    if failure == "receipt":
        owner.receipt["deployment_status"] = "Failed"
    expected = custody.SqlCleanupUnknown if failure == "close" else SourceConflict
    with pytest.raises(expected):
        seed.main()
    assert not (owner.root / "verified-seed").exists()
    assert "derive" not in owner.events
    if failure in ("close", "receipt"):
        assert "three_contracts" not in owner.events
    if failure == "close":
        assert custody.connection_retained(owner.connections[-1])
        with pytest.raises(custody.SqlCleanupUnknown):
            custody.require_sql_admission()
    else:
        assert all(connection.closed for connection in owner.connections)


def test_observer_cli_restart_refuses_a_different_linked_commit(owner):
    assert seed.main() == 0
    directory = owner.root / "verified-seed"
    retained = {path.name: path.read_bytes() for path in directory.iterdir()}
    owner.receipt["deployment_id"] = str(uuid4())
    with pytest.raises(ValueError, match="fresh committed read"):
        seed.main()
    assert {path.name: path.read_bytes() for path in directory.iterdir()} == retained
    assert all(connection.closed for connection in owner.connections)


@pytest.mark.parametrize("fail_at", [1, 2, 4])
def test_observer_cli_interrupted_publication_preserves_first_proof(owner, monkeypatch, fail_at):
    original = Path.rename
    calls = 0

    def interrupted(path, target):
        nonlocal calls
        calls += 1
        if calls == fail_at:
            raise OSError("publication interrupted")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(OSError, match="publication interrupted"):
        seed.main()
    proof_path = owner.root / "verified-seed/sql-evidence.json"
    retained = proof_path.read_bytes() if proof_path.exists() else None
    monkeypatch.setattr(Path, "rename", original)
    assert seed.main() == 0
    if retained is not None:
        assert proof_path.read_bytes() == retained
    assert all(connection.closed for connection in owner.connections)
