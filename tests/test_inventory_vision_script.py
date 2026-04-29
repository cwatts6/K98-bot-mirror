from __future__ import annotations

import subprocess
import sys


def test_script_import_does_not_touch_sql_modules():
    code = (
        "import scripts.test_inventory_vision as mod, sys; "
        "print(bool(mod.main)); "
        "print('pyodbc' in sys.modules); "
        "print('constants' in sys.modules)"
    )

    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout.splitlines() == ["True", "False", "False"]
