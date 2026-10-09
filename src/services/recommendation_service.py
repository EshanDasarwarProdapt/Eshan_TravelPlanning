from typing import Dict, Any, List, Optional
from src.rag.hybrid_retriever import hybrid_retriever
from src.rag.reranker import reranker
from src.agents.preference_classifier import classify_preferences

class RecommendationService:
    """
    High-level orchestration service for hybrid travel recommendation queries.
    """
    def search_travel_experiences(
        self,
        query: str,
        n_results: int = 10,
        destination: Optional[str] = None,
        category: Optional[str] = None,
        travel_type: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        return hybrid_retriever.retrieve(
            query=query,
            n_results=n_results,
            destination_filter=destination,
            category_filter=category,
            travel_type_filter=travel_type,
            rating_min=min_rating
        )

    def get_ranked_recommendations(self, query: str) -> Dict[str, Any]:
        preferences = classify_preferences(query)
        retrieved = self.search_travel_experiences(query, n_results=15)
        return {
            "preferences": preferences,
            "results": retrieved,
            "total_matches": len(retrieved)
        }


recommendation_service = RecommendationService()
