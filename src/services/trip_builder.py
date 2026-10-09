"""User-driven trip flow.

The traveler names a destination and a departure city, picks a way to get
there and a hotel, then gives the party and the length of stay. The estimate
is the sum of those choices plus meal, sightseeing, and local-travel rates
for the city. It is not a split of a budget they typed in advance.
"""
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from src.knowledge.travel_facts import (
    canonical_city,
    get_city,
    hotels_for,
    rooms_for,
    same_city,
    spots_for,
)

INTEREST_WORDS = (
    ("wildlife", "wildlife"),
    ("safari", "wildlife"),
    ("beach", "beaches"),
    ("heritage", "heritage"),
    ("fort", "heritage"),
    ("palace", "heritage"),
    ("temple", "heritage"),
    ("adventure", "adventure"),
    ("trek", "adventure"),
    ("food", "food"),
    ("nightlife", "nightlife"),
    ("shopping", "shopping"),
    ("market", "shopping"),
    ("nature", "nature"),
    ("park", "nature"),
)


FARE_PROMPT = """You price real intercity trips. Give typical fares a traveler would see for this origin and destination around the date in the user message.

RULES:
1. price_inr is the round-trip fare for one adult, in INR, for a trip in the next month.
2. Flight means typical economy. Train means AC 3-tier or chair car. Bus means an AC sleeper or Volvo seater.
3. For two cities in the same country, include flight, train, and bus whenever that mode has regular service. Use mode "bus" for a Volvo or AC sleeper coach. Leave a mode out only when that service does not exist.
4. duration_minutes is one-way travel time. duration is a short phrase for that one-way time.
5. label is the usual carrier or operator for that mode, such as a real airline, Indian Railways, or a real bus operator on this route.
6. price_inr and duration_minutes must be real integers for this route. Do not return 0 or 1.
7. Return JSON only:
{
  "options": [
    {
      "mode": "flight",
      "label": "string",
      "duration": "string",
      "stops": "string",
      "price_inr": 0,
      "duration_minutes": 0
    }
  ]
}"""

_FARE_CACHE: Dict[Tuple[str, str], Tuple[float, List[Dict[str, Any]]]] = {}
_FARE_TTL_SECONDS = 60 * 60


def _mode_name(value: Any) -> str:
    low = str(value or "").strip().lower()
    if "bus" in low or "volvo" in low:
        return "bus"
    if "train" in low or "rail" in low:
        return "train"
    if "flight" in low or low == "air":
        return "flight"
    return ""


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r"[^\d]", "", value)
        return int(digits) if digits else None
    return None


def _clean_fare_options(raw: Any) -> List[Dict[str, Any]]:
    rows = raw.get("options") if isinstance(raw, dict) else None
    if not isinstance(rows, list):
        return []
    cleaned = []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        mode = _mode_name(row.get("mode"))
        if not mode or mode in seen:
            continue
        price = _as_int(row.get("price_inr"))
        minutes = _as_int(row.get("duration_minutes"))
        if price is None or minutes is None:
            continue
        if not 400 <= price <= 800000:
            continue
        if not 20 <= minutes <= 72 * 60:
            continue
        label = str(row.get("label") or mode).strip()[:80]
        duration = str(row.get("duration") or "").strip()[:80]
        stops = str(row.get("stops") or "").strip()[:80]
        cleaned.append({
            "mode": mode,
            "label": label or mode,
            "route": "",
            "duration": duration or f"about {minutes} minutes each way",
            "stops": stops or "Check the operator",
            "per_person_price": price,
            "duration_minutes": minutes,
            "fastest": False,
            "booking_tip": "Typical round-trip fare from the travel model for one adult. Confirm on the airline, IRCTC, or the bus operator before you book.",
        })
        seen.add(mode)
    cleaned.sort(key=lambda item: (item["duration_minutes"], item["per_person_price"]))
    if cleaned:
        cleaned[0]["fastest"] = True
    return cleaned


