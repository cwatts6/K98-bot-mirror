"""A reviewed trigger delta must not authorize other startup contract drift."""

from copy import deepcopy
import json
from pathlib import Path, PureWindowsPath
from uuid import uuid4

import pytest

from scripts import prepare_k98_update as updater


@pytest.fixture
def previous(monkeypatch):
    value = {
        "bot-template.json": {
            "sql_contract": {"principal": "restricted", "metadata_hash": "s"},
            "legacy_sql_contract": {"principal": "restricted", "source": {"modules": []}},
            "application_sql_contract": {
                "metadata_hash": "old",
                "permissions_hash": "unchanged",
                "sources": ["unchanged"],
                "scope_hash": "unchanged",
                "review_id": str(uuid4()),
            },
        }
    }
    monkeypatch.setattr(
        updater,
        "MGE_APPLICATION_BEFORE",
        updater.sha256(updater.encode(value["bot-template.json"]["application_sql_contract"])),
    )
    return value


def test_only_metadata_and_review_change_without_mutating_predecessor(previous):
    original = deepcopy(previous)
    result = updater.mge_application_contract_transition(previous, updater.MGE_APPLICATION_RELEASE)
    assert previous == original
    pairs = result["contracts"]
    assert pairs["sql_contract"]["before"] == pairs["sql_contract"]["after"]
    assert pairs["legacy_sql_contract"]["before"] == pairs["legacy_sql_contract"]["after"]
    pair = pairs["application_sql_contract"]
    changed = {key for key in pair["before"] if pair["before"][key] != pair["after"][key]}
    assert changed == {"metadata_hash", "review_id"}
    assert pair["after"]["metadata_hash"] == updater.MGE_APPLICATION_AFTER_METADATA
    pair["after"]["sources"].append("mutation")
    assert previous == original


@pytest.mark.parametrize(
    "field", ["metadata_hash", "permissions_hash", "sources", "scope_hash", "review_id"]
)
def test_any_predecessor_contract_drift_is_refused(previous, field):
    previous["bot-template.json"]["application_sql_contract"][field] = "drift"
    with pytest.raises(ValueError, match="predecessor application contract"):
        updater.mge_application_contract_transition(previous, updater.MGE_APPLICATION_RELEASE)


@pytest.mark.parametrize(
    "field", ["version", "profile", "bot_predecessors", "sql_commit", "migrations", "extra"]
)
def test_other_release_cannot_borrow_contract_amendment(previous, field):
    description = deepcopy(updater.MGE_APPLICATION_RELEASE)
    description[field] = "other"
    with pytest.raises(ValueError, match="exact reviewed release"):
        updater.mge_application_contract_transition(previous, description)


