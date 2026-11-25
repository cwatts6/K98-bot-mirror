"""Stable tab routing shared by capture and retained-input replacement."""

import hashlib

from kvk.dal.new_source_import_dal import SourceConflict


def legacy_grid_identity(title, registered):
    if title in registered:
        return registered[title]
    candidate = int.from_bytes(hashlib.sha256(title.encode()).digest()[:4], "big") & 0x7FFFFFFF
    used = set(registered.values())
    for _ in range(len(used) + 1):
        if candidate not in used:
            return candidate
        candidate = (candidate + 1) & 0x7FFFFFFF
    raise SourceConflict("No free registered worksheet identity.")
