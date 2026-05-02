from __future__ import annotations

from pathlib import Path

from constants import DATA_DIR

MGE_COMMANDERS_CACHE_PATH = Path(DATA_DIR) / "mge_commanders_cache.json"
MGE_VARIANT_COMMANDERS_CACHE_PATH = Path(DATA_DIR) / "mge_variant_commanders_cache.json"

# Shared target generation / regeneration step used by publish and leadership services.
DEFAULT_TARGET_DECREMENT_SCORE = 500_000
