from __future__ import annotations

import ast
from pathlib import Path

from kvk.rendering import (
    kvk_history_renderer,
    kvk_rankings_card_renderer,
    kvk_stats_card_renderer,
    kvk_targets_card_renderer,
)

RENDERER_PATHS = (
    Path("kvk/rendering/kvk_stats_card_renderer.py"),
    Path("kvk/rendering/kvk_targets_card_renderer.py"),
    Path("kvk/rendering/kvk_rankings_card_renderer.py"),
    Path("kvk/rendering/kvk_history_renderer.py"),
)


def _import_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            modules.update(f"{node.module}.{alias.name}" for alias in node.names)
    return modules


def test_kvk_renderers_do_not_import_prekvk_text_helpers() -> None:
    for path in RENDERER_PATHS:
        modules = _import_modules(path)

        assert "prekvk.report_image_renderer" not in modules


def test_stats_and_targets_text_helpers_delegate_to_core_visual_text(monkeypatch) -> None:
    calls: list[tuple[tuple[int, int], str]] = []

    def fake_draw_text(draw, xy, text, *, fill, font, bold=False):
        calls.append((xy, text))

    monkeypatch.setattr(kvk_stats_card_renderer.visual_text, "draw_text", fake_draw_text)
    monkeypatch.setattr(kvk_targets_card_renderer.visual_text, "draw_text", fake_draw_text)

    kvk_stats_card_renderer._draw_text(object(), (1, 2), "Stats Name")
    kvk_targets_card_renderer._draw_text(object(), (3, 4), "Targets Name")

    assert calls == [((1, 2), "Stats Name"), ((3, 4), "Targets Name")]


def test_history_and_rankings_keep_kvk_text_wrapper_path_to_core_visual_text(monkeypatch) -> None:
    calls: list[tuple[tuple[int, int], str]] = []

    def fake_draw_text(draw, xy, text, *, fill, font, bold=False):
        calls.append((xy, text))

    monkeypatch.setattr(kvk_stats_card_renderer.visual_text, "draw_text", fake_draw_text)

    kvk_rankings_card_renderer._draw_text(object(), (5, 6), "Ranking Name")
    kvk_history_renderer._draw_text(object(), (7, 8), "History Name")

    assert calls == [((5, 6), "Ranking Name"), ((7, 8), "History Name")]
