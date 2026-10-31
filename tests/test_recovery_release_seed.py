from copy import deepcopy
import json
from uuid import uuid4

import pytest
from test_export_runtime_composition import (
    application_installation_fixture,
    installation_fixture,
    legacy_permission_fixture,
)

from core.export_process_identity import TRUST_MODEL
from kvk.dal.new_source_import_dal import digest
from scripts.recovery_release_seed import checksum, encode, sql_observation, verified_seed


def evidence(monkeypatch):
    installed, contract = installation_fixture(profile="reader")
    legacy, legacy_contract = legacy_permission_fixture(monkeypatch)
    application, application_contract = application_installation_fixture(monkeypatch)
    bot = dict(
        trust_model=TRUST_MODEL,
        sql_contract=contract,
        legacy_sql_contract=legacy_contract,
        application_sql_contract=application_contract,
    )
    record = dict(
        version=5,
        trust_model=TRUST_MODEL,
        kind="sql_installation",
        deployment_id=str(uuid4()),
        review_id=str(uuid4()),
        observations=[],
    )
    collected = dict(
        observed_utc="2026-10-16T10:00:00+00:00",
        installation=installed,
        legacy=legacy,
        application=application,
    )
    return bot, record, collected


def test_observation_uses_complete_collected_rows_and_preserves_review_identity(monkeypatch):
    bot, prior, collected = evidence(monkeypatch)
    original = deepcopy((bot, prior, collected))
    record = sql_observation(bot, prior, collected)
    assert (bot, prior, collected) == original
    assert {k: v for k, v in record.items() if k != "observations"} == {
        k: v for k, v in prior.items() if k != "observations"
    }
    assert record["observations"] == [
        dict(
            contract_sha256=checksum(bot["sql_contract"]),
            observed_utc=collected["observed_utc"],
            server=collected["installation"]["target"]["ServerName"],
            database=collected["installation"]["target"]["DatabaseName"],
            principal=collected["installation"]["target"]["Principal"],
        )
    ]


@pytest.mark.parametrize(
    "damage",
    [
        "wrong_server",
        "elevated_principal",
        "missing_migration",
        "wrong_migration_hash",
        "failed_migration",
        "changed_module",
        "missing_permission",
        "legacy_drift",
        "application_drift",
        "missing_snapshot",
        "extra_field",
        "no_timezone",
    ],
)
def test_no_observation_is_emitted_for_incomplete_or_changed_sql(monkeypatch, damage):
    bot, prior, collected = evidence(monkeypatch)
    installation = collected["installation"]
    if damage == "wrong_server":
        installation["target"]["ServerName"] = "another-server"
    elif damage == "elevated_principal":
        installation["target"]["DatabaseOwner"] = 1
    elif damage == "missing_migration":
        installation["migrations"].pop()
    elif damage == "wrong_migration_hash":
        installation["migrations"][0]["ChecksumSha256"] = "f" * 64
    elif damage == "failed_migration":
        installation["migrations"][0]["Status"] = "Failed"
    elif damage == "changed_module":
        installation["metadata"]["objects"][0]["ModuleDefinition"] = "changed"
    elif damage == "missing_permission":
        installation["permissions"].pop()
    elif damage == "legacy_drift":
        collected["legacy"]["modules"][0]["ModuleDefinition"] = "changed"
    elif damage == "application_drift":
        collected["application"]["column_permissions"][0]["Allowed"] = 0
    elif damage == "missing_snapshot":
        del collected["application"]
    elif damage == "extra_field":
        collected["expected_metadata_hash"] = "f" * 64
    else:
        collected["observed_utc"] = "2026-10-16T10:00:00"
    with pytest.raises((ValueError, RuntimeError)):
        sql_observation(bot, prior, collected)
    assert prior["observations"] == []


