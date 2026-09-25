from __future__ import annotations

import pytest


def test_commands_register_all_includes_mge():
    from commands import (
        mge_cmds,
        register_all,  # import smoke
    )

    assert callable(register_all)
    assert hasattr(mge_cmds, "register_mge")
    assert callable(mge_cmds.register_mge)


@pytest.mark.asyncio
async def test_mge_package_import_smoke():
    import mge

    assert hasattr(mge, "__version__")
