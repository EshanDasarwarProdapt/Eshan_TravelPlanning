import pytest
from src.agents.preference_classifier import classify_preferences
from src.agents.destination_analyzer import analyze_destinations
from src.agents.budget_analyst import calculate_budget_feasibility
from src.agents.activity_recommender import recommend_activities
from src.agents.accommodation_finder import find_accommodations
from src.agents.itinerary_planner import plan_itinerary
from src.agents.quality_validator import evaluate_plan_quality

def test_agent_1_preference_classifier():
    query = "I have 5 days and around ₹40,000. I'm travelling with friends and want beaches, good food, nightlife and some adventure."
    prefs = classify_preferences(query)
    assert prefs["duration_days"] == 5
    assert prefs["budget"] == 40000.0
    assert prefs["traveler_type"] == "friends"
    assert any("beach" in i for i in prefs["interests"])

def test_agent_2_destination_analyzer():
    prefs = {
        "duration_days": 5,
        "budget": 40000,
        "traveler_type": "friends",
        "interests": ["beaches", "nightlife"],
        "destination": None
    }
    res = analyze_destinations("5 days beaches nightlife friends", prefs)
    assert "recommended_destinations" in res
    assert len(res["recommended_destinations"]) > 0
    assert "primary_recommendation" in res

def test_agent_3_budget_analyst():
    prefs = {"duration_days": 5, "budget": 40000, "travel_style": "moderate", "currency": "INR"}
    dest_info = {"estimated_daily_cost": 4500}
    budget_res = calculate_budget_feasibility(prefs, dest_info)
    assert budget_res["feasible"] is True
    assert budget_res["estimated_total"] > 0
    assert "accommodation" in budget_res["breakdown"]

def test_agent_4_activity_recommender():
    prefs = {"interests": ["beaches", "nightlife"], "traveler_type": "friends"}
    dest_info = {"primary_recommendation": "Goa"}
    budget_info = {"daily_average_per_person": 4500}
    acts = recommend_activities(prefs, dest_info, budget_info)
    assert "recommended_activities" in acts
    assert len(acts["recommended_activities"]) > 0

def test_agent_5_accommodation_finder():
    prefs = {"duration_days": 5, "traveler_type": "friends", "travel_style": "moderate"}
    dest_info = {"primary_recommendation": "Goa"}
    budget_info = {"breakdown": {"accommodation": 15000}}
    accom = find_accommodations(prefs, dest_info, budget_info)
    assert "recommended_lodging_options" in accom
    assert "data_grounding_note" in accom

def test_agent_6_itinerary_planner():
    prefs = {"duration_days": 3, "traveler_type": "friends", "interests": ["beaches"]}
    dest_info = {"primary_recommendation": "Goa"}
    budget_info = {"daily_average_per_person": 4000}
    acts = {"recommended_activities": [{"name": "Beach visit", "category": "beaches"}]}
    accom = {"recommended_lodging_options": []}
    itin = plan_itinerary(prefs, dest_info, budget_info, acts, accom)
    assert "daily_itinerary" in itin
    assert len(itin["daily_itinerary"]) == 3

def test_agent_7_quality_validator():
    prefs = {"duration_days": 3, "interests": ["beaches"]}
    dest_info = {"primary_recommendation": "Goa"}
    budget_info = {"feasible": True}
    acts = {"recommended_activities": [{"category": "beaches"}]}
    itin = {"daily_itinerary": [{"day_number": 1}, {"day_number": 2}, {"day_number": 3}]}
    val = evaluate_plan_quality(prefs, dest_info, budget_info, acts, itin)
    assert "quality_score" in val
    assert val["quality_score"] >= 0.80
    assert val["approved"] is True

def test_agent_flight_finder():
    from src.agents.flight_finder import find_flights
    prefs = {"duration_days": 5, "travel_style": "moderate", "currency": "INR"}
    dest_info = {"primary_recommendation": "Goa"}
    budget_info = {"estimated_total": 40000, "transport": {"recommended_mode": "flight"}}
    flight_res = find_flights(prefs, dest_info, budget_info)
    assert "flight_options" in flight_res
    assert len(flight_res["flight_options"]) > 0
    assert any("airline" in opt for opt in flight_res["flight_options"])

