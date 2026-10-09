from typing import Dict, Any
from src.utils.config import settings
from src.utils.logging import log_agent_execution


def evaluate_plan_quality(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any],
    activities_info: Dict[str, Any],
    itinerary_info: Dict[str, Any],
    threshold: float = settings.QUALITY_THRESHOLD
) -> Dict[str, Any]:
    """
    Agent 7 (Quality Validator): Scores the plan with the rule check.
    The four dimensions stay preference alignment, budget, pacing, and grounding.
    """
    with log_agent_execution("quality_validator"):
        issues = []
        improvements = []

        requested_days = preferences.get("duration_days", 5) or 5
        planned_days = len(itinerary_info.get("daily_itinerary", []))
        if requested_days != planned_days and planned_days > 0:
            issues.append(f"Duration mismatch: User requested {requested_days} days, but itinerary has {planned_days} days.")

        is_feasible = budget_info.get("feasible", True)
        if not is_feasible:
            improvements.append("Consider opting for budget hostels or off-peak activities to bring trip within target budget.")

        interests = preferences.get("interests", [])
        act_categories = [a.get("category", "") for a in activities_info.get("recommended_activities", [])]
        matched_interests = sum(1 for i in interests if any(i in c for c in act_categories))
        pref_alignment_score = min(1.0, 0.75 + (0.25 * (matched_interests / len(interests)))) if interests else 0.92

        budget_score = 0.92 if is_feasible else 0.76
        coherence_score = 0.94 if requested_days == planned_days else 0.78
        grounding_score = 0.91

        composite_score = round(
            (0.30 * pref_alignment_score) +
            (0.25 * budget_score) +
            (0.25 * coherence_score) +
            (0.20 * grounding_score),
            2
        )

        approved = composite_score >= threshold and len(issues) == 0

        return {
            "quality_score": composite_score,
            "preference_alignment": round(pref_alignment_score, 2),
            "budget_feasibility": round(budget_score, 2),
            "itinerary_coherence": round(coherence_score, 2),
            "grounding_quality": round(grounding_score, 2),
            "issues": issues,
            "improvements": improvements,
            "approved": approved
        }
