from __future__ import annotations

import copy
import json
import unittest

from tools import TOOL_FUNCTIONS
from tools.research_chronology import build_research_chronology


EXPECTED_KEYS = {
    "events",
    "undated_items",
    "invalid_date_items",
    "groups",
    "warnings",
    "error",
    "message",
}
EVENT_KEYS = {
    "date",
    "date_precision",
    "raw_date",
    "date_source",
    "title",
    "summary",
    "url",
    "source",
    "original_index",
}


def assert_contract(test_case: unittest.TestCase, result: dict[str, object]) -> None:
    test_case.assertEqual(set(result), EXPECTED_KEYS)
    test_case.assertIsInstance(result["events"], list)
    test_case.assertIsInstance(result["undated_items"], list)
    test_case.assertIsInstance(result["invalid_date_items"], list)
    test_case.assertIsInstance(result["groups"], list)
    test_case.assertIsInstance(result["warnings"], list)
    test_case.assertIsInstance(result["message"], str)


class ResearchChronologyTests(unittest.TestCase):
    def test_output_contract(self) -> None:
        result = build_research_chronology([{"title": "A", "date": "2026-03-02"}])
        assert_contract(self, result)
        self.assertEqual(set(result["events"][0]), EVENT_KEYS)

    def test_invalid_items_type(self) -> None:
        for items in (None, "invalid", 123, {"title": "A"}):
            with self.subTest(items=items):
                result = build_research_chronology(items)  # type: ignore[arg-type]
                assert_contract(self, result)
                self.assertIsInstance(result["error"], str)
                self.assertEqual(result["events"], [])

    def test_empty_list(self) -> None:
        result = build_research_chronology([])
        assert_contract(self, result)
        self.assertIsNotNone(result["error"])

    def test_invalid_item_entries_are_skipped(self) -> None:
        result = build_research_chronology(["invalid", None, 123, {"title": "Valid", "published_at": "2026-03-02"}])
        self.assertEqual(len(result["events"]), 1)
        self.assertEqual(result["events"][0]["original_index"], 3)
        self.assertTrue(any("index 0" in warning for warning in result["warnings"]))

    def test_item_without_title_or_summary_is_skipped(self) -> None:
        result = build_research_chronology([{"published_at": "2026-03-02"}])
        self.assertEqual(result["events"], [])
        self.assertTrue(any("no title or summary" in warning for warning in result["warnings"]))

    def test_invalid_arguments(self) -> None:
        cases = [
            {"sort_order": "latest"},
            {"group_by": "week"},
            {"max_items": "20"},
            {"max_items": True},
            {"max_items": False},
            {"max_items": 0},
            {"max_items": -1},
            {"max_items": 101},
            {"max_items": 1.5},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                result = build_research_chronology([{"title": "A", "date": "2026"}], **kwargs)
                assert_contract(self, result)
                self.assertIsInstance(result["error"], str)

    def test_max_items_truncates_input_order(self) -> None:
        result = build_research_chronology(
            [
                {"title": "A", "date": "2024"},
                {"title": "B", "date": "2025"},
                {"title": "C", "date": "2026"},
            ],
            max_items=2,
        )
        self.assertEqual([event["title"] for event in result["events"]], ["A", "B"])
        self.assertTrue(any("Only the first 2" in warning for warning in result["warnings"]))

    def test_metadata_priority(self) -> None:
        result = build_research_chronology([{
            "title": "A",
            "published_at": "2026-03-02",
            "date": "2025-01-01",
        }])
        self.assertEqual(result["events"][0]["date"], "2026-03-02")
        self.assertEqual(result["events"][0]["date_source"], "published_at")

        result = build_research_chronology([{
            "title": "B",
            "date": "2025-01-01",
            "created_at": "2024-01-01",
        }])
        self.assertEqual(result["events"][0]["date"], "2025-01-01")
        self.assertEqual(result["events"][0]["date_source"], "date")

        result = build_research_chronology([{
            "title": "C",
            "created_at": "2024-01-01",
            "updated_at": "2023-01-01",
        }])
        self.assertEqual(result["events"][0]["date"], "2024-01-01")
        self.assertEqual(result["events"][0]["date_source"], "created_at")

    def test_metadata_beats_text_and_invalid_metadata_does_not_fallback(self) -> None:
        result = build_research_chronology([{
            "title": "A",
            "summary": "The event happened on March 2, 2026.",
            "published_at": "2025-01-01",
        }])
        self.assertEqual(result["events"][0]["date"], "2025-01-01")
        self.assertEqual(result["events"][0]["date_source"], "published_at")

        result = build_research_chronology([{
            "title": "B",
            "summary": "The event happened on March 2, 2026.",
            "published_at": "2026-02-30",
            "date": "2026-03-02",
        }])
        self.assertEqual(result["events"], [])
        self.assertEqual(len(result["invalid_date_items"]), 1)
        self.assertEqual(result["invalid_date_items"][0]["date_source"], "published_at")

    def test_empty_metadata_field_falls_through(self) -> None:
        result = build_research_chronology([{
            "title": "A",
            "published_at": " ",
            "date": "2026-03-02",
        }])
        self.assertEqual(result["events"][0]["date"], "2026-03-02")
        self.assertEqual(result["events"][0]["date_source"], "date")

    def test_supported_date_formats(self) -> None:
        cases = [
            ("2026-03-02", "2026-03-02", "day"),
            ("2026/03/02", "2026-03-02", "day"),
            ("2026-03-02T12:30:00", "2026-03-02", "day"),
            ("2026-03-02T12:30:00Z", "2026-03-02", "day"),
            ("2026-03-02T12:30:00+07:00", "2026-03-02", "day"),
            ("2026-03-02 12:30:00", "2026-03-02", "day"),
            ("02/03/2026", "2026-03-02", "day"),
            ("02-03-2026", "2026-03-02", "day"),
            ("March 2, 2026", "2026-03-02", "day"),
            ("2 March 2026", "2026-03-02", "day"),
            ("Mar 2, 2026", "2026-03-02", "day"),
            ("ngày 2 tháng 3 năm 2026", "2026-03-02", "day"),
            ("2 tháng 3 năm 2026", "2026-03-02", "day"),
            ("2026-03", "2026-03", "month"),
            ("2026/03", "2026-03", "month"),
            ("March 2026", "2026-03", "month"),
            ("Mar 2026", "2026-03", "month"),
            ("tháng 3 năm 2026", "2026-03", "month"),
            ("2026", "2026", "year"),
            ("năm 2026", "2026", "year"),
        ]
        for raw_date, expected_date, expected_precision in cases:
            with self.subTest(raw_date=raw_date):
                result = build_research_chronology([{"title": "A", "date": raw_date}])
                self.assertEqual(result["error"], None)
                self.assertEqual(result["events"][0]["date"], expected_date)
                self.assertEqual(result["events"][0]["date_precision"], expected_precision)

    def test_invalid_dates_and_leap_day(self) -> None:
        invalid_dates = ["2026-02-30", "2026-13-01", "31/04/2026", "29/02/2025"]
        for raw_date in invalid_dates:
            with self.subTest(raw_date=raw_date):
                result = build_research_chronology([{"title": "A", "date": raw_date}])
                self.assertEqual(result["events"], [])
                self.assertEqual(result["invalid_date_items"][0]["reason"], "Invalid calendar date.")

        result = build_research_chronology([{"title": "Leap", "date": "29/02/2024"}])
        self.assertEqual(result["events"][0]["date"], "2024-02-29")

    def test_unsupported_metadata_format(self) -> None:
        result = build_research_chronology([{
            "title": "A",
            "date": "This event happened in 2026 according to a report.",
        }])
        self.assertEqual(result["invalid_date_items"][0]["reason"], "Unsupported date format.")
        self.assertEqual(result["events"], [])

    def test_text_extraction_priority_and_undated(self) -> None:
        result = build_research_chronology([{
            "title": "No title date",
            "summary": "The event happened on March 2, 2026.",
        }])
        self.assertEqual(result["events"][0]["date"], "2026-03-02")
        self.assertEqual(result["events"][0]["date_source"], "summary")

        result = build_research_chronology([{
            "title": "Event on March 2, 2026",
            "summary": "No supported date here.",
        }])
        self.assertEqual(result["events"][0]["date_source"], "title")

        result = build_research_chronology([{
            "title": "Event on March 2, 2026",
            "summary": "Summary says April 3, 2025.",
        }])
        self.assertEqual(result["events"][0]["date"], "2025-04-03")
        self.assertEqual(result["events"][0]["date_source"], "summary")

        result = build_research_chronology([{"title": "No date", "summary": "No supported date here."}])
        self.assertEqual(len(result["undated_items"]), 1)
        self.assertEqual(result["undated_items"][0]["reason"], "No supported date was found.")

    def test_multiple_text_dates_and_no_nested_candidates(self) -> None:
        result = build_research_chronology([{
            "title": "A",
            "summary": "Announced on March 2, 2026 and launched on June 15, 2026.",
        }])
        self.assertEqual(result["events"][0]["date"], "2026-03-02")
        self.assertEqual(result["events"][0]["raw_date"], "March 2, 2026")
        self.assertTrue(any("multiple supported dates" in warning for warning in result["warnings"]))

        result = build_research_chronology([{
            "title": "A",
            "summary": "Announced on March 2, 2026.",
        }])
        self.assertFalse(any("multiple supported dates" in warning for warning in result["warnings"]))

    def test_sorting_and_precision_preservation(self) -> None:
        items = [
            {"title": "Later", "date": "2026-06-15"},
            {"title": "Earlier", "date": "2025-01-10"},
            {"title": "Year", "date": "2024"},
            {"title": "Month", "date": "2024-03"},
        ]
        ascending = build_research_chronology(items, sort_order="ascending")
        descending = build_research_chronology(items, sort_order="descending")
        self.assertEqual([event["title"] for event in ascending["events"]], ["Year", "Month", "Earlier", "Later"])
        self.assertEqual([event["title"] for event in descending["events"]], ["Later", "Earlier", "Month", "Year"])
        self.assertEqual(ascending["events"][0]["date"], "2024")
        self.assertEqual(ascending["events"][1]["date"], "2024-03")

    def test_stable_ties_for_ascending_and_descending(self) -> None:
        items = [
            {"title": "Event B", "date": "2026-03-02"},
            {"title": "Event A", "date": "2026-03-02"},
        ]
        ascending = build_research_chronology(items, sort_order="ascending")
        descending = build_research_chronology(items, sort_order="descending")
        self.assertEqual([event["title"] for event in ascending["events"]], ["Event B", "Event A"])
        self.assertEqual([event["title"] for event in descending["events"]], ["Event B", "Event A"])

    def test_grouping(self) -> None:
        items = [
            {"title": "Year-only event", "date": "2025"},
            {"title": "Month event", "date": "2025-03"},
            {"title": "Day event", "date": "2025-03-10"},
            {"title": "Next year", "date": "2026-01-01"},
        ]
        none = build_research_chronology(items, group_by="none")
        by_year = build_research_chronology(items, group_by="year")
        by_month = build_research_chronology(items, group_by="month")

        self.assertEqual(none["groups"], [])
        self.assertEqual([group["key"] for group in by_year["groups"]], ["2025", "2026"])
        self.assertEqual([group["key"] for group in by_month["groups"]], [
            "2025-unknown-month",
            "2025-03",
            "2026-01",
        ])
        self.assertEqual(
            [event["title"] for group in by_month["groups"] for event in group["events"]],
            [event["title"] for event in by_month["events"]],
        )

    def test_deterministic_json_and_input_immutable(self) -> None:
        items = [
            {"title": "Event B", "date": "2026-03-02"},
            {"title": "Event A", "date": "2026-03-02"},
            {"title": "Year event", "date": "2025"},
        ]
        original = copy.deepcopy(items)
        first = build_research_chronology(items, group_by="year")
        second = build_research_chronology(items, group_by="year")
        self.assertEqual(first, second)
        self.assertEqual(items, original)
        json.dumps(first, ensure_ascii=False)

    def test_import_and_registry(self) -> None:
        self.assertTrue(callable(build_research_chronology))
        self.assertIn("research_chronology", TOOL_FUNCTIONS)
        self.assertIs(TOOL_FUNCTIONS["research_chronology"], build_research_chronology)


if __name__ == "__main__":
    unittest.main()
