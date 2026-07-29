# research_chronology

## Purpose

Organize existing research items into a structured chronology using explicit date evidence from metadata, summary text, or title text.

The tool prepares dated events, undated items, invalid-date items, and optional year/month groups. It does not fetch new data or verify whether an event actually occurred.

## Use when

- A list of source or research items already exists.
- Events need to be ordered by date.
- Items without supported dates need to be separated for review.
- Date metadata or text dates need deterministic normalization.
- Chronology data should be prepared before formatting.

## Do not use when

- Recent posts need to be fetched from a social media account.
- Web search is needed.
- A URL needs to be read.
- No source items are available.
- The task requires fact-checking events.
- The task requires inferring dates without explicit evidence.
- The task requires deciding which source is more correct.

## Inputs

- `items`: List of research item dictionaries. Each item may include `title`, `summary`, `url`, `source`, `published_at`, `date`, `created_at`, or `updated_at`. A valid item must have at least one non-empty `title` or `summary`.
- `sort_order`: `ascending` or `descending`. Defaults to `ascending`.
- `group_by`: `none`, `year`, or `month`. Defaults to `none`.
- `max_items`: Integer from 1 to 100. Defaults to 20. Only the first `max_items` input entries are processed.

## Date priority

Date evidence is selected in this order:

```text
published_at
-> date
-> created_at
-> updated_at
-> summary
-> title
```

Metadata fields are parsed as full date strings. If the first non-empty metadata date is invalid or unsupported, the item is placed in `invalid_date_items`; lower-priority metadata fields and text fields are not used as fallback.

Dates are extracted from `summary` and then `title` only when no metadata date is present.

## Supported date formats

- ISO day: `2026-03-02`, `2026/03/02`
- ISO datetime: `2026-03-02T12:30:00`, `2026-03-02T12:30:00Z`, `2026-03-02 12:30:00`, `2026-03-02T12:30:00+07:00`
- Day-first numeric: `02/03/2026`, `02-03-2026`
- English day: `March 2, 2026`, `March 2 2026`, `2 March 2026`, `Mar 2, 2026`, `2 Mar 2026`
- Vietnamese day: `2 tháng 3 năm 2026`, `ngày 2 tháng 3 năm 2026`
- Month precision: `2026-03`, `2026/03`, `March 2026`, `Mar 2026`, `tháng 3 năm 2026`
- Year precision: `2026`, `năm 2026`

Day-first numeric dates are interpreted as `DD/MM/YYYY` or `DD-MM-YYYY`. Month-first numeric dates are not supported.

## Metadata parsing

Metadata date fields must match a supported date format as a full string after whitespace normalization. The parser intentionally does not extract a year from a long metadata sentence such as `This event happened in 2026 according to a report.`

## Text extraction

For `summary` and `title`, supported date patterns may appear inside a sentence. The parser checks more specific patterns before less specific patterns and suppresses nested matches, so `March 2, 2026` does not also produce `March 2026` or `2026`.

If one item contains multiple supported text dates, the first textual occurrence is used and a warning is added.

## Output

The tool always returns:

```python
{
    "events": [],
    "undated_items": [],
    "invalid_date_items": [],
    "groups": [],
    "warnings": [],
    "error": None,
    "message": "",
}
```

Each event includes:

```python
{
    "date": "2026-03-02",
    "date_precision": "day",
    "raw_date": "March 2, 2026",
    "date_source": "summary",
    "title": "Project A announced",
    "summary": "Project A was announced on March 2, 2026.",
    "url": "https://example.com/a",
    "source": "Company Blog",
    "original_index": 0,
}
```

Missing `title`, `summary`, `url`, or `source` values are returned as empty strings. `date_precision` is one of `day`, `month`, or `year`.

## Sorting

Events are sorted by an internal `(year, month, day)` key. Lower-precision dates use internal sort placeholders only:

- year precision sorts as month `1`, day `1`
- month precision sorts as day `1`
- day precision uses the actual date

The output preserves the real precision. It does not convert `2026` to `2026-01-01` or `2026-03` to `2026-03-01`.

Ties keep original input order in both ascending and descending order.

## Grouping

- `group_by="none"` returns `groups: []`.
- `group_by="year"` groups events by `YYYY`.
- `group_by="month"` groups day/month events by `YYYY-MM`.
- Year-only events with `group_by="month"` use `YYYY-unknown-month`, not `YYYY-01`.

Group order follows the top-level chronology order. Events inside each group keep the same order as top-level `events`.

## Validation and errors

- `items` must be a list.
- Empty `items` returns the full output contract with an error.
- Non-object item entries are skipped with an index warning.
- Items missing both `title` and `summary` are skipped with an index warning.
- `sort_order` must be `ascending` or `descending`.
- `group_by` must be `none`, `year`, or `month`.
- `max_items` must be an integer from 1 to 100. Boolean values are rejected.
- If more than `max_items` input entries are provided, only the first `max_items` are processed and a warning is added.

## Warnings and errors

Warnings are deterministic strings. Invalid dates use stable reasons such as:

- `Invalid calendar date.`
- `Invalid calendar month.`
- `Unsupported date format.`

The tool does not return raw Python exception messages.

## Determinism

The tool does not use randomness, current time, locale-dependent parsing, network calls, file I/O, APIs, or LLMs. The same input and arguments return the same output.

## Limitations

This tool organizes only the information supplied in the input.

It does not verify that an event actually occurred.

It does not infer missing dates without explicit evidence.

The resulting chronology may be incomplete if the input sources are incomplete.

Unsupported examples include relative dates, quarters, seasons, vague dates, date ranges, and month-first numeric dates.

## Examples

```python
items = [
    {
        "title": "Project proposal",
        "summary": "The project proposal was published in 2024.",
        "source": "Research Lab",
    },
    {
        "title": "Pilot announced",
        "summary": "The pilot was announced on March 2, 2025.",
        "source": "Company Blog",
    },
    {
        "title": "Public launch",
        "published_at": "2026-06-15T09:30:00Z",
        "summary": "The product became publicly available.",
        "source": "Official Newsroom",
    },
]
```

```python
{
    "events": [
        {
            "date": "2024",
            "date_precision": "year",
            "raw_date": "2024",
            "date_source": "summary",
            "title": "Project proposal",
            "summary": "The project proposal was published in 2024.",
            "url": "",
            "source": "Research Lab",
            "original_index": 0,
        },
        {
            "date": "2025-03-02",
            "date_precision": "day",
            "raw_date": "March 2, 2025",
            "date_source": "summary",
            "title": "Pilot announced",
            "summary": "The pilot was announced on March 2, 2025.",
            "url": "",
            "source": "Company Blog",
            "original_index": 1,
        },
        {
            "date": "2026-06-15",
            "date_precision": "day",
            "raw_date": "2026-06-15T09:30:00Z",
            "date_source": "published_at",
            "title": "Public launch",
            "summary": "The product became publicly available.",
            "url": "",
            "source": "Official Newsroom",
            "original_index": 2,
        },
    ],
    "undated_items": [],
    "invalid_date_items": [],
    "groups": [],
    "warnings": [],
    "error": None,
    "message": "Built chronology with 3 dated events, 0 undated items, and 0 invalid-date items.",
}
```
