from __future__ import annotations

from scripts.select_tests import select_tests


def test_select_tests_maps_stats_commands() -> None:
    commands = select_tests(["commands/stats_cmds.py"])

    assert "python -m pytest -q tests/test_stats_service.py tests/test_mykvkstats.py" in commands
    assert "python scripts/smoke_imports.py" in commands
    assert "python scripts/validate_command_registration.py" in commands


def test_select_tests_stats_service_triggers_stats_tests() -> None:
    commands = select_tests(["stats_service.py"])

    assert "python -m pytest -q tests/test_stats_service.py tests/test_mykvkstats.py" in commands


def test_stats_alerts_excludes_stats_service_tests() -> None:
    """stats_alerts/ is a separate subsystem and must not pull in stats service tests."""
    commands = select_tests(["stats_alerts/some_module.py"])

    assert (
        "python -m pytest -q tests/test_stats_service.py tests/test_mykvkstats.py" not in commands
    )


def test_select_tests_maps_subsystems_and_deduplicates() -> None:
    commands = select_tests(
        ["ark/draft_service.py", "ark/ark_scheduler.py", "ui/views/ark_views.py"]
    )

    assert commands.count("python -m pytest -q tests/test_ark_*.py") == 1
    assert "python -m pytest -q tests/test_ui_imports.py" in commands


def test_select_tests_includes_full_tests_for_test_changes() -> None:
    commands = select_tests(["tests/test_select_tests.py"])

    assert "python -m pytest -q tests" in commands
