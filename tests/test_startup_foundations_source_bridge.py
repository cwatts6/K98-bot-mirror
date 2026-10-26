"""Historical assertions retain exact bytes; this grants no deployment capability."""

import json
from pathlib import Path

import pytest

from tests.updater_source_assertions import before_startup_foundations_hash


@pytest.mark.parametrize("damage", ["source", "mapping"])
def test_exact_successor_bridge_rejects_unreviewed_changes(tmp_path, damage):
    root = Path(__file__).resolve().parents[1]
    fixture = Path("tests/fixtures/p1_startup_source_pairs.json")
    (tmp_path / fixture).parent.mkdir(parents=True)
    raw = (root / fixture).read_bytes()
    (tmp_path / fixture).write_bytes(raw)
    member = json.loads(raw)[0]
    path = member["path"]
    (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / path).write_bytes((root / path).read_bytes())
    assert before_startup_foundations_hash(tmp_path, path) == member["before"]
    if damage == "source":
        (tmp_path / path).write_bytes(b"unreviewed replacement")
    else:
        (tmp_path / fixture).write_bytes(raw + b" ")
    with pytest.raises(AssertionError):
        before_startup_foundations_hash(tmp_path, path)
