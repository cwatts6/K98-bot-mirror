"""Activation policy/gate may be separate from the authenticated seed; no live I/O."""

from copy import deepcopy
import json
from pathlib import PureWindowsPath

import pytest

from scripts.prepare_k98_update import release_seed, sha256
from services.export_execution_protocol import encode
from tests.test_export_release_seed import predecessor


@pytest.mark.parametrize("split", [False, True])
def test_active_policy_and_log_rebind_without_losing_activation(tmp_path, monkeypatch, split):
    previous = predecessor(tmp_path, monkeypatch)
    policy = previous["AutomaticStartupPolicy.json"]
    policy["flags"].update(KVK_SOURCE_INTAKE_ENABLED=True, KVK_SOURCE_RECOVERY_ENABLED=True)
    seed_directory = PureWindowsPath(policy["seed_plan"]["path"]).parent
    active_directory = seed_directory.parent / "activation" if split else seed_directory
    policy_path = str(active_directory / "AutomaticStartupPolicy.json")
    gate = f"$policy='{policy_path}'\n$policyHash='{sha256(encode(policy))}'\n$log='{active_directory}\\wrapper-startup.log'\n"
    original = deepcopy(previous)
    for index in range(2):
        before = deepcopy(previous)
        before_policy = deepcopy(previous["AutomaticStartupPolicy.json"])
        payload = release_seed(
            previous, {"DL_bot.py": str(index + 1) * 64}, gate, policy_path=policy_path
        )
        assert previous == before
        gate = payload.pop("Start-ReviewedAutomaticStartup.ps1").decode()
        previous = {name: json.loads(raw) for name, raw in payload.items()}
        policy = previous["AutomaticStartupPolicy.json"]
        target_directory = PureWindowsPath(policy["seed_plan"]["path"]).parent
        policy_path = str(target_directory / "AutomaticStartupPolicy.json")
        assert f"$policy='{policy_path}'" in gate
        assert f"$log='{target_directory}\\wrapper-startup.log'" in gate
        assert f"$policyHash='{sha256(encode(policy))}'" in gate
        assert policy["flags"] == original["AutomaticStartupPolicy.json"]["flags"]
        assert policy["predecessor"] == {
            "state_directory": before_policy["state_directory"],
            "policy_sha256": sha256(encode(before_policy)),
        }
        assert policy["seed_plan"]["sha256"] == sha256(
            payload["ManualProcessPairPlan-CANDIDATE.json"]
        )
        assert (
            previous["bot-template.json"]["sql_contract"]
            == original["bot-template.json"]["sql_contract"]
        )


@pytest.mark.parametrize(
    "damage", ["wrong_path", "relative", "wrong_name", "duplicate", "hash", "seed"]
)
def test_split_policy_preparation_rejects_unbound_or_changed_inputs(tmp_path, monkeypatch, damage):
    previous = predecessor(tmp_path, monkeypatch)
    policy = previous["AutomaticStartupPolicy.json"]
    path = r"C:\K98\activation\AutomaticStartupPolicy.json"
    gate = f"$policy='{path}'\n$policyHash='{sha256(encode(policy))}'\n"
    if damage == "wrong_path":
        path = r"C:\K98\other\AutomaticStartupPolicy.json"
    elif damage == "relative":
        path = "AutomaticStartupPolicy.json"
    elif damage == "wrong_name":
        path = r"C:\K98\activation\Other.json"
    elif damage == "duplicate":
        gate += gate
    elif damage == "hash":
        gate = gate.replace(sha256(encode(policy)), "0" * 64)
    else:
        previous["bot-template.json"]["unexpected"] = True
    with pytest.raises(ValueError):
        release_seed(previous, {"DL_bot.py": "a" * 64}, gate, policy_path=path)
