"""Central configuration constants for the Italian Text Quality Analyzer backend."""

from __future__ import annotations

from pathlib import Path

# spaCy model used for Italian tokenization, lemmatization, POS tagging,
# dependency parsing, sentence segmentation, and named entity recognition.
SPACY_MODEL_NAME = "it_core_news_sm"

# All file paths are derived from this package directory so the backend works
# regardless of the current terminal directory.
BASE_DIR = Path(__file__).resolve().parent
BASE_VOCABULARY_PATH = BASE_DIR / "data" / "base_vocabulary.csv"

# Default thresholds used by the API request model. The sidebar can override
# these values by sending explicit parameters in the /analyze request.
DEFAULT_LONG_SENTENCE_WORD_LIMIT = 30
DEFAULT_LOW_GULPEASE_LIMIT = 40
DEFAULT_MANY_COMMAS_LIMIT = 4
DEFAULT_SHORT_PARAGRAPH_WORD_LIMIT = 20

DEFAULT_SENTENCE_SCIX_WARNING_LIMIT = 90.0
DEFAULT_PARAGRAPH_SCIX_WARNING_LIMIT = 90.0

# Dependency labels used as clause-complexity signals. The weights are not
# universal linguistic truths; they are prototype weights for editorial warning.
CLAUSE_HEAD_DEP_WEIGHTS = {
    "advcl": 1.0,
    "acl": 1.0,
    "relcl": 1.0,
    "ccomp": 1.0,
    "csubj": 1.0,
    "xcomp": 0.5,
}

# spaCy uses "mark" for many subordination markers.
MARKER_DEP_LABELS = {"mark"}

# A compact list of Italian discourse connectives used for a simple transition
# count. This is not a full discourse parser.
DISCOURSE_CONNECTIVES = [
    "perché",
    "quindi",
    "tuttavia",
    "inoltre",
    "infatti",
    "perciò",
    "dunque",
    "sebbene",
    "anche se",
    "nonostante",
    "al contrario",
    "di conseguenza",
    "per questo motivo",
    "invece",
    "mentre",
    "prima",
    "dopo",
    "alla fine",
]

# Audience profiles are heuristic interpretation layers.
# They do not change the raw Gulpease, SCIX, or Base Vocabulary coverage values.
# They only define how strict the system should be for different reader groups.
#
# Important:
# - Gulpease thresholds are based on common readability interpretation bands for Italian.
# - SCIX thresholds are project-specific because SCIX is a prototype index in this system.
# - Base Vocabulary coverage thresholds are heuristic and should be calibrated with real texts later.
AUDIENCE_PROFILES = {
    "elementary_school_readers": {
        "label": "Elementary school readers",
        "min_gulpease": 80,
        "ideal_gulpease": 85,
        "max_scix": 45,
        "min_base_coverage": 0.94,
        "focus": "Use very clear sentences, high base-vocabulary coverage, and low syntactic complexity.",
    },
    "middle_school_readers": {
        "label": "Middle school readers",
        "min_gulpease": 60,
        "ideal_gulpease": 70,
        "max_scix": 70,
        "min_base_coverage": 0.88,
        "focus": "Keep sentences manageable and avoid unnecessary rare vocabulary.",
    },
    "high_school_readers": {
        "label": "High school readers",
        "min_gulpease": 40,
        "ideal_gulpease": 55,
        "max_scix": 100,
        "min_base_coverage": 0.78,
        "focus": "Moderate syntactic complexity is acceptable, but clarity should remain high.",
    },
    "general_public": {
        "label": "General public",
        "min_gulpease": 55,
        "ideal_gulpease": 65,
        "max_scix": 85,
        "min_base_coverage": 0.82,
        "focus": "Prioritize clarity, accessible vocabulary, and smooth paragraph transitions.",
    },
    "academic_readers": {
        "label": "Academic readers",
        "min_gulpease": 40,
        "ideal_gulpease": 50,
        "max_scix": 130,
        "min_base_coverage": 0.68,
        "focus": "Higher lexical and syntactic complexity can be acceptable if the argument remains clear.",
    },
    "technical_readers": {
        "label": "Technical readers",
        "min_gulpease": 35,
        "ideal_gulpease": 45,
        "max_scix": 150,
        "min_base_coverage": 0.60,
        "focus": "Technical vocabulary may be acceptable, but sentence structure should still support comprehension.",
    },
    "childrens_literature": {
        "label": "Children’s literature",
        "min_gulpease": 80,
        "ideal_gulpease": 88,
        "max_scix": 45,
        "min_base_coverage": 0.94,
        "focus": "Use simple structures and familiar vocabulary, while allowing expressive or imaginative words.",
    },
    "literary_fiction": {
        "label": "Literary fiction",
        "min_gulpease": 45,
        "ideal_gulpease": 55,
        "max_scix": 160,
        "min_base_coverage": 0.65,
        "focus": "Complexity and rare vocabulary may be stylistic choices; warnings should be interpreted as reading-effort signals.",
    },
}