def seed_fixture(monkeypatch):
    bot, prior, collected = evidence(monkeypatch)
    authority = dict(
        trust_model=TRUST_MODEL,
        sql_contract=deepcopy(bot["sql_contract"]),
        deployment_boundary=dict(
            sql_contract_hash="a" * 64,
            review=dict(
                records=dict(
                    sql_installation=dict(
                        path="C:/protected/sql_installation.json", sha256=checksum(prior)
                    )
                )
            ),
        ),
    )
    plan = dict(
        templates={
            role: dict(path=role + ".json", sha256="b" * 64) for role in ("bot", "authority")
        }
    )
    policy = dict(
        seed_plan=dict(path="C:/protected/plan.json", sha256=checksum(plan)),
        source_hashes={"a.py": "c" * 64},
        flags={"exports": True},
        state_directory="C:/protected/state",
        predecessor={"state_directory": "C:/protected/prior", "policy_sha256": "d" * 64},
    )
    candidate = {
        n: encode(v)
        for n, v in {
            "bot-template.json": bot,
            "authority-template.json": authority,
            "ManualProcessPairPlan-CANDIDATE.json": plan,
            "AutomaticStartupPolicy.json": policy,
            "sql_installation.json": prior,
        }.items()
    }
    candidate["Start-ReviewedAutomaticStartup.ps1"] = ("verify " + checksum(policy)).encode()
    return candidate, collected, bot, policy


def test_historical_single_identity_record_retains_version_one(monkeypatch):
    bot, prior, collected = evidence(monkeypatch)
    del bot["trust_model"]
    del prior["trust_model"]
    prior["version"] = 1
    result = sql_observation(bot, prior, collected)
    assert result["version"] == 1 and "trust_model" not in result


@pytest.mark.parametrize(
    "damage",
    [
        "old_version",
        "future_version",
        "boolean_version",
        "missing_trust",
        "wrong_trust",
        "wrong_bot_trust",
        "extra_field",
    ],
)
def test_record_version_and_trust_must_match_the_reviewed_template(monkeypatch, damage):
    bot, prior, collected = evidence(monkeypatch)
    if damage == "old_version":
        prior["version"] = 1
    elif damage == "future_version":
        prior["version"] = 6
    elif damage == "boolean_version":
        prior["version"] = True
    elif damage == "missing_trust":
        del prior["trust_model"]
    elif damage == "wrong_trust":
        prior["trust_model"] = "foreign"
    elif damage == "wrong_bot_trust":
        bot["trust_model"] = "foreign"
    else:
        prior["unexpected"] = True
    with pytest.raises(ValueError, match="Exact deployment SQL observation"):
        sql_observation(bot, prior, collected)


def test_authority_and_bot_trust_must_agree_before_seed_rebinding(monkeypatch):
    candidate, collected, _, _ = seed_fixture(monkeypatch)
    authority = json.loads(candidate["authority-template.json"])
    authority["trust_model"] = "foreign"
    candidate["authority-template.json"] = encode(authority)
    with pytest.raises(ValueError, match="bot/authority"):
        verified_seed(candidate, collected)


def test_seed_rebinds_actual_observation_without_changing_flags_or_source(monkeypatch):
    candidate, collected, bot, policy = seed_fixture(monkeypatch)
    original = deepcopy(candidate)
    result = verified_seed(candidate, collected)
    assert candidate == original
    assert verified_seed(candidate, collected) == result  # durable restart derivation
    actual_policy = json.loads(result["AutomaticStartupPolicy.json"])
    assert actual_policy["flags"] == policy["flags"]
    assert actual_policy["source_hashes"] == policy["source_hashes"]
    assert json.loads(result["bot-template.json"]) == bot
    actual_authority = json.loads(result["authority-template.json"])
    actual_record = json.loads(result["sql_installation.json"])
    assert actual_authority["deployment_boundary"]["sql_contract_hash"] == checksum(
        bot["sql_contract"]
    )
    assert actual_authority["deployment_boundary"]["review"]["records"]["sql_installation"][
        "sha256"
    ] == checksum(actual_record)
    assert actual_policy["seed_plan"]["sha256"] == checksum(
        json.loads(result["ManualProcessPairPlan-CANDIDATE.json"])
    )
    assert (
        result["Start-ReviewedAutomaticStartup.ps1"]
        == ("verify " + checksum(actual_policy)).encode()
    )


