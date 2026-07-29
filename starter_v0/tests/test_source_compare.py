from __future__ import annotations

import json
import unittest

from tools import TOOL_FUNCTIONS
from tools.source_compare import compare_sources


def assert_contract(test_case: unittest.TestCase, result: dict[str, object]) -> None:
    test_case.assertEqual(
        set(result),
        {"items", "comparison", "warnings", "error", "message"},
    )
    comparison = result["comparison"]
    test_case.assertIsInstance(comparison, dict)
    test_case.assertEqual(
        set(comparison),
        {"agreements", "unique_claims", "potential_conflicts", "missing_metadata"},
    )
    test_case.assertIsInstance(result["items"], list)
    test_case.assertIsInstance(result["warnings"], list)
    test_case.assertIsInstance(result["message"], str)


class SourceCompareTests(unittest.TestCase):
    def test_output_contract(self) -> None:
        result = compare_sources([
            {"summary": "AI adoption increased."},
            {"summary": "AI adoption increased in education."},
        ])
        assert_contract(self, result)

    def test_invalid_items_type(self) -> None:
        for invalid_items in (None, "invalid", 123, {}):
            with self.subTest(invalid_items=invalid_items):
                result = compare_sources(invalid_items)  # type: ignore[arg-type]
                assert_contract(self, result)
                self.assertIsInstance(result["error"], str)
                self.assertEqual(result["items"], [])

    def test_empty_list(self) -> None:
        result = compare_sources([])
        assert_contract(self, result)
        self.assertIsNotNone(result["error"])
        self.assertEqual(result["comparison"]["agreements"], [])
        self.assertEqual(result["comparison"]["unique_claims"], [])
        self.assertEqual(result["comparison"]["potential_conflicts"], [])

    def test_invalid_item_entries_are_skipped(self) -> None:
        result = compare_sources(["invalid", None, {"summary": "Valid source"}])  # type: ignore[list-item]
        assert_contract(self, result)
        self.assertEqual(len(result["items"]), 1)
        self.assertGreaterEqual(len(result["warnings"]), 3)
        self.assertTrue(any("item 0" in warning for warning in result["warnings"]))
        self.assertTrue(any("item 1" in warning for warning in result["warnings"]))

    def test_missing_summary_items_are_skipped(self) -> None:
        result = compare_sources([
            {"title": "A"},
            {"summary": ""},
            {"summary": "   "},
            {"summary": None},
            {"summary": 123},
            {"summary": "Valid source"},
        ])
        assert_contract(self, result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["summary"], "Valid source")

    def test_one_valid_source_warning(self) -> None:
        result = compare_sources([{"title": "A", "summary": "AI adoption increased."}])
        assert_contract(self, result)
        self.assertIsNone(result["error"])
        self.assertEqual(len(result["items"]), 1)
        self.assertTrue(any("at least two" in warning for warning in result["warnings"]))
        self.assertEqual(result["comparison"]["agreements"], [])
        self.assertEqual(result["comparison"]["unique_claims"], [])
        self.assertEqual(result["comparison"]["potential_conflicts"], [])

    def test_invalid_criterion(self) -> None:
        result = compare_sources([{"summary": "A"}, {"summary": "B"}], criterion="invalid")
        assert_contract(self, result)
        self.assertIsInstance(result["error"], str)
        self.assertIn("Invalid criterion", result["error"])

    def test_invalid_max_items(self) -> None:
        for max_items in (True, 1, 11, "5", None):
            with self.subTest(max_items=max_items):
                result = compare_sources([{"summary": "A"}, {"summary": "B"}], max_items=max_items)  # type: ignore[arg-type]
                assert_contract(self, result)
                self.assertIsInstance(result["error"], str)
                self.assertIn("max_items", result["error"])

    def test_truncation_preserves_order(self) -> None:
        result = compare_sources(
            [{"title": f"Source {index}", "summary": f"Claim {index} has enough words."} for index in range(5)],
            max_items=2,
        )
        assert_contract(self, result)
        self.assertEqual([item["title"] for item in result["items"]], ["Source 0", "Source 1"])
        self.assertTrue(any("max_items=2" in warning for warning in result["warnings"]))

    def test_agreements(self) -> None:
        result = compare_sources([
            {"title": "A", "summary": "AI adoption increased significantly in education."},
            {"title": "B", "summary": "AI adoption increased significantly across education."},
        ])
        agreements = result["comparison"]["agreements"]
        self.assertGreaterEqual(len(agreements), 1)
        self.assertEqual(agreements[0]["source_indices"], [0, 1])
        self.assertGreaterEqual(agreements[0]["similarity"], 0.45)

    def test_unique_claims(self) -> None:
        result = compare_sources([
            {
                "title": "A",
                "summary": "AI adoption increased in education. Universities automated admissions workflows.",
            },
            {
                "title": "B",
                "summary": "AI adoption increased across education. Hospitals piloted clinical documentation tools.",
            },
        ])
        unique_claims = result["comparison"]["unique_claims"]
        self.assertEqual([claim["source_index"] for claim in unique_claims], [0, 1])

    def test_numeric_conflict(self) -> None:
        result = compare_sources([
            {"summary": "AI adoption increased by 20 percent in universities."},
            {"summary": "AI adoption increased by 35 percent in universities."},
        ])
        conflict_types = [item["type"] for item in result["comparison"]["potential_conflicts"]]
        self.assertIn("numeric_difference", conflict_types)

    def test_directional_conflict(self) -> None:
        result = compare_sources([
            {"summary": "AI adoption increased in universities."},
            {"summary": "AI adoption decreased in universities."},
        ])
        conflict_types = [item["type"] for item in result["comparison"]["potential_conflicts"]]
        self.assertIn("directional_difference", conflict_types)

    def test_negation_conflict(self) -> None:
        result = compare_sources([
            {"summary": "The policy improved research quality."},
            {"summary": "The policy did not improve research quality."},
        ])
        conflict_types = [item["type"] for item in result["comparison"]["potential_conflicts"]]
        self.assertIn("negation_difference", conflict_types)

    def test_missing_metadata(self) -> None:
        result = compare_sources([
            {"title": "A", "summary": "AI adoption increased in education."},
            {"url": "https://example.com/b", "source": "B", "summary": "AI adoption increased in education."},
        ])
        self.assertEqual(result["comparison"]["missing_metadata"], [
            {"item_index": 0, "original_index": 0, "missing_fields": ["url", "source"]},
            {"item_index": 1, "original_index": 1, "missing_fields": ["title"]},
        ])

    def test_criterion_behavior(self) -> None:
        items = [
            {"summary": "AI adoption increased by 20 percent in universities. Shared claim appears here."},
            {"summary": "AI adoption increased by 35 percent in universities. Shared claim appears here."},
        ]
        coverage = compare_sources(items, criterion="coverage")
        agreement = compare_sources(items, criterion="agreement")
        conflicts = compare_sources(items, criterion="conflicts")

        self.assertGreaterEqual(len(coverage["comparison"]["agreements"]), 1)
        self.assertGreaterEqual(len(coverage["comparison"]["potential_conflicts"]), 1)
        self.assertGreaterEqual(len(agreement["comparison"]["agreements"]), 1)
        self.assertEqual(agreement["comparison"]["potential_conflicts"], [])
        self.assertEqual(conflicts["comparison"]["agreements"], [])
        self.assertGreaterEqual(len(conflicts["comparison"]["potential_conflicts"]), 1)

    def test_deterministic_output(self) -> None:
        items = [
            {"title": "A", "summary": "AI adoption increased in education."},
            {"title": "B", "summary": "AI adoption increased across education."},
        ]
        self.assertEqual(compare_sources(items), compare_sources(items))

    def test_json_serialization(self) -> None:
        result = compare_sources([
            {"summary": "AI adoption increased in education."},
            {"summary": "AI adoption increased across education."},
        ])
        json.dumps(result, ensure_ascii=False)

    def test_registry(self) -> None:
        self.assertIn("source_compare", TOOL_FUNCTIONS)
        self.assertIs(TOOL_FUNCTIONS["source_compare"], compare_sources)


if __name__ == "__main__":
    unittest.main()
