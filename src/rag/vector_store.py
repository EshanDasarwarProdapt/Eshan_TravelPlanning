import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from src.rag.embeddings import embedding_service
from src.utils.logging import get_logger
from src.utils.config import settings

logger = get_logger("vector_store")

class ChromaVectorStore:
    """
    Manages local ChromaDB collection storage, indexing, and vector similarity search.
    """
    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIRECTORY, collection_name: str = settings.CHROMA_COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Connected to ChromaDB collection '{self.collection_name}' at '{self.persist_dir}'")

    def add_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Adds or updates chunks in the ChromaDB collection."""
        if not documents:
            return
            
        total = len(documents)
        logger.info(f"Indexing {total} documents into ChromaDB...")
        
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]
            ids = [d["id"] for d in batch]
            texts = [d["text"] for d in batch]
            metadatas = [d["metadata"] for d in batch]
            embeddings = embedding_service.embed_documents(texts)
            
            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        logger.info(f"Successfully indexed {total} documents.")

    def search(
        self,
        query: str,
        n_results: int = 10,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic similarity search with optional metadata filtering.
        """
        query_embedding = embedding_service.embed_query(query)
        
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)
        
        formatted = []
        if results and results.get("ids") and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                doc_id = results["ids"][0][i]
                text = results["documents"][0][i]
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else 0.0
                # Cosine similarity = 1 - cosine_distance
                similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                
                formatted.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": metadata,
                    "score": round(similarity, 4),
                    "search_type": "semantic"
                })
        return formatted

    def count(self) -> int:
        return self.collection.count()


vector_store = ChromaVectorStore()
