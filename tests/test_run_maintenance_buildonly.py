import pytest

from file_utils import build_maintenance_cmd, run_maintenance_subprocess


@pytest.mark.asyncio
async def test_run_maintenance_subprocess_build_only_matches_builder():
    """
    Verify run_maintenance_subprocess(build_only=True, kwargs=...) returns the same
    command list produced by build_maintenance_cmd(...) so the builder and runner
    agree on the invocation format.
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

    cmd_from_builder = build_maintenance_cmd("post_stats", args=args, kwargs=kwargs)
    cmd_from_runner = await run_maintenance_subprocess(
        "post_stats", args=args, kwargs=kwargs, timeout=1.0, build_only=True
    )

    assert isinstance(cmd_from_runner, list)
    assert cmd_from_builder == cmd_from_runner
