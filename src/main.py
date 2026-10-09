import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routes import router
from src.utils.config import settings
from src.utils.logging import get_logger
from src.rag.vector_store import vector_store
from src.rag.keyword_search import bm25_search
from src.rag.chunking import create_document_chunks
from src.rag.preprocessing import load_and_preprocess_dataset

logger = get_logger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="""
    ## AI-Powered Travel Planning & Itinerary Assistant (Waypoint)
    A high-precision, grounded travel intelligence engine featuring:
    - **7 Primary Agents** orchestrated via **LangGraph**: Preference Classifier, Destination Analyzer, Budget Analyst, Activity Recommender, Accommodation Finder, Itinerary Planner, Quality Validator.
    - **Hybrid RAG**: Vector Search (ChromaDB) + Keyword Search (BM25) with Reciprocal Rank Fusion (RRF).
    - **Dataset Grounding**: UCI Dataset 485 (Travel Review Ratings).
    - **LLM-as-a-Judge**: Multi-dimensional quality validation with iterative refinement loop.
    """,
    openapi_url="/api/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    logger.info("Initializing Waypoint Travel Intelligence Service...")
    # Initialize in-memory BM25 index if documents not yet loaded into BM25
    if not bm25_search.documents:
        raw_csv = "./data/raw/google_review_ratings.csv"
        if not os.path.exists(raw_csv):
            raw_csv = "./data/raw/tripadvisor_review.csv"
        if os.path.exists(raw_csv):
            try:
                records = load_and_preprocess_dataset(raw_csv)
                chunks = create_document_chunks(records)
                bm25_search.fit(chunks)
                logger.info(f"BM25 Search Index initialized with {len(chunks)} records.")
            except Exception as e:
                logger.warning(f"Could not auto-fit BM25 on startup: {e}")


@app.get("/", summary="Root Endpoint")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
        "health": "/health",
        "api_v1": {
            "plan_trip": "POST /api/v1/plan-trip",
            "search": "POST /api/v1/search",
            "recommend": "POST /api/v1/recommend",
            "itinerary": "POST /api/v1/itinerary"
        }
    }


if __name__ == "__main__":
    uvicorn.run("src.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
