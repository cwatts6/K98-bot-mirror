from io import BytesIO

import pandas as pd
import pytest

from mge.mge_xlsx_parser import parse_mge_results_xlsx, validate_results_filename


def _make_workbook_bytes() -> bytes:
    df = pd.DataFrame(
        [
            {"Rank": 1, "Player ID": 17868677, "Player": "Nikkiᵂᴬᴿ", "Score": "39,417,197"},
            {"Rank": 2, "Player ID": 18546768, "Player": "Ì am Òðinn", "Score": "20,175,585"},
            {"Rank": 3, "Player ID": 4677418, "Player": "Fox义", "Score": "17,653,200"},
        ]
    )
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as w:
        # write title rows so header is row 3
        pd.DataFrame([["MGE Overall — KD 1198"], [None]]).to_excel(
            w, index=False, header=False, sheet_name="Overall"
        )
        df.to_excel(w, index=False, startrow=2, sheet_name="Overall")
    return bio.getvalue()


def test_filename_valid():
    validate_results_filename("mge_rankings_kd1198_20260311.xlsx")


def test_filename_invalid():
    with pytest.raises(ValueError):
        validate_results_filename("bad.xlsx")


def test_parse_overall_sheet_header_row3_unicode_and_score():
    content = _make_workbook_bytes()
    rows = parse_mge_results_xlsx(content, "mge_rankings_kd1198_20260311.xlsx")
    assert len(rows) == 3
    assert rows[0].player_name == "Nikkiᵂᴬᴿ"
    assert rows[0].score == 39417197
    assert rows[2].player_name == "Fox义"
