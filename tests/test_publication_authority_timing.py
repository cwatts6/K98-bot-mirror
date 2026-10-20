"""Exercise timing visibility in a fresh authority interpreter, without SQL or Google."""

from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("fails", [False, True])
def test_authority_startup_enables_only_bounded_publication_timing(fails):
    script = """
import logging
import core.export_execution_host as host
import scripts.run_export_authority as launcher
from services import export_reconciliation_service as module

class StopBeforeManifest(Exception):
    pass

launcher.bootstrap = lambda *args, **kwargs: None
def stop(*args, **kwargs):
    raise StopBeforeManifest()
host.assert_protected_path = stop
try:
    launcher.main(["--manifest", "not-opened"])
except StopBeforeManifest:
    pass
else:
    raise AssertionError("Must stop before reading a manifest or opening SQL")
module.configure_publication_timing()
assert not logging.getLogger().handlers
assert logging.getLogger().getEffectiveLevel() == logging.WARNING
times = iter([100.0, 272.5])
module.monotonic = lambda: next(times)
try:
    with module.publication_phase("sealed_response_replay"):
        if FAILS:
            raise ValueError("private spreadsheet contents")
except ValueError as error:
    assert str(error) == "private spreadsheet contents"
    assert FAILS
logging.getLogger("unrelated_provider").info("private credentials")
module.logger.info("private module details")
""".replace("FAILS", repr(fails))
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    assert "UTC publication_verification_phase phase=sealed_response_replay" in result.stderr
    assert f"completed={not fails} duration_ms=172500" in result.stderr
    assert "private" not in result.stderr
