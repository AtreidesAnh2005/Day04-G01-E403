from __future__ import annotations

import re
from datetime import date, datetime
from types import MappingProxyType
from typing import Any


VALID_SORT_ORDERS = {"ascending", "descending"}
VALID_GROUP_BY = {"none", "year", "month"}
MIN_ITEMS = 1
MAX_ITEMS = 100
DATE_FIELDS = ("published_at", "date", "created_at", "updated_at")
TEXT_DATE_FIELDS = ("summary", "title")
DATE_SOURCES = (*DATE_FIELDS, *TEXT_DATE_FIELDS)
TEXT_FIELDS = ("title", "summary", "url", "source")

MONTHS = MappingProxyType({
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
})
MONTH_PATTERN = (
    "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|"
    "aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
)
VI_DAY_WORD = r"ng(?:ày|.y)"
VI_MONTH_WORD = r"th(?:áng|.ng)"
VI_YEAR_WORD = r"n(?:ăm|.m)"


def _empty_result(message: str = "") -> dict[str, Any]:
    return {
        "events": [],
        "undated_items": [],
        "invalid_date_items": [],
        "groups": [],
        "warnings": [],
        "error": None,
        "message": message,
    }


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def _clean_optional_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return _normalize_whitespace(value)


def _base_item(item: dict[str, Any], original_index: int) -> dict[str, Any]:
    normalized = {field: _clean_optional_text(item.get(field)) for field in TEXT_FIELDS}
    normalized["original_index"] = original_index
    return normalized


def _has_content(item: dict[str, Any]) -> bool:
    return bool(_clean_optional_text(item.get("title")) or _clean_optional_text(item.get("summary")))


def _extract_metadata_date(item: dict[str, Any]) -> tuple[str, str] | None:
    for field in DATE_FIELDS:
        value = item.get(field)
        if isinstance(value, str):
            text = _normalize_whitespace(value)
            if text:
                return text, field
        elif value is not None:
            return str(value), field
    return None


def _valid_date(year: int, month: int, day: int) -> bool:
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _month_number(value: str) -> int | None:
    return MONTHS.get(value.lower().rstrip("."))


def _candidate(
    *,
    raw_date: str,
    date_value: str,
    precision: str,
    sort_key: tuple[int, int, int],
    date_source: str,
    span: tuple[int, int] = (0, 0),
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "date": date_value,
        "date_precision": precision,
        "raw_date": _normalize_whitespace(raw_date),
        "date_source": date_source,
        "sort_key": sort_key,
        "span": span,
        "reason": reason,
    }


def _format_day(year: int, month: int, day: int) -> str:
    return f"{year:04d}-{month:02d}-{day:02d}"


def _format_month(year: int, month: int) -> str:
    return f"{year:04d}-{month:02d}"


def _parse_day(year: int, month: int, day: int, raw_date: str, date_source: str, span: tuple[int, int]) -> dict[str, Any]:
    if not _valid_date(year, month, day):
        return _candidate(
            raw_date=raw_date,
            date_value=_format_day(year, max(1, min(month, 12)), max(1, min(day, 31))),
            precision="day",
            sort_key=(0, 0, 0),
            date_source=date_source,
            span=span,
            reason="Invalid calendar date.",
        )
    return _candidate(
        raw_date=raw_date,
        date_value=_format_day(year, month, day),
        precision="day",
        sort_key=(year, month, day),
        date_source=date_source,
        span=span,
    )


def _parse_month(year: int, month: int, raw_date: str, date_source: str, span: tuple[int, int]) -> dict[str, Any]:
    if not 1 <= month <= 12:
        return _candidate(
            raw_date=raw_date,
            date_value=_format_month(year, max(1, min(month, 12))),
            precision="month",
            sort_key=(0, 0, 0),
            date_source=date_source,
            span=span,
            reason="Invalid calendar month.",
        )
    return _candidate(
        raw_date=raw_date,
        date_value=_format_month(year, month),
        precision="month",
        sort_key=(year, month, 1),
        date_source=date_source,
        span=span,
    )


