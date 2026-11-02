from __future__ import annotations

from copy import deepcopy

import pytest

from core.discord_embed_limits import (
    MAX_AUTHOR_CHARACTERS,
    MAX_DESCRIPTION_CHARACTERS,
    MAX_EMBEDS_PER_MESSAGE,
    MAX_FIELD_NAME_CHARACTERS,
    MAX_FIELD_VALUE_CHARACTERS,
    MAX_FIELDS_PER_EMBED,
    MAX_FOOTER_CHARACTERS,
    MAX_TITLE_CHARACTERS,
    MAX_TOTAL_CHARACTERS,
    EmbedPayloadLimitError,
    measure_embed_payload,
    require_valid_embed_payload,
    truncate_text,
    validate_embed_payload,
)


def _valid_payload() -> dict:
    return {
        "title": "title",
        "description": "description",
        "author": {"name": "author"},
        "footer": {"text": "footer"},
        "fields": [{"name": "name", "value": "value"}],
    }


@pytest.mark.parametrize(
    ("component", "limit", "path"),
    [
        ("title", MAX_TITLE_CHARACTERS, "embeds[0].title"),
        ("description", MAX_DESCRIPTION_CHARACTERS, "embeds[0].description"),
    ],
)
def test_component_exact_boundary_and_one_over(component, limit, path):
    payload = _valid_payload()
    payload[component] = "x" * limit
    assert validate_embed_payload(payload) == ()

    payload[component] += "x"
    assert [str(item) for item in validate_embed_payload(payload)] == [
        f"{path}: {limit + 1}/{limit}"
    ]


@pytest.mark.parametrize(
    ("container", "component", "limit", "path"),
    [
        ("author", "name", MAX_AUTHOR_CHARACTERS, "embeds[0].author.name"),
        ("footer", "text", MAX_FOOTER_CHARACTERS, "embeds[0].footer.text"),
    ],
)
def test_nested_component_exact_boundary_and_one_over(container, component, limit, path):
    payload = _valid_payload()
    payload[container][component] = "x" * limit
    assert validate_embed_payload(payload) == ()

    payload[container][component] += "x"
    assert [str(item) for item in validate_embed_payload(payload)] == [
        f"{path}: {limit + 1}/{limit}"
    ]


@pytest.mark.parametrize(
    ("component", "limit", "path"),
    [
        ("name", MAX_FIELD_NAME_CHARACTERS, "embeds[0].fields[0].name"),
        ("value", MAX_FIELD_VALUE_CHARACTERS, "embeds[0].fields[0].value"),
    ],
)
def test_field_component_exact_boundary_and_one_over(component, limit, path):
    payload = _valid_payload()
    payload["fields"][0][component] = "x" * limit
    assert validate_embed_payload(payload) == ()

    payload["fields"][0][component] += "x"
    assert [str(item) for item in validate_embed_payload(payload)] == [
        f"{path}: {limit + 1}/{limit}"
    ]


def test_embed_count_exact_boundary_and_one_over():
    payloads = [{} for _ in range(MAX_EMBEDS_PER_MESSAGE)]
    assert validate_embed_payload(payloads) == ()

    payloads.append({})
    assert [str(item) for item in validate_embed_payload(payloads)] == [
        f"embeds: {MAX_EMBEDS_PER_MESSAGE + 1}/{MAX_EMBEDS_PER_MESSAGE}"
    ]


def test_field_count_exact_boundary_and_one_over():
    payload = {"fields": [{"name": "n", "value": "v"}] * MAX_FIELDS_PER_EMBED}
    assert validate_embed_payload(payload) == ()

    payload["fields"].append({"name": "n", "value": "v"})
    assert [str(item) for item in validate_embed_payload(payload)] == [
        f"embeds[0].fields: {MAX_FIELDS_PER_EMBED + 1}/{MAX_FIELDS_PER_EMBED}"
    ]


def test_combined_character_exact_boundary_and_one_over_across_embeds():
    payloads = [
        {"description": "a" * (MAX_TOTAL_CHARACTERS // 2)},
        {"description": "b" * (MAX_TOTAL_CHARACTERS // 2)},
    ]
    assert validate_embed_payload(payloads) == ()

    payloads[1]["description"] += "b"
    assert [str(item) for item in validate_embed_payload(payloads)] == [
        f"message.embed_text_total: {MAX_TOTAL_CHARACTERS + 1}/{MAX_TOTAL_CHARACTERS}"
    ]


def test_measurement_and_remaining_budgets_accept_to_dict_object():
    class EmbedLike:
        def __init__(self, payload):
            self.payload = deepcopy(payload)

        def to_dict(self):
            return deepcopy(self.payload)

    usage = require_valid_embed_payload(EmbedLike(_valid_payload()))

    assert usage.embed_count == 1
    assert usage.field_counts == (1,)
    assert usage.total_characters == len("titledescriptionauthorfooternamevalue")
    assert usage.remaining_embeds == MAX_EMBEDS_PER_MESSAGE - 1
    assert usage.remaining_fields() == MAX_FIELDS_PER_EMBED - 1
    assert usage.remaining_characters == MAX_TOTAL_CHARACTERS - usage.total_characters


def test_require_valid_embed_payload_materializes_generator_once():
    payloads = ({"title": f"Embed {index}"} for index in range(2))

    usage = require_valid_embed_payload(payloads)

    assert usage.embed_count == 2
    assert usage.total_characters == len("Embed 0") + len("Embed 1")
    assert usage.field_counts == (0, 0)


def test_require_valid_payload_reports_all_component_paths():
    payload = _valid_payload()
    payload["title"] = "x" * (MAX_TITLE_CHARACTERS + 1)
    payload["fields"][0]["value"] = "y" * (MAX_FIELD_VALUE_CHARACTERS + 1)

    with pytest.raises(EmbedPayloadLimitError) as exc_info:
        require_valid_embed_payload(payload)

    assert [item.path for item in exc_info.value.violations] == [
        "embeds[0].title",
        "embeds[0].fields[0].value",
    ]


def test_truncate_text_marks_only_truncated_values():
    assert truncate_text("abc", 3) == "abc"
    assert truncate_text("abcd", 3) == "ab…"
    assert truncate_text("abcd", 2, marker="...") == ".."
    assert truncate_text("abcd", 0) == ""


def test_measure_rejects_text_instead_of_treating_it_as_embeds():
    with pytest.raises(TypeError, match="must not be text"):
        measure_embed_payload("not an embed")
