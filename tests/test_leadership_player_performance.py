from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from scripts import measure_leadership_player_review as measurement


def test_measurement_case_parser_keeps_private_id_out_of_label() -> None:
    assert measurement._case("recent_dense=123") == ("recent_dense", 123)

    with pytest.raises(argparse.ArgumentTypeError):
        measurement._case("Recent Dense=123")
    with pytest.raises(argparse.ArgumentTypeError):
        measurement._case("governor_123=123")
    with pytest.raises(argparse.ArgumentTypeError):
        measurement._case("recent_dense=0")


def test_measurement_requires_explicit_read_only_confirmation() -> None:
    with pytest.raises(SystemExit, match="confirm-read-only"):
        measurement.main(["--case", "recent_dense=123"])


def test_measurement_harness_is_sequential_and_does_not_clear_sql_caches() -> None:
    source = measurement.Path(measurement.__file__).read_text(encoding="utf-8")

    assert '"case_concurrency": 1' in source
    assert '"sql_reads_per_load_max_concurrent": 3' in source
    assert '"shareable_without_sanitization": False' in source
    assert '"sql_cache_cleared": False' in source
    assert "DBCC FREEPROCCACHE" not in source
    assert "DBCC DROPCLEANBUFFERS" not in source


def test_measurement_output_is_confined_to_ignored_private_root(tmp_path: Path) -> None:
    default_path = measurement._resolve_output_path(measurement._DEFAULT_OUTPUT)

    assert default_path.parent == measurement._PRIVATE_OUTPUT_ROOT
    with pytest.raises(SystemExit, match="phase81_private"):
        measurement._resolve_output_path(tmp_path / "shareable.json")
    with pytest.raises(SystemExit, match=r"\.json"):
        measurement._resolve_output_path(
            measurement._PRIVATE_OUTPUT_ROOT / "phase81-app-timing.txt"
        )
