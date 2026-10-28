"""The local source bridge authenticates bytes and cannot approve installation."""

import json
from pathlib import Path

import pytest

from tests.updater_source_assertions import before_mge_lifecycle_hash


@pytest.mark.parametrize("damage", ["source", "mapping", "missing"])
def test_mge_bridge_rejects_unknown_successor(tmp_path, damage):
    root = Path(__file__).resolve().parents[1]
    fixture = Path("tests/fixtures/p1_mge_lifecycle_source_pairs.json")
    raw = (root / fixture).read_bytes()
    (tmp_path / fixture).parent.mkdir(parents=True)
    (tmp_path / fixture).write_bytes(raw)
    member = json.loads(raw)[0]
    path = member["path"]
    (tmp_path / path).write_bytes((root / path).read_bytes())
    assert before_mge_lifecycle_hash(tmp_path, path) == member["before"]
    if damage == "source":
        (tmp_path / path).write_bytes(b"unknown source")
    elif damage == "mapping":
        (tmp_path / fixture).write_bytes(raw + b" ")
    else:
        (tmp_path / fixture).unlink()
    with pytest.raises((AssertionError, FileNotFoundError)):
        before_mge_lifecycle_hash(tmp_path, path)
