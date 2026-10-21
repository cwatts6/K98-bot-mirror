"""Protected restart history must identify the exact prior pair and publication."""

from copy import deepcopy
import hashlib
import json
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from core.export_automatic_pair import validate_issuer_record
from scripts.run_export_startup_issuer import acknowledge_role, read_previous, release_history
from tests.test_export_process_pair import pair_fixture


def history(tmp_path, bindings):
    value = dict(
        version=1,
        sequence=1,
        policy_sha256="a" * 64,
        bindings=bindings,
        publication=dict(
            version=1,
            plan_sha256="b" * 64,
            manifests=dict(authority="c" * 64, bot="d" * 64),
        ),
    )
    path = tmp_path / "incarnation-00000000000000000001-fixture.json"
    return path, value


def test_empty_history_has_no_session_to_reconcile(tmp_path):
    assert read_previous(tmp_path, "a" * 64, lambda p, **kw: p, "fixture") is None


def test_successor_inherits_exact_predecessor_without_relabeling_history(tmp_path, monkeypatch):
    _, _, bindings = pair_fixture(tmp_path, monkeypatch)
    sid = bindings["bot"]["token_profile"]["user_sid"]
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()
    path, value = history(old, bindings)
    path.write_text(json.dumps(value), encoding="utf-8")
    policy = dict(
        state_directory=str(new), predecessor=dict(state_directory=str(old), policy_sha256="a" * 64)
    )
    observed, directory = release_history(policy, "b" * 64, lambda p, **kw: p, sid)
    assert observed == value
    assert observed["policy_sha256"] == "a" * 64
    assert directory == str(old)
    assert not list(new.iterdir())


def test_empty_or_unrelated_predecessor_cannot_authorize_new_release(tmp_path):
    new = tmp_path / "new"
    old = tmp_path / "old"
    new.mkdir()
    old.mkdir()
    policy = dict(
        state_directory=str(new), predecessor=dict(state_directory=str(old), policy_sha256="a" * 64)
    )
    with pytest.raises(ValueError, match="no retained"):
        release_history(policy, "b" * 64, lambda p, **kw: p, "fixture")


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "policy",
        "sequence",
        "partial_commit",
        "bad_digest",
        "other_role",
        "boolean_version",
        "pair_sid",
    ],
)
def test_exact_prior_history_is_required(tmp_path, monkeypatch, damage):
    _, _, bindings = pair_fixture(tmp_path, monkeypatch)
    sid = bindings["bot"]["token_profile"]["user_sid"]
    path, value = history(tmp_path, deepcopy(bindings))
    if damage == "policy":
        value["policy_sha256"] = "f" * 64
    elif damage == "sequence":
        value["sequence"] = 2
    elif damage == "partial_commit":
        value["publication"]["manifests"].pop("authority")
    elif damage == "bad_digest":
        value["publication"]["manifests"]["authority"] = "not-a-hash"
    elif damage == "other_role":
        value["publication"]["manifests"]["other"] = "c" * 64
    elif damage == "boolean_version":
        value["publication"]["version"] = True
    elif damage == "pair_sid":
        value["bindings"]["authority"]["token_profile"]["user_sid"] = "S-1-5-18"
    path.write_text(json.dumps(value), encoding="utf-8")
    inspected = []

    def inspect(p, **kw):
        inspected.append((p, kw))
        return p

    if damage:
        with pytest.raises(ValueError):
            read_previous(tmp_path, "a" * 64, inspect, sid)
    else:
        assert read_previous(tmp_path, "a" * 64, inspect, sid) == value
    assert inspected == [(path, {"private": True})]


@pytest.mark.parametrize("damage", [None, "ordinary", "ui_access", "image", "plan"])
def test_gate_pins_the_administrative_issuer(tmp_path, monkeypatch, damage):
    plan, _, bindings = pair_fixture(tmp_path, monkeypatch)
    raw = b"fixed-plan"
    issuer = deepcopy(bindings["authority"])
    issuer["token_profile"].update(elevation_type=2, elevated=True, ui_access=False)
    record = dict(
        version=1,
        issuer=issuer,
        pipe_id="74a0c2dd-443f-4b18-a79a-1a60858d8875",
        plan_sha256=hashlib.sha256(raw).hexdigest(),
    )
    if damage == "ordinary":
        issuer["token_profile"].update(elevation_type=3, elevated=False)
    elif damage == "ui_access":
        issuer["token_profile"]["ui_access"] = True
    elif damage == "image":
        issuer["sha256"] = "f" * 64
    elif damage == "plan":
        record["plan_sha256"] = "f" * 64
    if damage:
        with pytest.raises(ValueError):
            validate_issuer_record(record, plan, raw)
    else:
        assert validate_issuer_record(record, plan, raw) == issuer


@pytest.mark.parametrize(
    "damage",
    [None, "foreign_job", "foreign_image", "wrong_role", "wrong_plan", "missing_native_pid"],
)
def test_acknowledgment_needs_native_job_membership_and_exact_role(monkeypatch, tmp_path, damage):
    plan, _, bindings = pair_fixture(tmp_path, monkeypatch)
    raw = b"reviewed-plan"
    handle = Mock()
    api = SimpleNamespace(OpenProcess=Mock(return_value=handle))
    monkeypatch.setitem(sys.modules, "win32api", api)
    import ctypes
    from ctypes import wintypes

    def get_pid(pipe, target):
        ctypes.cast(target, ctypes.POINTER(wintypes.ULONG)).contents.value = 123
        return damage != "missing_native_pid"

    monkeypatch.setattr(
        ctypes,
        "WinDLL",
        lambda *args, **kw: SimpleNamespace(GetNamedPipeClientProcessId=get_pid),
        raising=False,
    )
    member = Mock(return_value=damage != "foreign_job")
    monkeypatch.setattr("core.export_startup_windows.role_member", member)
    descriptor = deepcopy(bindings["authority"])
    if damage == "foreign_image":
        descriptor["sha256"] = "f" * 64
    snapshot = Mock(return_value=descriptor)
    monkeypatch.setattr("core.export_process_identity.process_snapshot", snapshot)
    message = dict(version=1, role="authority", plan_sha256=hashlib.sha256(raw).hexdigest())
    if damage == "wrong_role":
        message["role"] = "bot"
    elif damage == "wrong_plan":
        message["plan_sha256"] = "f" * 64
    channel = Mock()
    channel.receive.return_value = message
    pipe_factory = Mock(return_value=channel)
    monkeypatch.setattr("core.export_execution_host.MessagePipe", pipe_factory)
    created = SimpleNamespace(process=object())
    if damage:
        with pytest.raises(ValueError):
            acknowledge_role(1, created, "authority", plan, raw)
        channel.send.assert_not_called()
        if damage != "missing_native_pid":
            handle.Close.assert_called_once()
        else:
            api.OpenProcess.assert_not_called()
        if damage == "foreign_job":
            snapshot.assert_not_called()
    else:
        assert acknowledge_role(1, created, "authority", plan, raw) == (descriptor, handle)
        channel.send.assert_called_once_with(dict(version=1, accepted=True))
        handle.Close.assert_not_called()
        member.assert_called_once_with(handle, created)
    pipe_factory.assert_called_once_with(1, timeout_ms=30000, process=created.process)
