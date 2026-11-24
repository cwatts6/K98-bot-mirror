"""Keep both bot entry points held on the enrolled offline DEV Windows guest."""

import os
import sys


def enforce_dev_startup_hold():
    if sys.platform != "win32":
        return

    import socket

    try:
        name = socket.gethostname().partition(".")[0].casefold()
        if not name or name == "k98-dev-vm":
            raise SystemExit("K98 DEV startup held")
    except OSError:
        raise SystemExit("K98 DEV startup held") from None

    try:
        # The protected directory also identifies the installation after a rename.
        os.lstat(r"C:\Program Files\K98Dev05Offline")
    except FileNotFoundError:
        return
    except OSError:
        pass
    raise SystemExit("K98 DEV startup held")
