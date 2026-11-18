"""
Tests for ARK team workflow DAL contracts.

These tests mock the underlying DB helpers (run_one_strict_async, execute_async,
run_query_strict_async) so they do not require a live database. They validate the
logic and return-value contracts of:
  - replace_match_draft_rows
  - promote_match_draft_to_final
  - clear_match_final_rows
  - list_match_team_rows
"""

from __future__ import annotations

import pytest

import ark.dal.ark_dal as dal

# ---------------------------------------------------------------------------
# replace_match_draft_rows
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_replace_draft_rows_returns_true_with_assignments(monkeypatch):
    """Normal write path: not finalized, assignments provided → True."""
    calls: list[str] = []

    async def _run_one_strict(sql, params=None):
        # First call is the finalized guard SELECT → return 0 final rows
        calls.append("guard")
        return {"FinalCount": 0}

    async def _execute(sql, params=None, *, commit=True):
        calls.append("execute")
        return len(params) if params else 0

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)
    monkeypatch.setattr(dal, "execute_async", _execute)

    result = await dal.replace_match_draft_rows(
        match_id=1,
        assignments=[(101, 1), (102, 2)],
        actor_discord_id=9,
        source="test",
        check_finalized_only=False,
    )
    assert result is True
    assert "guard" in calls
    assert "execute" in calls


@pytest.mark.asyncio
async def test_replace_draft_rows_returns_true_empty_assignments(monkeypatch):
    """Reset path: not finalized, empty assignments → True (draft cleared)."""

    async def _run_one_strict(sql, params=None):
        return {"FinalCount": 0}

    async def _execute(sql, params=None, *, commit=True):
        return 0

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)
    monkeypatch.setattr(dal, "execute_async", _execute)

    result = await dal.replace_match_draft_rows(
        match_id=2,
        assignments=[],
        actor_discord_id=9,
        source="test_reset",
        check_finalized_only=False,
    )
    assert result is True


@pytest.mark.asyncio
async def test_replace_draft_rows_blocked_when_finalized(monkeypatch):
    """Finalized guard: IsFinal=1 rows exist → returns False, no mutation."""
    execute_calls: list = []

    async def _run_one_strict(sql, params=None):
        return {"FinalCount": 3}

    async def _execute(sql, params=None, *, commit=True):
        execute_calls.append(sql)
        return 0

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)
    monkeypatch.setattr(dal, "execute_async", _execute)

    result = await dal.replace_match_draft_rows(
        match_id=3,
        assignments=[(101, 1)],
        actor_discord_id=9,
        source="test",
        check_finalized_only=False,
    )
    assert result is False
    # No DELETE or INSERT should have been called
    assert execute_calls == []


@pytest.mark.asyncio
async def test_replace_draft_rows_check_finalized_only_not_finalized(monkeypatch):
    """check_finalized_only=True, no finals → returns True (can mutate)."""

    async def _run_one_strict(sql, params=None):
        return {"FinalCount": 0}

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)

    result = await dal.replace_match_draft_rows(
        match_id=4,
        assignments=[],
        actor_discord_id=9,
        source="test",
        check_finalized_only=True,
    )
    assert result is True


@pytest.mark.asyncio
async def test_replace_draft_rows_check_finalized_only_finalized(monkeypatch):
    """check_finalized_only=True, finals exist → returns False (cannot mutate)."""

    async def _run_one_strict(sql, params=None):
        return {"FinalCount": 2}

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)

    result = await dal.replace_match_draft_rows(
        match_id=5,
        assignments=[],
        actor_discord_id=9,
        source="test",
        check_finalized_only=True,
    )
    assert result is False


@pytest.mark.asyncio
async def test_replace_draft_rows_deduplicates_assignments(monkeypatch):
    """Duplicate governor IDs in input are deduplicated before insert."""
    inserted_params: list = []

    async def _run_one_strict(sql, params=None):
        return {"FinalCount": 0}

    async def _execute(sql, params=None, *, commit=True):
        if params:
            inserted_params.extend(params)
        return 0

    monkeypatch.setattr(dal, "run_one_strict_async", _run_one_strict)
