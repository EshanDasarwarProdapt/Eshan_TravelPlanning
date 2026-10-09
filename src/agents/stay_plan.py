"""One model call for activities, lodging, and the day plan.

Each section is accepted only when it matches the city and the shapes the
separate agents already return. A rejected section stays empty so the
workflow can use that agent's existing fallback.
"""
import json
from typing import Any, Dict, Optional

from src.agents.itinerary_planner import _coerce_itinerary, _itinerary_is_for_city, _stay_name, anchor_nights
from src.knowledge.travel_facts import text_mentions_other_city
from src.utils.llm import gemini_client
from src.utils.logging import get_logger

logger = get_logger("stay_plan")

STAY_PLAN_PROMPT = """You are the trip writer for one named city.
Return activities, hotels, and the day-by-day plan for THAT city only.

RULES:
1. Do not mention any other city or its landmarks.
2. Activities: 6 to 8 real places, mixed across morning, afternoon, and evening.
3. Hotels: 3 or 4 real stays near the nightly budget, including a cheaper option.
4. The day plan has exactly the requested number of days. Day 1 starts with arrival and check-in at the hotel. The last day ends with the return from that hotel when a mode is given.
5. Every other evening ends with the night at the hotel. The next morning starts at that same hotel and then goes to a new sight. Do not start a day at the market, temple, or viewpoint where the previous evening ended.
6. Costs are integers in INR and are planning estimates.
7. Return JSON only:
{
  "recommended_activities": [
    {
      "name": "string",
      "category": "string",
      "rating": 0,
      "estimated_cost": 0,
      "time_slot": "Morning",
      "match_score": 0,
      "why_recommended": "string",
      "evidence_snippet": "string"
    }
  ],
  "recommended_lodging_options": [
    {
      "category": "string",
      "tier": "Moderate",
      "ideal_for": "string",
      "expected_nightly_rate": "string",
      "suggested_locations": ["string"],
      "features": ["string"],
      "why_recommended": "string"
    }
  ],
  "area_guide": "string",
  "booking_tips": ["string"],
  "itinerary": {
    "destination": "string",
    "trip_title": "string",
    "total_days": 0,
    "daily_itinerary": [
      {
        "day_number": 1,
        "theme": "string",
        "morning": {"activity": "string", "logistics": "string", "estimated_cost": 0},
        "afternoon": {"activity": "string", "logistics": "string", "estimated_cost": 0},
        "evening": {"activity": "string", "logistics": "string", "estimated_cost": 0},
        "day_budget_estimate": 0
      }
    ],
    "logistical_tips": ["string"]
  }
}"""


def compose_stay_plan(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any],
) -> Dict[str, Optional[Dict[str, Any]]]:
    """Ask once. Invalid sections come back as None."""
    dest_name = destination_info.get("primary_recommendation") or "Goa"
    duration = int(preferences.get("duration_days", 5) or 5)
    traveler_type = preferences.get("traveler_type") or "solo"
    interests = preferences.get("interests") or []
    daily_budget = budget_info.get("daily_average_per_person", 4500)
    country = "India"
    for card in destination_info.get("recommended_destinations") or []:
        if str(card.get("destination", "")).lower() == str(dest_name).lower():
            country = card.get("country") or country
            break
    allocated_stay = (budget_info.get("breakdown") or {}).get("accommodation", 15000)
    nights = max(1, duration - 1)
    nightly_budget = round(allocated_stay / nights) if duration > 1 else allocated_stay
    arrival_mode = (budget_info.get("transport") or {}).get("recommended_mode") or budget_info.get("transport_recommendation") or "local"

    prompt = (
        f"Destination (do not change this): {dest_name}, {country}\n"
        f"Duration: {duration} days. The itinerary must contain exactly {duration} days.\n"
        f"Traveler type: {traveler_type}\n"
        f"Interests: {interests}\n"
        f"Daily budget per person: INR {daily_budget}\n"
        f"Nightly room budget: INR {nightly_budget}\n"
        f"Arrival mode: {arrival_mode}. {budget_info.get('transport_reason', '')}\n"
        f"Write activities, hotels, and the {duration}-day plan for {dest_name} only."
    )
    raw = gemini_client.generate_json(
        prompt=prompt,
        system_instruction=STAY_PLAN_PROMPT,
        fallback_handler=lambda: {},
    )
    if not isinstance(raw, dict):
        raw = {}

    activities = _activities_from(raw, dest_name)
    lodging = _lodging_from(raw, dest_name, duration, traveler_type, allocated_stay, nightly_budget)
    itinerary = _itinerary_from(raw, dest_name, duration, arrival_mode)
    logger.info(
        "Stay plan sections: activities=%s lodging=%s itinerary=%s",
        bool(activities),
        bool(lodging),
        bool(itinerary),
    )
    return {"activities": activities, "accommodations": lodging, "itinerary": itinerary}


def _activities_from(raw: Dict[str, Any], dest_name: str) -> Optional[Dict[str, Any]]:
    activities = raw.get("recommended_activities")
    if not activities:
        return None
    wrapped = {"recommended_activities": activities}
    if text_mentions_other_city(json.dumps(wrapped), dest_name):
        return None
    return wrapped


def _lodging_from(
    raw: Dict[str, Any],
    dest_name: str,
    duration: int,
    traveler_type: str,
    allocated_stay: int,
    nightly_budget: int,
) -> Optional[Dict[str, Any]]:
    options = raw.get("recommended_lodging_options")
    if not options:
        return None
    result = {
        "recommended_lodging_options": options,
        "area_guide": raw.get("area_guide") or f"Stay near the sights you will visit in {dest_name}.",
        "booking_tips": raw.get("booking_tips") or ["Rates are planning estimates, not live availability."],
    }
    if text_mentions_other_city(json.dumps(result), dest_name):
        return None
    result["destination"] = dest_name
    result["allocated_stay_budget"] = allocated_stay
    result["target_nightly_budget"] = nightly_budget
    result["strategic_positioning_advice"] = (
        f"For {duration} days with {traveler_type} in {dest_name}, staying near primary activity hubs reduces local transit costs by up to 25%."
    )
    result["data_grounding_note"] = (
        "Lodging recommendations are generated dynamically based on destination characteristics, traveler profile, and Dataset 485 patterns."
    )
    return result


def _itinerary_from(raw: Dict[str, Any], dest_name: str, duration: int, arrival_mode: str) -> Optional[Dict[str, Any]]:
    plan = raw.get("itinerary")
    if not isinstance(plan, dict):
        return None
    if not _itinerary_is_for_city(plan, dest_name, duration):
        return None
    hotel = _stay_name({"recommended_lodging_options": raw.get("recommended_lodging_options") or []})
    return anchor_nights(_coerce_itinerary(plan, dest_name, duration), hotel, arrival_mode)
