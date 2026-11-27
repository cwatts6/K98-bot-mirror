"""Fixed entry point for the protected saved-result recovery packet."""

import json
from pathlib import Path
import runpy

if __name__ == "__main__":
    runner = runpy.run_path(str(Path(__file__).with_name("recover_stranded_export.py")))
    try:
        raise SystemExit(runner["main"](recovery="saved_result"))
    except Exception as error:
        print(
            json.dumps(
                dict(
                    stage="RECOVERY_STOPPED",
                    error_type=type(error).__name__,
                    instruction="Preserve the journal; no automatic claim clearing or provider replay.",
                )
            )
        )
        raise SystemExit(1) from None
