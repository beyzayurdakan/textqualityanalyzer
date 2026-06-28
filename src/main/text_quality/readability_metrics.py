"""Document-level readability and global metric calculations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .syntax_metrics import calculate_syntax_metrics_for_doc
from .text_utils import count_letters, get_word_tokens

# Readability and global document metrics are separated from API code so they
# can be unit-tested without running a FastAPI server.
def analyze_global_metrics(doc) -> Dict[str, Any]:
    """Calculate document-level metrics used by the rest of the analysis.
    
    The function returns counts, Gulpease, readability label, lexical diversity, and
    SCIX. Audience interpretation depends on these values, so they are computed near
    the beginning of the pipeline.
    """
    # The same token filter is used across all metric layers so global numbers
    # match sentence-level and paragraph-level calculations as closely as possible.
    word_tokens = get_word_tokens(doc)
    sentences = list(doc.sents)

    word_count = len(word_tokens)
    unique_word_count = len(set(token.text.lower() for token in word_tokens))
    sentence_count = len(sentences)
    letter_count = count_letters(doc.text)

    # Gulpease is the Italian-specific readability baseline used throughout the project.
    gulpease = calculate_gulpease(
        word_count=word_count,
        sentence_count=sentence_count,
        letter_count=letter_count,
    )

    lexical_diversity = calculate_lexical_diversity(word_tokens)
    syntax_metrics = calculate_syntax_metrics_for_doc(doc)

    return {
        "word_count": word_count,
        "unique_word_count": unique_word_count,
        "sentence_count": sentence_count,
        "letter_count": letter_count,
        "gulpease": gulpease,
        "readability_label": readability_label(gulpease),
        "lexical_diversity": lexical_diversity,
        "syntactic_complexity_index": syntax_metrics["syntactic_complexity_index"],
        "syntax_metrics": syntax_metrics,
    }


def calculate_gulpease(
    word_count: int,
    sentence_count: int,
    letter_count: int,
) -> Optional[float]:
    """Calculate the Italian Gulpease readability index.
    
    The formula uses words, sentences, and letters. A higher value means easier
    readability. None is returned when there are no words to avoid division by zero.
    """
    # Avoid division by zero for empty strings or documents with no alphabetic tokens.
    if word_count <= 0:
        return None

    # Gulpease formula: 89 + ((300 * sentences - 10 * letters) / words).
    return round(89 + ((300 * sentence_count - 10 * letter_count) / word_count), 1)


def readability_label(gulpease: Optional[float]) -> str:
    """Convert a Gulpease score into a broad readability label.
    
    The labels are intentionally simple because they are used in the sidebar as a
    quick interpretation, while the raw score remains available for detailed review.
    """
    if gulpease is None:
        return "Not enough text"

    if gulpease >= 80:
        return "Very easy readability"

    if gulpease >= 60:
        return "Medium readability"

    if gulpease >= 40:
        return "Difficult readability"

    return "Very difficult readability"


def calculate_lexical_diversity(word_tokens: List[Any]) -> Optional[float]:
    """Calculate a simple type-token ratio for word tokens.
    
    The score is the number of unique lowercased word forms divided by total word
    tokens. It is useful as a basic signal but should be interpreted with text length
    in mind.
    """
    if not word_tokens:
        return None

    # Lowercasing keeps "Casa" and "casa" from being counted as different types.
    unique_count = len(set(token.text.lower() for token in word_tokens))
    return round(unique_count / len(word_tokens), 3)
