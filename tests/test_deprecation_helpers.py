from commands.deprecation_helpers import CommandRedirect, build_deprecated_command_message


def test_deprecated_command_message_uses_neutral_output_wording():
    message = build_deprecated_command_message(
        CommandRedirect(old_path="/old", new_path="/new", detail="Extra guidance.")
    )

    assert "old output" in message
    assert "old report" not in message
    assert "/new" in message
    assert "Extra guidance." in message
