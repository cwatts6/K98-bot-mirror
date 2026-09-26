import pytest

from prekvk.models import PreKvkReportSort
from ui.views import prekvk_report_views
from ui.views.prekvk_report_views import PreKvkReportView, send_prekvk_report


@pytest.mark.asyncio
async def test_prekvk_report_view_exposes_sort_and_limit_controls():
    view = PreKvkReportView(
        requester_id=42,
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
    )

    custom_ids = [getattr(item, "custom_id", None) for item in view.children]

    assert "prekvk_report_top_10" in custom_ids
    assert "prekvk_report_top_50" in custom_ids
    assert "prekvk_report_top_100" not in custom_ids
    assert view.sort_select.placeholder == "Sort by"


@pytest.mark.asyncio
async def test_prekvk_report_view_rejects_wrong_user():
    view = PreKvkReportView(
        requester_id=42,
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
    )
    response = {}

    class Response:
        async def send_message(self, content=None, **kwargs):
            response["content"] = content
            response.update(kwargs)

    interaction = type(
        "Interaction",
        (),
        {
            "user": type("User", (), {"id": 99})(),
            "response": Response(),
        },
    )()

    await view._refresh(interaction)

    assert "not yours" in response["content"]
    assert "/prekvk report" in response["content"]
    assert response["ephemeral"] is True


@pytest.mark.asyncio
async def test_prekvk_report_view_refresh_failure_sends_private_feedback(monkeypatch):
    view = PreKvkReportView(
        requester_id=42,
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
    )
    followups = []

    async def _fail_build(**_kwargs):
        raise RuntimeError("database unavailable")

    class Response:
        async def defer(self):
            return None

    class Followup:
        async def send(self, content=None, **kwargs):
            followups.append((content, kwargs))

    interaction = type(
        "Interaction",
        (),
        {
            "user": type("User", (), {"id": 42})(),
            "response": Response(),
            "followup": Followup(),
        },
    )()
    monkeypatch.setattr(
        prekvk_report_views.report_service, "build_prekvk_report_payload", _fail_build
    )

    await view._refresh(interaction)

    assert followups
    assert "refresh failed" in followups[0][0]
    assert "/prekvk report" in followups[0][0]
    assert followups[0][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_prekvk_report_view_refresh_edits_component_message(monkeypatch):
    payload = type(
        "Payload",
        (),
        {
            "kvk_no": 15,
            "sort_by": PreKvkReportSort.STAGE1,
            "limit": 25,
            "rows": [object()],
        },
    )()
    view = PreKvkReportView(
        requester_id=42,
        kvk_no=15,
        sort_by=PreKvkReportSort.STAGE1,
        limit=25,
    )

    async def _build_payload(**_kwargs):
        return payload

    async def _no_file(_payload):
        return None

    class Response:
        async def defer(self):
            return None

    class Message:
        def __init__(self):
            self.kwargs = None

        async def edit(self, **kwargs):
            self.kwargs = kwargs

    message = Message()

    async def _wrong_target(**_kwargs):
        raise AssertionError("refresh should edit the component host message first")

    interaction = type(
        "Interaction",
        (),
        {
            "user": type("User", (), {"id": 42})(),
            "response": Response(),
            "message": message,
            "edit_original_response": _wrong_target,
        },
    )()
    monkeypatch.setattr(
        prekvk_report_views.report_service, "build_prekvk_report_payload", _build_payload
    )
    monkeypatch.setattr(prekvk_report_views, "_discord_file", _no_file)

    await view._refresh(interaction)

    assert view.message is message
    assert "sorted by **Stage 1**" in message.kwargs["content"]
    assert message.kwargs["view"] is view


@pytest.mark.asyncio
async def test_send_prekvk_report_stores_public_channel_message(monkeypatch):
    payload = type(
        "Payload",
        (),
        {
            "kvk_no": 15,
            "sort_by": PreKvkReportSort.OVERALL,
            "limit": 10,
            "rows": [object()],
        },
    )()
    public_message = object()

    async def _build_payload(**_kwargs):
        return payload

    async def _no_file(_payload):
        return None

    class Channel:
        def __init__(self):
            self.kwargs = None

        async def send(self, **kwargs):
            self.kwargs = kwargs
            return public_message

    class Followup:
        def __init__(self):
            self.sent = []

        async def send(self, content=None, **kwargs):
            self.sent.append((content, kwargs))

    channel = Channel()
    followup = Followup()
    ctx = type(
        "Ctx",
        (),
        {
            "user": type("User", (), {"id": 42})(),
            "channel": channel,
            "followup": followup,
        },
    )()
    monkeypatch.setattr(
        prekvk_report_views.report_service, "build_prekvk_report_payload", _build_payload
    )
    monkeypatch.setattr(prekvk_report_views, "_discord_file", _no_file)

    await send_prekvk_report(
        ctx=ctx,
        kvk_no=15,
        sort_by=PreKvkReportSort.OVERALL,
        limit=10,
    )

    view = channel.kwargs["view"]
    assert view.message is public_message
    assert followup.sent == [("PreKvK report posted.", {"ephemeral": True})]
