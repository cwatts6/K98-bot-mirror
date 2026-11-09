import asyncio

import pytest

from services.player_stats_cache_service import compose, observe_last


@pytest.mark.asyncio
async def test_main_subresult_prevents_second_last_entry():
    calls = []

    async def main():
        await asyncio.to_thread(
            observe_last, lambda: calls.append("nested") or {"_meta": {"count": 1}}
        )
        return {"main": True}

    async def last():
        pytest.fail("already entered")

    owner = await compose(main, last)
    assert calls == ["nested"]
    assert owner.last_state == "succeeded" and owner.main_output == {"main": True}


@pytest.mark.asyncio
@pytest.mark.parametrize("unknown", [True, False])
async def test_unknown_entered_is_never_replayed_but_preentry_failure_falls_back(unknown):
    calls = []

    async def main():
        if unknown:
            observe_last(lambda: None)
        raise RuntimeError("main failed")

    async def last():
        return observe_last(lambda: calls.append("fallback") or {})

    owner = await compose(main, last)
    assert calls == ([] if unknown else ["fallback"])
    assert owner.main_error is not None
    assert owner.last_state == ("outcome_unconfirmed" if unknown else "succeeded")


@pytest.mark.asyncio
async def test_separate_requests_never_share_owner():
    calls = []

    async def main():
        observe_last(lambda: calls.append(1) or {})
        return {}

    async def last():
        pytest.fail("duplicate")

    a, b = await asyncio.gather(compose(main, last), compose(main, last))
    assert a.invocation_id != b.invocation_id and calls == [1, 1]
