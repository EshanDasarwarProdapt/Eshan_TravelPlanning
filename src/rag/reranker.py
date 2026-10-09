from typing import List, Dict, Any, Optional
from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger("reranker")

class TravelRecommendationReranker:
    """
    Reranks candidate destinations and experiences using transparent multi-factor scoring:
    Score = w1*Preference_Match + w2*Semantic_Relevance + w3*Rating + w4*Evidence_Strength + w5*Budget_Compatibility
    """
    def __init__(
        self,
        w_pref: float = settings.WEIGHT_PREFERENCE_MATCH,
        w_sem: float = settings.WEIGHT_SEMANTIC_RELEVANCE,
        w_rat: float = settings.WEIGHT_RATING,
        w_evid: float = settings.WEIGHT_EVIDENCE_STRENGTH,
        w_bud: float = settings.WEIGHT_BUDGET_COMPATIBILITY
    ):
        self.w_pref = w_pref
        self.w_sem = w_sem
        self.w_rat = w_rat
        self.w_evid = w_evid
        self.w_bud = w_bud

    def rerank_destinations(
        self,
        destination_candidates: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Reranks and enriches destination candidates with detailed score components.
        """
        reranked = []
        user_budget = user_preferences.get("budget")
        duration = user_preferences.get("duration_days", 5) or 5
        interests = [i.lower() for i in user_preferences.get("interests", [])]
        traveler_type = str(user_preferences.get("traveler_type", "")).lower()

        for cand in destination_candidates:
            dest_name = cand.get("destination", "")
            meta = cand.get("metadata", {})
            semantic_score = float(cand.get("score", cand.get("semantic_score", 0.7)))
            
            # 1. Preference Match Score (0.0 to 1.0)
            pref_hits = 0
            dest_tags = [meta.get("category", "").lower(), meta.get("category_name", "").lower(), meta.get("highlights", "").lower()]
            for interest in interests:
                if any(interest in tag for tag in dest_tags):
                    pref_hits += 1
            pref_match_score = min(1.0, (pref_hits / len(interests))) if interests else 0.8
            if traveler_type and traveler_type in str(meta.get("travel_type", "")).lower():
                pref_match_score = min(1.0, pref_match_score + 0.15)

            # 2. Rating Score (Normalized 0.0 to 1.0 from 5.0 scale)
            raw_rating = float(meta.get("rating", cand.get("rating", 4.2)))
            rating_score = min(1.0, max(0.0, raw_rating / 5.0))

            # 3. Evidence Strength Score (Number of matching records and review density)
            evidence_count = int(cand.get("evidence_count", 1))
            evidence_score = min(1.0, 0.4 + (evidence_count * 0.15))

            # 4. Budget Compatibility Score
            daily_cost = float(meta.get("estimated_daily_cost_inr", cand.get("estimated_daily_cost_inr", 5000)))
            total_est_cost = daily_cost * duration
            if user_budget and user_budget > 0:
                cost_ratio = total_est_cost / user_budget
                if cost_ratio <= 1.0:
                    budget_score = 1.0 - (0.2 * cost_ratio) # In budget: 0.8 to 1.0
                else:
                    budget_score = max(0.2, 1.0 - (cost_ratio - 1.0)) # Over budget penalty
            else:
                budget_score = 0.85 # Neutral if budget not specified

            # Compute weighted composite score
            composite = (
                (self.w_pref * pref_match_score) +
                (self.w_sem * semantic_score) +
                (self.w_rat * rating_score) +
                (self.w_evid * evidence_score) +
                (self.w_bud * budget_score)
            )

            cand_copy = dict(cand)
            cand_copy["final_match_score"] = round(composite * 100, 1) # Percentage format (e.g. 92.4%)
            cand_copy["score_breakdown"] = {
                "preference_match": round(pref_match_score, 2),
                "semantic_relevance": round(semantic_score, 2),
                "historical_rating": round(rating_score, 2),
                "evidence_strength": round(evidence_score, 2),
                "budget_compatibility": round(budget_score, 2)
            }
            cand_copy["estimated_total_cost"] = int(total_est_cost)
            reranked.append(cand_copy)

        reranked.sort(key=lambda x: x["final_match_score"], reverse=True)
        return reranked


reranker = TravelRecommendationReranker()
