import types


def test_register_inventory_command_registers_import_inventory():
    import commands.inventory_cmds as mod

    fake_bot = types.SimpleNamespace(registered={})

    def slash_command(**kwargs):
        def deco(fn):
            fake_bot.registered[kwargs["name"]] = fn
            return fn

        return deco

    fake_bot.slash_command = slash_command

    mod.register_inventory(fake_bot)

    assert "import_inventory" in fake_bot.registered
