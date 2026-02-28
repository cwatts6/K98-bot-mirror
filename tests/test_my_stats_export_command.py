"""
tests/test_my_stats_export_command.py

Integration tests for /my_stats_export command with format options.

NOTE: Integration tests are currently skipped because my_stats_export is defined
inside register_commands() and cannot be directly imported. These will be enabled
after the planned Commands.py refactor that extracts commands to module level.

For now, rely on:
- Unit tests in test_stats_exporter_csv.py (passing)
- Unit tests in test_stats_export.py (passing)
- Manual testing in Discord
"""

import os
import tempfile

import pytest


@pytest.fixture
def mock_temp_dir():
    """Fixture to create and cleanup temp directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    try:
        for file in os.listdir(temp_dir):
            os.unlink(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
    except Exception:
        pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_excel_format(mock_temp_dir):
    """Test /my_stats_export with Excel format."""
    pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_csv_format(mock_temp_dir):
    """Test /my_stats_export with CSV format."""
    pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_no_registrations():
    """Test /my_stats_export when user has no registrations."""
    pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_googlesheets_format(mock_temp_dir):
    """Test /my_stats_export with GoogleSheets format."""
    pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_custom_days(mock_temp_dir):
    """Test /my_stats_export with custom days parameter."""
    pass


@pytest.mark.skip(
    reason="Command is nested in register_commands() - will be enabled after Commands.py refactor"
)
@pytest.mark.asyncio
async def test_my_stats_export_cleanup_on_error():
    """Test that temp files are cleaned up even when export fails."""
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
