"""The missing-birth diagnostic cannot produce a review or invoke Apply."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_stranded_export_recovery import legacy_recovery, stranded  # noqa: F401

from scripts.inspect_stranded_export_custody import observe
from services.stranded_export_recovery import StrandedExportRecovery


@pytest.fixture
def adapter(stranded, tmp_path):  # noqa: F811
    service, state, stream = stranded.service, stranded.state, stranded.stream
    scope = json.loads(stream["ScopeJson"])
    scope.pop("host_birth")
    stream["ScopeJson"] = json.dumps(scope)
    service.host.binding = {"fixture": True}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(dict(child_script="C:/fixture/child.py")))
    module = SimpleNamespace(StrandedExportRecovery=StrandedExportRecovery)
    namespace = dict(load_tool=Mock(return_value=module), service=service, after_inspect=Mock())
    exec(
        "def entry(args):\n assert args[1] == 'Inspect'\n cls=load_tool(None, '_stranded_recovery').StrandedExportRecovery\n instance=cls.__new__(cls)\n instance.__dict__.update(service.__dict__)\n instance.inspect()\n after_inspect()",
        namespace,
    )
    collector = Mock(return_value=dict(exact_live_writer=True, termination_authorized=False))
    args = dict(manifest_path=manifest, manifest_hash="a" * 64, stage=tmp_path, collector=collector)
    return namespace, args, service, state, stream


def test_missing_birth_uses_live_observation_without_creating_review(adapter):
    namespace, args, service, _, _ = adapter
    before = service._read()[0]
    result = observe(namespace["entry"], **args)
    assert result["stage"] == "LIVE_CUSTODY_OBSERVED_NOT_RECOVERED"
    assert result["apply_authorized"] is False
    args["collector"].assert_called_once()
    namespace["after_inspect"].assert_not_called()
    assert service.journal.values == {}
    assert service._read()[0] == before
    service.execution.transition.assert_not_called()
    service.coordinator.fail_reviewed.assert_not_called()


def test_original_checks_still_block_before_native_inspection(adapter):
    namespace, args, service, state, _ = adapter
    state["job"]["Version"] += 1
    assert observe(namespace["entry"], **args)["stage"] == "CUSTODY_DIAGNOSTIC_STOPPED"
    args["collector"].assert_not_called()
    assert service.journal.values == {}


def test_unknown_scope_is_not_legacy_absence(adapter):
    namespace, args, _, _, stream = adapter
    scope = json.loads(stream["ScopeJson"])
    scope["unexpected"] = "private"
    stream["ScopeJson"] = json.dumps(scope)
    result = observe(namespace["entry"], **args)
    assert result["failed_check"] == "unexpected_scope_shape"
    args["collector"].assert_not_called()


def test_native_error_is_redacted_and_never_returns_review(adapter):
    namespace, args, service, _, _ = adapter
    args["collector"].side_effect = ValueError("private path and secret")
    result = observe(namespace["entry"], **args)
    assert result["failed_check"] == "unclassified_stop"
    assert "private" not in json.dumps(result)
    assert service.journal.values == {}
    namespace["after_inspect"].assert_not_called()


def test_state_change_during_inspection_stops(adapter):
    namespace, args, _, state, _ = adapter

    def change(**_):
        state["job"]["Version"] += 1
        return {}

    args["collector"].side_effect = change
    assert observe(namespace["entry"], **args)["failed_check"] == "state_changed_during_inspection"
    namespace["after_inspect"].assert_not_called()


def test_prior_apply_intent_refuses_every_operation(adapter):
    namespace, args, _, _, _ = adapter
    (args["stage"] / "journal").mkdir()
    (args["stage"] / "journal" / "intent.json").write_text("{}")
    assert observe(namespace["entry"], **args)["stage"] == "CUSTODY_DIAGNOSTIC_REFUSED"
    args["collector"].assert_not_called()
    namespace["load_tool"].assert_not_called()
