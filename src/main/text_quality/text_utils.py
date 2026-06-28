"""Shared text normalization and token-filtering helpers."""

from __future__ import annotations

import re
import unicodedata
from typing import Any, List, Optional

# Small, dependency-light helper functions used by several analysis modules.
# This keeps token filtering and text normalization consistent across metrics.
def normalize_lookup_key(value: str) -> str:
    """Normalize text for dictionary lookup and stable lemma comparison.
    
    The function lowercases, trims whitespace, normalizes apostrophes, and applies
    Unicode NFC normalization so CSV lemmas and spaCy tokens are compared reliably.
    """
    text = str(value or "").strip().lower()
    text = text.replace("’", "'")
    text = unicodedata.normalize("NFC", text)
    return text


def normalize_paragraphs(
    full_text: str,
    paragraphs: Optional[List[str]],
) -> List[str]:
    """Create a clean paragraph list from Apps Script paragraphs or raw full text.
    
    When Google Docs provides paragraph segmentation it is preferred. Otherwise the
    function falls back to blank-line splitting, then line splitting, then the full
    text as a single paragraph.
    """
    # Prefer paragraph boundaries provided by the Google Docs Apps Script because
    # they reflect the real document structure better than raw text splitting.
    if paragraphs is not None:
        cleaned = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
        if cleaned:
            return cleaned

    # Fallback 1: use blank lines, which usually indicate paragraph breaks in
    # copied plain text.
    by_blank_lines = [
        part.strip()
        for part in re.split(r"\n\s*\n", full_text.strip())
        if part.strip()
    ]

    if len(by_blank_lines) > 1:
        return by_blank_lines

    # Fallback 2: use individual non-empty lines when no blank-line paragraphs exist.
    by_lines = [
        line.strip()
        for line in full_text.splitlines()
        if line.strip()
    ]

    if by_lines:
        return by_lines

    return [full_text.strip()]


def get_word_tokens(span_or_doc) -> List[Any]:
    """Return alphabetic spaCy tokens that should count as words.
    
    This shared helper keeps word counts consistent across Gulpease, lexical
    diversity, global metrics, sentence metrics, and paragraph metrics.
    """
    return [
        token
        for token in span_or_doc
        if token.is_alpha
    ]


def count_letters(text: str) -> int:
    """Count alphabetic letters, including accented Latin characters.
    
    Gulpease uses letter count rather than character count, so punctuation, spaces,
    digits, and symbols are intentionally excluded.
    """
    matches = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ]", text)
    return len(matches)


def trim_text(text: str, max_length: int) -> str:
    """Normalize whitespace and shorten text for sidebar previews.
    
    The function keeps previews compact while preserving the original text in the
    detailed paragraph payload.
    """
    clean = re.sub(r"\s+", " ", text).strip()

    if len(clean) <= max_length:
        return clean

    return clean[: max_length - 3] + "..."


def plural(count: int, singular: str, plural_form: Optional[str] = None) -> str:
    """Return the correct singular or plural word for simple English messages.
    
    The helper keeps overview text readable without duplicating pluralization logic
    in the summary builder.
    """
    if count == 1:
        return singular

    if plural_form:
        return plural_form

    return singular + "s"


def normalize_lemma(token) -> str:
    """Return a safe lowercase lemma for a spaCy token.
    
    If spaCy does not provide a lemma, the surface token text is used as a fallback
    so downstream counting functions do not receive an empty key.
    """
    lemma = token.lemma_.lower().strip()

    if not lemma:
        lemma = token.text.lower().strip()

    return lemma


def is_content_token(token) -> bool:
    """Decide whether a token is meaningful enough for lexical repetition analysis.
    
    The filter removes punctuation, stop words, very short words, and non-content
    parts of speech so repetition results focus on nouns, verbs, adjectives, adverbs,
    and proper nouns.
    """
    if not token.is_alpha:
        return False

    if token.is_stop:
        return False

    if len(token.text) < 4:
        return False

    return token.pos_ in {"NOUN", "PROPN", "VERB", "ADJ", "ADV"}