def _parse_year(year: int, raw_date: str, date_source: str, span: tuple[int, int]) -> dict[str, Any]:
    if year < 1:
        return _candidate(
            raw_date=raw_date,
            date_value=str(year),
            precision="year",
            sort_key=(0, 0, 0),
            date_source=date_source,
            span=span,
            reason="Invalid calendar year.",
        )
    return _candidate(
        raw_date=raw_date,
        date_value=f"{year:04d}",
        precision="year",
        sort_key=(year, 1, 1),
        date_source=date_source,
        span=span,
    )


def _candidate_from_match(match: re.Match[str], pattern_name: str, date_source: str) -> dict[str, Any]:
    raw_date = match.group(0)
    span = match.span()

    if pattern_name in {"iso_day", "iso_datetime"}:
        return _parse_day(int(match.group("year")), int(match.group("month")), int(match.group("day")), raw_date, date_source, span)
    if pattern_name == "day_first":
        return _parse_day(int(match.group("year")), int(match.group("month")), int(match.group("day")), raw_date, date_source, span)
    if pattern_name == "english_month_day":
        month = _month_number(match.group("month_name")) or 0
        return _parse_day(int(match.group("year")), month, int(match.group("day")), raw_date, date_source, span)
    if pattern_name == "english_day_month":
        month = _month_number(match.group("month_name")) or 0
        return _parse_day(int(match.group("year")), month, int(match.group("day")), raw_date, date_source, span)
    if pattern_name == "vietnamese_day":
        return _parse_day(int(match.group("year")), int(match.group("month")), int(match.group("day")), raw_date, date_source, span)
    if pattern_name == "iso_month":
        return _parse_month(int(match.group("year")), int(match.group("month")), raw_date, date_source, span)
    if pattern_name == "english_month":
        month = _month_number(match.group("month_name")) or 0
        return _parse_month(int(match.group("year")), month, raw_date, date_source, span)
    if pattern_name == "vietnamese_month":
        return _parse_month(int(match.group("year")), int(match.group("month")), raw_date, date_source, span)
    if pattern_name in {"year", "vietnamese_year"}:
        return _parse_year(int(match.group("year")), raw_date, date_source, span)

    return _candidate(
        raw_date=raw_date,
        date_value=raw_date,
        precision="",
        sort_key=(0, 0, 0),
        date_source=date_source,
        span=span,
        reason="Unsupported date format.",
    )


def _pattern_specs(metadata: bool) -> list[tuple[str, str]]:
    boundary_start = r"(?<!\d)" if not metadata else r"^"
    boundary_end = r"(?!\d)" if not metadata else r"$"
    sep = r"\s*" if metadata else r""
    return [
        (
            "iso_datetime",
            rf"{boundary_start}(?P<year>\d{{4}})-(?P<month>\d{{2}})-(?P<day>\d{{2}})"
            rf"[T ]\d{{2}}:\d{{2}}:\d{{2}}(?:Z|[+-]\d{{2}}:\d{{2}})?{boundary_end}",
        ),
        ("iso_day", rf"{boundary_start}(?P<year>\d{{4}})[-/](?P<month>\d{{2}})[-/](?P<day>\d{{2}}){boundary_end}"),
        ("day_first", rf"{boundary_start}(?P<day>\d{{2}})[/-](?P<month>\d{{2}})[/-](?P<year>\d{{4}}){boundary_end}"),
        (
            "english_month_day",
            rf"{boundary_start}(?P<month_name>{MONTH_PATTERN})\.?{sep}\s+(?P<day>\d{{1,2}}),?{sep}\s+(?P<year>\d{{4}}){boundary_end}",
        ),
        (
            "english_day_month",
            rf"{boundary_start}(?P<day>\d{{1,2}}){sep}\s+(?P<month_name>{MONTH_PATTERN})\.?,?{sep}\s+(?P<year>\d{{4}}){boundary_end}",
        ),
        (
            "vietnamese_day",
            rf"{boundary_start}(?:{VI_DAY_WORD}\s+)?(?P<day>\d{{1,2}})\s+{VI_MONTH_WORD}\s+(?P<month>\d{{1,2}})\s+{VI_YEAR_WORD}\s+(?P<year>\d{{4}}){boundary_end}",
        ),
        ("iso_month", rf"{boundary_start}(?P<year>\d{{4}})[-/](?P<month>\d{{2}}){boundary_end}"),
        ("english_month", rf"{boundary_start}(?P<month_name>{MONTH_PATTERN})\.?{sep}\s+(?P<year>\d{{4}}){boundary_end}"),
        ("vietnamese_month", rf"{boundary_start}{VI_MONTH_WORD}\s+(?P<month>\d{{1,2}})\s+{VI_YEAR_WORD}\s+(?P<year>\d{{4}}){boundary_end}"),
        ("vietnamese_year", rf"{boundary_start}{VI_YEAR_WORD}\s+(?P<year>\d{{4}}){boundary_end}"),
        ("year", rf"{boundary_start}(?P<year>\d{{4}}){boundary_end}"),
    ]


