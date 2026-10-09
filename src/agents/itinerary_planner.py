import json
from typing import Dict, Any, List, Optional
from src.knowledge.travel_facts import spots_for, text_mentions_other_city, canonical_city, same_city
from src.utils.llm import gemini_client
from src.utils.logging import log_agent_execution

ITINERARY_SYSTEM_PROMPT = """You are the Itinerary Planner Agent in an AI Travel Planning System.
Build a day-by-day plan for the destination, duration, activities, hotels, and transport in the user message.

RULES:
1. Every day has morning, afternoon, and evening. Use real places from the activity list and the named city.
2. Day 1 starts with arrival by the recommended mode (flight, train, bus, or already in the city). The last day ends with the return journey.
3. The number of days must equal total_days. The destination field must be the requested city.
4. Do not copy any other city's plan. If the city is Bengaluru, do not mention Goa, beaches in Goa, Anjuna, or Vagator.
5. estimated_cost values are integers in INR. The sum of day_budget_estimate should stay inside the on-ground budget.
6. The evening of every day except departure ends at the hotel for the night. Do not leave the traveler overnight at a market, temple, beach, or viewpoint.
7. The next morning starts at that same hotel, then goes to a new sight. Never start a day at the place where the previous evening ended.
8. Return JSON only. The braces below describe types, not a sample trip:
{
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
}"""

def _slot(activity: str, logistics: str, cost: int) -> Dict[str, Any]:
    return {"activity": activity, "logistics": logistics, "estimated_cost": int(cost)}


def _stay_name(accommodation_info: Optional[Dict[str, Any]]) -> str:
    options = (accommodation_info or {}).get("recommended_lodging_options") or []
    for option in options:
        name = str(option.get("category") or option.get("name") or "").strip()
        if name:
            return name
    return "the hotel"


def _stop_key(text: str) -> str:
    low = (text or "").lower()
    for prefix in (
        "morning at ", "afternoon at ", "evening at ", "night at ",
        "leave ", "start at ",
    ):
        if low.startswith(prefix):
            low = low[len(prefix):]
    return " ".join(low.split())


def _same_stop(left: str, right: str) -> bool:
    a, b = _stop_key(left), _stop_key(right)
    if len(a) < 4 or len(b) < 4:
        return False
    return a == b or a in b or b in a


def anchor_nights(plan: Dict[str, Any], hotel_name: str, arrival_mode: str = "local") -> Dict[str, Any]:
    """End each night at the hotel, and start the next morning from that hotel."""
    days = plan.get("daily_itinerary") or []
    hotel = hotel_name or "the hotel"
    originals = [
        {
            "morning": str((day.get("morning") or {}).get("activity") or ""),
            "afternoon": str((day.get("afternoon") or {}).get("activity") or ""),
            "evening": str((day.get("evening") or {}).get("activity") or ""),
        }
        for day in days
    ]
    last = len(days)
    for index, day in enumerate(days):
        morning = dict(day.get("morning") or {})
        evening = dict(day.get("evening") or {})
        if index > 0 and not originals[index]["morning"].lower().startswith("leave "):
            morning_act = _stop_key(originals[index]["morning"]) or originals[index]["morning"]
            previous_evening = originals[index - 1]["evening"]
            if _same_stop(morning_act, previous_evening):
                afternoon_act = _stop_key(originals[index]["afternoon"])
                morning_act = afternoon_act if afternoon_act and not _same_stop(afternoon_act, previous_evening) else f"a new sight in {plan.get('destination') or 'the city'}"
            morning["activity"] = f"Leave {hotel}, where you stayed last night, and go to {morning_act}"
            morning["logistics"] = f"The new day starts at {hotel}, not at yesterday's last stop."
            day["morning"] = morning

        departing = index + 1 == last and arrival_mode in {"flight", "train", "bus"}
        if departing:
            evening["activity"] = f"Check out of {hotel} and take the return {arrival_mode}"
            evening["logistics"] = f"Leave from {hotel}. Do not start the journey from the last sight."
        else:
            evening["activity"] = f"Dinner, then the night at {hotel}"
            evening["logistics"] = f"Go back to {hotel} after dinner. Tomorrow starts at this hotel, not at the last sight."
        day["evening"] = evening
    plan["daily_itinerary"] = days
    return plan


