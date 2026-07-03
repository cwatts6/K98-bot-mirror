from __future__ import annotations

from datetime import UTC, datetime
import json

from voting import survey_dal


def test_answer_audit_rows_include_text_and_detail_payloads():
    now = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)
    rows = [
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps(
                {
                    "choices": {"10": [101]},
                    "text": {"11": "old text"},
                    "details": {"10": {"101": "old detail"}},
                }
            ),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 10,
            "QuestionKey": "q1",
            "Prompt": "Choice?",
            "QuestionType": "SingleChoice",
            "SurveyOptionID": 101,
            "OptionKey": "opt1",
            "Label": "A",
            "AnswerText": None,
            "DetailText": "new detail",
        },
        {
            "SurveyID": 42,
            "Title": "Planning",
            "ClosedAtUtc": now,
            "ResponseID": 9,
            "DiscordUserID": 123,
            "OriginalAnswersJson": json.dumps(
                {
                    "choices": {"10": [101]},
                    "text": {"11": "old text"},
                    "details": {"10": {"101": "old detail"}},
                }
            ),
            "ResponseCreatedAtUtc": now,
            "ResponseUpdatedAtUtc": now,
            "SurveyQuestionID": 11,
            "QuestionKey": "q2",
            "Prompt": "Explain?",
            "QuestionType": "Text",
            "SurveyOptionID": None,
            "OptionKey": None,
            "Label": None,
            "AnswerText": "new text",
            "DetailText": None,
        },
    ]

    audit_rows = survey_dal._answer_audit_from_rows(rows)

    assert audit_rows[0].selected_option_ids == (101,)
    assert audit_rows[0].selected_option_detail_notes == ("new detail",)
    assert audit_rows[0].original_selected_option_detail_notes == ("old detail",)
    assert audit_rows[1].text_answer == "new text"
    assert audit_rows[1].original_text_answer == "old text"
