from __future__ import annotations

import re

_WHITESPACE = re.compile(r"\s+")
_SEPARATORS = re.compile(r"[_\-]+")


def normalize_kvk_mode(value: object) -> str:
    """Return a stable lookup key for KVK mode names."""
    text = str(value or "").strip().lower()
    text = _SEPARATORS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text)
    return text
