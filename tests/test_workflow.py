import pytest
from src.services.langgraph_workflow import travel_graph

def test_langgraph_full_execution():
    query = "5 days in Goa with friends, nightlife and beaches for ₹40,000"
    state = {
        "user_query": query,
        "sanitized_query": "",
        "guardrail_status": {},
        "preferences": {},
        "retrieved_documents": [],
        "destinations": {},
        "budget_analysis": {},
        "activities": {},
        "accommodations": {},
        "itinerary": {},
        "validation": {},
        "refinement_count": 0,
        "refinement_feedback": "",
        "agent_traces": [],
        "errors": []
    }
    
    result = travel_graph.invoke(state)
    
    assert len(result["errors"]) == 0
    assert result["preferences"]["duration_days"] == 5
    assert len(result["destinations"]["recommended_destinations"]) > 0
    assert result["budget_analysis"]["estimated_total"] > 0
    assert len(result["activities"]["recommended_activities"]) > 0
    assert len(result["itinerary"]["daily_itinerary"]) == 5
    assert result["validation"]["quality_score"] > 0.70
    assert len(result["agent_traces"]) >= 7
