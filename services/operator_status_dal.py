"""Read-only SQL connectivity check, outside command modules."""

from constants import _conn


def check_connection():
    with _conn() as connection:
        connection.execute("SELECT 1")
    return True, "SQL connected"
