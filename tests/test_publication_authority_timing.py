"""Authority timings survive absent console handles and remain diagnostic only."""

from pathlib import Path
import subprocess
import sys

import pytest

from services import export_reconciliation_service as module


@pytest.mark.parametrize("fails", [False, True])
def test_authority_startup_retains_timing_without_standard_error(tmp_path, fails):
    script = r"""
import json
import logging
from pathlib import Path
import sys
import core.export_execution_host as host
import scripts.run_export_authority as launcher
from services import export_reconciliation_service as module

root = Path(sys.argv[1])
manifest_file = root / "manifest.json"
manifest_file.write_text(json.dumps({"evidence_root": str(root)}))
launcher.bootstrap = lambda *args, **kwargs: None
host.assert_protected_path = lambda path, **kwargs: Path(path)
host.current_sid = lambda: "test-only"
launcher.manifest_contract = lambda data, **kwargs: data
host.DeploymentBoundary = lambda manifest: None
class StopBeforeSQL(Exception):
    pass
def stop(manifest):
    raise StopBeforeSQL()
launcher.connection_factory = stop
sys.stderr = None
try:
    launcher.main(["--manifest", str(manifest_file)])
except StopBeforeSQL:
    pass
else:
    raise AssertionError("Must stop before opening SQL")
module.configure_publication_timing(root, inspect_path=host.assert_protected_path)
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
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == result.stderr == ""
    saved = (tmp_path / "publication-timing.log").read_text()
    assert len(saved.splitlines()) == 1
    assert "UTC publication_verification_phase phase=sealed_response_replay" in saved
    assert f"completed={not fails} duration_ms=172500" in saved
    assert "private" not in saved


def test_timing_refuses_untrusted_root_before_creating_file(tmp_path):
    def denied(path, **kwargs):
        raise PermissionError("untrusted")

    with pytest.raises(PermissionError):
        module.configure_publication_timing(tmp_path, inspect_path=denied)
    assert not list(tmp_path.iterdir())


def test_timing_refuses_hardlinked_diagnostic_without_touching_evidence(tmp_path):
    evidence = tmp_path / "retained-evidence"
    evidence.write_text("preserve")
    (tmp_path / "publication-timing.log").hardlink_to(evidence)
    with pytest.raises(ValueError, match="regular diagnostic"):
        module.configure_publication_timing(tmp_path, inspect_path=lambda path, **kwargs: path)
    assert evidence.read_text() == "preserve"


def test_timing_rotation_is_bounded_and_disk_failure_preserves_proof_result(tmp_path, monkeypatch):
    module.configure_publication_timing(tmp_path, inspect_path=lambda path, **kwargs: path)
    handler = next(
        h
        for h in module.publication_timing_logger.handlers
        if isinstance(h, module._PublicationTimingHandler)
    )
    try:
        handler.maxBytes = 256
        for _ in range(20):
            with module.publication_phase("retained_history"):
                pass
        logs = list(tmp_path.glob("publication-timing.log*"))
        assert len(logs) == 3
        assert all(path.stat().st_size < 256 for path in logs)

        def disk_failed():
            raise OSError("private disk exception")

        monkeypatch.setattr(handler, "_check_paths", disk_failed)
        with module.publication_phase("sealed_history"):
            result = "confirmed"
        assert result == "confirmed"
        with pytest.raises(ValueError, match="original proof failure"):
            with module.publication_phase("sealed_history"):
                raise ValueError("original proof failure")
        assert all("private" not in path.read_text() for path in logs)
    finally:
        module.publication_timing_logger.removeHandler(handler)
        handler.close()
