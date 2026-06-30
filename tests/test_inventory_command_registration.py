import types


class _FakeGroup:
    def __init__(self, name, description, guild_ids=None):
        self.name = name
        self.description = description
        self.guild_ids = guild_ids
        self.commands = {}

    def command(self, **kwargs):
        def deco(fn):
            self.commands[kwargs["name"]] = fn
            return fn

        return deco


def test_register_inventory_command_registers_grouped_admin_commands(monkeypatch):
    import commands.inventory_cmds as mod

    fake_bot = types.SimpleNamespace(registered={}, groups={})

    def slash_command(**kwargs):
        def deco(fn):
            fake_bot.registered[kwargs["name"]] = fn
            return fn

        return deco

    def add_application_command(group):
        fake_bot.groups[group.name] = group

    fake_bot.slash_command = slash_command
    fake_bot.add_application_command = add_application_command
    monkeypatch.setattr(mod.discord, "SlashCommandGroup", _FakeGroup)

    mod.register_inventory(fake_bot)

    assert fake_bot.groups["inventory"].commands.keys() == {"import", "audit"}
    assert "import_inventory" not in fake_bot.registered
    assert "inventory_import_audit" not in fake_bot.registered
    assert "myinventory" in fake_bot.registered
    assert "inventory_preferences" in fake_bot.registered
    assert "export_inventory" in fake_bot.registered
