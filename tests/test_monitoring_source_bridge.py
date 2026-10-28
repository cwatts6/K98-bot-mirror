"""Local successor assertions do not grant production installation authority."""

import json
from pathlib import Path

import pytest

from tests.updater_source_assertions import before_monitoring_hash


@pytest.mark.parametrize("damage", ["source", "mapping", "missing"])
def test_monitoring_bridge_requires_exact_mapping_and_source(tmp_path, damage):
    root = Path(__file__).resolve().parents[1]
    fixture = Path("tests/fixtures/p1_monitoring_source_pairs.json")
    raw = (root / fixture).read_bytes()
    (tmp_path / fixture).parent.mkdir(parents=True)
    (tmp_path / fixture).write_bytes(raw)
    mge = Path("tests/fixtures/p1_mge_lifecycle_source_pairs.json")
    (tmp_path / mge).write_bytes((root / mge).read_bytes())
    attempt = Path("tests/fixtures/procconfig_admission_source_pairs.json")
    (tmp_path / attempt).write_bytes((root / attempt).read_bytes())
    lifecycle = Path("tests/fixtures/coordination_lifecycle_source_pairs.json")
    (tmp_path / lifecycle).write_bytes((root / lifecycle).read_bytes())
    checkpoint = Path("tests/fixtures/checkpoint_observation_source_pairs.json")
    (tmp_path / checkpoint).write_bytes((root / checkpoint).read_bytes())
    health = Path("tests/fixtures/health_activity_source_pairs.json")
    (tmp_path / health).write_bytes((root / health).read_bytes())
    member = json.loads(raw)[0]
    path = member["path"]
    (tmp_path / path).write_bytes((root / path).read_bytes())
    assert before_monitoring_hash(tmp_path, path) == member["before"]
    if damage == "source":
        (tmp_path / path).write_bytes(b"unreviewed replacement")
    elif damage == "mapping":
        (tmp_path / fixture).write_bytes(raw + b" ")
    else:
        (tmp_path / fixture).unlink()
    with pytest.raises((AssertionError, FileNotFoundError)):
        before_monitoring_hash(tmp_path, path)
