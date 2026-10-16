"""Bounded, complete private admin review data; never added to public alert evidence."""

import json
import re

from kvk.dal.new_source_import_dal import SourceConflict, digest


def registration_review(state):
    original = json.loads(state["preparation"]["RequestJson"])["request"]["config"]
    current = state["current_registration"]
    fields = []

    def document(label, value):
        text = json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2)
        # The view escapes Markdown. Even worst-case escaping stays below one
        # Discord field's limit, and no part of a retained value is truncated.
        for offset in range(0, len(text), 400):
            fields.append(
                dict(label=f"{label} ({offset // 400 + 1})", text=text[offset : offset + 400])
            )

    document("Retained scan inputs", state["producer"]["inputs"])
    for label, configuration in (("Original", original), ("Current", current)):
        fields.append(
            dict(label=label + " registration fingerprint", text=digest(configuration).hex())
        )
        for index, file in enumerate(configuration.get("destinations", []), 1):
            if not isinstance(file, str) or not re.fullmatch(r"[A-Za-z0-9_-]{6,128}", file):
                raise SourceConflict(
                    "Destination identity is invalid; no confirmation is available."
                )
            fields.append(dict(label=f"{label} destination {index}", file_id=file))
        # Review the output contract as well as links: the same files can have
        # different registered output roles, ranges or preservation policies.
        document(
            label + " output settings",
            {k: v for k, v in configuration.items() if k != "destinations"},
        )
    return fields
