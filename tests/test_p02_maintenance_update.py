"""Source-only contract correction, exact predecessor and sealed caller gates."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater, verify_k98_update_pair as verifier
from services.application_maintenance_contract import POLICY
from services.export_execution_protocol import encode
from tests.test_p016_application_contract_repair import assert_complete_repair_packet

ROOT = Path(__file__).resolve().parents[1]


def test_all_90_previous_transitions_remain_immutable():
    transitions = updater.reviewed_transitions()
    assert len(transitions) == 94
    assert transitions[90]["id"] == "p02_maintenance_compatibility_v1"
    assert hashlib.sha256(json.dumps(transitions[:90], sort_keys=True).encode()).hexdigest() == (
        "06255ea6b75c30801cc080b41c405d0489bd67bb6554b451f04b565158057ec7"
    )


@pytest.mark.parametrize("path", sorted(updater.P02_MAINTENANCE_COMPATIBILITY_PATHS))
def test_historical_source_bridge_authenticates_each_successor_before_mapping(monkeypatch, path):
    from tests.updater_source_assertions import before_p02_maintenance_hash

    family = next(
        t for t in updater.reviewed_transitions() if t["id"] == "p02_maintenance_compatibility_v1"
    )
    member = next(m for m in family["members"] if m["path"] == path)
    assert before_p02_maintenance_hash(ROOT, path) == member["before_sha256"]
    original = Path.read_bytes
    monkeypatch.setattr(
        Path, "read_bytes", lambda p: original(p) + (b"\n# unknown\n" if p == ROOT / path else b"")
    )
    with pytest.raises(AssertionError):
        before_p02_maintenance_hash(ROOT, path)


@pytest.fixture
def bot(monkeypatch):

    # The complete packet test needs its fixture's real installation contract.
    value = {
        "application_sql_contract": {
            "version": 3,
            "metadata_hash": "fixed-shape",
            "permissions_hash": "fixed-rights",
        },
        "legacy_sql_contract": {"source": {"modules": []}, "principal": "fixture"},
        "sql_contract": {},
    }
    monkeypatch.setattr(
        verifier,
        "P02_MAINTENANCE_BEFORE",
        {k: hashlib.sha256(encode(v)).hexdigest() for k, v in value.items()},
    )
    return value


def config():
    return {
        "before": verifier.P02_MAINTENANCE_REPAIR["predecessor"],
        "application_contract_repair": deepcopy(verifier.P02_MAINTENANCE_REPAIR),
    }


def candidate(bot):
    return {
        k: v["after"]
        for k, v in verifier.p02_maintenance_transition(config()["before"], bot)[
            "contracts"
        ].items()
    }


def test_exact_opt_in_keeps_metadata_rights_sources_and_old_seed(bot):
    before = deepcopy(bot)
    after = candidate(bot)
    assert verifier.repair_verification_bot(config(), bot, after) == after
    assert after["application_sql_contract"] == before["application_sql_contract"] | {
        "maintenance_policy": POLICY,
        "review_id": "3edc8fa5-bb12-5d30-b676-ea2e86af67c2",
    }
    assert bot == before
    assert after["sql_contract"] == bot["sql_contract"]
    assert after["legacy_sql_contract"] == bot["legacy_sql_contract"]


@pytest.mark.parametrize(
    "damage",
    [
        "predecessor",
        "old_application",
        "old_legacy",
        "old_installation",
        "policy",
        "hash",
        "rights",
        "sql",
        "recovery_seed",
        "marker",
    ],
)
def test_mismatched_amendment_or_added_work_cannot_pass(bot, damage):
    cfg, after = config(), candidate(bot)
    if damage == "predecessor":
        cfg["before"] = "f" * 40
    elif damage.startswith("old_"):
        key = {
            "old_application": "application_sql_contract",
            "old_legacy": "legacy_sql_contract",
            "old_installation": "sql_contract",
        }[damage]
        bot[key]["unexpected"] = True
    elif damage in {"sql", "recovery_seed"}:
        cfg[damage] = None
    elif damage == "marker":
        cfg["application_contract_repair"]["version"] = True
    else:
        after["application_sql_contract"][
            {"policy": "maintenance_policy", "hash": "metadata_hash", "rights": "permissions_hash"}[
                damage
            ]
        ] = "drift"
    with pytest.raises(ValueError):
        verifier.repair_verification_bot(cfg, bot, after)


@pytest.mark.parametrize("preflight", [True, False])
def test_real_preflight_and_successor_select_same_exact_candidate(
    tmp_path, monkeypatch, bot, preflight
):
    import core.export_startup_windows as windows

    cfg, after = config(), candidate(bot)

    def save(name, value):
        p = tmp_path / name
        p.write_bytes(encode(value))
        return {"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}

    old = {"seed_plan": save("old-plan.json", {"templates": {"bot": save("old-bot.json", bot)}})}
    old_ref = save("old-policy.json", old)
    cfg["old_policy"] = {"Path": old_ref["path"], "SHA256": old_ref["sha256"]}
    new_ref = save("bot-template.json", after)
    new = {"seed_plan": save("new-plan.json", {"templates": {"bot": new_ref}})}
    cfg["seed_members"] = [{"name": "bot-template.json", "sha256": new_ref["sha256"]}]
    monkeypatch.setattr(windows, "administrative_path", lambda p, **kw: Path(p))
    monkeypatch.setattr(verifier, "__file__", str(tmp_path / "Verify-NewPair.py"))
    verified = []
    monkeypatch.setattr(verifier, "verify_bot_sql_contracts", lambda b: verified.append(b))
    verifier.verify_sql_contracts(cfg, old if preflight else new, preflight=preflight)
    assert verified == [after]


def test_complete_source_seed_start_readiness_packet_never_replays_sql(tmp_path, monkeypatch, bot):
    # Pin the actual fixture installation contract before exercising the whole
    # packet builder; the production authority constants are not altered on disk.
    from tests.test_export_release_seed import predecessor

    installed = predecessor(tmp_path, monkeypatch)["bot-template.json"]["sql_contract"]
    bot["sql_contract"] = installed
    monkeypatch.setitem(
        verifier.P02_MAINTENANCE_BEFORE,
        "sql_contract",
        hashlib.sha256(encode(installed)).hexdigest(),
    )
    family = {
        "id": config()["application_contract_repair"]["id"],
        "members": [
            {
                "path": p,
                "before_sha256": (
                    updater.sha256(b"old\n")
                    if p.endswith("export_runtime_composition.py")
                    else None
                ),
                "after_sha256": updater.sha256(b"new\n"),
            }
            for p in sorted(updater.P02_MAINTENANCE_COMPATIBILITY_PATHS)
        ],
    }
    assert_complete_repair_packet(
        tmp_path,
        monkeypatch,
        bot,
        verifier.P02_MAINTENANCE_REPAIR,
        "p02_maintenance_transition",
        family=family,
    )


def test_historical_registered_source_family_and_current_archive_are_exact():
    from tests.updater_source_assertions import before_schema_transaction_fix_hash

    family = next(
        t
        for t in updater.reviewed_transitions()
        if t["id"] == config()["application_contract_repair"]["id"]
    )
    assert {m["path"] for m in family["members"]} == updater.P02_MAINTENANCE_COMPATIBILITY_PATHS
    for m in family["members"]:
        assert before_schema_transaction_fix_hash(ROOT, m["path"]) == m["after_sha256"]
    assert tuple(sorted(verifier.CONTRACT_ARCHIVE_MEMBERS)) == verifier.CONTRACT_ARCHIVE_MEMBERS
    assert {
        "services/application_maintenance_contract.py",
        "services/application_maintenance_dal.py",
        "services/export_runtime_composition.py",
        "kvk/dal/new_source_import_dal.py",
    } <= set(verifier.CONTRACT_ARCHIVE_MEMBERS)
    assert {"core/sql_connection_custody.py", "core/sql_operation_policy.py"} <= set(
        verifier.CONTRACT_ARCHIVE_MEMBERS
    )
    verifier.build_contract_archive(ROOT)