def _fares_from_model(origin: str, destination: str) -> List[Dict[str, Any]]:
    key = (origin.lower(), destination.lower())
    cached = _FARE_CACHE.get(key)
    now = time.time()
    if cached and now - cached[0] < _FARE_TTL_SECONDS:
        return cached[1]

    from src.utils.llm import gemini_client

    raw = gemini_client.generate_json(
        prompt=(
            f"Today is 8 October 2026.\n"
            f"Origin city: {origin}\n"
            f"Destination city: {destination}\n"
            f"Give the typical round-trip fares for one adult."
        ),
        system_instruction=FARE_PROMPT,
        timeout=45,
    )
    options = _clean_fare_options(raw)
    if not options:
        raise ValueError(
            f"The travel model did not return fares from {origin} to {destination}. Try again in a moment."
        )
    for option in options:
        option["route"] = f"{origin} → {destination} → {origin}"
    _FARE_CACHE[key] = (now, options)
    return options


def _party_label(travelers: int) -> str:
    if travelers <= 1:
        return "solo"
    if travelers == 2:
        return "couple"
    return "family"


def _interests(text: str) -> List[str]:
    low = (text or "").lower()
    found = []
    for word, tag in INTEREST_WORDS:
        if word in low and tag not in found:
            found.append(tag)
    return found or ["sightseeing"]


def list_trip_options(destination: str, origin: str) -> Dict[str, Any]:
    dest_name = canonical_city(destination)
    origin_name = canonical_city(origin)
    if not dest_name or not origin_name:
        raise ValueError("Enter both a destination and your current city.")

    local_only = same_city(origin_name, dest_name)
    if local_only:
        ranked = []
    else:
        from src.knowledge.stored_prices import fare_options
        ranked = fare_options(origin_name, dest_name)
        if ranked is None:
            ranked = _fares_from_model(origin_name, dest_name)

    hotels = []
    for hotel in hotels_for(dest_name, nightly_cap=1_000_000):
        hotels.append({
            "name": hotel["name"],
            "tier": hotel.get("tier") or "Stay",
            "nightly": int(hotel.get("nightly") or 0),
            "area": hotel.get("area") or dest_name,
            "features": list(hotel.get("features") or []),
        })

    if local_only:
        note = f"You are already in {dest_name}, so there is no intercity ticket."
    else:
        from src.knowledge.stored_prices import price_for
        if price_for(dest_name) and origin_name == "Delhi":
            note = (
                f"Ways from {origin_name} to {dest_name}, fastest first. "
                "These round-trip fares are the stored Delhi prices for this Explore trip, for one adult."
            )
        else:
            note = (
                f"Ways from {origin_name} to {dest_name}, fastest first. "
                "Each price is the travel model's typical round-trip fare for one adult."
            )

    return {
        "destination": dest_name,
        "origin": origin_name,
        "local_only": local_only,
        "note": note,
        "transport": ranked,
        "hotels": hotels,
    }


def _selected_transport(options: Dict[str, Any], mode: str) -> Optional[Dict[str, Any]]:
    wanted = (mode or "").strip().lower()
    if options["local_only"] or wanted == "local":
        return {
            "mode": "local",
            "label": "Already in the city",
            "per_person_price": 0,
            "route": options["destination"],
            "duration": "No intercity ticket",
        }
    for option in options["transport"]:
        if option["mode"] == wanted:
            return option
    return None


def _selected_hotel(options: Dict[str, Any], hotel_name: str) -> Optional[Dict[str, Any]]:
    wanted = re.sub(r"\s+", " ", (hotel_name or "").strip()).lower()
    for hotel in options["hotels"]:
        if hotel["name"].strip().lower() == wanted:
            return hotel
    return None


def _place_cost(activity: str, spots: List[Dict[str, Any]]) -> int:
    low = activity.lower()
    for spot in spots:
        name = (spot.get("name") or "").lower()
        if name and name in low:
            return int(spot.get("estimated_cost") or 0)
    return 0


