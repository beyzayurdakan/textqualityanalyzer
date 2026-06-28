"""Audience-profile interpretation logic for raw readability and complexity metrics.

The functions in this module do not recalculate raw metrics. They translate
Gulpease, SCIX, and Base Vocabulary coverage into audience-specific statuses."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .config import AUDIENCE_PROFILES

# Audience profiles interpret metrics according to reader expectations.
# They do not modify the raw metric values.
def analyze_target_audiences(
    requested_profiles: List[str],
    global_metrics: Dict[str, Any],
    base_vocabulary: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Evaluate the text against each requested target-audience profile.
    
    Raw scores are read from global metrics and Base Vocabulary analysis. The output
    adds audience-specific suitability labels, interpretations, thresholds, and
    recommended editorial focus without changing the underlying metric values.
    """
    # Normalize the frontend selection before reading profile thresholds. This
    # prevents an invalid checkbox value from causing a KeyError.
    selected = normalize_requested_audiences(requested_profiles)

    results = []

    for key in selected:
        profile = AUDIENCE_PROFILES[key]

        # These are raw scores calculated elsewhere. Audience analysis only
        # interprets them through the selected profile's threshold values.
        gulpease = global_metrics.get("gulpease")
        scix = global_metrics.get("syntactic_complexity_index")
        coverage = base_vocabulary.get("coverage") if base_vocabulary.get("available") else None

        # Gulpease is easier when higher, so it uses a minimum threshold.
        gulpease_status = evaluate_minimum_metric(
            value=gulpease,
            minimum=profile["min_gulpease"],
            higher_is_better=True,
        )

        # SCIX is harder when higher, so it uses a maximum threshold.
        scix_status = evaluate_maximum_metric(
            value=scix,
            maximum=profile["max_scix"],
        )

        # Base Vocabulary coverage is better when higher, so it also uses a
        # minimum threshold. If the CSV is missing, coverage remains unavailable.
        vocabulary_status = evaluate_minimum_metric(
            value=coverage,
            minimum=profile["min_base_coverage"],
            higher_is_better=True,
        )

        overall_fit = combine_audience_statuses(
            gulpease_status=gulpease_status,
            scix_status=scix_status,
            vocabulary_status=vocabulary_status,
        )

        # Keep all thresholds in the payload so the frontend/report can explain
        # not only the status, but also the rule used to produce it.
        results.append({
            "key": key,
            "label": profile["label"],
            "overall_fit": overall_fit,
            "minimum_gulpease": profile["min_gulpease"],
            "ideal_gulpease": profile["ideal_gulpease"],
            "maximum_scix": profile["max_scix"],
            "minimum_base_vocabulary_coverage": profile["min_base_coverage"],
            "gulpease": gulpease,
            "gulpease_status": gulpease_status,
            "gulpease_interpretation": interpret_gulpease_for_audience(
                gulpease=gulpease,
                profile=profile,
            ),
            "syntactic_complexity_index": scix,
            "scix_status": scix_status,
            "scix_interpretation": interpret_scix_for_audience(
                scix=scix,
                profile=profile,
            ),
            "base_vocabulary_coverage": coverage,
            "base_vocabulary_coverage_percentage": (
                round(coverage * 100, 2)
                if coverage is not None
                else None
            ),
            "base_vocabulary_status": vocabulary_status,
            "base_vocabulary_interpretation": interpret_base_vocabulary_for_audience(
                coverage=coverage,
                profile=profile,
            ),
            "recommended_focus": profile["focus"],
        })

    return results


def normalize_requested_audiences(requested_profiles: List[str]) -> List[str]:
    """Return a clean list of valid, unique audience profile keys.
    
    Invalid or duplicated profile names are ignored to protect the backend from
    frontend mistakes. If no valid profile remains, the general-public profile is
    used as a safe default.
    """
    if not requested_profiles:
        return ["general_public"]

    valid = []

    # Preserve the user's order while removing invalid and duplicate profile keys.
    for item in requested_profiles:
        key = str(item).strip()

        if key in AUDIENCE_PROFILES and key not in valid:
            valid.append(key)

    return valid if valid else ["general_public"]


