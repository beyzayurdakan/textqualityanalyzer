"""High-level orchestration for the complete text-quality analysis workflow.

The pipeline keeps the backend response compatible with the existing Google Docs
sidebar while delegating each metric family to a focused module."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .audience_analysis import analyze_target_audiences
from .base_vocabulary_analysis import analyze_base_vocabulary
from .lexical_analysis import (
    analyze_discourse_connectives,
    analyze_lemma_repetitions,
    analyze_named_entities,
    analyze_pos_distribution,
)
from .models import AnalyzeRequest
from .overview import build_analysis_overview
from .paragraph_analysis import analyze_paragraphs
from .readability_metrics import analyze_global_metrics
from .sentence_analysis import analyze_sentences
from .text_utils import normalize_paragraphs


def run_text_quality_analysis(
    request: AnalyzeRequest,
    nlp_model: Any,
    base_vocabulary: Dict[str, str],
    base_vocabulary_path: Path,
) -> Dict[str, Any]:
    """Run the complete analysis pipeline and preserve the original response shape."""
    # The API route already rejects empty text, but the stripped version is used here
    # so the NLP model does not process leading/trailing whitespace as document content.
    text = request.text.strip()

    # The spaCy document is the shared linguistic object used by global, sentence,
    # lexical, entity, and vocabulary modules.
    doc = nlp_model(text)

    # Google Docs can send exact paragraph segmentation. If it does not, the helper
    # reconstructs paragraphs from blank lines or line breaks.
    paragraphs = normalize_paragraphs(request.text, request.paragraphs)

    # Global metrics are calculated first because audience interpretation depends on them.
    global_metrics = analyze_global_metrics(doc)

    # Local analyses power the sidebar pagers and clickable document selections.
    sentence_results = analyze_sentences(doc, request)
    paragraph_results = analyze_paragraphs(
        paragraphs=paragraphs,
        request=request,
        nlp_model=nlp_model,
    )

    # Lexical and linguistic signals add explanations beyond a single readability score.
    lemma_repetitions = analyze_lemma_repetitions(doc)
    pos_distribution = analyze_pos_distribution(doc)
    named_entities = analyze_named_entities(doc)
    discourse = analyze_discourse_connectives(text)

    # Base Vocabulary is optional. If the CSV is missing, the payload reports that clearly.
    base_vocabulary_result = analyze_base_vocabulary(
        doc=doc,
        base_vocabulary=base_vocabulary,
        base_vocabulary_path=base_vocabulary_path,
    )

    target_audience_analysis = analyze_target_audiences(
        requested_profiles=request.target_audiences,
        global_metrics=global_metrics,
        base_vocabulary=base_vocabulary_result,
    )

    analysis_overview = build_analysis_overview(
        global_metrics=global_metrics,
        sentence_results=sentence_results,
        lemma_repetitions=lemma_repetitions,
        paragraph_results=paragraph_results,
        discourse=discourse,
        base_vocabulary=base_vocabulary_result,
        target_audience_analysis=target_audience_analysis,
        request=request,
    )

    # The response keys below intentionally match the original one-file backend.
    # Sidebar.html reads these names directly, so changing them would break the
    # Google Docs add-on even if the internal Python structure is cleaner.
    return {
        "global_metrics": global_metrics,
        "target_audience_analysis": target_audience_analysis,
        "base_vocabulary": base_vocabulary_result,
        "sentence_analysis": sentence_results,
        "lemma_repetitions": lemma_repetitions,
        "pos_distribution": pos_distribution,
        "named_entities": named_entities,
        "discourse_connectives": discourse,
        "paragraph_analysis": paragraph_results,
        "analysis_overview": analysis_overview,

        # Compatibility field for older sidebar versions.
        "suggestions": analysis_overview,

        "notes": {
            "purpose": (
                "This backend adds a spaCy-based linguistic layer to the "
                "Google Docs MVP. It supports the author/editor and does not "
                "replace human judgment."
            ),
            "base_vocabulary": (
                "Base Vocabulary analysis uses spaCy lemmas. Words outside the Base Vocabulary "
                "are shown as possible misspellings or non-base vocabulary, not as certain errors."
            ),
            "syntactic_complexity_index": (
                "The prototype SCIX formula used here is: "
                "SCIX = MLS * C/S * (1 + SR), where MLS is mean length of sentence, "
                "C/S is clauses per sentence, and SR is dependent clauses per clause."
            ),
            "target_audience": (
                "Target audience profiles do not change the raw Gulpease or SCIX scores. "
                "They change how the same scores are interpreted."
            ),
            "limitations": [
                "Base Vocabulary absence is not proof of a spelling error.",
                "Named entities are model predictions and may contain mistakes.",
                "SCIX is a prototype index, not an official universal Italian threshold.",
                "Cohesion analysis is a simple overlap-based heuristic, not full discourse parsing.",
                "The model is trained mostly on written/news-like text, so literary or technical texts may need tuning.",
            ],
        },
    }
