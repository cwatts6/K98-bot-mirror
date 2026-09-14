"""Pure pagination helpers for the three-column Player Record card."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from dataclasses import dataclass
from math import ceil

from leadership_player_review.models import AliasRecord, AllianceEpisode

RECORD_PAGE_SIZE = 10


@dataclass(frozen=True, slots=True)
class AliasDisplayRow:
    """One visual alias row: either a Governor ID heading or an alias observation."""

    governor_id: int
    alias: AliasRecord | None = None

    @property
    def is_heading(self) -> bool:
        return self.alias is None


@dataclass(frozen=True, slots=True)
class AllianceDisplayRow:
    """One visual alliance row: either a Governor ID heading or an episode."""

    governor_id: int
    episode: AllianceEpisode | None = None

    @property
    def is_heading(self) -> bool:
        return self.episode is None


def alias_pages(
    aliases: Iterable[AliasRecord], *, page_size: int = RECORD_PAGE_SIZE
) -> tuple[tuple[AliasDisplayRow, ...], ...]:
    """Group aliases by exact Governor ID and keep a heading with every page fragment."""
    if page_size < 2:
        raise ValueError("alias pages require room for a heading and at least one alias")

    groups: OrderedDict[int, list[AliasRecord]] = OrderedDict()
    for alias in aliases:
        groups.setdefault(alias.governor_id, []).append(alias)

    pages: list[tuple[AliasDisplayRow, ...]] = []
    current: list[AliasDisplayRow] = []
    for governor_id, rows in groups.items():
        remaining = list(rows)
        while remaining:
            if current and len(current) > page_size - 2:
                pages.append(tuple(current))
                current = []
            current.append(AliasDisplayRow(governor_id))
            available = page_size - len(current)
            current.extend(AliasDisplayRow(governor_id, alias) for alias in remaining[:available])
            remaining = remaining[available:]
            if remaining:
                pages.append(tuple(current))
                current = []

    if current:
        pages.append(tuple(current))
    return tuple(pages)


def alliance_pages(
    episodes: Iterable[AllianceEpisode], *, page_size: int = RECORD_PAGE_SIZE
) -> tuple[tuple[AllianceDisplayRow, ...], ...]:
    """Group alliance episodes by Governor ID with headings on page fragments."""
    if page_size < 2:
        raise ValueError("alliance pages require room for a heading and at least one episode")

    groups: OrderedDict[int, list[AllianceEpisode]] = OrderedDict()
    for episode in episodes:
        groups.setdefault(episode.governor_id, []).append(episode)

    pages: list[tuple[AllianceDisplayRow, ...]] = []
    current: list[AllianceDisplayRow] = []
    for governor_id, rows in groups.items():
        remaining = list(rows)
        while remaining:
            if current and len(current) > page_size - 2:
                pages.append(tuple(current))
                current = []
            current.append(AllianceDisplayRow(governor_id))
            available = page_size - len(current)
            current.extend(
                AllianceDisplayRow(governor_id, episode) for episode in remaining[:available]
            )
            remaining = remaining[available:]
            if remaining:
                pages.append(tuple(current))
                current = []

    if current:
        pages.append(tuple(current))
    return tuple(pages)


def record_page_count(
    *,
    linked_count: int,
    aliases: Iterable[AliasRecord],
    episodes: Iterable[AllianceEpisode],
) -> int:
    """Return the common page count used by both the renderer and Discord controls."""
    linked_pages = ceil(max(0, linked_count) / RECORD_PAGE_SIZE)
    return max(1, linked_pages, len(alias_pages(aliases)), len(alliance_pages(episodes)))
