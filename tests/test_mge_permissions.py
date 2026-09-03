from __future__ import annotations


def test_mge_cmds_imports_required_permission_decorators():
    import commands.mge_cmds as m

    # ensures Task N pattern present
    assert hasattr(m, "register_mge")
    # static sanity via module dict usage
    src_names = set(m.__dict__.keys())
    assert "is_admin_or_leadership_only" in src_names
    assert "channel_only" in src_names
