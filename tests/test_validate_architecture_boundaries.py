from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_architecture_boundaries import validate_files


def _write(root: Path, relative: str, content: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_sql_in_command_fails(tmp_path: Path) -> None:
    command = _write(
        tmp_path,
        "commands/stats_cmds.py",
        'def handler():\n    query = "SELECT * FROM KVK.Player"\n',
    )

    findings = validate_files(tmp_path, [command])

    assert len(findings) == 1
    assert findings[0].message == "SQL keyword found in command layer"
    assert findings[0].path == "commands/stats_cmds.py"


def test_allow_override_suppresses_architecture_findings(tmp_path: Path) -> None:
    command = _write(
        tmp_path,
        "commands/admin_cmds.py",
        '# architecture-check: allow\nquery = "SELECT 1"\n',
    )

    assert validate_files(tmp_path, [command]) == []


def test_allow_marker_does_not_suppress_distant_violations(tmp_path: Path) -> None:
    """A single allow marker at the top must not suppress violations elsewhere."""
    command = _write(
        tmp_path,
        "commands/admin_cmds.py",
        '# architecture-check: allow\n\n\nquery = "SELECT 1"\n',
    )

    findings = validate_files(tmp_path, [command])
    assert len(findings) == 1
    assert findings[0].message == "SQL keyword found in command layer"


def test_dal_import_in_view_fails(tmp_path: Path) -> None:
    view = _write(
        tmp_path,
        "ui/views/mge_signup_view.py",
        "from mge.dal import mge_signup_dal\n",
    )

    findings = validate_files(tmp_path, [view])

    assert len(findings) == 1
    assert findings[0].message == "DAL/repository import found in view layer"


def test_discord_reference_in_service_fails(tmp_path: Path) -> None:
    service = _write(
        tmp_path,
        "services/example_service.py",
        "import discord\n\ndef build_embed() -> discord.Embed:\n    ...\n",
    )

    findings = validate_files(tmp_path, [service])

    assert len(findings) == 2
    assert {finding.message for finding in findings} == {
        "Discord type/reference found in service layer"
    }


def test_discord_reference_in_root_level_service_fails(tmp_path: Path) -> None:
    """Root-level service files must be validated even though they're not in a sub-directory."""
    service = _write(
        tmp_path,
        "stats_service.py",
        "import discord\n\ndef build_embed() -> discord.Embed:\n    ...\n",
    )

    findings = validate_files(tmp_path, [service])

    assert len(findings) >= 1
    assert all(
        finding.message == "Discord type/reference found in service layer" for finding in findings
    )
