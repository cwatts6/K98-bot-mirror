"""Local source mappings authenticate successors without authorizing deployment."""

import json
from pathlib import Path

import pytest

from tests.updater_source_assertions import before_a1a_hash


@pytest.mark.parametrize("damage", ["source", "mapping", "missing"])
def test_a1a_bridge_rejects_unknown_successor(tmp_path, damage):
    root = Path(__file__).resolve().parents[1]
    fixture = Path("tests/fixtures/p1_a1a_source_pairs.json")
    raw = (root / fixture).read_bytes()
    (tmp_path / fixture).parent.mkdir(parents=True)
    (tmp_path / fixture).write_bytes(raw)
    member = json.loads(raw)[0]
    path = member["path"]
    (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / path).write_bytes((root / path).read_bytes())
    assert before_a1a_hash(tmp_path, path) == member["before"]
    if damage == "source":
        (tmp_path / path).write_bytes(b"unknown source")
    elif damage == "mapping":
        (tmp_path / fixture).write_bytes(raw + b" ")
    else:
        (tmp_path / fixture).unlink()
    with pytest.raises(AssertionError):
        assert before_a1a_hash(tmp_path, path) == member["before"]
