"""Pydantic request models used by FastAPI and the analysis pipeline."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .config import (
    DEFAULT_LONG_SENTENCE_WORD_LIMIT,
    DEFAULT_LOW_GULPEASE_LIMIT,
    DEFAULT_MANY_COMMAS_LIMIT,
    DEFAULT_PARAGRAPH_SCIX_WARNING_LIMIT,
    DEFAULT_SENTENCE_SCIX_WARNING_LIMIT,
    DEFAULT_SHORT_PARAGRAPH_WORD_LIMIT,
)

# Request schema shared by FastAPI and the analysis service.
# Keeping it separate avoids importing FastAPI inside metric modules.
class AnalyzeRequest(BaseModel):
    """Request body accepted by the /analyze endpoint.
    
    The model contains the Google Docs text, optional paragraph segmentation from
    Apps Script, selected target audiences, and editable warning thresholds used by
    the sentence and paragraph analysis modules.
    """
    text: str = Field(..., description="Full text to analyze.")

    paragraphs: Optional[List[str]] = Field(
        default=None,
        description="Optional paragraph list from Google Docs."
    )

    target_audiences: List[str] = Field(
        default_factory=lambda: ["general_public"],
        description="Selected target audience profiles."
    )

    long_sentence_word_limit: int = DEFAULT_LONG_SENTENCE_WORD_LIMIT
    low_gulpease_limit: int = DEFAULT_LOW_GULPEASE_LIMIT
    many_commas_limit: int = DEFAULT_MANY_COMMAS_LIMIT
    short_paragraph_word_limit: int = DEFAULT_SHORT_PARAGRAPH_WORD_LIMIT

    sentence_scix_warning_limit: float = DEFAULT_SENTENCE_SCIX_WARNING_LIMIT
    paragraph_scix_warning_limit: float = DEFAULT_PARAGRAPH_SCIX_WARNING_LIMIT
