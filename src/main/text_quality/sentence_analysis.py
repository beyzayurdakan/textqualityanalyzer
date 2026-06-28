"""Sentence-level metric extraction and warning generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .models import AnalyzeRequest
from .readability_metrics import calculate_gulpease, calculate_lexical_diversity
from .syntax_metrics import (
    analyze_subordination_profile,
    calculate_syntactic_complexity_metrics,
    find_subordinate_markers,
)
from .text_utils import count_letters, get_word_tokens

# Sentence analysis produces local warnings shown in the Google Docs sidebar.
# It intentionally returns plain dictionaries to preserve the existing frontend contract.
def analyze_sentences(doc, request: AnalyzeRequest) -> List[Dict[str, Any]]:
    """Analyze every sentence and generate local warning data for the sidebar.
    
    Each sentence receives length, letter count, Gulpease, lexical diversity, comma
    count, subordination profile, SCIX, warnings, and linguistic signals. The output
    uses dictionaries to stay compatible with the current Apps Script frontend.
    """
    results = []

    # Sentence numbers are one-based because they are shown to non-technical users
    # in the Google Docs sidebar.
    for index, sent in enumerate(doc.sents, start=1):
        word_tokens = get_word_tokens(sent)
        word_count = len(word_tokens)
        unique_word_count = len(set(token.text.lower() for token in word_tokens))
        letter_count = count_letters(sent.text)
        comma_count = sent.text.count(",")

        gulpease = calculate_gulpease(
            word_count=word_count,
            sentence_count=1,
            letter_count=letter_count,
        )

        lexical_diversity = calculate_lexical_diversity(word_tokens)

        # Subordination is analyzed before SCIX because the sentence-level SCIX
        # formula needs the number of detected dependent clause structures.
        subordination_profile = analyze_subordination_profile(sent)

        dependent_clause_count = subordination_profile["clause_structure_count"]
        total_clauses = 1 + dependent_clause_count

        syntax_metrics = calculate_syntactic_complexity_metrics(
            word_count=word_count,
            sentence_count=1,
            total_clauses=total_clauses,
            dependent_clause_count=dependent_clause_count,
        )

        # Warnings are user-facing; linguistic_signals are explanatory details that
        # can be displayed even when no hard warning threshold is crossed.
        warnings, linguistic_signals = build_sentence_warnings_and_signals(
            word_count=word_count,
            gulpease=gulpease,
            comma_count=comma_count,
            syntactic_complexity_index=syntax_metrics["syntactic_complexity_index"],
            request=request,
        )

        results.append({
            "number": index,
            "text": sent.text.strip(),
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "letter_count": letter_count,
            "gulpease": gulpease,
            "lexical_diversity": lexical_diversity,
            "syntactic_complexity_index": syntax_metrics["syntactic_complexity_index"],
            "syntax_metrics": syntax_metrics,
            "comma_count": comma_count,
            "subordinate_markers": find_subordinate_markers(sent),
            "subordination_profile": subordination_profile,
            "clause_structure_count": subordination_profile["clause_structure_count"],
            "weighted_clause_score": subordination_profile["weighted_clause_score"],
            "clause_nesting_depth": subordination_profile["clause_nesting_depth"],
            "warnings": warnings,
            "linguistic_signals": linguistic_signals,
        })

    return results


def build_sentence_warnings_and_signals(
    word_count: int,
    gulpease: Optional[float],
    comma_count: int,
    syntactic_complexity_index: Optional[float],
    request: AnalyzeRequest,
) -> Tuple[List[str], List[str]]:
    """Create warning messages and explanatory signals for one sentence.
    
    Warnings are threshold-based and user-configurable through AnalyzeRequest. The
    separate signals list records informative metrics, such as SCIX, even when they
    do not necessarily cross a warning threshold.
    """
    warnings = []
    signals = []

    # Long sentences are one of the simplest and most actionable readability signals.
    if word_count > request.long_sentence_word_limit:
        warnings.append(
            f"Long sentence: {word_count} words."
        )

    if gulpease is not None and gulpease < request.low_gulpease_limit:
        warnings.append(
            f"Low sentence readability: Gulpease {gulpease}."
        )

    # Commas are only flagged when the sentence is also medium/long, because short
    # enumerations can contain commas without being difficult.
    if comma_count >= request.many_commas_limit and word_count > 20:
        warnings.append(
            f"Many commas in a long or medium-length sentence: {comma_count} commas."
        )

    if (
        syntactic_complexity_index is not None
        and syntactic_complexity_index >= request.sentence_scix_warning_limit
    ):
        warnings.append(
            f"High Syntactic Complexity Index: SCIX {syntactic_complexity_index}."
        )

    if syntactic_complexity_index is not None:
        signals.append(
            f"Syntactic Complexity Index calculated as {syntactic_complexity_index}."
        )

    return warnings, signals
