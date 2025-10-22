# test_time_and_format.py
"""
Unit tests for stats_alert.time_and_format module.

Tests cover format_date_utc and format_time_utc with various input types:
- None values
- datetime.date objects
- naive datetime objects
- aware datetime objects (UTC)
"""

from datetime import UTC, date, datetime
import os
import sys

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stats_alert.time_and_format import format_date_utc, format_time_utc


def test_format_date_utc_with_none():
    """Test format_date_utc returns 'TBD' for None input."""
    assert format_date_utc(None) == "TBD"


def test_format_date_utc_with_date():
    """Test format_date_utc with datetime.date object."""
    d = date(2025, 1, 2)
    result = format_date_utc(d)
    assert result == "02 Jan 2025"


def test_format_date_utc_with_naive_datetime():
    """Test format_date_utc with naive datetime object."""
    dt = datetime(2025, 1, 2, 10, 30, 45)
    result = format_date_utc(dt)
    assert result == "02 Jan 2025"


def test_format_date_utc_with_aware_datetime():
    """Test format_date_utc with aware datetime object (UTC)."""
    dt = datetime(2025, 1, 2, 10, 30, 45, tzinfo=UTC)
    result = format_date_utc(dt)
    assert result == "02 Jan 2025"


def test_format_date_utc_custom_format():
    """Test format_date_utc with custom format string."""
    dt = datetime(2025, 1, 2, 10, 30, 45)
    result = format_date_utc(dt, fmt="%d %b")
    assert result == "02 Jan"


def test_format_date_utc_full_month():
    """Test format_date_utc with full month name."""
    dt = datetime(2025, 1, 2)
    result = format_date_utc(dt, fmt="%d %B %Y")
    assert result == "02 January 2025"


def test_format_time_utc_with_none():
    """Test format_time_utc returns '—' for None input."""
    assert format_time_utc(None) == "—"


def test_format_time_utc_with_naive_datetime():
    """Test format_time_utc with naive datetime object."""
    dt = datetime(2025, 1, 2, 14, 30, 45)
    result = format_time_utc(dt)
    assert result == "14:30:45"


def test_format_time_utc_with_aware_datetime():
    """Test format_time_utc with aware datetime object (UTC)."""
    dt = datetime(2025, 1, 2, 14, 30, 45, tzinfo=UTC)
    result = format_time_utc(dt)
    assert result == "14:30:45"


def test_format_time_utc_custom_format():
    """Test format_time_utc with custom format string."""
    dt = datetime(2025, 1, 2, 14, 30, 45)
    result = format_time_utc(dt, fmt="%H:%M")
    assert result == "14:30"


def test_format_time_utc_midnight():
    """Test format_time_utc at midnight."""
    dt = datetime(2025, 1, 2, 0, 0, 0)
    result = format_time_utc(dt)
    assert result == "00:00:00"


def test_format_time_utc_end_of_day():
    """Test format_time_utc at end of day."""
    dt = datetime(2025, 1, 2, 23, 59, 59)
    result = format_time_utc(dt)
    assert result == "23:59:59"


# Run tests if executed directly
if __name__ == "__main__":
    print("Running tests for time_and_format module...")

    test_format_date_utc_with_none()
    print("✓ test_format_date_utc_with_none")

    test_format_date_utc_with_date()
    print("✓ test_format_date_utc_with_date")

    test_format_date_utc_with_naive_datetime()
    print("✓ test_format_date_utc_with_naive_datetime")

    test_format_date_utc_with_aware_datetime()
    print("✓ test_format_date_utc_with_aware_datetime")

    test_format_date_utc_custom_format()
    print("✓ test_format_date_utc_custom_format")

    test_format_date_utc_full_month()
    print("✓ test_format_date_utc_full_month")

    test_format_time_utc_with_none()
    print("✓ test_format_time_utc_with_none")

    test_format_time_utc_with_naive_datetime()
    print("✓ test_format_time_utc_with_naive_datetime")

    test_format_time_utc_with_aware_datetime()
    print("✓ test_format_time_utc_with_aware_datetime")

    test_format_time_utc_custom_format()
    print("✓ test_format_time_utc_custom_format")

    test_format_time_utc_midnight()
    print("✓ test_format_time_utc_midnight")

    test_format_time_utc_end_of_day()
    print("✓ test_format_time_utc_end_of_day")

    print("\nAll tests passed! ✓")
