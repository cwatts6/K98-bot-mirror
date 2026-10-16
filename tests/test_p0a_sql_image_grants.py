"""Qualification cannot alter a non-fixture DB or accept unreviewed grants."""

from pathlib import Path
import subprocess

import pytest

from scripts.rehearse_p0a_sql_image_grants import install_reference_grants, predecessor_grants


def inputs():
    import json

    root = Path(__file__).resolve().parents[1]
    raw = subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "show",
            "ded19ccda7c3c7ebeeb9379b15a72ae39cb935a4:deploy/s11_application_grants.json",
        ]
    )
    spec = json.loads((root / "scripts/p0a_release_spec.json").read_bytes())
    return raw, {row["name"] for row in spec["sql"]["profile"]["images"]}


@pytest.mark.parametrize(
    "target",
    [
        ("MINI_AMD", "ROK_TRACKER"),
        ("9SX2VF4\\K98DEV", "ROK_TRACKER"),
        ("9SX2VF4\\K98DEV", "S11_G4_Recovery_20260928_97337"),
    ],
)
def test_reference_grants_refuse_non_fixture_before_any_write(target):
    class Connection:
        def execute(self, query):
            assert query.startswith("SELECT ")
            return self

        def fetchone(self):
            return target

    raw, names = inputs()
    with pytest.raises(ValueError, match="local disposable"):
        install_reference_grants(Connection(), raw, names)


def test_unreviewed_plan_and_incomplete_inventory_are_refused():
    raw, names = inputs()
    with pytest.raises(ValueError, match="Exact predecessor"):
        predecessor_grants(raw + b" ", names)
    names.remove("dbo.usp_ExportExecutionSessionTransition")
    with pytest.raises(ValueError, match="Complete affected"):
        predecessor_grants(raw, names)
