# source_compare

## Purpose

Compares source items that the agent has already collected from other research tools. The tool analyzes only the provided summaries and returns heuristic signals about overlapping content, unique content, potential conflicts, and missing metadata.

## Use when

- The user asks to compare two or more existing sources.
- The agent already has source items from tools such as lookup, fetch, social_search, or timeline.
- The agent needs a structured comparison of agreements, unique claims, or potential conflicts.

## Do not use when

- No source items have been collected yet.
- Only one source is available.
- New sources need to be searched.
- A new URL needs to be read.
- The task requires fact-checking.
- The task requires deciding which source is correct.
- The task requires scoring real-world trustworthiness.

## Inputs

- `items`: A list of source item dictionaries. Each item may contain `title`, `url`, `source`, `summary`, and `section`. The `summary` field is required for a source to be compared.
- `criterion`: One of `coverage`, `agreement`, or `conflicts`.
- `max_items`: Integer from 2 to 10. The tool processes the first `max_items` valid source items in input order.

## Criteria

- `coverage`: Returns agreements, unique claims, potential conflicts, and missing metadata.
- `agreement`: Returns agreements and missing metadata. Unique claims and potential conflicts remain empty.
- `conflicts`: Returns potential conflicts and missing metadata. Agreements and unique claims remain empty.

## Output

The tool always returns a dictionary with this structure:

```python
{
    "items": [],
    "comparison": {
        "agreements": [],
        "unique_claims": [],
        "potential_conflicts": [],
        "missing_metadata": [],
    },
    "warnings": [],
    "error": None,
    "message": "",
}
```

- `items`: Valid source items after minimal normalization, with `original_index`.
- `comparison.agreements`: Similar sentences found in two sources.
- `comparison.unique_claims`: Substantial sentences without a similar sentence in another source.
- `comparison.potential_conflicts`: Heuristic conflict signals.
- `comparison.missing_metadata`: Missing `title`, `url`, or `source` for otherwise valid source items.
- `warnings`: Non-fatal validation or heuristic warnings.
- `error`: `None` when processing can continue, otherwise a string.
- `message`: Short result summary.

## Validation and errors

- If `items` is not a list, the tool returns the full output contract with an error.
- If `items` is empty, the tool returns the full output contract with an error.
- If an item is not a dictionary, it is skipped and a warning with its index is added.
- If a source is missing `summary`, has a non-string `summary`, or has an empty `summary`, it is skipped and a warning with its index is added.
- If only one valid source remains, the source is returned and a warning says at least two sources are required for comparison.
- If `criterion` is not one of `coverage`, `agreement`, or `conflicts`, the tool returns the full output contract with an error.
- If `max_items` is not an integer from 2 to 10, or is a boolean, the tool returns the full output contract with an error.
- If more than `max_items` valid sources are provided, extra valid sources are skipped in input order and a warning is added.

## Comparison heuristics

- Sentence splitting uses `.`, `!`, `?`, `;`, and newline boundaries.
- Tokenization lowercases text for internal comparison and extracts Unicode word and number tokens with regular expressions.
- Jaccard similarity compares token overlap between sentences.
- Agreements are substantial sentence pairs from different sources whose similarity reaches the agreement threshold and that do not show an obvious conflict signal.
- Unique claims are substantial sentences that do not have a similar sentence in another source.
- Numeric differences are flagged when similar sentences contain different numbers.
- Directional differences are flagged when similar sentences contain basic increase and decrease signals.
- Negation differences are flagged when similar sentences differ by basic negation signals.

## Limitations

This tool compares only the text supplied in the input.

It does not verify factual correctness.

It does not determine which source is trustworthy.

Potential conflicts are heuristic signals for manual review, not factual conclusions.

## Example input

```python
items = [
    {
        "title": "University Report A",
        "url": "https://example.com/a",
        "source": "Source A",
        "summary": (
            "AI adoption increased by 20 percent in universities. "
            "Most institutions focused on administrative automation."
        ),
    },
    {
        "title": "University Report B",
        "url": "https://example.com/b",
        "source": "Source B",
        "summary": (
            "AI adoption increased by 35 percent in universities. "
            "Most institutions focused on administrative automation."
        ),
    },
]
```

## Example output

```python
{
    "items": [
        {
            "title": "University Report A",
            "url": "https://example.com/a",
            "source": "Source A",
            "summary": "AI adoption increased by 20 percent in universities. Most institutions focused on administrative automation.",
            "original_index": 0,
        },
        {
            "title": "University Report B",
            "url": "https://example.com/b",
            "source": "Source B",
            "summary": "AI adoption increased by 35 percent in universities. Most institutions focused on administrative automation.",
            "original_index": 1,
        },
    ],
    "comparison": {
        "agreements": [
            {
                "text": "Most institutions focused on administrative automation.",
                "source_indices": [0, 1],
                "source_titles": ["University Report A", "University Report B"],
                "similarity": 1.0,
            }
        ],
        "unique_claims": [],
        "potential_conflicts": [
            {
                "type": "numeric_difference",
                "source_indices": [0, 1],
                "texts": [
                    "AI adoption increased by 20 percent in universities.",
                    "AI adoption increased by 35 percent in universities.",
                ],
                "details": {
                    "similarity": 0.7778,
                    "numbers": [["20"], ["35"]],
                },
            }
        ],
        "missing_metadata": [],
    },
    "warnings": ["Potential conflicts are heuristic signals for manual review."],
    "error": None,
    "message": "Compared 2 source items using the coverage criterion.",
}
```
