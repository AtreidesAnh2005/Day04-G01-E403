from __future__ import annotations

import re
from typing import Any


VALID_CRITERIA = {"coverage", "agreement", "conflicts"}
MIN_ITEMS = 2
MAX_ITEMS = 10
SOURCE_FIELDS = ("title", "url", "source", "summary", "section")
METADATA_FIELDS = ("title", "url", "source")
MIN_SENTENCE_TOKENS = 3

# Conservative enough to avoid unrelated short sentences, permissive enough for
# near-duplicate research summaries with small wording changes.
AGREEMENT_THRESHOLD = 0.45
CONFLICT_THRESHOLD = 0.35
NEGATION_CONFLICT_THRESHOLD = 0.4

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "across",
    "did",
    "was",
    "were",
}
INCREASE_TERMS = {
    "increase",
    "increased",
    "rising",
    "grew",
    "growth",
    "tăng",
    "tăng lên",
    "gia tăng",
}
DECREASE_TERMS = {
    "decrease",
    "decreased",
    "falling",
    "declined",
    "drop",
    "giảm",
    "giảm xuống",
    "suy giảm",
}
NEGATION_TERMS = {"not", "no", "never", "without", "không", "chưa", "chẳng"}


def _empty_result(message: str = "") -> dict[str, Any]:
    return {
        "items": [],
        "comparison": {
            "agreements": [],
            "unique_claims": [],
            "potential_conflicts": [],
            "missing_metadata": [],
        },
        "warnings": [],
        "error": None,
        "message": message,
    }


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_item(item: dict[str, Any], original_index: int) -> tuple[dict[str, Any] | None, list[str]]:
    summary = item.get("summary")
    if not isinstance(summary, str) or not _normalize_text(summary):
        return None, []

    normalized: dict[str, Any] = {}
    for field in SOURCE_FIELDS:
        value = item.get(field)
        if isinstance(value, str):
            text = _normalize_text(value)
            if text:
                normalized[field] = text

    normalized["original_index"] = original_index
    missing_fields = [field for field in METADATA_FIELDS if field not in normalized]
    return normalized, missing_fields


def _split_sentences(text: str) -> list[str]:
    sentences: list[str] = []
    for match in re.finditer(r"[^.!?;\n]+[.!?;]?", text):
        sentence = _normalize_text(match.group(0))
        if sentence:
            sentences.append(sentence)
    return sentences


def _token_variants(token: str) -> set[str]:
    variants = {token}
    if len(token) > 4 and token.endswith("ed"):
        base = token[:-2]
        variants.add(base)
        variants.add(base + "e")
    if len(token) > 5 and token.endswith("ing"):
        variants.add(token[:-3])
    if len(token) > 3 and token.endswith("s") and not token.isdigit():
        variants.add(token[:-1])
    return variants


def _tokenize(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw_token in re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE):
        if raw_token in STOPWORDS:
            continue
        if len(raw_token) < 2 and not raw_token.isdigit():
            continue
        tokens.update(_token_variants(raw_token))
    return tokens


def _jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _extract_numbers(text: str) -> list[str]:
    return re.findall(r"\d+(?:[.,]\d+)?", text)


def _contains_term(text: str, tokens: set[str], terms: set[str]) -> bool:
    lowered = text.lower()
    return any((" " in term and term in lowered) or term in tokens for term in terms)


def _sentence_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item_index, item in enumerate(items):
        for sentence_index, sentence in enumerate(_split_sentences(item["summary"])):
            tokens = _tokenize(sentence)
            records.append({
                "item_index": item_index,
                "sentence_index": sentence_index,
                "text": sentence,
                "tokens": tokens,
                "numbers": _extract_numbers(sentence),
                "has_increase": _contains_term(sentence, tokens, INCREASE_TERMS),
                "has_decrease": _contains_term(sentence, tokens, DECREASE_TERMS),
                "has_negation": _contains_term(sentence, tokens, NEGATION_TERMS),
            })
    return records


def _source_title(item: dict[str, Any], item_index: int) -> str:
    return str(item.get("title") or item.get("source") or f"Source {item_index + 1}")


def _is_substantial(record: dict[str, Any]) -> bool:
    return len(record["tokens"]) >= MIN_SENTENCE_TOKENS


def _conflict_type(left: dict[str, Any], right: dict[str, Any], similarity: float) -> str | None:
    if similarity < CONFLICT_THRESHOLD:
        return None
    if left["numbers"] and right["numbers"] and left["numbers"] != right["numbers"]:
        return "numeric_difference"
    if (left["has_increase"] and right["has_decrease"]) or (left["has_decrease"] and right["has_increase"]):
        return "directional_difference"
    if similarity >= NEGATION_CONFLICT_THRESHOLD and left["has_negation"] != right["has_negation"]:
        return "negation_difference"
    return None


def _build_potential_conflicts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for left_index, left in enumerate(records):
        if not _is_substantial(left):
            continue
        for right in records[left_index + 1:]:
            if left["item_index"] == right["item_index"] or not _is_substantial(right):
                continue
            similarity = _jaccard(left["tokens"], right["tokens"])
            conflict_type = _conflict_type(left, right, similarity)
            if conflict_type is None:
                continue

            key = (conflict_type, left["item_index"], right["item_index"], left["text"].lower(), right["text"].lower())
            if key in seen:
                continue
            seen.add(key)

            details: dict[str, Any] = {"similarity": round(similarity, 4)}
            if conflict_type == "numeric_difference":
                details["numbers"] = [left["numbers"], right["numbers"]]

            conflicts.append({
                "type": conflict_type,
                "source_indices": [left["item_index"], right["item_index"]],
                "texts": [left["text"], right["text"]],
                "details": details,
            })

    return conflicts