def test_observed_fingerprint_is_not_adopted_as_expected(monkeypatch):
    bot, prior, collected = evidence(monkeypatch)
    collected["installation"]["metadata"]["objects"][0]["ModuleDefinition"] = "drift"
    changed_hash = digest(collected["installation"]["metadata"]).hex()
    expected_hash = bot["sql_contract"]["metadata_hash"]
    assert changed_hash != expected_hash
    with pytest.raises((ValueError, RuntimeError)):
        sql_observation(bot, prior, collected)
    assert bot["sql_contract"]["metadata_hash"] == expected_hash


def cli_fixture(monkeypatch, tmp_path):
    import hashlib
    import sys
    from types import SimpleNamespace

    import core.export_startup_windows as windows
    import scripts.prepare_k98_update as preparer
    import scripts.recovery_release_seed as helper
    import scripts.verify_k98_update_pair as verifier

    candidate, collected, _, policy = seed_fixture(monkeypatch)
    config = dict(
        release_id=str(uuid4()),
        root=str(tmp_path),
        sid="fixture",
        new_policy=policy,
        recovery_seed="live_sql_observation_v1",
        seed_members=[
            dict(name=n, sha256=hashlib.sha256(b).hexdigest()) for n, b in candidate.items()
        ],
    )
    for name, raw in candidate.items():
        (tmp_path / name).write_bytes(raw)
    binding = tmp_path / "ReleaseBindings.json"
    binding.write_bytes(encode(config))
    args = ["helper", "--bindings", str(binding), "--sha256", checksum(config)]
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(
        helper, "sys", SimpleNamespace(flags=SimpleNamespace(isolated=1), path=sys.path)
    )
    monkeypatch.setattr(windows, "administrative_path", lambda p, **_: p)
    monkeypatch.setattr(verifier, "verify_bot_sql_contracts", lambda _: deepcopy(collected))
    monkeypatch.setattr(
        helper,
        "load_release_verifier",
        lambda _: {"verify_bot_sql_contracts": verifier.verify_bot_sql_contracts},
    )
    original_writers = preparer.output_writers
    monkeypatch.setattr(
        preparer, "output_writers", lambda sid, **_: original_writers(sid, secure_output=False)
    )
    return helper, args, collected


def test_cli_retains_actual_evidence_and_verifies_same_seed_after_restart(monkeypatch, tmp_path):
    helper, args, collected = cli_fixture(monkeypatch, tmp_path)
    assert helper.main() == 10
    args.append("--create")
    assert helper.main() == 0
    evidence_path = tmp_path / "verified-seed/sql-evidence.json"
    retained = evidence_path.read_bytes()
    assert json.loads(retained)["collected"] == collected
    args.remove("--create")
    assert helper.main() == 0
    assert evidence_path.read_bytes() == retained


@pytest.mark.parametrize("fail_at", [1, 3, 7])
def test_interrupted_seed_write_resumes_without_replacing_collected_evidence(
    monkeypatch, tmp_path, fail_at
):
    from pathlib import Path

    helper, args, _ = cli_fixture(monkeypatch, tmp_path)
    args.append("--create")
    original = Path.rename
    calls = 0

    def interrupted(path, target):
        nonlocal calls
        calls += 1
        if calls == fail_at:
            raise OSError("simulated interruption before atomic publication")
        return original(path, target)

    monkeypatch.setattr(Path, "rename", interrupted)
    with pytest.raises(OSError, match="simulated interruption"):
        helper.main()
    proof = tmp_path / "verified-seed/sql-evidence.json"
    retained = proof.read_bytes() if proof.exists() else None
    monkeypatch.setattr(Path, "rename", original)
    args.remove("--create")
    assert helper.main() == 11
    args.append("--create")
    assert helper.main() == 0
    if retained is not None:
        assert proof.read_bytes() == retained


