"""Qualification cannot alter a non-fixture DB or accept unreviewed grants."""

import hashlib
import json

import pytest

from scripts import rehearse_p0a_sql_image_grants as grants


@pytest.mark.parametrize(
    "target",
    [
        ("MINI_AMD", "ROK_TRACKER"),
        ("9SX2VF4\\K98DEV", "ROK_TRACKER"),
        ("9SX2VF4\\K98DEV", "S11_G4_Recovery_20260928_97337"),
    ],
)
def test_reference_grants_refuse_non_fixture_before_any_write(target, monkeypatch):
    class Connection:
        def execute(self, query):
            assert query.startswith("SELECT ")
            return self

        def fetchone(self):
            return target

    # Isolate the target guard from predecessor-source availability. The real
    # source-plan path is covered by the separate disposable SQL rehearsal.
    monkeypatch.setattr(grants, "predecessor_grants", lambda raw, names: [("dbo.fixed", "EXECUTE")])
    with pytest.raises(ValueError, match="local disposable"):
        grants.install_reference_grants(Connection(), b"unused", {"dbo.fixed"})


def test_unreviewed_plan_and_incomplete_inventory_are_refused(monkeypatch):
    raw = json.dumps(
        {"grants": [{"object": f"dbo.p{n}", "permission": "EXECUTE"} for n in range(13)]}
    ).encode()
    names = {f"dbo.p{n}" for n in range(13)}
    with pytest.raises(ValueError, match="Exact predecessor"):
        grants.predecessor_grants(raw, names)
    monkeypatch.setattr(grants, "PREDECESSOR_PLAN_SHA256", hashlib.sha256(raw).hexdigest())
    names.remove("dbo.p0")
    with pytest.raises(ValueError, match="Complete affected"):
        grants.predecessor_grants(raw, names)
