from typing import List, Dict, Any

def create_document_chunks(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Creates structured document chunks with standardized metadata for indexing.
    Each chunk encapsulates the destination context, user feedback, category score,
    travel style, and cost indicators.
    """
    documents = []
    
    for idx, rec in enumerate(records):
        doc_id = f"doc_{rec['user_id']}_{idx}"
        
        # Build dense content text optimized for semantic and keyword retrieval
        content = (
            f"Destination: {rec['destination']}, {rec['country']}\n"
            f"Category: {rec['category_name']} ({rec['category']})\n"
            f"Rating: {rec['rating']}/5.0\n"
            f"Traveler Type: {rec['travel_type']}\n"
            f"Highlights & Activities: {rec['highlights']}\n"
            f"Recommended Accommodation: {', '.join(rec['stay_types'])}\n"
            f"Estimated Daily Cost: INR {rec['estimated_daily_cost_inr']}\n"
            f"Review Summary: {rec['review_text']}"
        )
        
        metadata = {
            "doc_id": doc_id,
            "user_id": rec["user_id"],
            "destination": rec["destination"],
            "country": rec["country"],
            "category": rec["category"],
            "category_name": rec["category_name"],
            "rating": float(rec["rating"]),
            "travel_type": rec["travel_type"],
            "visit_date": rec["visit_date"],
            "estimated_daily_cost_inr": int(rec["estimated_daily_cost_inr"]),
            "best_season": rec["best_season"]
        }
        
        documents.append({
            "id": doc_id,
            "text": content,
            "metadata": metadata
        })
        
    return documents