@pytest.mark.parametrize(
    "damage",
    ["foreign_release", "wrong_bindings", "tampered_catalog", "tampered_seed", "unexpected_file"],
)
def test_restart_refuses_corrupted_or_foreign_evidence(monkeypatch, tmp_path, damage):
    helper, args, _ = cli_fixture(monkeypatch, tmp_path)
    args.append("--create")
    assert helper.main() == 0
    folder = tmp_path / "verified-seed"
    proof = json.loads((folder / "sql-evidence.json").read_bytes())
    if damage == "foreign_release":
        proof["release_id"] = str(uuid4())
    elif damage == "wrong_bindings":
        proof["bindings_sha256"] = "0" * 64
    elif damage == "tampered_catalog":
        proof["collected"]["installation"]["target"]["DatabaseOwner"] = 1
    elif damage == "tampered_seed":
        (folder / "bot-template.json").write_bytes(b"{}")
    else:
        (folder / "unreviewed.json").write_bytes(b"{}")
    (folder / "sql-evidence.json").write_bytes(encode(proof))
    with pytest.raises((ValueError, RuntimeError)):
        helper.main()


def test_failed_live_verification_writes_no_seed_or_observation(monkeypatch, tmp_path):
    import scripts.verify_k98_update_pair as verifier

    helper, args, _ = cli_fixture(monkeypatch, tmp_path)
    args.append("--create")

    def failed(_):
        raise RuntimeError("live SQL contract mismatch")

    monkeypatch.setattr(verifier, "verify_bot_sql_contracts", failed)
    with pytest.raises(RuntimeError, match="live SQL contract mismatch"):
        helper.main()
    assert not (tmp_path / "verified-seed").exists()


@pytest.mark.parametrize("drift", [None, "installation", "legacy", "application"])
def test_live_collector_returns_actual_rows_only_after_all_comparisons(monkeypatch, drift):
    from types import SimpleNamespace
    from unittest.mock import Mock

    import kvk.dal.new_source_admin_dal as connection_dal
    from scripts.verify_k98_update_pair import verify_bot_sql_contracts
    import services.export_execution_dal as dal
    import services.export_runtime_composition as composition

    bot, _, collected = evidence(monkeypatch)
    if drift == "installation":
        collected[drift]["target"]["DatabaseOwner"] = 1
    elif drift == "legacy":
        collected[drift]["modules"][0]["ModuleDefinition"] = "unexpected body"
    elif drift == "application":
        collected[drift]["column_permissions"][0]["Allowed"] = 0
    connection, cursor = Mock(), Mock()
    connection.cursor.return_value = cursor
    factory = Mock(return_value=connection)
    monkeypatch.setattr(connection_dal, "configured_connection", factory)
    monkeypatch.setattr(
        dal,
        "ExportExecutionDAL",
        lambda _: SimpleNamespace(installation_snapshot=lambda **__: collected["installation"]),
    )
    monkeypatch.setattr(dal, "legacy_installation_snapshot", lambda *_: collected["legacy"])
    monkeypatch.setattr(
        composition, "application_snapshot_for_contract", lambda *_: collected["application"]
    )
    if drift:
        with pytest.raises((ValueError, RuntimeError)):
            verify_bot_sql_contracts(bot)
    else:
        result = verify_bot_sql_contracts(bot)
        for name in ("installation", "legacy", "application"):
            assert result[name] is collected[name]
        assert result["observed_utc"] != collected["observed_utc"]
    if drift == "installation":
        factory.assert_not_called()
    else:
        cursor.close.assert_called_once()
        connection.close.assert_called_once()
