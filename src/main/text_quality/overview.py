"""Human-readable summary generation for the Google Docs sidebar."""

from __future__ import annotations

from typing import Any, Dict, List

from .models import AnalyzeRequest
from .text_utils import plural

# The overview turns detailed metric dictionaries into short human-readable
# findings consumed by the existing sidebar and legacy "suggestions" field.
def build_analysis_overview(
    global_metrics: Dict[str, Any],
    sentence_results: List[Dict[str, Any]],
    lemma_repetitions: List[Dict[str, Any]],
    paragraph_results: List[Dict[str, Any]],
    discourse: Dict[str, Any],
    base_vocabulary: Dict[str, Any],
    target_audience_analysis: List[Dict[str, Any]],
    request: AnalyzeRequest,
) -> List[str]:
    """Build concise human-readable findings from the detailed analysis payload.
    
    The sidebar displays these strings as an overview pager. The function keeps
    summary wording centralized so individual metric modules can stay focused on
    calculation instead of user-facing report text.
    """
    overview = []

    # Each block below adds one short, user-facing summary sentence. The detailed
    # evidence remains available in the corresponding metric sections.
    warning_sentences = [
        sentence
        for sentence in sentence_results
        if sentence["warnings"]
    ]

    if warning_sentences:
        overview.append(
            f"{len(warning_sentences)} {plural(len(warning_sentences), 'sentence')} have readability or complexity warnings."
        )

    paragraph_warnings = [
        paragraph
        for paragraph in paragraph_results
        if paragraph["warnings"]
    ]

    if paragraph_warnings:
        overview.append(
            f"{len(paragraph_warnings)} {plural(len(paragraph_warnings), 'paragraph')} have paragraph-level warnings."
        )

    high_scix_sentences = [
        sentence
        for sentence in sentence_results
        if (
            sentence.get("syntactic_complexity_index") is not None
            and sentence.get("syntactic_complexity_index") >= request.sentence_scix_warning_limit
        )
    ]

    if high_scix_sentences:
        overview.append(
            f"{len(high_scix_sentences)} {plural(len(high_scix_sentences), 'sentence')} have a high Syntactic Complexity Index."
        )

    if lemma_repetitions:
        top = lemma_repetitions[0]
        overview.append(
            f"The lemma '{top['lemma']}' is repeated {top['count']} {plural(top['count'], 'time')}."
        )

    # Base Vocabulary is optional. When available, it is one of the clearest
    # document-level signals, so its coverage is always summarized.
    if base_vocabulary.get("available"):
        overview.append(
            f"Base Vocabulary coverage is {base_vocabulary.get('coverage_percentage')}%."
        )

        possible_count = len(base_vocabulary.get("possible_misspellings", []))

        if possible_count > 0:
            overview.append(
                f"{possible_count} possible misspelling or non-base vocabulary item {plural(possible_count, 'was', 'were')} detected."
            )
    else:
        overview.append(
            "Base Vocabulary analysis is unavailable because the vocabulary file was not found."
        )

    difficult_audiences = [
        item
        for item in target_audience_analysis
        if item["overall_fit"] == "difficult for this audience"
    ]

    if difficult_audiences:
        overview.append(
            f"The text may be difficult for {len(difficult_audiences)} selected target {plural(len(difficult_audiences), 'audience')}."
        )

    if discourse["total_connectives"] == 0 and global_metrics["word_count"] > 150:
        overview.append(
            "No discourse connectives were detected. Paragraph transitions may need review."
        )

    # Always return at least one item so the sidebar overview pager never renders
    # an empty state for a successful analysis.
    if not overview:
        overview.append(
            "No major warnings were detected by the current spaCy-based analysis."
        )

    return overview
