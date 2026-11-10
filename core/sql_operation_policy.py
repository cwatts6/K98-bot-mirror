"""Existing SQL operation limits, in their actual units and ownership scopes."""

LOGIN_TIMEOUT_SECONDS = 5
DEFAULT_STATEMENT_SECONDS = 15
METADATA_LOCK_MILLISECONDS = 1000
COORDINATION_HORIZON_SECONDS = 15.0
PRODUCER_ADMISSION_MILLISECONDS = 0
RECOVERY_STATEMENT_SECONDS = 3
RECOVERY_LOCK_MILLISECONDS = 0


def player_statement_seconds(requested, inherited):
    """Legacy 300s config cannot raise the dedicated 15s statement policy."""
    if type(requested) is not int or requested <= 0:
        raise ValueError("Player report statement timeout must be a positive integer.")
    if type(inherited) is not int or inherited < 0:
        raise ValueError("A known SQL connection timeout is required.")
    return min(requested, DEFAULT_STATEMENT_SECONDS, inherited or DEFAULT_STATEMENT_SECONDS)
