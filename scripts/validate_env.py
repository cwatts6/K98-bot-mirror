# scripts/validate_env.py
from __future__ import annotations

import os
from pathlib import Path
import sys

print("🔎 Validating environment & config…")

# --- Ensure project root is on sys.path ---
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]  # one level up from scripts/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional debug (uncomment if needed)
# print("cwd =", os.getcwd())
# print("root on path?", PROJECT_ROOT in map(Path, map(Path, sys.path)))

try:
    import bot_config as cfg  # now should resolve from project root
except Exception as e:
    print(f"❌ Failed to import bot_config: {e!r}")
    # Helpful hint if the file is missing or misnamed
    maybe = PROJECT_ROOT / "bot_config.py"
    if not maybe.exists():
        print(f"ℹ️  Expected at: {maybe}")
    sys.exit(1)

issues: list[str] = []

# If you implemented the required-env tracker as suggested:
_fail = getattr(cfg, "_fail_if_required", None)

# Basic required envs your code relies on frequently
required = [
    "GUILD_ID",
    "ADMIN_USER_ID",
    "NOTIFY_CHANNEL_ID",
    "SQL_SERVER",
    "SQL_DATABASE",
    "SQL_USERNAME",
    "SQL_PASSWORD",
]
for k in required:
    if not os.getenv(k):
        issues.append(f"Missing env: {k}")

# Show parsed LEADERSHIP_ROLE_IDS (safe even if empty)
try:
    roles = getattr(cfg, "LEADERSHIP_ROLE_IDS", [])
    print(f"LEADERSHIP_ROLE_IDS parsed -> {roles!r}")
except Exception as e:
    issues.append(f"LEADERSHIP_ROLE_IDS parse error: {e!r}")

# Defer hard failure to the end (keeps import-time safe)
if issues:
    print("\n⚠️  Found issues:")
    for i in issues:
        print(" -", i)
    # if cfg provides fail helper, use it to raise
    if _fail:
        try:
            _fail()
        except Exception as e:
            print(f"\n❌ {e}")
    sys.exit(2)

print("✅ Env looks OK.")
