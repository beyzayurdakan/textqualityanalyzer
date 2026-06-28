"""FastAPI entry point for the Italian Text Quality Analyzer backend.

This file intentionally contains only web-server concerns: route definitions,
CORS configuration, input validation, and the call into the analysis pipeline."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from text_quality.analysis_pipeline import run_text_quality_analysis
from text_quality.config import BASE_VOCABULARY_PATH, SPACY_MODEL_NAME
from text_quality.models import AnalyzeRequest
from text_quality.resources import BASE_VOCABULARY, nlp

# The FastAPI application is intentionally kept in this small file.
# This makes deployment simple: uvicorn main:app --reload
app = FastAPI(
    title="Italian Text Quality Analyzer - spaCy Backend",
    description=(
        "A prototype NLP backend for the Google Docs Text Quality Analyzer. "
        "It adds spaCy-based linguistic analysis, target-audience interpretation, "
        "Base Vocabulary coverage, possible misspelling signals, named entities, "
        "paragraph analysis, and a prototype Syntactic Complexity Index."
    ),
    version="0.5.0",
)

# The Google Docs Apps Script calls this backend from a browser-like environment.
# CORS is open for the prototype/ngrok workflow; restrict this in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, str]:
    """Return a minimal status message for a browser health check."""
    return {
        "message": "Italian Text Quality Analyzer spaCy backend is running.",
        "docs": "Open /docs to test the API interactively.",
    }


@app.get("/health")
def health() -> Dict[str, Any]:
    """Expose runtime information used to check deployment readiness."""
    return {
        "status": "ok",
        "spacy_model": SPACY_MODEL_NAME,
        "pipeline": nlp.pipe_names,
        "base_vocabulary_loaded": bool(BASE_VOCABULARY),
        "base_vocabulary_size": len(BASE_VOCABULARY),
        "base_vocabulary_path": str(BASE_VOCABULARY_PATH),
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> Dict[str, Any]:
    """Analyze the full Google Docs text and return the sidebar-compatible payload."""
    text = request.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text is empty.")

    return run_text_quality_analysis(
        request=request,
        nlp_model=nlp,
        base_vocabulary=BASE_VOCABULARY,
        base_vocabulary_path=BASE_VOCABULARY_PATH,
    )
