from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_deferred_items import validate_file

VALID_DEFERRED = """# Notes

### Deferred Optimisation
- Area: commands/stats_cmds.py
- Type: architecture
- Description: Command contains legacy SQL that should move behind a DAL.
- Suggested Fix: Move query execution into a stats repository function.
- Impact: medium
- Risk: low
- Dependencies:
"""


def test_valid_deferred_item_passes(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text(VALID_DEFERRED, encoding="utf-8")

    assert validate_file(tmp_path, path) == []


def test_missing_deferred_field_fails(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text(
        """### Deferred Optimisation
- Area: commands/stats_cmds.py
- Type: architecture
- Description: Command contains legacy SQL.
- Impact: medium
- Risk: low
- Dependencies:
""",
        encoding="utf-8",
    )

    findings = validate_file(tmp_path, path)

    assert any("Suggested Fix" in finding.message for finding in findings)


def test_vague_deferred_phrase_fails(tmp_path: Path) -> None:
    path = tmp_path / "notes.md"
    path.write_text("We should improve later after this PR.\n", encoding="utf-8")

    findings = validate_file(tmp_path, path)

    assert len(findings) == 1
    assert findings[0].message == "vague deferred-work phrase found"
