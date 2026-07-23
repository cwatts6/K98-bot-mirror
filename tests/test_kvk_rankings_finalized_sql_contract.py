from pathlib import Path

from kvk.dal import kvk_history_dal, kvk_rankings_dal
from kvk.services import kvk_rankings_service
from services import kvk_history_service


def test_hall_of_fame_is_final_output_only_and_healed_is_engaged_ascending() -> None:
    source = Path(kvk_rankings_dal.__file__).read_text(encoding="utf-8")
    ranking_service_source = Path(kvk_rankings_service.__file__).read_text(encoding="utf-8")
    history_dal_source = Path(kvk_history_dal.__file__).read_text(encoding="utf-8")
    history_service_source = Path(kvk_history_service.__file__).read_text(encoding="utf-8")

    assert "dbo.KVKFinalReportHeader" in source
    assert "OUTPUT_COMPLETE" in source
    assert "@FinalizedKvkNos" in source
    assert "finalized.ID = src.KVK_NO" in source
    assert "kvk_history_service.get_finalized_kvks" in ranking_service_source
    assert "fetch_output_complete_kvk_candidates" in history_dal_source
    assert "history.KVK_NO IN ({finalized_placeholders})" in history_dal_source
    assert "kvk_state.resolve_kvk_scan_state" in history_service_source
    assert 'state == "ENDED"' in history_service_source
    assert 'direction = "ASC" if healed_metric else "DESC"' in source
    assert "src.[KillPointsDelta]" in source
    assert "src.[T4&T5_Kills]" in source
    assert "src.[Deads_Delta]" in source
