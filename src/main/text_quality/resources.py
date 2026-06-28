"""Runtime resource loading for spaCy and the Italian Base Vocabulary CSV."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

import spacy

from .config import BASE_VOCABULARY_PATH, SPACY_MODEL_NAME
from .text_utils import normalize_lookup_key

# Resource loading is isolated here so the API layer and metric modules do not
# need to know how spaCy or the Base Vocabulary CSV are initialized.
def load_spacy_model():
    """Load the configured Italian spaCy model and prepare it for long documents.
    
    The function raises a clear runtime error when the model is missing so setup
    problems are easier to diagnose during local development or ngrok deployment.
    """
    try:
        # Loading happens once at import time so each request can reuse the same
        # NLP pipeline instead of paying model startup cost repeatedly.
        nlp_model = spacy.load(SPACY_MODEL_NAME)

        # Google Docs manuscripts can be long; the default spaCy max_length may be
        # too small for full-document analysis.
        nlp_model.max_length = 2_000_000
        return nlp_model
    except OSError as exc:
        raise RuntimeError(
            f"Could not load spaCy model '{SPACY_MODEL_NAME}'. "
            f"Install it with: python -m spacy download {SPACY_MODEL_NAME}"
        ) from exc


def normalize_category(value: str) -> str:
    """Normalize a Base Vocabulary category value from the CSV file.
    
    Empty or missing categories are converted to BASE, and non-empty categories are
    uppercased so category counts remain consistent across different CSV formats.
    """
    category = str(value or "BASE").strip().upper()
    return category if category else "BASE"


def load_base_vocabulary(path: Path) -> Dict[str, str]:
    """
    Load Base Vocabulary lemmas from CSV.

    Supported formats:
    1. lemma,category
    2. lemma

    Example:
    lemma,category
    andare,FO
    persona,FO
    ragazza,AU
    """
    # A missing CSV is not fatal. The analysis payload will mark Base Vocabulary
    # as unavailable while all other metrics continue to work.
    if not path.exists():
        return {}

    vocabulary: Dict[str, str] = {}

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(2048)
        file.seek(0)

        # Support both a formal CSV with a header and a quick one-lemma-per-line file.
        has_header = "lemma" in sample.splitlines()[0].lower()

        if has_header:
            reader = csv.DictReader(file)
            for row in reader:
                lemma = normalize_lookup_key(row.get("lemma", ""))
                category = normalize_category(row.get("category", "BASE"))
                if lemma:
                    vocabulary[lemma] = category
        else:
            reader = csv.reader(file)
            for row in reader:
                if not row:
                    continue

                lemma = normalize_lookup_key(row[0])
                category = normalize_category(row[1] if len(row) > 1 else "BASE")

                if lemma:
                    vocabulary[lemma] = category

    return vocabulary


# Load runtime resources once at application import time.
# In a larger production system this could move to FastAPI lifespan events.
nlp = load_spacy_model()
BASE_VOCABULARY = load_base_vocabulary(BASE_VOCABULARY_PATH)
