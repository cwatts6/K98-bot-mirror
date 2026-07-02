from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from commands import vote_admin_cmds
from ui.views.vote_admin_update_view import VoteAdminUpdateView
from voting.models import VoteLookupChoice
from voting.service import VoteValidationError


def _vote_create_option_required_flags() -> list[tuple[str, bool]]:
    tree = ast.parse(Path("commands/vote_admin_cmds.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "vote_create":
            defaults_by_arg = dict(
                zip(node.args.args[-len(node.args.defaults) :], node.args.defaults, strict=True)
            )
            flags: list[tuple[str, bool]] = []
            for arg in node.args.args:
                if arg.arg == "ctx":
                    continue
                default = defaults_by_arg[arg]
                required = True
                if isinstance(default, ast.Call):
                    for keyword in default.keywords:
                        if (
                            keyword.arg == "required"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is False
                        ):
                            required = False
                flags.append((arg.arg, required))
            return flags
    raise AssertionError("vote_create command was not found")


def _vote_create_option_max_lengths() -> dict[str, str]:
    tree = ast.parse(Path("commands/vote_admin_cmds.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "vote_create":
            defaults_by_arg = dict(
                zip(node.args.args[-len(node.args.defaults) :], node.args.defaults, strict=True)
            )
            lengths: dict[str, str] = {}
            for arg in node.args.args:
                if arg.arg == "ctx":
                    continue
                default = defaults_by_arg[arg]
                if isinstance(default, ast.Call):
                    for keyword in default.keywords:
                        if keyword.arg == "max_length" and isinstance(keyword.value, ast.Name):
                            lengths[arg.arg] = keyword.value.id
            return lengths
    raise AssertionError("vote_create command was not found")


def _vote_admin_command_names() -> set[str]:
    tree = ast.parse(Path("commands/vote_admin_cmds.py").read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                if not (
                    isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "command"
                ):
                    continue
                for keyword in decorator.keywords:
                    if (
                        keyword.arg == "name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        names.add(keyword.value.value)
    return names


def _vote_export_defaults() -> dict[ast.arg, ast.expr]:
    tree = ast.parse(Path("commands/vote_admin_cmds.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "vote_export":
            return dict(
                zip(node.args.args[-len(node.args.defaults) :], node.args.defaults, strict=True)
            )
    raise AssertionError("vote_export command was not found")


def test_vote_create_places_required_options_before_optional_options() -> None:
    seen_optional = False
    for name, required in _vote_create_option_required_flags():
        if required:
            assert not seen_optional, f"{name} is required after an optional slash option"
        else:
            seen_optional = True


def test_vote_create_description_remains_optional() -> None:
    flags = dict(_vote_create_option_required_flags())

    assert flags["description"] is False


def test_vote_create_uses_individual_option_fields() -> None:
    flags = dict(_vote_create_option_required_flags())

    assert "options" not in flags
    assert flags["option_1"] is True
    assert flags["option_2"] is True
    assert flags["option_3"] is False
    assert flags["option_6"] is False


def test_vote_create_applies_string_max_lengths() -> None:
    lengths = _vote_create_option_max_lengths()

    assert lengths["title"] == "MAX_TITLE_LEN"
    assert lengths["description"] == "MAX_DESCRIPTION_LEN"
    for name in ("option_1", "option_2", "option_3", "option_4", "option_5", "option_6"):
        assert lengths[name] == "MAX_OPTION_LABEL_LEN"


def test_vote_admin_registers_export_subcommand() -> None:
    assert {"create", "update", "close", "status", "export"}.issubset(_vote_admin_command_names())


def test_vote_export_adds_optional_mode_defaulting_to_totals() -> None:
    defaults = _vote_export_defaults()

    assert "mode" in {arg.arg for arg in defaults}
    mode_default = defaults[next(arg for arg in defaults if arg.arg == "mode")]
    assert isinstance(mode_default, ast.Call)
    keywords = {keyword.arg: keyword.value for keyword in mode_default.keywords}
    assert isinstance(keywords["default"], ast.Name)
    assert keywords["default"].id == "_EXPORT_MODE_TOTALS"
    assert isinstance(keywords["required"], ast.Constant)
    assert keywords["required"].value is False


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("42", 42),
        ("#42", 42),
        (42, 42),
    ],
)
def test_parse_vote_post_id_accepts_explicit_ids(value, expected) -> None:
    assert vote_admin_cmds._parse_vote_post_id(value) == expected


@pytest.mark.parametrize("value", ["rally 2026", "Vote #42", "42 rally", "#42 rally"])
def test_parse_vote_post_id_rejects_non_explicit_text(value: str) -> None:
    with pytest.raises(VoteValidationError, match="Choose a vote"):
        vote_admin_cmds._parse_vote_post_id(value)


@pytest.mark.asyncio
async def test_vote_post_autocomplete_returns_vote_ids_as_values(monkeypatch):
    async def fake_search_vote_choices(*, query, limit):
        assert query == "rally"
        assert limit == 25
        return [
            VoteLookupChoice(
                vote_post_id=42,
                title="Best rally time?",
                status="Open",
                channel_id=5,
                closes_at_utc=datetime(2026, 7, 1, 20, 0, tzinfo=UTC),
            )
        ]

    monkeypatch.setattr(vote_admin_cmds, "search_vote_choices", fake_search_vote_choices)

    choices = await vote_admin_cmds._vote_post_autocomplete(SimpleNamespace(value="rally"))

    assert choices[0].value == "42"
    assert "Best rally time?" in choices[0].name


@pytest.mark.asyncio
async def test_closed_vote_post_autocomplete_returns_closed_vote_ids(monkeypatch):
    async def fake_search_closed_vote_choices(*, query, limit):
        assert query == "rally"
        assert limit == 25
        return [
            VoteLookupChoice(
                vote_post_id=42,
                title="Best rally time?",
                status="Closed",
                channel_id=5,
                closes_at_utc=datetime(2026, 7, 1, 20, 0, tzinfo=UTC),
                closed_at_utc=datetime(2026, 7, 1, 21, 0, tzinfo=UTC),
            )
        ]

    monkeypatch.setattr(
        vote_admin_cmds, "search_closed_vote_choices", fake_search_closed_vote_choices
    )

    choices = await vote_admin_cmds._closed_vote_post_autocomplete(SimpleNamespace(value="rally"))

    assert choices[0].value == "42"
    assert "Best rally time?" in choices[0].name
    assert "Closed" in choices[0].name
    assert "2026-07-01 21:00 UTC" in choices[0].name


@pytest.mark.asyncio
async def test_send_vote_update_panel_uses_ephemeral_followup():
    captured: dict[str, object] = {}

    class _Followup:
        async def send(self, **kwargs):
            captured["followup"] = kwargs

    class _Interaction:
        async def edit_original_response(self, **kwargs):
            captured["edit"] = kwargs

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=123),
        followup=_Followup(),
        interaction=_Interaction(),
    )
    snapshot = SimpleNamespace(vote_post_id=7)

    await vote_admin_cmds._send_vote_update_panel(ctx, snapshot)

    followup = captured["followup"]
    assert followup["content"] == "Choose what to update for Vote #7."
    assert followup["ephemeral"] is True
    assert isinstance(followup["view"], VoteAdminUpdateView)
    assert captured["edit"] == {"content": "Update panel opened for Vote #7."}


@pytest.mark.asyncio
async def test_send_vote_update_panel_falls_back_to_original_response():
    captured: dict[str, object] = {}

    class _Interaction:
        async def edit_original_response(self, **kwargs):
            captured["edit"] = kwargs

    ctx = SimpleNamespace(
        user=SimpleNamespace(id=123),
        followup=None,
        interaction=_Interaction(),
    )
    snapshot = SimpleNamespace(vote_post_id=7)

    await vote_admin_cmds._send_vote_update_panel(ctx, snapshot)

    edit = captured["edit"]
    assert edit["content"] == "Choose what to update for Vote #7."
    assert isinstance(edit["view"], VoteAdminUpdateView)


@pytest.mark.asyncio
async def test_resolve_voter_discord_names_uses_cached_and_fetched_members() -> None:
    class _Guild:
        def get_member(self, user_id):
            if user_id == 123:
                return SimpleNamespace(display_name="Cached Name")
            return None

        async def fetch_member(self, user_id):
            if user_id == 456:
                return SimpleNamespace(display_name="Fetched Name")
            return None

    ctx = SimpleNamespace(guild=_Guild())

    names = await vote_admin_cmds._resolve_voter_discord_names(ctx, (123, 456, 789))

    assert names == {
        123: "Cached Name",
        456: "Fetched Name",
        789: "Unknown",
    }
