from pathlib import Path

from PIL import Image, ImageDraw

from core import visual_text


def test_text_clusters_keep_joined_symbol_sequences_together():
    astronaut = "Orbit\U0001f469\u200d\U0001f680"
    flag = "Flag\U0001f1ec\U0001f1e7"
    thumbs_up = "Boost\U0001f44d\U0001f3fd"

    assert visual_text.text_clusters(astronaut)[5:] == ["\U0001f469\u200d\U0001f680"]
    assert visual_text.text_clusters(flag)[4:] == ["\U0001f1ec\U0001f1e7"]
    assert visual_text.text_clusters(thumbs_up)[5:] == ["\U0001f44d\U0001f3fd"]


def test_font_candidates_cover_symbols_and_wide_player_names():
    assert any(
        candidate.endswith("seguiemj.ttf")
        for candidate in visual_text.font_candidates_for_char("\U0001f98a")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in visual_text.font_candidates_for_char("\u3010")
    )
    assert any(
        candidate.endswith("LeelawUI.ttf")
        for candidate in visual_text.font_candidates_for_char("\u0e5b")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in visual_text.font_candidates_for_char("\u4e49")
    )
    assert any(
        candidate.endswith("msyh.ttc")
        for candidate in visual_text.font_candidates_for_char("\u3400")
    )
    assert visual_text.cluster_font_size("\u30c5", 18) == 22
    assert visual_text.cluster_font_size("\u0e5b", 18) == 22


def test_font_for_text_skips_unsupported_candidate(monkeypatch):
    visual_text.font_for_text.cache_clear()
    used_paths = []

    monkeypatch.setattr(
        visual_text,
        "font_candidates_for_text",
        lambda text, *, bold=False: ["unsupported.ttf", "supported.ttf"],
    )
    monkeypatch.setattr(
        visual_text,
        "font_supports_text",
        lambda path, text: path == "supported.ttf",
    )

    def _fake_truetype(path, *, size):
        used_paths.append(path)
        return object()

    monkeypatch.setattr(visual_text.ImageFont, "truetype", _fake_truetype)

    assert visual_text.font_for_text("\u4e49", 18) is not None
    assert used_paths == ["supported.ttf"]
    visual_text.font_for_text.cache_clear()


def test_font_supports_text_reuses_cached_coverage():
    visual_text.font_coverage.cache_clear()
    visual_text.font_supports_text.cache_clear()

    path = "C:/Windows/Fonts/definitely_missing_test_font.ttf"

    assert visual_text.font_supports_text(path, "A") is False
    assert visual_text.font_supports_text(path, "B") is False
    assert visual_text.font_coverage.cache_info().misses == 1
    assert visual_text.font_coverage.cache_info().hits == 1


def test_fit_text_to_width_truncates_by_rendered_width():
    image = Image.new("RGBA", (420, 80))
    draw = ImageDraw.Draw(image)
    base_font = visual_text.font(18)
    text = "\u30c5" * 80

    fitted = visual_text.fit_text_to_width(draw, text, width=120, base_font=base_font)

    assert fitted.endswith(".")
    assert visual_text.text_width(draw, fitted, font=base_font) <= 120


def test_font_supports_real_wide_fonts_when_installed():
    msyh = Path("C:/Windows/Fonts/msyh.ttc")
    if msyh.exists():
        assert visual_text.font_supports_text(str(msyh), "\u4e49")
    leelaw = Path("C:/Windows/Fonts/LeelawUI.ttf")
    if leelaw.exists():
        assert visual_text.font_supports_text(str(leelaw), "\u0e5b")
