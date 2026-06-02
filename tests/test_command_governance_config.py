from __future__ import annotations

from pathlib import Path


def test_pre_commit_runs_command_registration_validator() -> None:
    config = Path(".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "id: validate-command-registration" in config
    assert "entry: python scripts/validate_command_registration.py" in config
    assert "pass_filenames: false" in config


def test_command_governance_workflow_runs_validator_and_focused_tests() -> None:
    workflow = Path(".github/workflows/command-governance.yml").read_text(encoding="utf-8")

    assert "python scripts/validate_command_registration.py" in workflow
    assert "command-registration-inventory.md" in workflow
    assert (
        "python -m pytest -q tests/test_validate_command_registration.py "
        "tests/test_command_inventory.py tests/test_command_registration_smoke.py"
    ) in workflow
