"""Manual release boundaries; fixtures do not certify installed Windows ACLs."""

from copy import deepcopy
import hashlib
from pathlib import Path, PureWindowsPath
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.export_process_pair import bind_templates, publication, watchdog_launch
from services.export_execution_protocol import encode
from tests.test_export_single_account import SID, process_bindings


def pair_fixture(tmp_path, monkeypatch):
    # Validate real Windows path syntax even on Ubuntu. Only the disposable
    # fixture volume is mapped to native tmp storage; production validators
    # and all other paths remain unchanged.
    native_path = Path
    volume = PureWindowsPath("C:/K98-pair-fixture") / tmp_path.name

    def fixture_path(value, *, private=False):
        candidate = PureWindowsPath(value)
        if candidate.is_relative_to(volume):
            return native_path(tmp_path).joinpath(*candidate.relative_to(volume).parts)
        return native_path(value)

    import scripts.provision_export_process_pair as publisher
    import scripts.run_export_process_gate as gate

    monkeypatch.setattr(sys.modules[__name__], "Path", fixture_path)
    monkeypatch.setattr(publisher, "Path", fixture_path)
    monkeypatch.setattr(gate, "Path", fixture_path)
    bindings = process_bindings()
    plan = dict(
        version=1,
        source_hashes={"DL_bot.py": "b" * 64},
        application_sid=SID,
        token_profiles={role: item["token_profile"] for role, item in bindings.items()},
        python=bindings["bot"]["executable"],
        python_sha256="a" * 64,
        templates={
            role: {"path": str(volume / (role + "-template.json")), "sha256": "c" * 64}
            for role in bindings
        },
        manifests={role: str(volume / (role + ".json")) for role in bindings},
        commit_file=str(volume / "commit.json"),
    )
    authority = dict(
        version=3,
        source_hashes=deepcopy(plan["source_hashes"]),
        process_bindings=None,
        deployment_boundary={"version": 5, "host": "fixture", "process_bindings": None},
        runtime_registration={"reviewed": True},
        sql_contract={"source_expected": "fixed"},
        authority_sid=SID,
        bot_sid=SID,
        pipe_id="reviewed-pipe",
        trust_model="single_account_application_v1",
    )
    bot = dict(
        version=2,
        trust_model="single_account_application_v1",
        source_hashes=deepcopy(plan["source_hashes"]),
        registration={"reviewed": True},
        sql_contract=deepcopy(authority["sql_contract"]),
        authority={key: authority[key] for key in ("authority_sid", "bot_sid", "pipe_id")},
    )
    bot["authority"].update(host="fixture", process_bindings=None, deployment_hash=None)
    return plan, dict(authority=authority, bot=bot), bindings


def test_binding_changes_only_explicit_process_fields_and_retains_reviewed_contracts(
    tmp_path, monkeypatch
):
    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    original = deepcopy(templates)
    bound = bind_templates(plan, templates, bindings)
    assert templates == original
    assert bound["authority"]["process_bindings"] == bindings
    assert (
        bound["bot"]["authority"]["deployment_hash"]
        == hashlib.sha256(encode(bound["authority"]["deployment_boundary"])).hexdigest()
    )
    assert bound["authority"]["sql_contract"] == original["authority"]["sql_contract"]
    with pytest.raises(ValueError, match="Fresh"):
        bind_templates(plan, bound, bindings)


