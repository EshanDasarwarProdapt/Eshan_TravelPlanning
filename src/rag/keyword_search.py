import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from src.utils.logging import get_logger

logger = get_logger("keyword_search")

def tokenize(text: str) -> List[str]:
    """Lowercase alpha-numeric tokenization for BM25."""
    return [w for w in re.findall(r"\b\w+\b", text.lower()) if len(w) > 1]


class BM25KeywordSearch:
    """
    In-memory BM25 Okapi indexer for exact keyword and lexical travel preference retrieval.
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Okapi] = None

    def fit(self, documents: List[Dict[str, Any]]):
        """Indexes document chunks into BM25 corpus."""
        self.documents = documents
        self.corpus_tokens = [tokenize(doc["text"]) for doc in documents]
        if self.corpus_tokens:
            self.bm25 = BM25Okapi(self.corpus_tokens)
            logger.info(f"BM25 index built with {len(self.documents)} documents.")

    def search(
        self,
        query: str,
        n_results: int = 10,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top-N documents using BM25 scoring with optional metadata filtering.
        """
        if not self.bm25 or not self.documents:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        doc_scores = self.bm25.get_scores(query_tokens)
        
        # Max score normalization
        max_score = max(doc_scores) if len(doc_scores) > 0 and max(doc_scores) > 0 else 1.0

        scored_docs = []
        for idx, score in enumerate(doc_scores):
            if score <= 0:
                continue
            doc = self.documents[idx]
            
            # Apply metadata filter if specified
            if where_filter:
                match = True
                for k, v in where_filter.items():
                    if doc["metadata"].get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            norm_score = min(1.0, score / max_score)
            scored_docs.append({
                "id": doc["id"],
                "text": doc["text"],
                "metadata": doc["metadata"],
                "score": round(float(norm_score), 4),
                "raw_bm25": round(float(score), 4),
                "search_type": "keyword_bm25"
            })

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:n_results]


bm25_search = BM25KeywordSearch()
