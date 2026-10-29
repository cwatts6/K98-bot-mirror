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


def admission_context(state):
    original = json.loads(state["preparation"]["RequestJson"])["request"]["config"]
    current = state["current_registration"]
    inputs = state["producer"]["inputs"]
    return dict(
        input_file=str(inputs["metadata"].get("source_filename") or inputs["completed_filename"])[
            :260
        ],
        retained_input=inputs["completed_filename"],
        original_created_utc=state["preparation"]["CreatedUTC"],
        producer_procedure="Saved stats SQL stage",
        original_fault=(
            "writer_admission_refused_before_execution"
            if state["original_phase"] == "refused"
            else state["original_phase"]
        ),
        current_blocker="waiting_for_access" if state["blockers"] else None,
        original_configuration_sha256=digest(original).hex(),
        current_configuration_sha256=digest(current).hex(),
        original_destination_count=len(original.get("destinations", [])),
        current_destination_count=len(current.get("destinations", [])),
        registration_matches=original == current,
        changed_setting_names=[
            str(k)[:40]
            for k in sorted(set(original) | set(current))
            if original.get(k) != current.get(k)
        ][:6],
        rank=inputs["rank"],
        seed=inputs["seed"],
        summary="Review this exact retained input. Admission evidence is separate from completion of an import or delivery.",
    )


def admission_summary(evidence, action):
    context, decision = evidence["failure_context"], evidence["actions"][action]
    return [
        dict(
            label="Which input?",
            text=f"Created: {context['original_created_utc']} UTC\nInput: {context['input_file'][:120]}\nRetained SQL input: {context['retained_input']}\nRank: {str(context['rank'])[:64]}; seed: {str(context['seed'])[:64]}",
        ),
        dict(label="What is known?", text=evidence["explanation"]),
        dict(
            label="Configuration",
            text=(
                "Original and current settings match. "
                if context["registration_matches"]
                else "Original and current settings DIFFER. "
            )
            + f"Original destinations: {context['original_destination_count']}; current: {context['current_destination_count']}. "
            + (
                "Changed settings: " + ", ".join(context["changed_setting_names"]) + ". "
                if context["changed_setting_names"]
                else ""
            )
            + "Full settings and links are available in technical details.",
        ),
        dict(label="Your decision", text=decision["check"]),
        dict(label="What happens next?", text=decision["effect"]),
    ]