@pytest.mark.parametrize(
    "damage",
    [
        "elevation",
        "identity",
        "interpreter",
        "duplicate_pid",
        "source",
        "sql",
        "registration",
        "alias",
        "nested_model",
        "model",
        "host",
        "relative_path",
    ],
)
def test_binding_rejects_wrong_identity_or_changed_static_expectations(
    tmp_path, monkeypatch, damage
):
    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    if damage == "elevation":
        plan["token_profiles"]["bot"]["elevated"] = True
    elif damage == "identity":
        bindings["bot"]["token_profile"] = bindings["bot"]["token_profile"] | {"privileges": []}
    elif damage == "interpreter":
        bindings["authority"]["sha256"] = "d" * 64
    elif damage == "duplicate_pid":
        bindings["bot"]["pid"] = bindings["authority"]["pid"]
    elif damage == "relative_path":
        plan["commit_file"] = "relative.json"
    elif damage == "alias":
        plan["commit_file"] = plan["manifests"]["bot"]
    elif damage == "nested_model":
        templates["bot"]["authority"]["trust_model"] = "single_account_application_v1"
    elif damage == "model":
        templates["bot"]["trust_model"] = "other"
    elif damage == "host":
        templates["bot"]["authority"]["host"] = "other"
    else:
        key = {"source": "source_hashes", "sql": "sql_contract", "registration": "registration"}[
            damage
        ]
        templates["bot"][key] = {"unreviewed": True}
    with pytest.raises(ValueError):
        bind_templates(plan, templates, bindings)


@pytest.mark.parametrize("damage", [None, "hash", "pin", "partial"])
def test_gate_needs_complete_commit_and_exact_original_incarnation(tmp_path, monkeypatch, damage):
    import core.export_process_identity as identity
    import scripts.run_export_process_gate as gate

    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    raw = encode(plan)
    manifests = bind_templates(plan, templates, bindings)
    for role in bindings:
        Path(plan["manifests"][role]).write_bytes(encode(manifests[role]))
    commit = publication(raw, manifests)
    if damage == "hash":
        commit["manifests"]["bot"] = "f" * 64
    if damage == "partial":
        Path(plan["manifests"]["bot"]).unlink()
    Path(plan["commit_file"]).write_bytes(encode(commit))
    observed = deepcopy(bindings["bot"])
    if damage == "pin":
        observed["created_filetime"] += 1
    monkeypatch.setattr(identity, "process_snapshot", Mock(return_value=observed))
    operation = lambda: gate.wait_for_publication(
        plan, raw, templates, "bot", object(), bindings["bot"], Mock(side_effect=Path)
    )
    if damage:
        with pytest.raises((ValueError, FileNotFoundError)):
            operation()
    else:
        assert operation() == bindings


def test_gate_does_not_read_manifests_until_final_commit(tmp_path, monkeypatch):
    import core.export_process_identity as identity
    import scripts.run_export_process_gate as gate

    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    raw = encode(plan)
    manifests = bind_templates(plan, templates, bindings)
    monkeypatch.setattr(identity, "process_snapshot", Mock(return_value=bindings["bot"]))

    def publish(_seconds):
        for role in bindings:
            Path(plan["manifests"][role]).write_bytes(encode(manifests[role]))
        Path(plan["commit_file"]).write_bytes(encode(publication(raw, manifests)))

    sleeper = Mock(side_effect=publish)
    monkeypatch.setattr(gate.time, "sleep", sleeper)
    assert (
        gate.wait_for_publication(
            plan, raw, templates, "bot", object(), bindings["bot"], Mock(side_effect=Path)
        )
        == bindings
    )
    sleeper.assert_called_once_with(1)


def test_partial_administrative_publication_retains_files_without_releasing_gates(
    tmp_path, monkeypatch
):
    import core.export_execution_host as host
    import core.export_process_identity as identity
    import scripts.provision_export_process_pair as publisher
    import scripts.run_export_authority as launcher

    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(launcher, "manifest_contract", Mock())
    monkeypatch.setattr(host, "DeploymentBoundary", Mock())
    monkeypatch.setitem(
        sys.modules,
        "win32security",
        SimpleNamespace(ConvertStringSidToSid=lambda value: value, SetNamedSecurityInfo=Mock()),
    )
    monkeypatch.setattr(
        identity, "pinned_process_alive", Mock(side_effect=[True, True, True, False])
    )
    with pytest.raises(ValueError, match="during publication"):
        publisher.publish_pair(
            plan,
            encode(plan),
            templates,
            bindings,
            {role: object() for role in bindings},
            Mock(side_effect=Path),
        )
    assert all(Path(path).exists() for path in plan["manifests"].values())
    assert not Path(plan["commit_file"]).exists()
    with pytest.raises(ValueError, match="already exists"):
        publisher.publish_pair(
            plan,
            encode(plan),
            templates,
            bindings,
            {role: object() for role in bindings},
            Mock(side_effect=Path),
        )


