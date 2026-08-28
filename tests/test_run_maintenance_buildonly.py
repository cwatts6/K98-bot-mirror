import pytest

from file_utils import build_maintenance_cmd, run_maintenance_subprocess

_OFFLOAD_PREFIX = "__OFFLOAD_JSON__:"
_OFFLOAD_FILE_PREFIX = "__OFFLOAD_FILE__:"


def _normalize_cmd(cmd):
    """Replace randomized OFFLOAD_JSON/OFFLOAD_FILE paths with a stable placeholder."""
    result = []
    for tok in cmd:
        if tok.startswith(_OFFLOAD_PREFIX):
            result.append(_OFFLOAD_PREFIX + "<tmp>")
        elif tok.startswith(_OFFLOAD_FILE_PREFIX):
            result.append(_OFFLOAD_FILE_PREFIX + "<tmp>")
        else:
            result.append(tok)
    return result


@pytest.mark.asyncio
async def test_run_maintenance_subprocess_build_only_matches_builder():
    """
    Verify run_maintenance_subprocess(build_only=True, kwargs=...) returns the same
    command list produced by build_maintenance_cmd(...) so the builder and runner
    agree on the invocation format (excluding randomised temp-file paths).
    """
    args = ["positional"]
    kwargs = {
        "server": "MINI_AMD",
        "database": "ROK_TRACKER",
        "username": "SHEETS_USER",
        "password": "secret!",
        "verbose": True,
        "noop": False,
        "noneval": None,
        "count": 5,
    }

    cmd_from_builder, _ = build_maintenance_cmd("post_stats", args=args, kwargs=kwargs)
    cmd_from_runner = await run_maintenance_subprocess(
        "post_stats", args=args, kwargs=kwargs, timeout=1.0, build_only=True
    )

    assert isinstance(cmd_from_runner, list)
    # Normalize OFFLOAD_JSON paths (they are randomised temp file names) before comparing
    assert _normalize_cmd(cmd_from_builder) == _normalize_cmd(cmd_from_runner)
