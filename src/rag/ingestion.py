import os
import json
from typing import Dict, Any, List
from src.rag.preprocessing import load_and_preprocess_dataset
from src.rag.chunking import create_document_chunks
from src.rag.vector_store import vector_store
from src.rag.keyword_search import bm25_search
from src.utils.logging import get_logger
from src.utils.config import settings

logger = get_logger("ingestion")

def run_ingestion_pipeline(raw_csv_path: str = settings.RAW_DATA_PATH) -> Dict[str, Any]:
    """
    Executes the full RAG data ingestion pipeline:
    1. Preprocesses raw UCI dataset records.
    2. Constructs document chunks with rich metadata.
    3. Saves processed JSON cache.
    4. Indexes into ChromaDB vector database.
    5. Builds the BM25 keyword search index.
    """
    logger.info(f"Starting ingestion pipeline from {raw_csv_path}...")
    
    # Preprocess
    records = load_and_preprocess_dataset(raw_csv_path)
    logger.info(f"Preprocessed {len(records)} travel review records.")
    
    # Save processed JSON
    os.makedirs(os.path.dirname(settings.PROCESSED_DATA_PATH), exist_ok=True)
    with open(settings.PROCESSED_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
        
    # Chunking
    document_chunks = create_document_chunks(records)
    logger.info(f"Constructed {len(document_chunks)} structured document chunks.")
    
    # Vector DB Indexing
    vector_store.add_documents(document_chunks)
    
    # Keyword BM25 Indexing
    bm25_search.fit(document_chunks)
    
    summary = {
        "status": "success",
        "records_count": len(records),
        "chunks_indexed": len(document_chunks),
        "vector_store_collection": vector_store.collection_name,
        "processed_file": settings.PROCESSED_DATA_PATH
    }
    logger.info(f"Ingestion completed successfully: {summary}")
    return summary
