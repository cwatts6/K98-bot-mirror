"""Automatic renewal cannot learn SQL/provider expectations or widen a token."""

from copy import deepcopy
import hashlib
import json
from pathlib import PureWindowsPath

import pytest

from core.export_automatic_pair import RECORDS, incarnation_files, verify_automatic_token
from core.export_process_pair import bind_templates
from services.export_execution_protocol import encode
from tests.test_export_process_pair import pair_fixture


def seed(tmp_path, monkeypatch):
    plan, templates, bindings = pair_fixture(tmp_path, monkeypatch)
    for value in bindings.values():
        value["token_profile"].update(
            elevation_type=3, group_sids=["S-1-5-32-545", "S-1-5-5-0-123"]
        )
    plan["token_profiles"] = {r: deepcopy(b["token_profile"]) for r, b in bindings.items()}
    boundary = templates["authority"]["deployment_boundary"]
    boundary.update(
        deployment_id="reviewed-deployment", review=dict(review_id="reviewed-source", records={})
    )
    records = {}
    for kind in RECORDS:
        record = dict(
            kind=kind,
            deployment_id=boundary["deployment_id"],
            review_id="reviewed-source",
            trust_model="single_account_application_v1",
            version=5,
            observations=[dict(observed_utc="2026-01-01T00:00:00Z", factual_expected="unchanged")],
        )
        records[kind] = record
        boundary["review"]["records"][kind] = dict(
            path="C:/K98/" + kind + ".json", sha256=hashlib.sha256(encode(record)).hexdigest()
        )
    profile = deepcopy(plan["token_profiles"]["bot"])
    profile["group_sids"][-1] = "S-1-5-5-0-456"
    nonce = "11111111-2222-4333-8444-555555555555"
    directory = str(PureWindowsPath(plan["commit_file"]).parent.parent / nonce)
    return plan, templates, records, profile, nonce, directory, bindings


def renew(values):
    plan, templates, records, profile, nonce, directory, _ = values
    return incarnation_files(
        plan,
        templates,
        records,
        profile=profile,
        nonce=nonce,
        directory=directory,
        observed_utc="2026-02-01T00:00:00Z",
    )


def test_fresh_incarnation_preserves_deployment_review_and_historical_facts(tmp_path, monkeypatch):
    values = seed(tmp_path, monkeypatch)
    original = deepcopy(values[:3])
    files, plan, templates = renew(values)
    assert len(files) == 10 and values[:3] == tuple(original)
    assert "commit.json" not in files and "authority-manifest.json" not in files
    for kind in RECORDS - {"bot_identity"}:
        assert json.loads(files[kind + ".json"]) == values[2][kind]
    observation = json.loads(files["bot_identity.json"])["observations"][0]
    assert observation["observed_utc"] == "2026-02-01T00:00:00Z"
    assert observation["group_sids"] == values[3]["group_sids"]
    assert templates["authority"]["sql_contract"] == values[1]["authority"]["sql_contract"]
    assert (
        templates["authority"]["runtime_registration"]
        == values[1]["authority"]["runtime_registration"]
    )
    assert templates["authority"]["deployment_boundary"]["deployment_id"] == "reviewed-deployment"
    bindings = deepcopy(values[-1])
    for descriptor in bindings.values():
        descriptor["token_profile"] = deepcopy(values[3])
    bound = bind_templates(plan, templates, bindings)
    assert bound["authority"]["process_bindings"] == bindings


@pytest.mark.parametrize(
    "damage", ["elevated", "ui_access", "sid", "privilege", "group", "no_logon", "duplicate_logon"]
)
def test_only_logon_sid_can_change(tmp_path, monkeypatch, damage):
    values = seed(tmp_path, monkeypatch)
    profile, reviewed = values[3], values[0]["token_profiles"]["bot"]
    if damage == "elevated":
        profile["elevated"] = True
    elif damage == "ui_access":
        profile["ui_access"] = True
    elif damage == "sid":
        profile["user_sid"] = "S-1-5-21-999"
    elif damage == "privilege":
        profile["privileges"] = sorted(profile["privileges"] + ["SeImpersonatePrivilege"])
    elif damage == "group":
        profile["group_sids"] = sorted(profile["group_sids"] + ["S-1-5-32-544"])
    elif damage == "no_logon":
        profile["group_sids"].pop()
    else:
        profile["group_sids"] = sorted(profile["group_sids"] + ["S-1-5-5-0-789"])
    with pytest.raises(ValueError):
        verify_automatic_token(profile, reviewed, values[0]["application_sid"])


@pytest.mark.parametrize(
    "damage",
    [
        "path_escape",
        "old_directory",
        "tampered_record",
        "wrong_deployment",
        "old_bindings",
        "missing_record",
    ],
)
def test_unreviewed_or_reused_inputs_cannot_be_renewed(tmp_path, monkeypatch, damage):
    values = list(seed(tmp_path, monkeypatch))
    if damage == "path_escape":
        values[5] = "C:/Other/" + values[4]
    elif damage == "old_directory":
        values[5] = str(PureWindowsPath(values[0]["commit_file"]).parent)
    elif damage == "tampered_record":
        values[2]["file_access"]["observations"][0]["factual_expected"] = "learned"
    elif damage == "wrong_deployment":
        values[2]["file_access"]["deployment_id"] = "another"
    elif damage == "old_bindings":
        values[1]["authority"]["process_bindings"] = values[-1]
    else:
        values[2].pop("writer_drain")
    with pytest.raises(ValueError):
        renew(values)
