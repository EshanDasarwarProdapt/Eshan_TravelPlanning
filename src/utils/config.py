import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Travel Planning & Itinerary Assistant"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"]
    
    # LLM provider. AI Credits is an OpenAI-compatible chat API.
    LLM_API_KEY: str = Field(default="", env="LLM_API_KEY")
    LLM_BASE_URL: str = Field(default="https://aicredits.in/v1", env="LLM_BASE_URL")
    LLM_MODEL: str = Field(default="gpt-5-nano", env="LLM_MODEL")

    # Kept so an older Gemini-only setup still loads. The planner uses LLM_* above.
    GEMINI_API_KEY: str = Field(default="", env="GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    
    # Vector DB & Embeddings
    CHROMA_PERSIST_DIRECTORY: str = Field(default="./data/chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    CHROMA_COLLECTION_NAME: str = Field(default="travel_reviews_uci_485", env="CHROMA_COLLECTION_NAME")
    EMBEDDING_MODEL_NAME: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL_NAME")
    
    # Data Paths
    RAW_DATA_PATH: str = "./data/raw/travel_reviews_uci_485.csv"
    PROCESSED_DATA_PATH: str = "./data/processed/processed_travel_reviews.json"
    SAMPLE_DATA_PATH: str = "./data/sample_data/sample_trips.json"
    
    # Recommendation Scoring Weights
    WEIGHT_PREFERENCE_MATCH: float = 0.30
    WEIGHT_SEMANTIC_RELEVANCE: float = 0.25
    WEIGHT_RATING: float = 0.20
    WEIGHT_EVIDENCE_STRENGTH: float = 0.15
    WEIGHT_BUDGET_COMPATIBILITY: float = 0.10
    
    # Quality & LangGraph Loop Controls
    QUALITY_THRESHOLD: float = 0.80
    MAX_REFINEMENT_LOOPS: int = 2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
