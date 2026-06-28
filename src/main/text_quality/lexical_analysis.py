"""Lexical and linguistic signal extraction beyond basic readability scores."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

import spacy

from .config import DISCOURSE_CONNECTIVES
from .text_utils import get_word_tokens, is_content_token, normalize_lemma

# Lexical analysis contains the non-readability linguistic signals used by the sidebar:
# lemma repetition, POS distribution, named entities, and discourse connective counts.
def analyze_lemma_repetitions(doc) -> List[Dict[str, Any]]:
    """Detect frequent repeated content lemmas in the document.
    
    The analysis groups inflected forms under the same lemma, which is more useful
    for Italian than counting only exact repeated word forms. Function words are
    excluded so the result focuses on meaningful lexical repetition.
    """
    # Count lemmas, not only surface forms, so "parlare", "parla", and
    # "parlato" can be interpreted as one repeated lexical item.
    lemma_counter: Counter[str] = Counter()
    surface_forms: Dict[str, Counter[str]] = defaultdict(Counter)

    for token in doc:
        if not is_content_token(token):
            continue

        lemma = normalize_lemma(token)

        if not lemma:
            continue

        lemma_counter[lemma] += 1
        surface_forms[lemma][token.text.lower()] += 1

    results = []

    # Repetitions below three occurrences are usually normal, especially in short
    # texts, so they are not shown as warning candidates.
    for lemma, count in lemma_counter.most_common():
        if count < 3:
            continue

        results.append({
            "lemma": lemma,
            "count": count,
            "forms": [
                {"form": form, "count": form_count}
                for form, form_count in surface_forms[lemma].most_common()
            ],
        })

        if len(results) >= 15:
            break

    return results


def analyze_pos_distribution(doc) -> Dict[str, Any]:
    """Calculate the distribution of spaCy part-of-speech tags in word tokens.
    
    The returned percentages help describe the grammatical makeup of the text and
    can support future style or genre comparisons.
    """
    word_tokens = get_word_tokens(doc)
    total = len(word_tokens)

    # spaCy POS tags are counted over alphabetic word tokens only, matching the
    # rest of the backend's word-counting convention.
    pos_counter = Counter(token.pos_ for token in word_tokens)

    distribution = []

    for pos, count in pos_counter.most_common():
        percentage = round((count / total) * 100, 2) if total else 0

        distribution.append({
            "pos": pos,
            "description": spacy.explain(pos) or pos,
            "count": count,
            "percentage": percentage,
        })

    return {
        "total_word_tokens": total,
        "distribution": distribution,
    }


def analyze_named_entities(doc) -> Dict[str, Any]:
    """Collect named entities predicted by spaCy and count repeated entity mentions.
    
    Entities are grouped by label so the sidebar can display people, places,
    organizations, and other entity categories in a compact way.
    """
    entity_counter: Counter[Tuple[str, str]] = Counter()

    # Entity recognition is model-predicted, so the output should be treated as
    # a signal for review rather than a guaranteed factual/entity annotation.
    for ent in doc.ents:
        entity_text = ent.text.strip()

        if not entity_text:
            continue

        entity_counter[(entity_text, ent.label_)] += 1

    entities = []

    for (text, label), count in entity_counter.most_common():
        entities.append({
            "text": text,
            "label": label,
            "description": spacy.explain(label) or label,
            "count": count,
        })

    grouped_by_label: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for entity in entities:
        grouped_by_label[entity["label"]].append(entity)

    return {
        "entities": entities[:50],
        "grouped_by_label": dict(grouped_by_label),
    }


def analyze_discourse_connectives(text: str) -> Dict[str, Any]:
    """Count a curated list of Italian discourse connectives in the raw text.
    
    This is a lightweight cohesion signal. It does not perform full discourse
    parsing, but it helps identify whether explicit transitions are present.
    """
    lower_text = text.lower()
    counts = []

    for connective in DISCOURSE_CONNECTIVES:
        # Word boundaries reduce false positives where a connective appears as
        # part of a longer word. Multi-word connectives are handled literally.
        pattern = r"\b" + re.escape(connective.lower()) + r"\b"
        matches = re.findall(pattern, lower_text)
        count = len(matches)

        if count > 0:
            counts.append({
                "connective": connective,
                "count": count,
            })

    total_count = sum(item["count"] for item in counts)

    return {
        "total_connectives": total_count,
        "connectives": sorted(counts, key=lambda item: item["count"], reverse=True),
        "interpretation": (
            "This is a simple count of discourse connectives. "
            "A very low count may suggest weak explicit transitions, "
            "but some genres intentionally use fewer connectives."
        ),
    }
