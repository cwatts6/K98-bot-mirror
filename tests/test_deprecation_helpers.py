from types import SimpleNamespace

import pytest

from commands.deprecation_helpers import (
    CommandRedirect,
    build_deprecated_command_message,
    send_deprecated_command_redirect,
)


def test_deprecated_command_message_uses_neutral_output_wording():
    message = build_deprecated_command_message(
        CommandRedirect(old_path="/old", new_path="/new", detail="Extra guidance.")
    )

    assert "old output" in message
    assert "old report" not in message
    assert "/new" in message
    assert "Extra guidance." in message


class _FakeResponse:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    def is_done(self) -> bool:
        return False

    async def send_message(self, content, *, ephemeral: bool, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral, "kwargs": kwargs})


class _FakeFollowup:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, content, *, ephemeral: bool, **kwargs):
        self.sent.append({"content": content, "ephemeral": ephemeral, "kwargs": kwargs})


@pytest.mark.asyncio
async def test_deprecated_command_redirect_uses_initial_response_when_not_deferred():
    response = _FakeResponse()
    followup = _FakeFollowup()
    ctx = SimpleNamespace(interaction=SimpleNamespace(response=response, followup=followup))

    await send_deprecated_command_redirect(
        ctx,
        CommandRedirect(old_path="/old", new_path="/new"),
        ephemeral=True,
    )

    assert response.sent == [
        {
            "content": "`/old` is deprecated and no longer returns the old output.\n"
            "Please use `/new` instead.",
            "ephemeral": True,
            "kwargs": {},
        }
    ]
    assert followup.sent == []