def fallback_itinerary_builder(
    dest_name: str,
    duration: int,
    traveler_type: str,
    activities: List[Dict[str, Any]],
    budget_daily: int,
    arrival_mode: str = "local",
    hotel_name: str = "the hotel",
) -> Dict[str, Any]:
    """Day plan built from this city's places, used when the model copies another trip."""
    daily_plans = []
    names = []
    for activity in activities:
        name = activity.get("name")
        if name and name not in names:
            names.append(name)
    if not names:
        names = [s["name"] for s in spots_for(dest_name)]
    if not names:
        names = [f"a main sight in {dest_name}", f"a second neighbourhood in {dest_name}"]

    per_slot = max(100, int(budget_daily * 0.25))
    hotel = hotel_name or "the hotel"
    mode_label = {
        "flight": f"Land in {dest_name}, collect bags, and check in at {hotel}",
        "train": f"Arrive by train in {dest_name} and check in at {hotel}",
        "bus": f"Arrive by bus in {dest_name} and check in at {hotel}",
        "local": f"Start the trip at {hotel}",
    }.get(arrival_mode, f"Arrive in {dest_name} and check in at {hotel}")
    cursor = 0

    def next_sight() -> str:
        nonlocal cursor
        name = names[cursor % len(names)]
        cursor += 1
        return name

    for day in range(1, duration + 1):
        if day == 1:
            morning = _slot(mode_label, f"The first night is at {hotel}. Keep the rest of the morning light after the journey.", per_slot)
        else:
            place = next_sight()
            morning = _slot(
                f"Leave {hotel}, where you stayed last night, and go to {place}",
                f"The new day starts at {hotel}, not at yesterday's last stop.",
                per_slot,
            )
        afternoon_place = next_sight()
        if day == duration and arrival_mode in {"flight", "train", "bus"}:
            evening = _slot(
                f"Check out of {hotel} and take the return {arrival_mode}",
                f"Leave from {hotel}. Allow 3 hours before a flight, or 90 minutes before a train.",
                per_slot,
            )
        else:
            evening = _slot(
                f"Dinner, then the night at {hotel}",
                f"Go back to {hotel} after dinner. Tomorrow starts at this hotel.",
                per_slot,
            )
        daily_plans.append({
            "day_number": day,
            "theme": f"Day {day} in {dest_name}",
            "morning": morning,
            "afternoon": _slot(
                f"Afternoon at {afternoon_place}",
                "Cab or metro from the morning stop. This is a visit, not an overnight.",
                per_slot,
            ),
            "evening": evening,
            "day_budget_estimate": int(budget_daily),
        })

    return {
        "destination": dest_name,
        "trip_title": f"{duration}-Day Curated {dest_name} Experience for {traveler_type.capitalize()}",
        "total_days": duration,
        "daily_itinerary": daily_plans,
        "logistical_tips": [
            f"Pre-book major activity tickets in {dest_name} during peak season to avoid queues.",
            "Maintain digital backups of IDs and ensure comfortable walking shoes.",
            "Stay hydrated and allocate 1-2 hours of free time daily for spontaneous exploration."
        ]
    }


def _itinerary_is_for_city(plan: Dict[str, Any], dest_name: str, duration: int) -> bool:
    days = plan.get("daily_itinerary") or []
    if len(days) != duration:
        return False
    got = plan.get("destination") or ""
    if not same_city(got, dest_name) and canonical_city(dest_name) not in got and dest_name.lower() not in got.lower():
        return False
    if text_mentions_other_city(json.dumps(plan), dest_name):
        return False
    return True


def _coerce_itinerary(plan: Dict[str, Any], dest_name: str, duration: int) -> Dict[str, Any]:
    plan["destination"] = dest_name
    plan["total_days"] = duration
    cleaned = []
    for index, day in enumerate(plan.get("daily_itinerary") or [], start=1):
        def slot(raw: Any) -> Dict[str, Any]:
            raw = raw or {}
            cost = raw.get("estimated_cost", 0)
            if isinstance(cost, str):
                digits = "".join(ch for ch in cost if ch.isdigit())
                cost = int(digits) if digits else 0
            return {
                "activity": str(raw.get("activity") or "Free time"),
                "logistics": str(raw.get("logistics") or ""),
                "estimated_cost": int(cost or 0),
            }
        cleaned.append({
            "day_number": int(day.get("day_number") or index),
            "theme": str(day.get("theme") or f"Day {index} in {dest_name}"),
            "morning": slot(day.get("morning")),
            "afternoon": slot(day.get("afternoon")),
            "evening": slot(day.get("evening")),
            "day_budget_estimate": int(day.get("day_budget_estimate") or 0),
        })
    plan["daily_itinerary"] = cleaned
    plan["logistical_tips"] = [str(tip) for tip in (plan.get("logistical_tips") or [])]
    return plan


def plan_itinerary(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any],
    activities_info: Dict[str, Any],
    accommodation_info: Dict[str, Any],
    refinement_feedback: str = "",
    transport_info: Optional[Dict[str, Any]] = None,
    use_model: bool = True,
) -> Dict[str, Any]:
    """
    Agent 6 (Itinerary Planner): Builds structured, realistic day-by-day itinerary
    incorporating all multi-agent context and any iterative refinement feedback.
    """
    with log_agent_execution("itinerary_planner"):
        dest_name = destination_info.get("primary_recommendation", "Goa")
        duration = int(preferences.get("duration_days", 5) or 5)
        traveler_type = preferences.get("traveler_type", "friends")
        budget_daily = budget_info.get("daily_average_per_person", 4500)
        activities = activities_info.get("recommended_activities", [])
        arrival_mode = (transport_info or budget_info.get("transport") or {}).get("recommended_mode") or budget_info.get("transport_recommendation") or "local"

        hotel_name = _stay_name(accommodation_info)

        def fallback_handler():
            return fallback_itinerary_builder(
                dest_name,
                duration,
                traveler_type,
                activities,
                budget_daily,
                arrival_mode=arrival_mode,
                hotel_name=hotel_name,
            )

        if not use_model:
            return fallback_handler()

        prompt = (
            f"Destination (do not change this): {dest_name}\n"
            f"Duration: {duration} days. You must return exactly {duration} days.\n"
            f"Traveler Type: {traveler_type}\n"
            f"Interests: {preferences.get('interests', [])}\n"
            f"How they should arrive: {arrival_mode}. Reason: {budget_info.get('transport_reason', '')}\n"
            f"On-ground daily budget per person: ₹{budget_daily}\n"
            f"Recommended activities to place on the plan: {activities}\n"
            f"Hotels to choose from: {accommodation_info}\n"
            f"{'REFINEMENT FEEDBACK: ' + refinement_feedback if refinement_feedback else ''}\n\n"
            f"Write the {duration}-day plan for {dest_name} only."
        )

        res = gemini_client.generate_json(
            prompt=prompt,
            system_instruction=ITINERARY_SYSTEM_PROMPT,
            fallback_handler=fallback_handler
        )

        if not isinstance(res, dict) or not _itinerary_is_for_city(res, dest_name, duration):
            return fallback_handler()
        plan = _coerce_itinerary(res, dest_name, duration)
        return anchor_nights(plan, hotel_name, arrival_mode)
