import os
import hashlib
import numpy as np
from typing import List, Union
from src.utils.logging import get_logger
from src.utils.config import settings

logger = get_logger("embeddings")

class EmbeddingService:
    """
    Modular embedding generator supporting SentenceTransformers with local fallback.
    """
    def __init__(self, model_name: str = settings.EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self.dimension = 384
        self._initialize_model()

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            self.dimension = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Dimension: {self.dimension}")
        except Exception as e:
            logger.warning(f"SentenceTransformer initialization notice: {e}. Using deterministic hashing vectorizer fallback.")
            self._model = None
            self.dimension = 384

    def _hash_vectorize(self, text: str) -> List[float]:
        """Deterministic TF-IDF/Hash projection fallback (384-d unit normalized vector)."""
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec.tolist()
            
        for word in words:
            # Deterministic hash to bucket
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 + np.log(1 + len(word)))

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.warning(f"Error during batch sentence encoding: {e}. Falling back to deterministic hashing vectorizer.")
        return [self._hash_vectorize(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self.dimension
        if self._model is not None:
            try:
                embedding = self._model.encode(text, normalize_embeddings=True)
                return embedding.tolist()
            except Exception as e:
                logger.warning(f"Error during query sentence encoding: {e}. Falling back to deterministic hashing vectorizer.")
        return self._hash_vectorize(text)


embedding_service = EmbeddingService()
