"""Return/reupgrade uses the installed source and SQL policy, without native execution."""

from copy import deepcopy
import json
import os
from pathlib import Path

import pytest

from scripts import p0a_release as policy
from tests.test_observer_release_policy import release  # noqa: F401


@pytest.fixture(params=list(policy.RETURN_PROFILES))
def transition(request):
    spec, _, environment, _ = request.getfixturevalue("release")
    root = Path(os.environ["K98_OBSERVER_SQL_SOURCE"])
    identity = request.param
    names = [
        "deploy/" + name
        for name in (
            "Deploy-SqlMigration.ps1",
            "SqlDeploy.ModuleRelease.ps1",
            "SqlDeploy.P02D4Release.ps1",
            "SqlDeploy.Phase1Release.ps1",
            "SqlDeploy.P02ObserverRelease.ps1",
            "SqlDeploy.P02ObserverReturn.ps1",
        )
    ] + [
        "migrations/" + identity + suffix
        for suffix in (".sql", ".release.json", ".before.sql", ".after.sql")
    ]
    files = {name: (root / name).read_bytes() for name in names}
    spec["sql"]["profile"] = json.loads(files["migrations/" + identity + ".release.json"])
    spec["sql"]["members"] = [dict(path=n, sha256=policy.sha(b)) for n, b in sorted(files.items())]
    # Pure policy fixture: native issuance still independently validates every
    # typed incarnation field. No fixture identity is a release identity.
    spec["contracts"]["application_sql_contract"]["after"]["observation_installation"] = {
        "sequence_object_id": 1234
    }
    if policy.RETURN_PROFILES[identity][0] == "return":
        for pair in spec["contracts"].values():
            pair["before"], pair["after"] = pair["after"], pair["before"]
    return spec, files, environment


def test_fixed_pair_transports_untouched_sql_and_retains_contracts(transition):
    spec, files, environment = transition
    original = deepcopy(spec)
    policy.validate_specification(spec)
    binding, payload = policy.sql_payload(spec, environment, files.get)
    assert spec == original
    assert len(payload) == 10
    item = binding["profiles"][0]
    assert item["sha256"] == policy.RETURN_PROFILES[item["id"]][1]
    assert payload[item["file"]] == files["migrations/" + item["file"]]
    assert all(policy.sha(payload[r["name"]]) == r["sha256"] for r in binding["members"])


@pytest.mark.parametrize(
    "damage", ["helper", "profile", "sql", "environment", "fixed", "identity", "direction"]
)
def test_return_policy_refuses_incomplete_or_substituted_transition(transition, damage):
    spec, files, environment = transition
    direction = spec["sql"]["profile"]["action"]
    observed = "before" if direction == "return" else "after"
    if damage == "helper":
        spec["sql"]["members"] = [
            r for r in spec["sql"]["members"] if not r["path"].endswith("P02ObserverReturn.ps1")
        ]
    elif damage == "profile":
        spec["sql"]["profile"]["action"] = "reupgrade" if direction == "return" else "return"
    elif damage == "sql":
        files["migrations/" + spec["sql"]["profile"]["migration_id"] + ".sql"] += b"-- drift"
    elif damage == "environment":
        environment["compatibility_level"] = 150
    elif damage == "fixed":
        spec["contracts"]["sql_contract"]["after"]["metadata_hash"] = "f" * 64
    elif damage == "identity":
        del spec["contracts"]["application_sql_contract"][observed]["observation_installation"]
    else:
        for pair in spec["contracts"].values():
            pair["before"], pair["after"] = pair["after"], pair["before"]
    with pytest.raises(ValueError):
        policy.validate_specification(spec)
        policy.sql_payload(spec, environment, files.get)