def build_trip(
    destination: str,
    origin: str,
    transport_mode: str,
    hotel_name: str,
    trip_days: int,
    travelers: int,
    stay_days: int,
    preferences: str = "",
) -> Dict[str, Any]:
    if stay_days > trip_days:
        raise ValueError("Days in the city cannot be longer than the whole trip.")

    options = list_trip_options(destination, origin)
    chosen = _selected_transport(options, transport_mode)
    if chosen is None:
        raise ValueError("Choose one of the ways shown to reach the city.")
    hotel = _selected_hotel(options, hotel_name)
    if hotel is None:
        raise ValueError("Choose one of the hotels shown for this city.")

    dest_name = options["destination"]
    profile = get_city(dest_name) or {}
    travelers = max(1, int(travelers))
    stay_days = max(1, int(stay_days))
    nights = max(1, stay_days - 1) if stay_days > 1 else 1
    rooms = rooms_for(travelers)
    interests = _interests(preferences)
    traveler_type = _party_label(travelers)

    from src.agents.activity_recommender import recommend_activities
    from src.agents.itinerary_planner import plan_itinerary

    preferences_payload = {
        "destination": dest_name,
        "origin": options["origin"],
        "duration_days": stay_days,
        "traveler_type": traveler_type,
        "interests": interests,
        "travel_style": "moderate",
    }
    destination_info = {"primary_recommendation": dest_name}
    activities_info = recommend_activities(
        preferences_payload,
        destination_info,
        {"daily_average_per_person": 5000},
        use_model=False,
    )
    lodging = {
        "recommended_lodging_options": [{"category": hotel["name"], "name": hotel["name"]}],
    }
    itinerary = plan_itinerary(
        preferences=preferences_payload,
        destination_info=destination_info,
        budget_info={"transport_recommendation": chosen["mode"], "daily_average_per_person": 0},
        activities_info=activities_info,
        accommodation_info=lodging,
        transport_info={"recommended_mode": chosen["mode"]},
        use_model=False,
    )

    spots = spots_for(dest_name, interests)
    food_day = int(profile.get("food_per_day") or 800)
    local_day = int(profile.get("local_per_day") or 500)
    sightseeing = 0
    for day in itinerary.get("daily_itinerary") or []:
        day_sights = 0
        for key in ("morning", "afternoon", "evening"):
            slot = day.get(key) or {}
            found = _place_cost(slot.get("activity") or "", spots)
            slot_cost = found * travelers
            slot["estimated_cost"] = slot_cost
            day_sights += slot_cost
        meals = food_day * travelers
        day["day_budget_estimate"] = day_sights + meals + local_day
        sightseeing += day_sights

    ticket = int(chosen["per_person_price"]) * travelers
    stay_cost = int(hotel["nightly"]) * nights * rooms
    meals_total = food_day * travelers * stay_days
    local_total = local_day * stay_days
    lines = [
        {
            "label": f"{chosen['mode'].capitalize()} {options['origin']} to {dest_name}",
            "amount": ticket,
            "detail": (
                "No intercity ticket."
                if chosen["mode"] == "local"
                else f"Round trip for {travelers} traveler{'s' if travelers != 1 else ''}, about ₹{int(chosen['per_person_price']):,} each."
            ),
        },
        {
            "label": hotel["name"],
            "amount": stay_cost,
            "detail": f"₹{int(hotel['nightly']):,} a night × {nights} night{'s' if nights != 1 else ''} × {rooms} room{'s' if rooms != 1 else ''}.",
        },
        {
            "label": "Meals",
            "amount": meals_total,
            "detail": f"About ₹{food_day:,} a person each day for {stay_days} days in {dest_name}.",
        },
        {
            "label": "Sightseeing",
            "amount": sightseeing,
            "detail": "Entry estimates for the places on the day plan, for the whole group.",
        },
        {
            "label": "Getting around the city",
            "amount": local_total,
            "detail": f"About ₹{local_day:,} a day for cabs or local transit.",
        },
    ]
    total = sum(line["amount"] for line in lines)
    same = same_city(options["origin"], dest_name)
    travel_days = trip_days - stay_days
    extra = ""
    if travel_days > 0 and not same:
        extra = f" {travel_days} of the {trip_days} trip days are travel days and are not extra hotel nights."

    return {
        "destination": dest_name,
        "origin": options["origin"],
        "hotel_name": hotel["name"],
        "transport_mode": chosen["mode"],
        "trip_days": int(trip_days),
        "stay_days": stay_days,
        "nights": nights,
        "travelers": travelers,
        "rooms": rooms,
        "itinerary": itinerary,
        "cost_lines": lines,
        "estimated_total": total,
        "currency": "INR",
        "note": (
            "This total adds the way you chose, the hotel you chose, and city estimates for meals, sights, and local travel. "
            "It is a planning estimate, not a live fare or a room rate."
            + extra
        ),
    }
