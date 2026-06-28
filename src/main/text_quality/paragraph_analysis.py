"""Paragraph-level readability, syntactic complexity, and cohesion analysis."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from .models import AnalyzeRequest
from .readability_metrics import calculate_gulpease, calculate_lexical_diversity, readability_label
from .syntax_metrics import calculate_syntax_metrics_for_doc
from .text_utils import count_letters, get_word_tokens, is_content_token, normalize_lemma, trim_text

# Paragraph analysis uses a separate spaCy pass per paragraph so local sentence
# boundaries, entities, and syntax are calculated in paragraph context.
def analyze_paragraphs(
    paragraphs: List[str],
    request: AnalyzeRequest,
    nlp_model: Any,
) -> List[Dict[str, Any]]:
    """Analyze each paragraph independently for local readability and complexity.
    
    A separate spaCy document is created for every paragraph so sentence boundaries,
    entities, content lemmas, Gulpease, lexical diversity, SCIX, and cohesion signals
    are calculated in paragraph context.
    """
    results = []

    # The previous signature is used for a simple paragraph-to-paragraph cohesion
    # estimate. The first paragraph has no previous paragraph to compare against.
    previous_signature: Optional[Set[str]] = None

    for number, paragraph_text in enumerate(paragraphs, start=1):
        paragraph_doc = nlp_model(paragraph_text)
        word_tokens = get_word_tokens(paragraph_doc)
        sentences = list(paragraph_doc.sents)

        word_count = len(word_tokens)
        unique_word_count = len(set(token.text.lower() for token in word_tokens))
        sentence_count = len(sentences)
        letter_count = count_letters(paragraph_text)

        gulpease = calculate_gulpease(
            word_count=word_count,
            sentence_count=sentence_count,
            letter_count=letter_count,
        )

        lexical_diversity = calculate_lexical_diversity(word_tokens)
        syntax_metrics = calculate_syntax_metrics_for_doc(paragraph_doc)

        # A paragraph signature combines named entities and content lemmas. This
        # gives the cohesion heuristic both character/place continuity and topic
        # vocabulary continuity.
        entities = sorted(set(ent.text.strip() for ent in paragraph_doc.ents))
        content_lemmas = sorted(
            set(
                normalize_lemma(token)
                for token in paragraph_doc
                if is_content_token(token)
            )
        )

        signature = set(entities) | set(content_lemmas)

        cohesion = calculate_cohesion_with_previous(
            current_signature=signature,
            previous_signature=previous_signature,
        )

        label = readability_label(gulpease)
        warnings = []

        # Short fragments can produce unstable readability scores, so they are
        # reported with a reliability warning instead of being overinterpreted.
        if word_count < request.short_paragraph_word_limit:
            warnings.append(
                "This paragraph is short, so readability analysis may be less reliable."
            )

        if gulpease is not None and gulpease < request.low_gulpease_limit:
            warnings.append(
                f"Paragraph readability is low: Gulpease {gulpease}."
            )

        if (
            syntax_metrics["syntactic_complexity_index"] is not None
            and syntax_metrics["syntactic_complexity_index"] >= request.paragraph_scix_warning_limit
        ):
            warnings.append(
                f"High paragraph Syntactic Complexity Index: SCIX {syntax_metrics['syntactic_complexity_index']}."
            )

        # Cohesion is only checked after paragraph 1. The threshold is intentionally
        # low because this is a weak lexical-overlap heuristic, not full discourse analysis.
        if (
            cohesion is not None
            and cohesion["overlap_score"] < 0.08
            and word_count >= request.short_paragraph_word_limit
        ):
            warnings.append(
                "Low overlap with previous paragraph: possible abrupt topic shift."
            )

        results.append({
            "number": number,
            "text": paragraph_text,
            "preview": trim_text(paragraph_text, 160),
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "sentence_count": sentence_count,
            "letter_count": letter_count,
            "gulpease": gulpease,
            "lexical_diversity": lexical_diversity,
            "syntactic_complexity_index": syntax_metrics["syntactic_complexity_index"],
            "syntax_metrics": syntax_metrics,
            "readability_label": label,
            "entities": entities,
            "content_lemmas": content_lemmas[:30],
            "cohesion_with_previous": cohesion,
            "warnings": warnings,
        })

        previous_signature = signature

    return results


def calculate_cohesion_with_previous(
    current_signature: Set[str],
    previous_signature: Optional[Set[str]],
) -> Optional[Dict[str, Any]]:
    """Estimate lexical/entity overlap between the current and previous paragraph.
    
    This simple Jaccard-style overlap is only a heuristic. A low value may indicate
    an abrupt topic shift, but it is not a full discourse-coherence judgment.
    """
    if previous_signature is None:
        return None

    if not current_signature or not previous_signature:
        return {
            "shared_items": [],
            "overlap_score": 0.0,
        }

    # Jaccard-style overlap: shared topic/entity items divided by all unique
    # topic/entity items across the two neighboring paragraphs.
    shared_items = sorted(current_signature.intersection(previous_signature))
    union_size = len(current_signature.union(previous_signature))

    overlap_score = round(len(shared_items) / union_size, 3) if union_size else 0.0

    return {
        "shared_items": shared_items[:20],
        "overlap_score": overlap_score,
    }
