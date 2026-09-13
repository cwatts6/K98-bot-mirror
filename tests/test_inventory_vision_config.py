from __future__ import annotations

import os
import subprocess
import sys


def test_openai_vision_config_defaults():
    env = os.environ.copy()
    env["OPENAI_API_KEY"] = ""
    env["OPENAI_VISION_MODEL"] = ""
    env["OPENAI_VISION_FALLBACK_MODEL"] = ""
    env["OPENAI_VISION_PROMPT_VERSION"] = ""

    code = (
        "import bot_config; "
        "print(bot_config.OPENAI_API_KEY == ''); "
        "print(bot_config.OPENAI_VISION_MODEL); "
        "print(bot_config.OPENAI_VISION_FALLBACK_MODEL); "
        "print(bot_config.OPENAI_VISION_PROMPT_VERSION)"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )

    assert completed.stdout.splitlines() == [
        "True",
        "gpt-4.1-mini",
        "gpt-5.2",
        "inventory_vision_v1",
    ]