def _has_conflict_signal(left: dict[str, Any], right: dict[str, Any], similarity: float) -> bool:
    return _conflict_type(left, right, similarity) is not None


def _build_agreements(records: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    agreements: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    for left_index, left in enumerate(records):
        if not _is_substantial(left):
            continue
        for right in records[left_index + 1:]:
            if left["item_index"] == right["item_index"] or not _is_substantial(right):
                continue
            similarity = _jaccard(left["tokens"], right["tokens"])
            if similarity < AGREEMENT_THRESHOLD or _has_conflict_signal(left, right, similarity):
                continue

            source_indices = [left["item_index"], right["item_index"]]
            key = (left["text"].lower(), tuple(source_indices))
            if key in seen:
                continue
            seen.add(key)

            agreements.append({
                "text": left["text"],
                "source_indices": source_indices,
                "source_titles": [_source_title(items[index], index) for index in source_indices],
                "similarity": round(similarity, 4),
            })

    return agreements


def _build_unique_claims(records: list[dict[str, Any]], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_claims: list[dict[str, Any]] = []
    seen: set[tuple[int, str]] = set()

    for record in records:
        if not _is_substantial(record):
            continue
        has_match = False
        for other in records:
            if record is other or record["item_index"] == other["item_index"] or not _is_substantial(other):
                continue
            if _jaccard(record["tokens"], other["tokens"]) >= AGREEMENT_THRESHOLD:
                has_match = True
                break

        key = (record["item_index"], record["text"].lower())
        if not has_match and key not in seen:
            seen.add(key)
            item_index = record["item_index"]
            unique_claims.append({
                "text": record["text"],
                "source_index": item_index,
                "source_title": _source_title(items[item_index], item_index),
            })

    return unique_claims


def _populate_comparison(result: dict[str, Any], criterion: str) -> None:
    items = result["items"]
    if len(items) < MIN_ITEMS:
        return

    records = _sentence_records(items)
    if criterion in {"coverage", "agreement"}:
        result["comparison"]["agreements"] = _build_agreements(records, items)
    if criterion == "coverage":
        result["comparison"]["unique_claims"] = _build_unique_claims(records, items)
    if criterion in {"coverage", "conflicts"}:
        result["comparison"]["potential_conflicts"] = _build_potential_conflicts(records)
        if result["comparison"]["potential_conflicts"]:
            result["warnings"].append("Potential conflicts are heuristic signals for manual review.")


def compare_sources(
    items: list[dict[str, Any]],
    criterion: str = "coverage",
    max_items: int = 5,
) -> dict[str, Any]:
    """Compare already-collected source items with deterministic heuristics.

    The tool only analyzes text supplied in ``items``. It does not search,
    fetch URLs, call APIs or LLMs, verify facts, or decide which source is
    correct or trustworthy.

    Valid criterion values are "coverage", "agreement", and "conflicts".
    "coverage" returns agreements, unique claims, potential conflicts, and
    missing metadata. "agreement" returns only agreements and missing metadata.
    "conflicts" returns only potential conflicts and missing metadata.
    """
    result = _empty_result()

    if criterion not in VALID_CRITERIA:
        result["error"] = f"Invalid criterion: {criterion!r}. Expected one of: agreement, conflicts, coverage."
        result["message"] = "Invalid comparison criterion."
        return result

    if not isinstance(max_items, int) or isinstance(max_items, bool):
        result["error"] = "Invalid max_items: expected an integer between 2 and 10."
        result["message"] = "Invalid max_items."
        return result

    if max_items < MIN_ITEMS or max_items > MAX_ITEMS:
        result["error"] = "Invalid max_items: expected an integer between 2 and 10."
        result["message"] = "Invalid max_items."
        return result

    if not isinstance(items, list):
        result["error"] = "Invalid items: expected a list of source item dictionaries."
        result["message"] = "No valid source items were provided."
        return result

    if not items:
        result["error"] = "No source items were provided."
        result["message"] = "No valid source items were provided."
        return result

    skipped_for_limit = 0

    for original_index, item in enumerate(items):
        if not isinstance(item, dict):
            result["warnings"].append(f"Skipped item {original_index}: expected a dictionary.")
            continue

        normalized_item, missing_fields = _normalize_item(item, original_index)
        if normalized_item is None:
            result["warnings"].append(f"Skipped item {original_index}: missing or empty summary.")
            continue

        if len(result["items"]) >= max_items:
            skipped_for_limit += 1
            continue

        item_index = len(result["items"])
        result["items"].append(normalized_item)
        if missing_fields:
            result["comparison"]["missing_metadata"].append({
                "item_index": item_index,
                "original_index": original_index,
                "missing_fields": missing_fields,
            })

    valid_count = len(result["items"])
    if valid_count == 0:
        result["error"] = "No valid source items were provided."
        result["message"] = "No valid source items were provided."
    elif valid_count == 1:
        result["warnings"].append("Only one valid source was provided; at least two are required for comparison.")
        result["message"] = "Prepared 1 source for comparison."
    else:
        if skipped_for_limit:
            result["warnings"].append(
                f"Skipped {skipped_for_limit} additional valid source items because max_items={max_items}."
            )
            result["message"] = (
                f"Compared {valid_count} source items; {skipped_for_limit} additional valid items were skipped "
                f"because max_items={max_items}."
            )
        else:
            result["message"] = f"Compared {valid_count} source items using the {criterion} criterion."
        _populate_comparison(result, criterion)

    return result