def _overlaps(span: tuple[int, int], used_spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < used_end and end > used_start for used_start, used_end in used_spans)


def _parse_metadata_date(raw_date: str, date_source: str) -> dict[str, Any]:
    text = _normalize_whitespace(raw_date)
    for pattern_name, pattern in _pattern_specs(metadata=True):
        match = re.fullmatch(pattern, text, flags=re.IGNORECASE)
        if match:
            return _candidate_from_match(match, pattern_name, date_source)
    return _candidate(
        raw_date=text,
        date_value=text,
        precision="",
        sort_key=(0, 0, 0),
        date_source=date_source,
        reason="Unsupported date format.",
    )


def _extract_text_dates(text: str, date_source: str) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    used_spans: list[tuple[int, int]] = []
    for pattern_name, pattern in _pattern_specs(metadata=False):
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            span = match.span()
            if _overlaps(span, used_spans):
                continue
            candidates.append(_candidate_from_match(match, pattern_name, date_source))
            used_spans.append(span)
    return sorted(candidates, key=lambda item: (item["span"][0], item["span"][1]))


def _extract_date(item: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    metadata_date = _extract_metadata_date(item)
    if metadata_date is not None:
        raw_date, date_source = metadata_date
        candidate = _parse_metadata_date(raw_date, date_source)
        return candidate, [candidate]

    for field in TEXT_DATE_FIELDS:
        text = _clean_optional_text(item.get(field))
        if not text:
            continue
        candidates = _extract_text_dates(text, field)
        if candidates:
            return candidates[0], candidates

    return None, []


def _event_from_candidate(base: dict[str, Any], candidate: dict[str, Any], input_order: int) -> dict[str, Any]:
    event = dict(base)
    event.update({
        "date": candidate["date"],
        "date_precision": candidate["date_precision"],
        "raw_date": candidate["raw_date"],
        "date_source": candidate["date_source"],
        "_sort_key": candidate["sort_key"],
        "_input_order": input_order,
    })
    return event


def _invalid_item_from_candidate(base: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    invalid = dict(base)
    invalid.update({
        "raw_date": candidate["raw_date"],
        "date_source": candidate["date_source"],
        "reason": candidate["reason"] or "Unsupported date format.",
    })
    return invalid


def _undated_item(base: dict[str, Any]) -> dict[str, Any]:
    undated = dict(base)
    undated["reason"] = "No supported date was found."
    return undated


def _strip_internal_keys(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for event in events:
        public_event = dict(event)
        public_event.pop("_sort_key", None)
        public_event.pop("_input_order", None)
        cleaned.append(public_event)
    return cleaned


def _sort_events(events: list[dict[str, Any]], sort_order: str) -> list[dict[str, Any]]:
    if sort_order == "descending":
        return sorted(
            events,
            key=lambda event: (
                -event["_sort_key"][0],
                -event["_sort_key"][1],
                -event["_sort_key"][2],
                event["_input_order"],
            ),
        )
    return sorted(events, key=lambda event: (event["_sort_key"], event["_input_order"]))


def _group_key(event: dict[str, Any], group_by: str) -> str:
    if group_by == "year":
        return event["date"][:4]
    if event["date_precision"] == "year":
        return f"{event['date']}-unknown-month"
    return event["date"][:7]


def _build_groups(events: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    if group_by == "none":
        return []

    groups: list[dict[str, Any]] = []
    index_by_key: dict[str, int] = {}
    for event in events:
        key = _group_key(event, group_by)
        if key not in index_by_key:
            index_by_key[key] = len(groups)
            groups.append({"key": key, "events": []})
        groups[index_by_key[key]]["events"].append(dict(event))
    return groups


def _set_message(result: dict[str, Any]) -> None:
    event_count = len(result["events"])
    undated_count = len(result["undated_items"])
    invalid_count = len(result["invalid_date_items"])
    result["message"] = (
        f"Built chronology with {event_count} dated events, {undated_count} undated item"
        f"{'' if undated_count == 1 else 's'}, and {invalid_count} invalid-date item"
        f"{'' if invalid_count == 1 else 's'}."
    )


def build_research_chronology(
    items: list[dict[str, Any]],
    sort_order: str = "ascending",
    group_by: str = "none",
    max_items: int = 20,
) -> dict[str, Any]:
    """Build a structured chronology from already-collected research items.

    The tool uses explicit metadata dates first, then supported date patterns
    in ``summary`` and ``title``. It does not fetch data, call APIs or LLMs,
    infer missing dates, verify events, mutate input, or edit external state.
    """
    result = _empty_result()

    if sort_order not in VALID_SORT_ORDERS:
        result["error"] = "Invalid sort_order: expected 'ascending' or 'descending'."
        result["message"] = "Invalid sort_order."
        return result

    if group_by not in VALID_GROUP_BY:
        result["error"] = "Invalid group_by: expected 'none', 'year', or 'month'."
        result["message"] = "Invalid group_by."
        return result

    if not isinstance(max_items, int) or isinstance(max_items, bool):
        result["error"] = "Invalid max_items: expected an integer between 1 and 100."
        result["message"] = "Invalid max_items."
        return result

    if max_items < MIN_ITEMS or max_items > MAX_ITEMS:
        result["error"] = "Invalid max_items: expected an integer between 1 and 100."
        result["message"] = "Invalid max_items."
        return result

    if not isinstance(items, list):
        result["error"] = "Invalid items: expected a list of research item dictionaries."
        result["message"] = "No valid research items were provided."
        return result

    if not items:
        result["error"] = "No research items were provided."
        result["message"] = "No valid research items were provided."
        return result

    if len(items) > max_items:
        result["warnings"].append(f"Only the first {max_items} items were processed.")

    for original_index, item in enumerate(items[:max_items]):
        if not isinstance(item, dict):
            result["warnings"].append(f"Item at index {original_index} is not an object and was skipped.")
            continue

        if not _has_content(item):
            result["warnings"].append(f"Item at index {original_index} has no title or summary and was skipped.")
            continue

        base = _base_item(item, original_index)
        candidate, candidates = _extract_date(item)
        if candidate is None:
            result["undated_items"].append(_undated_item(base))
            continue

        if len(candidates) > 1 and candidate["date_source"] in TEXT_DATE_FIELDS:
            result["warnings"].append(
                f"Item at index {original_index} contains multiple supported dates; "
                "the first textual occurrence was used."
            )

        if candidate["reason"] is not None:
            result["invalid_date_items"].append(_invalid_item_from_candidate(base, candidate))
            continue

        result["events"].append(_event_from_candidate(base, candidate, original_index))

    result["events"] = _strip_internal_keys(_sort_events(result["events"], sort_order))
    result["groups"] = _build_groups(result["events"], group_by)
    _set_message(result)
    return result
