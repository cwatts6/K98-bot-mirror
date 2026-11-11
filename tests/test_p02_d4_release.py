"""Exact D4 combined admission; fixtures never grant live installation authority."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import prepare_k98_update as updater
from services.export_execution_protocol import encode

ROOT = Path(__file__).resolve().parents[1]


def descriptor():
    return dict(
        version=4,
        profile="p02_d4_v1",
        bot_predecessors=[updater.D4_PREDECESSOR],
        sql_commit=updater.D4_SQL_COMMIT,
        migrations=[dict(id=updater.D4_MIGRATION, sha256=updater.D4_PROFILE_HASH)],
        contract_transition=updater.D4_CONTRACT_TRANSITION,
    )


def test_committed_descriptor_and_coordination_boundary():
    assert json.loads((ROOT / updater.RELEASE_DESCRIPTION).read_bytes()) == descriptor()
    assert (
        updater.combined_description(encode(descriptor()), updater.D4_PREDECESSOR) == descriptor()
    )
    from services.export_execution_dal import INSTALLATION_OBJECTS

    assert len(updater.D4_OBJECTS) == 30
    assert not {n.casefold() for n in updater.D4_OBJECTS} & {
        n.casefold() for n in INSTALLATION_OBJECTS
    }


@pytest.mark.parametrize("field", list(descriptor()) + ["extra"])
def test_descriptor_drift_refuses(field):
    value = descriptor()
    value[field] = "unreviewed"
    with pytest.raises(ValueError):
        updater.validate_combined_description(encode(value))


@pytest.mark.parametrize("version", [1, 2, 3, True, 5])
def test_d4_cannot_masquerade_as_historical_descriptor(version):
    value = descriptor()
    value["version"] = version
    with pytest.raises(ValueError):
        updater.validate_combined_description(encode(value))


def test_source_only_incomplete_and_wrong_predecessor_adoption_refuse():
    files = {"services/export_d4_contract.py": b"fixture"}
    read = lambda rev, path: files.get(path) if rev == "target" else None
    with pytest.raises(ValueError, match="combined SQL descriptor"):
        updater.check_d4_release_binding(updater.D4_PREDECESSOR, "target", files, read)
    files[updater.RELEASE_DESCRIPTION] = encode(descriptor())
    with pytest.raises(ValueError, match="Complete D4 source"):
        updater.check_d4_release_binding(updater.D4_PREDECESSOR, "target", files, read)
    updater.check_d4_release_binding(
        updater.D4_PREDECESSOR, "target", updater.P02_D4_COMBINED_PATHS, read
    )
    with pytest.raises(ValueError):
        updater.check_d4_release_binding("a" * 40, "target", updater.P02_D4_COMBINED_PATHS, read)


@pytest.fixture
def contract_pair(monkeypatch):
    # Real private before/after hashes are independently exercised from receipts.
    bot = {
        key: dict(principal="fixture", metadata_hash="before") for key in updater.D4_CONTRACT_PINS
    }
    expected = deepcopy(bot)
    for key, updates in updater.D4_CONTRACT_UPDATES.items():
        expected[key].update(updates)
        field, path = updater.D4_SOURCE_FILES[key]
        expected[key][field] = json.loads((ROOT / path).read_bytes())
    monkeypatch.setattr(
        updater,
        "D4_CONTRACT_PINS",
        {
            key: dict(
                before=updater.sha256(encode(bot[key])),
                after=updater.sha256(encode(expected[key])),
            )
            for key in bot
        },
    )
    return bot, expected


def read_source(_revision, path):
    return (ROOT / path).read_bytes()


def test_contract_transition_preserves_input_and_coordination(contract_pair):
    bot, expected = contract_pair
    original = deepcopy(bot)
    result = updater.d4_contract_transition(
        {"bot-template.json": bot}, descriptor(), read_source, "target"
    )
    assert {key: pair["after"] for key, pair in result["contracts"].items()} == expected
    assert (
        result["contracts"]["sql_contract"]["before"]
        == result["contracts"]["sql_contract"]["after"]
    )
    result["contracts"]["sql_contract"]["after"]["principal"] = "changed"
    assert bot == original


@pytest.mark.parametrize("key", list(updater.D4_CONTRACT_PINS))
def test_any_predecessor_contract_drift_refuses_including_coordinator(contract_pair, key):
    bot, _ = contract_pair
    bot[key]["principal"] = "unreviewed"
    with pytest.raises(ValueError, match="predecessor startup contract"):
        updater.d4_contract_transition(
            {"bot-template.json": bot}, descriptor(), read_source, "target"
        )


@pytest.mark.parametrize("key", list(updater.D4_SOURCE_FILES))
def test_candidate_source_drift_refuses(contract_pair, key):
    bot, _ = contract_pair
    damaged = updater.D4_SOURCE_FILES[key][1]
    read = lambda rev, path: b"{}" if path == damaged else read_source(rev, path)
    with pytest.raises(ValueError, match="successor startup contract"):
        updater.d4_contract_transition({"bot-template.json": bot}, descriptor(), read, "target")


def test_registry_preserves_all_historical_entries_and_original_byte_bound():
    raw = (ROOT / "scripts/k98_update_transitions.json").read_bytes().replace(b"\r\n", b"\n")
    transitions = updater.reviewed_transitions()
    assert len(transitions) == 89
    prior = dict(version=1, transitions=transitions[:88])
    # Exact canonical digest of the already merged 88-entry registry.
    assert (
        hashlib.sha256(encode(prior)).hexdigest()
        == "00a61cb85ff2180b4261a42d4848f0d0a2732037e01d9ef3e174d9582d5b1b1a"
    )
    assert len(raw.replace(b"\n", b"\r\n")) <= 232448
    current = transitions[-1]
    assert current["id"] == updater.D4_CONTRACT_TRANSITION
    assert {m["path"] for m in current["members"]} == updater.P02_D4_COMBINED_PATHS
    for member in current["members"]:
        assert (
            updater.sha256((ROOT / member["path"]).read_bytes().replace(b"\r\n", b"\n"))
            == member["after_sha256"]
        )


def test_partial_or_foreign_family_never_matches_installed_registry():
    entry = updater.reviewed_transitions()[-1]
    # Content need not be synthetic hash preimages: patch only the hashing
    # boundary, leaving complete-pair and unchanged-peer admission real.
    assert any(m["before_sha256"] == m["after_sha256"] for m in entry["members"])
    with pytest.raises(ValueError, match="not installed/reviewed"):
        updater.check_protocol_transition(
            "services/export_d4_contract.py", lambda *_: b"foreign", "before", "target"
        )


def test_complete_packet_orders_sql_before_source_and_binds_new_seed(
    tmp_path, monkeypatch, contract_pair
):
    """Exercise real package/seed wiring; SQL bytes and identities are inert fixtures."""
    from pathlib import PureWindowsPath

    from scripts.prepare_k98_release import validate_updater_manifest
    import services.export_runtime_composition as composition
    from tests.test_export_release_seed import predecessor
    from tests.updater_source_assertions import installed_tool_fixture

    bot, expected = contract_pair
    bot["legacy_sql_contract"]["source"] = {"modules": []}
    monkeypatch.setitem(
        updater.D4_CONTRACT_PINS["legacy_sql_contract"],
        "before",
        updater.sha256(encode(bot["legacy_sql_contract"])),
    )
    previous = predecessor(tmp_path, monkeypatch)
    previous["bot-template.json"].update(deepcopy(bot))
    previous["authority-template.json"]["sql_contract"] = deepcopy(bot["sql_contract"])
    plan = previous["ManualProcessPairPlan-CANDIDATE.json"]
    for role in ("bot", "authority"):
        plan["templates"][role]["sha256"] = updater.sha256(
            encode(previous[role + "-template.json"])
        )
    policy = previous["AutomaticStartupPolicy.json"]
    policy["seed_plan"]["sha256"] = updater.sha256(encode(plan))
    path = str(
        PureWindowsPath(policy["seed_plan"]["path"]).with_name("AutomaticStartupPolicy.json")
    )
    tools, archive_hash = installed_tool_fixture(tmp_path)
    observation = dict(
        seed=previous,
        gate=f"$policy='{path}'\n$policyHash='{updater.sha256(encode(policy))}'\n",
        bindings=dict(
            before=updater.D4_PREDECESSOR,
            target="d" * 40,
            root="C:\\fixture",
            host="FIXTURE",
            sid="S-1-5-21-1-2-3-1001",
            old_policy=dict(Path=path, SHA256=updater.sha256(encode(policy))),
            old_plan=dict(Python="C:\\fixture\\python.exe", PythonSHA256="a" * 64),
            contract_verifier_sha256=archive_hash,
        ),
    )
    # Exact source-family admission has independent tests and the private receipt
    # rehearsal; here isolate packet wiring from synthetic predecessor source.
    monkeypatch.setattr(
        updater,
        "source_plan",
        lambda *args, **kwargs: (
            dict(
                before=updater.D4_PREDECESSOR,
                target="d" * 40,
                source_members=[],
                new_pins=policy["source_hashes"],
            ),
            {},
        ),
    )
    protected = {"dbo.UnrelatedProtected", *updater.D4_OBJECTS}
    monkeypatch.setattr(composition, "application_contract_scope", lambda _: protected)
    profile = encode(dict(images=[dict(name=name) for name in sorted(updater.D4_OBJECTS)]))
    batch = b"-- inert test fixture; never executed\n"
    monkeypatch.setattr(updater, "D4_PROFILE_HASH", updater.sha256(profile))
    monkeypatch.setattr(updater, "D4_SCRIPT_HASH", updater.sha256(batch))
    sql_files = {
        "deploy/" + name: b"# inert fixture\n"
        for name in (
            *updater.SQL_TOOLS,
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.RecoveryRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
        )
    }
    sql_files["migrations/" + updater.D4_MIGRATION + ".release.json"] = profile
    sql_files["migrations/" + updater.D4_MIGRATION + ".sql"] = batch

    def read(revision, name):
        if name == updater.RELEASE_DESCRIPTION:
            return encode(descriptor()) if revision == "d" * 40 else None
        return read_source(revision, name)

    result = updater.prepare_update(
        observation, [], read, tmp_path / "packet", tools, read_sql_blob=sql_files.get
    )
    package = Path(result["manifest"]).parent
    manifest = json.loads(Path(result["manifest"]).read_bytes())
    validate_updater_manifest(manifest)
    assert [step["kind"] for step in manifest["steps"]] == [
        "sql",
        "source",
        "seed",
        "start",
        "readiness",
    ]
    assert manifest["steps"][0]["apply"]["arguments"]["MigrationId"] == updater.D4_MIGRATION
    delivered = json.loads((package / "bot-template.json").read_bytes())
    assert {key: delivered[key] for key in expected} == expected
    assert (
        json.loads((package / "AutomaticStartupPolicy.json").read_bytes())["flags"]
        == policy["flags"]
    )
    for member in manifest["members"]:
        assert updater.sha256((package / member["name"]).read_bytes()) == member["sha256"]
    # Candidate retains old observation: only post-SQL real verification can
    # publish successful successor proof; packaging cannot invent that proof.
    assert (
        json.loads((package / "sql_installation.json").read_bytes())["observations"]
        == previous["sql_installation.json"]["observations"]
    )
