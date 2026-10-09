import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.rag.ingestion import run_ingestion_pipeline

if __name__ == "__main__":
    csv_file = "./data/raw/google_review_ratings.csv"
    if not os.path.exists(csv_file):
        csv_file = "./data/raw/tripadvisor_review.csv"
    
    print(f"[*] Ingesting UCI Dataset 485 from {csv_file}...")
    result = run_ingestion_pipeline(csv_file)
    print(f"[OK] Ingestion complete! Summary: {result}")