@pytest.mark.parametrize("independent_protection", [False, True])
def test_complete_packet_rebinds_only_application_contract_and_keeps_other_guards(
    tmp_path, monkeypatch, independent_protection
):
    from core.export_release_seed import successor_seed
    import services.export_runtime_composition as composition
    from tests.test_export_release_seed import predecessor
    from tests.test_mge_finalisation_updater import profile

    initial = predecessor(tmp_path, monkeypatch)
    bot = initial["bot-template.json"]
    bot["sql_contract"]["principal"] = "restricted"
    initial["authority-template.json"]["sql_contract"] = deepcopy(bot["sql_contract"])
    initial["ManualProcessPairPlan-CANDIDATE.json"]["templates"]["authority"]["sha256"] = (
        updater.sha256(updater.encode(initial["authority-template.json"]))
    )
    bot["application_sql_contract"] = {"principal": "restricted", "metadata_hash": "old"}
    bot["legacy_sql_contract"] = {
        "principal": "restricted",
        "source": {"modules": [{"name": "dbo.MGE_Events"}] if independent_protection else []},
    }
    initial["ManualProcessPairPlan-CANDIDATE.json"]["templates"]["bot"]["sha256"] = updater.sha256(
        updater.encode(bot)
    )
    initial["AutomaticStartupPolicy.json"]["seed_plan"]["sha256"] = updater.sha256(
        updater.encode(initial["ManualProcessPairPlan-CANDIDATE.json"])
    )
    monkeypatch.setattr(
        composition, "application_contract_scope", lambda _: sorted(updater.MGE_APPLICATION_PARENTS)
    )
    previous = {
        name: json.loads(raw)
        for name, raw in successor_seed(
            initial,
            {"DL_bot.py": updater.sha256(b"old\n")},
            deployment_id=str(uuid4()),
            review_id=str(uuid4()),
            pipe_id=str(uuid4()),
        ).items()
    }
    original = deepcopy(previous)
    monkeypatch.setattr(
        updater,
        "MGE_APPLICATION_BEFORE",
        updater.sha256(updater.encode(previous["bot-template.json"]["application_sql_contract"])),
    )
    p = profile()
    d = deepcopy(updater.MGE_APPLICATION_RELEASE)
    raw_profile = json.dumps(p).encode()
    d["migrations"][0]["sha256"] = updater.sha256(raw_profile)
    monkeypatch.setattr(updater, "MGE_APPLICATION_RELEASE", d)
    before = d["bot_predecessors"][0]
    target = "c" * 40
    policy = previous["AutomaticStartupPolicy.json"]
    policy_path = str(
        PureWindowsPath(policy["seed_plan"]["path"]).with_name("AutomaticStartupPolicy.json")
    )
    observation = dict(
        seed=previous,
        gate=f"$policy='{policy_path}'\n$policyHash='{updater.sha256(updater.encode(policy))}'\n",
        bindings=dict(
            before=before,
            target=target,
            root="C:\\fixture",
            host="FIXTURE",
            sid="S-1-5-21-1-2-3-1001",
            old_policy=dict(Path=policy_path, SHA256=updater.sha256(updater.encode(policy))),
            old_plan=dict(Python="C:\\fixture\\python.exe", PythonSHA256="a" * 64),
        ),
    )
    blobs = {
        (before, "DL_bot.py"): b"old\n",
        (target, "DL_bot.py"): b"new\n",
        (target, updater.RELEASE_DESCRIPTION): json.dumps(d).encode(),
    }
    files = {
        "deploy/" + name: name.encode()
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.TableRelease.ps1",
            "SqlDeploy.MgeFinalisation.ps1",
        )
    }
    files["migrations/" + p["migration_id"] + ".release.json"] = raw_profile

    def run():
        return updater.prepare_update(
            observation,
            ["DL_bot.py", updater.RELEASE_DESCRIPTION],
            lambda *key: blobs.get(key),
            tmp_path / "packet",
            Path(__file__).resolve().parents[1] / "scripts",
            read_sql_blob=files.get,
        )

    if independent_protection:
        with pytest.raises(ValueError, match="protected MGE"):
            run()
        assert not (tmp_path / "packet").exists()
        return
    result = run()
    package = Path(result["manifest"]).parent
    new_bot = json.loads((package / "bot-template.json").read_bytes())
    assert (
        new_bot["application_sql_contract"]["metadata_hash"]
        == updater.MGE_APPLICATION_AFTER_METADATA
    )
    assert new_bot["sql_contract"] == previous["bot-template.json"]["sql_contract"]
    assert new_bot["legacy_sql_contract"] == previous["bot-template.json"]["legacy_sql_contract"]
    assert previous == original
    new_policy = json.loads((package / "AutomaticStartupPolicy.json").read_bytes())
    assert new_policy["flags"] == policy["flags"]
    plan = json.loads((package / "ManualProcessPairPlan-CANDIDATE.json").read_bytes())
    assert plan["templates"]["bot"]["sha256"] == updater.sha256(
        (package / "bot-template.json").read_bytes()
    )
    assert new_policy["seed_plan"]["sha256"] == updater.sha256(
        (package / "ManualProcessPairPlan-CANDIDATE.json").read_bytes()
    )
    assert (
        updater.sha256((package / "AutomaticStartupPolicy.json").read_bytes())
        in (package / "Start-ReviewedAutomaticStartup.ps1").read_text()
    )
