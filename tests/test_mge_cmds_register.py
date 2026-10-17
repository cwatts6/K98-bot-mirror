from __future__ import annotations

from commands import mge_cmds


def test_register_exists():
    assert callable(mge_cmds.register_mge)
