from __future__ import annotations

REMINDER_DAILY = "daily"

# REMINDER_FINAL_DAY: deprecated — no longer dispatched as of Phase G+H.
# Retained here only for state-key compatibility so existing serialised keys
# in ark_reminder_state.json are not orphaned.  Do not use in new code.
REMINDER_FINAL_DAY = "final_day"

# REMINDER_24H: retained for state-key compatibility but no longer dispatched.
# The 24h channel reminder was removed (overlaps with daily registration repost).
# The 24h DM was removed at the same time.
REMINDER_24H = "24h"
REMINDER_4H = "4h"
REMINDER_1H = "1h"
REMINDER_START = "start"
REMINDER_CHECKIN_12H = "checkin_12h"
REMINDER_REGISTRATION_CLOSE_1H = "registration_close_1h"

ALL_DM_REMINDER_TYPES = {
    REMINDER_24H,
    REMINDER_4H,
    REMINDER_1H,
    REMINDER_START,
    REMINDER_CHECKIN_12H,
}