def test_flags_off_launch_and_enabled_manual_gate(tmp_path):
    ordinary = watchdog_launch(
        "python", tmp_path, coordination=False, intake=False, recovery=False, plan=None
    )
    assert ordinary == (["python", str(tmp_path / "DL_bot.py")], False)
    enabled, manual = watchdog_launch(
        "python",
        tmp_path,
        coordination=True,
        intake=True,
        recovery=False,
        plan=str(tmp_path / "plan.json"),
    )
    assert manual and enabled[1:3] == ["-I", "-B"]
    assert enabled[-4:] == ["--role", "bot", "--plan", str(tmp_path / "plan.json")]
    with pytest.raises(ValueError, match="Coordinated"):
        watchdog_launch(
            "python", tmp_path, coordination=True, intake=True, recovery=False, plan=None
        )


@pytest.mark.parametrize("intake,recovery", [(True, False), (False, True), (True, True)])
def test_independent_intake_and_recovery_keep_ordinary_startup(tmp_path, intake, recovery):
    assert watchdog_launch(
        "python", tmp_path, coordination=False, intake=intake, recovery=recovery, plan=None
    ) == (["python", str(tmp_path / "DL_bot.py")], False)


@pytest.mark.parametrize("failure", [None, "destination_exists", "peer_exit"])
def test_release_becomes_visible_only_after_complete_protected_staging(
    tmp_path, monkeypatch, failure
):
    import core.export_execution_host as host
    import core.export_process_identity as identity
    import scripts.provision_export_process_pair as publisher
    import scripts.run_export_authority as launcher

    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    commit = Path(plan["commit_file"])
    protected = set()
    monkeypatch.setattr(launcher, "manifest_contract", Mock())
    monkeypatch.setattr(host, "DeploymentBoundary", Mock())
    monkeypatch.setitem(
        sys.modules,
        "win32security",
        SimpleNamespace(
            ConvertStringSidToSid=lambda value: value,
            SetNamedSecurityInfo=lambda path, *_: protected.add(Path(path)),
        ),
    )
    monkeypatch.setattr(
        identity,
        "pinned_process_alive",
        Mock(side_effect=[True] * 4 + ([False] if failure == "peer_exit" else [True, True])),
    )

    def move(source, destination, flags):
        pending = Path(source)
        assert flags == 8  # no overwrite/copy fallback
        assert pending in protected and pending.read_bytes()
        assert not commit.exists()  # polling gate cannot see staging writes
        if failure == "destination_exists":
            commit.write_bytes(b"existing-publication")
            raise FileExistsError("Do not replace publication")
        pending.rename(destination)

    mover = Mock(side_effect=move)
    monkeypatch.setitem(sys.modules, "win32file", SimpleNamespace(MoveFileEx=mover))
    operation = lambda: publisher.publish_pair(
        plan,
        encode(plan),
        templates,
        bindings,
        {role: object() for role in bindings},
        Mock(side_effect=Path),
    )
    if failure:
        with pytest.raises((FileExistsError, ValueError)):
            operation()
        assert len(list(tmp_path.glob("*.pending"))) == 1
        if failure == "peer_exit":
            assert not commit.exists()
            mover.assert_not_called()
        else:
            assert commit.read_bytes() == b"existing-publication"
    else:
        expected = operation()
        assert commit.read_bytes() == encode(expected)
        assert not list(tmp_path.glob("*.pending"))
