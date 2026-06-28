"""Syntactic complexity helpers based on spaCy dependency analysis."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List

import spacy

from .config import CLAUSE_HEAD_DEP_WEIGHTS, MARKER_DEP_LABELS
from .text_utils import get_word_tokens

# Syntactic complexity is kept in one module because the sentence, paragraph,
# and global metrics all depend on the same SCIX formula and clause heuristics.
def calculate_syntax_metrics_for_doc(doc) -> Dict[str, Any]:
    """Calculate aggregate syntactic-complexity metrics for a spaCy document.
    
    The function counts words, sentences, and dependency-based dependent-clause
    structures, then passes those totals into the shared SCIX formula helper.
    """
    word_count = len(get_word_tokens(doc))
    sentences = list(doc.sents)

    dependent_clause_count = 0

    # Clause structures are counted sentence by sentence because spaCy dependency
    # labels are easiest to interpret inside a sentence boundary.
    for sent in sentences:
        profile = analyze_subordination_profile(sent)
        dependent_clause_count += profile["clause_structure_count"]

    sentence_count = len(sentences)
    total_clauses = sentence_count + dependent_clause_count

    return calculate_syntactic_complexity_metrics(
        word_count=word_count,
        sentence_count=sentence_count,
        total_clauses=total_clauses,
        dependent_clause_count=dependent_clause_count,
    )


def calculate_syntactic_complexity_metrics(
    word_count: int,
    sentence_count: int,
    total_clauses: int,
    dependent_clause_count: int,
) -> Dict[str, Any]:
    """Calculate SCIX and its component metrics from already-counted syntax totals.
    
    The formula is SCIX = MLS * C/S * (1 + SR), where MLS is mean sentence length,
    C/S is clauses per sentence, and SR is dependent clauses per clause.
    """
    # Empty inputs or parser edge cases should return a complete metric object
    # with None values instead of raising a division-by-zero error.
    if word_count <= 0 or sentence_count <= 0:
        return {
            "mean_length_sentence": None,
            "clauses_per_sentence": None,
            "subordination_ratio": None,
            "syntactic_complexity_index": None,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "total_clauses": total_clauses,
            "dependent_clause_count": dependent_clause_count,
            "formula": "SCIX = MLS * C/S * (1 + SR)",
        }

    # At minimum, each sentence is treated as one clause. This prevents malformed
    # parser output from producing fewer clauses than sentences.
    safe_total_clauses = max(total_clauses, sentence_count)

    mean_length_sentence = word_count / sentence_count
    clauses_per_sentence = safe_total_clauses / sentence_count
    subordination_ratio = (
        dependent_clause_count / safe_total_clauses
        if safe_total_clauses > 0
        else 0
    )

    # Prototype formula used consistently for document, paragraph, and sentence levels.
    scix = mean_length_sentence * clauses_per_sentence * (1 + subordination_ratio)

    return {
        "mean_length_sentence": round(mean_length_sentence, 3),
        "clauses_per_sentence": round(clauses_per_sentence, 3),
        "subordination_ratio": round(subordination_ratio, 3),
        "syntactic_complexity_index": round(scix, 3),
        "word_count": word_count,
        "sentence_count": sentence_count,
        "total_clauses": safe_total_clauses,
        "dependent_clause_count": dependent_clause_count,
        "formula": "SCIX = MLS * C/S * (1 + SR)",
    }


def find_subordinate_markers(sent) -> List[Dict[str, Any]]:
    """Return token-level subordination markers and clause structures for a sentence.
    
    The output is intended for explanation, not correction. It lists spaCy tokens
    whose dependency labels or POS tags suggest subordination or dependent clauses.
    """
    markers = []

    for token in sent:
        # "mark" and SCONJ tokens usually point to explicit subordination markers;
        # selected dependency labels point to the heads of dependent clauses.
        is_marker = token.dep_ in MARKER_DEP_LABELS or token.pos_ == "SCONJ"
        is_clause_structure = token.dep_ in CLAUSE_HEAD_DEP_WEIGHTS

        if not is_marker and not is_clause_structure:
            continue

        if is_clause_structure:
            role = "clause_structure"
            weight = CLAUSE_HEAD_DEP_WEIGHTS[token.dep_]
        else:
            role = "subordination_marker"
            weight = 0.0

        markers.append({
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "dep": token.dep_,
            "dep_description": spacy.explain(token.dep_) or token.dep_,
            "role": role,
            "weight": weight,
        })

    return markers


def analyze_subordination_profile(sent) -> Dict[str, Any]:
    """Summarize subordination and clause-structure signals for one sentence.
    
    The profile counts dependency labels, marker words, weighted clause structures,
    and estimated nesting depth so the backend can explain why a sentence may be
    syntactically complex.
    """
    # Clause tokens represent dependency heads that suggest subordinate or embedded
    # clausal structure. They are the main input for SCIX dependent-clause counts.
    clause_tokens = [
        token
        for token in sent
        if token.dep_ in CLAUSE_HEAD_DEP_WEIGHTS
    ]

    # Marker tokens are separate from clause heads. They are useful for explanation
    # even when they are not counted as full clause structures.
    marker_tokens = [
        token
        for token in sent
        if token.dep_ in MARKER_DEP_LABELS or token.pos_ == "SCONJ"
    ]

    clause_dep_counter = Counter(token.dep_ for token in clause_tokens)
    marker_counter = Counter(token.text.lower() for token in marker_tokens)

    weighted_clause_score = round(
        sum(CLAUSE_HEAD_DEP_WEIGHTS[token.dep_] for token in clause_tokens),
        2
    )

    clause_nesting_depth = estimate_clause_nesting_depth(sent, clause_tokens)

    clause_structures = [
        {
            "text": token.text,
            "lemma": token.lemma_,
            "dep": token.dep_,
            "dep_description": spacy.explain(token.dep_) or token.dep_,
            "weight": CLAUSE_HEAD_DEP_WEIGHTS[token.dep_],
        }
        for token in clause_tokens
    ]

    markers = [
        {
            "text": token.text,
            "lemma": token.lemma_,
            "dep": token.dep_,
            "pos": token.pos_,
            "dep_description": spacy.explain(token.dep_) or token.dep_,
        }
        for token in marker_tokens
    ]

    return {
        "marker_count": len(marker_tokens),
        "marker_counts": dict(marker_counter),
        "clause_structure_count": len(clause_tokens),
        "clause_structure_counts": dict(clause_dep_counter),
        "weighted_clause_score": weighted_clause_score,
        "clause_nesting_depth": clause_nesting_depth,
        "clause_structures": clause_structures,
        "markers": markers,
        "interpretation": interpret_subordination_profile(
            clause_count=len(clause_tokens),
            weighted_clause_score=weighted_clause_score,
            clause_nesting_depth=clause_nesting_depth,
        ),
    }


def estimate_clause_nesting_depth(sent, clause_tokens) -> int:
    """Estimate how deeply detected clause structures are nested in one sentence.
    
    The function walks from each clause token toward the dependency root and counts
    other clause tokens on that path. This is a heuristic, not a formal syntactic
    tree-depth theorem.
    """
    if not clause_tokens:
        return 0

    sent_token_ids = {token.i for token in sent}
    clause_token_ids = {token.i for token in clause_tokens}

    max_depth = 1

    for token in clause_tokens:
        # Start at depth 1 for the clause itself, then walk toward the dependency
        # root and count other clause tokens encountered on the path.
        depth = 1
        current = token.head
        visited = set()

        while current.i in sent_token_ids and current.i not in visited:
            visited.add(current.i)

            if current.i in clause_token_ids:
                depth += 1

            if current == current.head:
                break

            current = current.head

        max_depth = max(max_depth, depth)

    return max_depth


def interpret_subordination_profile(
    clause_count: int,
    weighted_clause_score: float,
    clause_nesting_depth: int,
) -> str:
    """Convert clause counts and nesting depth into an explanatory sentence.
    
    The interpretation avoids calling subordination an error; it frames detected
    structures as possible reading-effort signals that depend on context and genre.
    """
    if clause_count == 0:
        return "No major clausal structures were detected."

    if weighted_clause_score < 2 and clause_nesting_depth <= 1:
        return (
            "Some clausal structure was detected, but this is a normal "
            "grammatical feature and is not necessarily difficult."
        )

    if weighted_clause_score < 3 and clause_nesting_depth <= 1:
        return (
            "Multiple clausal structures were detected. This may increase "
            "complexity if combined with long sentence length or dense phrasing."
        )

    if clause_nesting_depth >= 2:
        return (
            "Nested clausal structures were detected. This can increase "
            "syntactic complexity, especially in long sentences."
        )

    return (
        "Several clausal structures were detected. This is a syntactic "
        "complexity signal, not an automatic grammar error."
    )
