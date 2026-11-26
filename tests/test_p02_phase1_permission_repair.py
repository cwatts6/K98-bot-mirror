"""Exact permission-order amendment; never a new SQL or privilege operation."""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from scripts import prepare_k98_update as updater, verify_k98_update_pair as verifier
from services.export_execution_protocol import encode


@pytest.fixture
def bot(monkeypatch):
    application = {
        "version": 3,
        "metadata_hash": "unchanged schema",
        "permissions_hash": "wrongly ordered projection",
        "scope_hash": "unchanged scope",
        "sources": [{"name": "dbo.MixedCase", "type": "U"}],
        "principal": "restricted",
        "review_id": "original",
    }
    after = deepcopy(application)
    after.update(
        permissions_hash=verifier.PHASE1_PERMISSION_HASH,
        review_id=verifier.PHASE1_PERMISSION_REVIEW,
    )
    monkeypatch.setattr(
        verifier, "PHASE1_PERMISSION_BEFORE", hashlib.sha256(encode(application)).hexdigest()
    )
    monkeypatch.setattr(
        verifier, "PHASE1_PERMISSION_AFTER", hashlib.sha256(encode(after)).hexdigest()
    )
    return {
        "application_sql_contract": application,
        "legacy_sql_contract": {"migration": "already applied"},
        "sql_contract": {"profile": "unchanged coordination"},
    }


def config():
    return {
        "before": verifier.PHASE1_PERMISSION_REPAIR["predecessor"],
        "application_contract_repair": deepcopy(verifier.PHASE1_PERMISSION_REPAIR),
    }


def candidate(bot):
    transition = verifier.phase1_permission_transition(config()["before"], bot)
    return {key: pair["after"] for key, pair in transition["contracts"].items()}


def test_only_exact_permission_fingerprint_and_review_identity_change(bot):
    original = deepcopy(bot)
    after = candidate(bot)
    assert verifier.repair_verification_bot(config(), bot, after) == after
    assert {
        key
        for key in bot["application_sql_contract"]
        if bot["application_sql_contract"][key] != after["application_sql_contract"][key]
    } == {"permissions_hash", "review_id"}
    assert after["sql_contract"] == bot["sql_contract"]
    assert after["legacy_sql_contract"] == bot["legacy_sql_contract"]
    after["application_sql_contract"]["sources"][0]["name"] = "changed"
    assert bot == original


@pytest.mark.parametrize(
    "field",
    ["version", "metadata_hash", "permissions_hash", "scope_hash", "sources", "principal", "extra"],
)
def test_changed_predecessor_is_not_adopted(bot, field):
    bot["application_sql_contract"][field] = "observed replacement"
    with pytest.raises(ValueError, match="predecessor application"):
        candidate(bot)


@pytest.mark.parametrize(
    "damage",
    [
        "predecessor",
        "sql",
        "recovery_seed",
        "marker",
        "marker_bool",
        "extra_marker",
        "application",
        "legacy",
        "coordination",
    ],
)
def test_wrong_candidate_or_extra_sql_work_is_refused(bot, damage):
    bindings, after = config(), candidate(bot)
    if damage == "predecessor":
        bindings["before"] = "f" * 40
    elif damage in {"sql", "recovery_seed"}:
        bindings[damage] = None
    elif damage == "marker":
        bindings["application_contract_repair"]["migration_sha256"] = "0" * 64
    elif damage == "marker_bool":
        bindings["application_contract_repair"]["version"] = True
    elif damage == "extra_marker":
        bindings["application_contract_repair"]["extra"] = "unchecked"
    elif damage == "application":
        after["application_sql_contract"]["permissions_hash"] = "accept arbitrary live rights"
    elif damage == "legacy":
        after["legacy_sql_contract"]["migration"] = "uninstalled"
    else:
        after["sql_contract"]["profile"] = "broader"
    with pytest.raises(ValueError):
        verifier.repair_verification_bot(bindings, bot, after)


def test_corrective_contract_and_future_installation_use_same_reviewed_expectation():
    expected = updater.PHASE1_CONTRACT_UPDATES["application_sql_contract"]
    assert expected["permissions_hash"] == verifier.PHASE1_PERMISSION_HASH
    assert expected["review_id"] == verifier.PHASE1_PERMISSION_REVIEW
    assert updater.PHASE1_CONTRACT_PINS["application_sql_contract"]["after"] == (
        verifier.PHASE1_PERMISSION_AFTER
    )


def test_complete_source_only_packet_preserves_flags_and_rebinds_corrected_seed(
    tmp_path, monkeypatch, bot
):
    from tests.test_p016_application_contract_repair import assert_complete_repair_packet

    assert_complete_repair_packet(
        tmp_path,
        monkeypatch,
        bot,
        verifier.PHASE1_PERMISSION_REPAIR,
        "phase1_permission_transition",
    )


@pytest.mark.skipif(os.name != "nt", reason="Native Windows PowerShell release recovery")
def test_native_partial_release_admission_and_atomic_selection():
    result = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(Path(__file__).with_suffix(".ps1")),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PHASE1_PERMISSION_REPAIR_TESTS_PASSED=26" in result.stdout
