from __future__ import annotations

import pytest

from scripts.select_tests import select_tests


def test_select_tests_maps_stats_commands() -> None:
    commands = select_tests(["commands/stats_cmds.py"])

    assert (
        "python -m pytest -q tests/test_stats_cmds.py "
        "tests/test_leadership_player_review.py tests/test_mykvkstats.py" in commands
    )
    assert "python scripts/smoke_imports.py" in commands
    assert "python scripts/validate_command_registration.py" in commands


def test_select_tests_leadership_player_review_triggers_focused_tests() -> None:
    commands = select_tests(["leadership_player_review/service.py"])

    assert "python -m pytest -q tests/test_leadership_player_review.py" in commands


def test_stats_alerts_excludes_leadership_player_review_tests() -> None:
    """stats_alerts/ is a separate subsystem and must not pull in stats service tests."""
    commands = select_tests(["stats_alerts/some_module.py"])

    assert "python -m pytest -q tests/test_leadership_player_review.py" not in commands


def test_select_tests_maps_subsystems_and_deduplicates() -> None:
    commands = select_tests(
        ["ark/draft_service.py", "ark/ark_scheduler.py", "ui/views/ark_views.py"]
    )

    assert commands.count("python -m pytest -q tests/test_ark_*.py") == 1
    assert "python -m pytest -q tests/test_ui_imports.py" in commands


def test_select_tests_includes_full_tests_for_test_changes() -> None:
    commands = select_tests(["tests/test_select_tests.py"])

    assert "python -m pytest -q tests" in commands


def test_release_identity_regressions_are_always_selected() -> None:
    for paths in ([], ["docs/readme.md"], ["scripts/prepare_k98_update.py"]):
        commands = select_tests(paths)
        assert any("tests/test_release_identity_regressions.py" in c for c in commands)


@pytest.mark.parametrize(
    "path",
    [
        "scripts/prepare_k98_update.py",
        "scripts/k98_update_transitions.json",
        r"tests\updater_source_assertions.py",
    ],
)
def test_updater_registry_changes_select_reader_and_inventory_checks(path: str) -> None:
    commands = select_tests([path])
    assert any(
        "tests/test_updater_reader_capabilities.py" in command
        and "tests/test_updater_transition_inventory.py" in command
        for command in commands
    )


def test_updater_registry_checks_are_focused_and_deduplicated() -> None:
    commands = select_tests(
        ["scripts/prepare_k98_update.py", "scripts/k98_update_transitions.json"]
    )
    assert sum("test_updater_reader_capabilities.py" in command for command in commands) == 1
    assert not any(
        "test_updater_reader_capabilities.py" in command
        for command in select_tests(["scripts/smoke_imports.py"])
    )
