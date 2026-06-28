"""Base Vocabulary coverage analysis for Italian text.

This module compares spaCy token lemmas against an injected vocabulary dictionary
and reports coverage plus possible misspelling or non-base-vocabulary signals."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict

from .text_utils import normalize_lemma, normalize_lookup_key

# Base Vocabulary analysis is separated from resource loading. The vocabulary
# dictionary is injected so tests can pass a small fixture instead of a real CSV.
def analyze_base_vocabulary(
    doc,
    base_vocabulary: Dict[str, str],
    base_vocabulary_path: Path,
) -> Dict[str, Any]:
    """Measure how much of the analyzed text is covered by the Italian Base Vocabulary.
    
    The function checks normalized lemmas and surface forms, counts covered and
    outside tokens, groups vocabulary categories, and reports the most frequent
    outside lemmas as possible misspellings or non-base-vocabulary items.
    """
    # The backend should still run when the CSV is not present. Returning an
    # unavailable payload is safer than raising an error and breaking the sidebar.
    if not base_vocabulary:
        return {
            "available": False,
            "path": str(base_vocabulary_path),
            "coverage": None,
            "coverage_percentage": None,
            "checked_token_count": 0,
            "covered_token_count": 0,
            "outside_token_count": 0,
            "category_distribution": {},
            "possible_misspellings": [],
            "message": (
                "Base Vocabulary file was not found or is empty. "
                "Add text_quality/data/base_vocabulary.csv to enable this analysis."
            )
        }

    checked_token_count = 0
    covered_token_count = 0
    outside_token_count = 0

    # category_counter tracks FO/AU/AD/etc. coverage when the CSV provides categories.
    category_counter: Counter[str] = Counter()

    # outside_counter groups unknown items by lemma so inflected forms are not
    # treated as separate vocabulary problems.
    outside_counter: Counter[str] = Counter()
    outside_forms: Dict[str, Counter[str]] = defaultdict(Counter)
    outside_pos: Dict[str, Counter[str]] = defaultdict(Counter)

    for token in doc:
        if not should_check_base_vocabulary_token(token):
            continue

        checked_token_count += 1

        # Try the lemma first because Italian inflection can produce many surface
        # forms. Fall back to the exact normalized token text for vocabulary files
        # that contain surface forms instead of lemmas.
        text_key = normalize_lookup_key(token.text)
        lemma_key = normalize_lookup_key(normalize_lemma(token))

        category = base_vocabulary.get(lemma_key) or base_vocabulary.get(text_key)

        if category:
            covered_token_count += 1
            category_counter[category] += 1
        else:
            outside_token_count += 1
            outside_counter[lemma_key] += 1
            outside_forms[lemma_key][text_key] += 1
            outside_pos[lemma_key][token.pos_] += 1

    coverage = (
        covered_token_count / checked_token_count
        if checked_token_count > 0
        else None
    )

    possible_misspellings = []

    # Limit the list to the most frequent outside lemmas so the sidebar remains
    # readable on long documents. The raw coverage counts still include all tokens.
    for lemma, count in outside_counter.most_common(40):
        forms = [
            {"form": form, "count": form_count}
            for form, form_count in outside_forms[lemma].most_common()
        ]

        pos_values = [
            {"pos": pos, "count": pos_count}
            for pos, pos_count in outside_pos[lemma].most_common()
        ]

        possible_misspellings.append({
            "lemma": lemma,
            "count": count,
            "forms": forms,
            "pos": pos_values,
            "reason": (
                "This lemma was not found in the Base Vocabulary. "
                "It may be a misspelling, a proper technical/literary word, or simply outside the base vocabulary."
            )
        })

    return {
        "available": True,
        "path": str(base_vocabulary_path),
        "vocabulary_size": len(base_vocabulary),
        "coverage": round(coverage, 4) if coverage is not None else None,
        "coverage_percentage": round(coverage * 100, 2) if coverage is not None else None,
        "checked_token_count": checked_token_count,
        "covered_token_count": covered_token_count,
        "outside_token_count": outside_token_count,
        "category_distribution": dict(category_counter),
        "possible_misspellings": possible_misspellings,
        "message": (
            "Words outside the Base Vocabulary are possible misspellings or non-base vocabulary. "
            "They are not automatically errors."
        )
    }


def should_check_base_vocabulary_token(token) -> bool:
    """Decide whether a token should be included in Base Vocabulary coverage.
    
    The filter excludes punctuation, numbers, very short words, and proper nouns so
    coverage is not distorted by names, abbreviations, or non-lexical tokens.
    """
    # Punctuation, numbers, and mixed symbols do not belong in a vocabulary list.
    if not token.is_alpha:
        return False

    # Proper names are intentionally excluded because their absence from a Base
    # Vocabulary list is expected and should not look like a spelling issue.
    if token.pos_ == "PROPN":
        return False

    if len(token.text) < 3:
        return False

    return True
