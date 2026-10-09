from typing import List, Dict, Any, Optional
from src.rag.vector_store import vector_store
from src.rag.keyword_search import bm25_search
from src.utils.logging import get_logger

logger = get_logger("hybrid_retriever")

class HybridRetriever:
    """
    Combines Semantic Vector Search and BM25 Keyword Search using Reciprocal Rank Fusion (RRF)
    and Weighted Score Fusion with metadata filtering.
    """
    def __init__(self, semantic_weight: float = 0.6, keyword_weight: float = 0.4, rrf_k: int = 60):
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        n_results: int = 10,
        destination_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        travel_type_filter: Optional[str] = None,
        rating_min: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Query ChromaDB for semantic relevance.
        2. Query BM25 index for keyword relevance.
        3. Merge candidates using Reciprocal Rank Fusion (RRF) and weighted linear fusion.
        4. Apply metadata filtering.
        """
        where_filter = {}
        if destination_filter:
            where_filter["destination"] = destination_filter
        if category_filter:
            where_filter["category"] = category_filter
        if travel_type_filter:
            where_filter["travel_type"] = travel_type_filter

        # Fetch candidate pools
        pool_size = max(n_results * 2, 20)
        semantic_results = vector_store.search(query, n_results=pool_size, where_filter=where_filter if where_filter else None)
        keyword_results = bm25_search.search(query, n_results=pool_size, where_filter=where_filter if where_filter else None)

        # Build fused scores map
        doc_map = {}
        rrf_scores = {}
        
        # 1. Process Semantic Ranks
        for rank, item in enumerate(semantic_results):
            doc_id = item["id"]
            doc_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (self.semantic_weight / (self.rrf_k + rank + 1))

        # 2. Process Keyword Ranks
        for rank, item in enumerate(keyword_results):
            doc_id = item["id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = item
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (self.keyword_weight / (self.rrf_k + rank + 1))

        # 3. Assemble fused results
        fused = []
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

        for doc_id, doc in doc_map.items():
            meta = doc.get("metadata", {})
            
            # Post-filter rating if specified
            if rating_min is not None and float(meta.get("rating", 0)) < rating_min:
                continue

            normalized_rrf = rrf_scores[doc_id] / max_rrf if max_rrf > 0 else 0.0
            
            # Find individual semantic & keyword scores if present
            sem_score = next((x["score"] for x in semantic_results if x["id"] == doc_id), 0.0)
            kw_score = next((x["score"] for x in keyword_results if x["id"] == doc_id), 0.0)
            
            composite_score = round(
                (self.semantic_weight * sem_score) + (self.keyword_weight * kw_score) * 0.5 + (0.5 * normalized_rrf), 
                4
            )

            fused.append({
                "id": doc_id,
                "text": doc["text"],
                "metadata": meta,
                "score": composite_score,
                "semantic_score": round(sem_score, 4),
                "keyword_score": round(kw_score, 4),
                "rrf_score": round(normalized_rrf, 4),
                "retrieval_method": "hybrid_rrf_weighted"
            })

        # Sort by composite score
        fused.sort(key=lambda x: x["score"], reverse=True)
        return fused[:n_results]


hybrid_retriever = HybridRetriever()
