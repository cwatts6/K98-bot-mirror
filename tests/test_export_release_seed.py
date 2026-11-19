from copy import deepcopy
import hashlib
import json
from pathlib import PureWindowsPath
from uuid import uuid4

import pytest

from core.export_automatic_pair import RECORDS
from core.export_release_seed import successor_seed
from services.export_execution_protocol import encode
from tests.test_export_automatic_pair import seed


def predecessor(tmp_path, monkeypatch):
    plan, templates, records, *_ = seed(tmp_path, monkeypatch)
    for role in templates:
        plan["templates"][role]["sha256"] = hashlib.sha256(encode(templates[role])).hexdigest()
    policy = dict(
        version=1,
        source_hashes=deepcopy(plan["source_hashes"]),
        seed_plan=dict(
            path="C:/K98/reviewed-deployment/ManualProcessPairPlan-CANDIDATE.json",
            sha256=hashlib.sha256(encode(plan)).hexdigest(),
        ),
        state_directory="C:/K98/history/reviewed-deployment",
        flags=dict(
            EXPORT_COORDINATION_ENABLED=True,
            KVK_SOURCE_INTAKE_ENABLED=False,
            KVK_SOURCE_RECOVERY_ENABLED=False,
        ),
    )
    return {
        "authority-template.json": templates["authority"],
        "bot-template.json": templates["bot"],
        "ManualProcessPairPlan-CANDIDATE.json": plan,
        "AutomaticStartupPolicy.json": policy,
        **{kind + ".json": value for kind, value in records.items()},
    }


def test_successor_preserves_observations_flags_and_contracts(tmp_path, monkeypatch):
    previous = predecessor(tmp_path, monkeypatch)
    original = deepcopy(previous)
    new_id = str(uuid4())
    payload = successor_seed(
        previous,
        {"DL_bot.py": "d" * 64, "core/new.py": "e" * 64},
        deployment_id=new_id,
        review_id=str(uuid4()),
        pipe_id=str(uuid4()),
    )
    assert previous == original
    values = {name: json.loads(raw) for name, raw in payload.items()}
    policy = values["AutomaticStartupPolicy.json"]
    assert PureWindowsPath(policy["state_directory"]) == PureWindowsPath("C:/K98/history") / new_id
    assert policy["flags"] == original["AutomaticStartupPolicy.json"]["flags"]
    assert (
        policy["predecessor"]["policy_sha256"]
        == hashlib.sha256(encode(original["AutomaticStartupPolicy.json"])).hexdigest()
    )
    for kind in RECORDS:
        assert values[kind + ".json"]["observations"] == original[kind + ".json"]["observations"]
    authority = values["authority-template.json"]
    assert authority["sql_contract"] == original["authority-template.json"]["sql_contract"]
    assert (
        authority["runtime_registration"]
        == original["authority-template.json"]["runtime_registration"]
    )
    assert (
        hashlib.sha256(payload["ManualProcessPairPlan-CANDIDATE.json"]).hexdigest()
        == policy["seed_plan"]["sha256"]
    )


@pytest.mark.parametrize("old_name", ["custom-history", "reviewed-deployment"])
def test_successor_state_is_fresh_sibling_even_without_uuid(tmp_path, monkeypatch, old_name):
    previous = predecessor(tmp_path, monkeypatch)
    old_policy = previous["AutomaticStartupPolicy.json"]
    old_policy["state_directory"] = "C:/K98/history/" + old_name
    new_id = str(uuid4())
    payload = successor_seed(
        previous,
        {"DL_bot.py": "a" * 64},
        deployment_id=new_id,
        review_id=str(uuid4()),
        pipe_id=str(uuid4()),
    )
    policy = json.loads(payload["AutomaticStartupPolicy.json"])
    old_state = PureWindowsPath(old_policy["state_directory"])
    new_state = PureWindowsPath(policy["state_directory"])
    assert new_state == old_state.parent / new_id
    assert new_state != old_state
    assert policy["predecessor"] == {
        "state_directory": old_policy["state_directory"],
        "policy_sha256": hashlib.sha256(encode(old_policy)).hexdigest(),
    }


@pytest.mark.parametrize("invalid", ["relative/history", "same-successor"])
def test_successor_rejects_relative_or_reused_state(tmp_path, monkeypatch, invalid):
    previous = predecessor(tmp_path, monkeypatch)
    new_id = str(uuid4())
    previous["AutomaticStartupPolicy.json"]["state_directory"] = (
        "C:/K98/history/" + new_id if invalid == "same-successor" else invalid
    )
    with pytest.raises(ValueError, match="sibling state"):
        successor_seed(
            previous,
            {"DL_bot.py": "a" * 64},
            deployment_id=new_id,
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        )


@pytest.mark.parametrize(
    "name",
    [
        "authority-template.json",
        "bot-template.json",
        "host_acl.json",
        "ManualProcessPairPlan-CANDIDATE.json",
    ],
)
def test_changed_predecessor_is_not_resealed_as_reviewed(tmp_path, monkeypatch, name):
    previous = predecessor(tmp_path, monkeypatch)
    previous[name]["unexpected"] = True
    with pytest.raises(ValueError):
        successor_seed(
            previous,
            {"DL_bot.py": "a" * 64},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        )


@pytest.mark.parametrize("path", ["../evil.py", "C:/evil.py", "core\\evil.py", "/evil.py"])
def test_source_paths_cannot_escape_release_inventory(tmp_path, monkeypatch, path):
    with pytest.raises(ValueError, match="inventory"):
        successor_seed(
            predecessor(tmp_path, monkeypatch),
            {path: "a" * 64},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        )
