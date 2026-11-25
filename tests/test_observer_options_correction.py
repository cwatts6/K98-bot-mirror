"""Fixed forward correction, original incarnation, and independent SQL source pins."""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from scripts import p0a_release as policy
from services import catalogue_observation_contract as contract
from services.catalogue_observation_dal import ObservationContractError
from tests.test_observation_installation_binding import approved
from tests.test_observer_release_policy import release  # noqa: F401


def test_both_protocols_remain_exact_and_do_not_accept_each_other():
    old = approved()
    new = dict(old, protocol_sha256=contract.OPTIONS_PROTOCOL_SHA256)
    a, b = map(contract.ObservationInstallation, (old, new))
    assert a.identity == b.identity
    aa, bb = dict(a.modules), dict(b.modules)
    assert {k for k in aa if aa[k] != bb[k]} == {"tr_P02CatalogueObservation"}
    a.require_modules(aa)
    b.require_modules(bb)
    for owner, modules in ((a, bb), (b, aa)):
        with pytest.raises(ObservationContractError, match="differ"):
            owner.require_modules(modules)


@pytest.mark.parametrize("protocol", [contract.PROTOCOL_SHA256, contract.OPTIONS_PROTOCOL_SHA256])
def test_altered_source_is_never_accepted_for_either_protocol(monkeypatch, protocol):
    monkeypatch.setattr(contract, "read_contract_resource", lambda _: b'{"modules": []}')
    with pytest.raises(ObservationContractError, match="Exact reviewed"):
        contract.reviewed_protocol_modules(protocol)


@pytest.fixture
def correction(request):
    spec, _, environment, _ = request.getfixturevalue("release")
    root = Path(os.environ["K98_OBSERVER_SQL_SOURCE"])
    names = [
        "deploy/" + n
        for n in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.P02ObserverRelease.ps1",
            "SqlDeploy.P02ObserverReturn.ps1",
            "SqlDeploy.P02ObserverOptions.ps1",
        )
    ]
    names += [
        "migrations/" + policy.OPTIONS_MIGRATION + suffix
        for suffix in (".sql", ".release.json", ".before.sql", ".after.sql")
    ]
    files = {n: (root / n).read_bytes() for n in names}
    spec["sql"]["profile"] = json.loads(
        files["migrations/" + policy.OPTIONS_MIGRATION + ".release.json"]
    )
    spec["sql"]["members"] = [dict(path=n, sha256=policy.sha(b)) for n, b in sorted(files.items())]
    for name in ("legacy_sql_contract", "application_sql_contract"):
        spec["contracts"][name]["before"] = deepcopy(spec["contracts"][name]["after"])
    pair = spec["contracts"]["application_sql_contract"]
    pair["before"].update(
        metadata_hash=policy.OPTIONS_BEFORE_METADATA,
        observation_installation=approved(),
        review_id="original",
    )
    pair["after"] = deepcopy(pair["before"])
    pair["after"].update(
        metadata_hash=policy.OPTIONS_AFTER_METADATA, review_id=policy.OPTIONS_REVIEW_ID
    )
    pair["after"]["observation_installation"]["protocol_sha256"] = contract.OPTIONS_PROTOCOL_SHA256
    return spec, files, environment


def test_sql_bytes_and_preserved_original_installation(correction):
    spec, files, environment = correction
    before = deepcopy(spec)
    policy.validate_specification(spec)
    binding, payload = policy.sql_payload(spec, environment, files.get)
    assert spec == before and len(payload) == 11
    assert binding["profiles"][0]["sha256"] == policy.OPTIONS_PROFILE_SHA256
    assert all(policy.sha(payload[r["name"]]) == r["sha256"] for r in binding["members"])


@pytest.mark.parametrize(
    "damage",
    [
        "incarnation",
        "bootstrap",
        "timestamp",
        "protocol",
        "metadata",
        "fixed",
        "legacy",
        "permission",
        "helper",
        "sql",
        "profile",
        "direction",
    ],
)
def test_substituted_or_incomplete_forward_correction_is_refused(correction, damage):
    spec, files, environment = correction
    after = spec["contracts"]["application_sql_contract"]["after"]
    if damage == "incarnation":
        after["observation_installation"]["sequence_object_id"] += 1
    elif damage == "bootstrap":
        after["observation_installation"]["bootstrap_generation"] = 2
    elif damage == "timestamp":
        after["observation_installation"]["sequence_modified"] = "2026-11-25T01:00:00.000000"
    elif damage == "protocol":
        after["observation_installation"]["protocol_sha256"] = contract.PROTOCOL_SHA256
    elif damage == "metadata":
        after["metadata_hash"] = "f" * 64
    elif damage in ("fixed", "legacy"):
        spec["contracts"]["sql_contract" if damage == "fixed" else "legacy_sql_contract"]["after"][
            "changed"
        ] = True
    elif damage == "permission":
        after["permissions_hash"] = "f" * 64
    elif damage == "helper":
        spec["sql"]["members"].pop()
    elif damage == "sql":
        files["migrations/" + policy.OPTIONS_MIGRATION + ".sql"] += b"--changed"
    elif damage == "profile":
        spec["sql"]["profile"]["protocol_sha256"] = "f" * 64
    else:
        for pair in spec["contracts"].values():
            pair["before"], pair["after"] = pair["after"], pair["before"]
    with pytest.raises(ValueError):
        policy.validate_specification(spec)
        policy.sql_payload(spec, environment, files.get)