def evaluate_minimum_metric(
    value: Optional[float],
    minimum: float,
    higher_is_better: bool,
) -> str:
    """Classify a metric where higher values are better against a minimum threshold.
    
    This is used for Gulpease and Base Vocabulary coverage. Values close to the
    minimum are marked borderline instead of immediately difficult, which makes the
    feedback less brittle for small score variations.
    """
    if value is None:
        return "unavailable"

    if higher_is_better:
        if value >= minimum:
            return "suitable"

        if value >= minimum * 0.85:
            return "borderline"

        return "difficult"

    return "unavailable"


def evaluate_maximum_metric(
    value: Optional[float],
    maximum: float,
) -> str:
    """Classify a metric where lower values are better against a maximum threshold.
    
    This is used for SCIX, where a value below the profile maximum is suitable and
    a moderately higher value is treated as borderline rather than a hard failure.
    """
    if value is None:
        return "unavailable"

    if value <= maximum:
        return "suitable"

    if value <= maximum * 1.25:
        return "borderline"

    return "difficult"


def combine_audience_statuses(
    gulpease_status: str,
    scix_status: str,
    vocabulary_status: str,
) -> str:
    """Combine individual audience checks into one overall fit label.
    
    The most severe available status wins: difficult outranks borderline, and
    borderline outranks suitable. Unavailable metrics are ignored so a missing Base
    Vocabulary file does not erase the readability and syntax interpretation.
    """
    statuses = [gulpease_status, scix_status, vocabulary_status]

    # Missing metrics should not dominate the result. For example, Base Vocabulary
    # may be unavailable because the CSV has not been added yet.
    available_statuses = [status for status in statuses if status != "unavailable"]

    if not available_statuses:
        return "not enough data"

    if "difficult" in available_statuses:
        return "difficult for this audience"

    if "borderline" in available_statuses:
        return "partially suitable"

    return "suitable"


def interpret_gulpease_for_audience(
    gulpease: Optional[float],
    profile: Dict[str, Any],
) -> str:
    """Create a plain-English explanation of the Gulpease score for one audience.
    
    The interpretation compares the score with the profile minimum and ideal values
    so the sidebar can explain whether the text is ideal, acceptable, or below the
    recommended level.
    """
    if gulpease is None:
        return "Gulpease could not be calculated."

    if gulpease >= profile["ideal_gulpease"]:
        return "The Gulpease score is in the ideal range for this audience."

    if gulpease >= profile["min_gulpease"]:
        return "The Gulpease score is acceptable for this audience."

    return "The Gulpease score is below the recommended level for this audience."


def interpret_scix_for_audience(
    scix: Optional[float],
    profile: Dict[str, Any],
) -> str:
    """Create a plain-English explanation of SCIX for one audience.
    
    SCIX is treated as a reading-effort signal. A high value does not mean the text
    is grammatically wrong; it means syntax may be demanding for that audience.
    """
    if scix is None:
        return "SCIX could not be calculated."

    if scix <= profile["max_scix"]:
        return "The Syntactic Complexity Index is within the expected range for this audience."

    return "The Syntactic Complexity Index may be high for this audience."


def interpret_base_vocabulary_for_audience(
    coverage: Optional[float],
    profile: Dict[str, Any],
) -> str:
    """Create a plain-English explanation of Base Vocabulary coverage for one audience.
    
    The function distinguishes unavailable coverage from low coverage, because a
    missing CSV file should not be interpreted as a weakness in the analyzed text.
    """
    if coverage is None:
        return "Base Vocabulary coverage is unavailable."

    if coverage >= profile["min_base_coverage"]:
        return "Base Vocabulary coverage is suitable for this audience."

    return "Base Vocabulary coverage may be low for this audience."
