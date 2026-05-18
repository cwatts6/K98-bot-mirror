import inspect

from commands.prekvk_cmds import register_prekvk


def test_prekvk_report_command_is_public_read_only_surface():
    source = inspect.getsource(register_prekvk)

    assert 'name="prekvk_report"' in source
    assert "@safe_command" in source
    assert "@track_usage()" in source
    assert "safe_defer(ctx, ephemeral=True)" in source
    assert "safe_defer(ctx, ephemeral=False)" not in source
    assert "@is_admin_and_notify_channel()" not in source
    assert "import_prekvk_bytes" not in source
    assert "handle_prekvk_upload" not in source
