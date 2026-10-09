import pytest
from src.rag.hybrid_retriever import hybrid_retriever
from src.rag.keyword_search import bm25_search
from src.rag.vector_store import vector_store
from src.rag.reranker import reranker

def test_vector_store_populated():
    count = vector_store.count()
    assert count > 0, "Vector store should have indexed records"

def test_semantic_search():
    results = vector_store.search("beaches nightlife water sports", n_results=5)
    assert len(results) > 0
    assert results[0]["score"] > 0.0
    assert "metadata" in results[0]

def test_hybrid_retrieval():
    results = hybrid_retriever.retrieve(
        query="beaches nightlife friends goa",
        n_results=5
    )
    assert len(results) > 0
    assert "score" in results[0]
    assert results[0]["retrieval_method"] == "hybrid_rrf_weighted"

def test_metadata_filtering():
    results = hybrid_retriever.retrieve(
        query="beaches",
        destination_filter="Goa",
        n_results=5
    )
    for doc in results:
        assert doc["metadata"].get("destination") == "Goa"

def test_reranker():
    candidates = [
        {
            "destination": "Goa",
            "rating": 4.8,
            "evidence_count": 5,
            "score": 0.85,
            "metadata": {
                "destination": "Goa",
                "category": "beaches",
                "category_name": "Beaches",
                "highlights": "Baga, Tito's lane, scuba diving",
                "estimated_daily_cost_inr": 4500,
                "travel_type": "friends"
            }
        },
        {
            "destination": "Kyoto",
            "rating": 4.9,
            "evidence_count": 2,
            "score": 0.60,
            "metadata": {
                "destination": "Kyoto",
                "category": "heritage",
                "category_name": "Heritage",
                "highlights": "Temples, torii gates",
                "estimated_daily_cost_inr": 12500,
                "travel_type": "solo"
            }
        }
    ]
    prefs = {
        "budget": 40000,
        "duration_days": 5,
        "traveler_type": "friends",
        "interests": ["beaches", "nightlife"]
    }
    reranked = reranker.rerank_destinations(candidates, prefs)
    assert len(reranked) == 2
    # Goa should rank higher due to preference and budget fit
    assert reranked[0]["destination"] == "Goa"
    assert "score_breakdown" in reranked[0]
