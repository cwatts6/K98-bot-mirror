import pytest

from ui.views.ark_views import ArkMatchResultModal


@pytest.mark.asyncio
async def test_modal_has_named_result_input():
    modal = ArkMatchResultModal(
        author_id=1,
        current_result="",
        current_notes="",
        result_label="Result X",
        on_submit=lambda *_: None,
    )
    assert hasattr(modal, "result_input")
    assert modal.result_input.label == "Result X"
