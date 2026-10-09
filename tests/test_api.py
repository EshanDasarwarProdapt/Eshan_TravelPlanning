import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_records_indexed"] > 0

def test_api_plan_trip():
    payload = {
        "query": "I have 5 days and around ₹40,000 for a trip to Goa with friends."
    }
    response = client.post("/api/v1/plan-trip", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "itinerary" in data
    assert "budget_analysis" in data
    assert "agent_traces" in data
    assert len(data["agent_traces"]) >= 7

def test_api_search():
    payload = {
        "query": "scenic mountains adventure",
        "n_results": 3
    }
    response = client.post("/api/v1/search", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_matches"] > 0

def test_api_recommend():
    payload = {
        "query": "4 days mountain adventure in Manali"
    }
    response = client.post("/api/v1/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["destinations"]) > 0

def test_api_direct_itinerary():
    payload = {
        "destination": "Goa",
        "duration_days": 3,
        "traveler_type": "friends",
        "budget": 30000,
        "interests": ["beaches", "nightlife"]
    }
    response = client.post("/api/v1/itinerary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["daily_itinerary"]) == 3
