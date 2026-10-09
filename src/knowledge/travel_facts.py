"""City aliases, budget-fit transport, and place lists.

Prices are planning estimates, not live fares. The LLM is the primary writer.
These facts keep a named city, a stated budget, and a real morning/afternoon/evening
plan when the model is unavailable or copies an unrelated example.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Tuple

# alias -> canonical city
ALIASES: Dict[str, str] = {
    "banglore": "Bengaluru",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "bengalore": "Bengaluru",
    "blr": "Bengaluru",
    "goa": "Goa",
    "manali": "Manali",
    "jaipur": "Jaipur",
    "udaipur": "Udaipur",
    "varanasi": "Varanasi",
    "shimla": "Shimla",
    "rishikesh": "Rishikesh",
    "leh": "Leh",
    "ladakh": "Leh",
    "andaman": "Andaman",
    "mumbai": "Mumbai",
    "bombay": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "madras": "Chennai",
    "kolkata": "Kolkata",
    "calcutta": "Kolkata",
    "pune": "Pune",
    "mysore": "Mysuru",
    "mysuru": "Mysuru",
    "ooty": "Ooty",
    "agra": "Agra",
    "kochi": "Kochi",
    "cochin": "Kochi",
    "pondicherry": "Pondicherry",
    "puducherry": "Pondicherry",
    "assam": "Assam",
    "guwahati": "Guwahati",
    "kaziranga": "Kaziranga",
    "shillong": "Shillong",
    "meghalaya": "Shillong",
    "kerala": "Kerala",
    "munnar": "Munnar",
    "alleppey": "Alleppey",
    "paris": "Paris",
    "dubai": "Dubai",
    "bali": "Bali",
    "kyoto": "Kyoto",
    "tokyo": "Tokyo",
    "rome": "Rome",
    "london": "London",
    "bangkok": "Bangkok",
    "singapore": "Singapore",
    "jaipur": "Jaipur",
}

# One-way INR per person. Round trip is computed later.
# Missing modes mean that mode is a poor fit (no practical bus, etc.).
CITIES: Dict[str, Dict[str, Any]] = {
    "Bengaluru": {
        "country": "India",
        "domestic": True,
        "highlights": "Lalbagh, Cubbon Park, Bangalore Palace, VV Puram food street, Nandi Hills, Commercial Street",
        "food_per_day": 900,
        "local_per_day": 650,
        "activity_per_day": 500,
        "hotel_nightly": {"budget": 2200, "moderate": 4500, "premium": 9000},
        "flight_one_way": {"Delhi": 5500, "Mumbai": 3800, "Chennai": 2800, "Hyderabad": 2600, "Kolkata": 5200},
        "train_one_way": {"Delhi": 1800, "Mumbai": 1400, "Chennai": 550, "Hyderabad": 650, "Kolkata": 1600},
        "bus_one_way": {"Delhi": 2400, "Mumbai": 1600, "Chennai": 700, "Hyderabad": 800, "Kolkata": 2200},
        "spots": [
            {"name": "Lalbagh Botanical Garden and the Glass House", "category": "nature", "time_slot": "Morning", "estimated_cost": 50},
            {"name": "Bangalore Palace audio tour", "category": "heritage", "time_slot": "Morning", "estimated_cost": 300},
            {"name": "Cubbon Park walk and Vidhana Soudha exterior", "category": "sightseeing", "time_slot": "Morning", "estimated_cost": 0},
            {"name": "Tipu Sultan's Summer Palace", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 50},
            {"name": "National Gallery of Modern Art", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 20},
            {"name": "Commercial Street and Russell Market", "category": "shopping", "time_slot": "Afternoon", "estimated_cost": 400},
            {"name": "VV Puram Thindi Beedi food street", "category": "food", "time_slot": "Evening", "estimated_cost": 400},
            {"name": "Church Street cafe and bookstore hop", "category": "food", "time_slot": "Evening", "estimated_cost": 700},
            {"name": "Indiranagar 100 Feet Road evening", "category": "nightlife", "time_slot": "Evening", "estimated_cost": 900},
            {"name": "ISKCON Temple Rajajinagar", "category": "spiritual", "time_slot": "Morning", "estimated_cost": 0},
            {"name": "Ulsoor Lake and surrounding cafes", "category": "nature", "time_slot": "Afternoon", "estimated_cost": 200},
            {"name": "Bannerghatta Biological Park", "category": "wildlife", "time_slot": "Morning", "estimated_cost": 800},
            {"name": "Nandi Hills sunrise viewpoint", "category": "nature", "time_slot": "Morning", "estimated_cost": 500},
            {"name": "Bull Temple and Bugle Rock park", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 0},
        ],
        "hotels": [
            {"name": "Zostel Bengaluru, Koramangala", "tier": "Budget", "nightly": 1400, "area": "Koramangala", "features": ["Social hostel", "Cafe", "Close to food streets"]},
            {"name": "Treebo Trend Rajmahal", "tier": "Budget", "nightly": 2400, "area": "Majestic", "features": ["Near City railway station", "Breakfast", "Simple rooms"]},
            {"name": "Ibis Bengaluru City Centre", "tier": "Moderate", "nightly": 4200, "area": "Richmond Road", "features": ["Central", "Reliable breakfast", "Easy cabs to MG Road"]},
            {"name": "Lemon Tree Premier, Ulsoor Lake", "tier": "Moderate", "nightly": 5200, "area": "Ulsoor", "features": ["Lake view", "Pool", "Close to Indiranagar"]},
            {"name": "Taj MG Road, Bengaluru", "tier": "Premium", "nightly": 11000, "area": "MG Road", "features": ["Central landmark", "Pool", "Fine dining"]},
        ],
    },
    "Goa": {
        "country": "India",
        "domestic": True,
        "highlights": "Baga, Anjuna, Aguada, Fontainhas, beach shacks",
        "food_per_day": 1000,
        "local_per_day": 700,
        "activity_per_day": 800,
        "hotel_nightly": {"budget": 2000, "moderate": 4500, "premium": 10000},
        "flight_one_way": {"Delhi": 6500, "Mumbai": 3500, "Bengaluru": 3200, "Chennai": 4000, "Hyderabad": 4200},
        "train_one_way": {"Delhi": 2200, "Mumbai": 900, "Bengaluru": 800, "Chennai": 1200, "Hyderabad": 1100},
        "bus_one_way": {"Delhi": 2800, "Mumbai": 900, "Bengaluru": 900, "Chennai": 1400, "Hyderabad": 1300},
        "spots": [
            {"name": "Calangute and Baga beach morning swim", "category": "beaches", "time_slot": "Morning", "estimated_cost": 200},
            {"name": "Aguada Fort and Sinquerim viewpoint", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 50},
            {"name": "Anjuna flea market", "category": "shopping", "time_slot": "Afternoon", "estimated_cost": 300},
            {"name": "Fontainhas Latin Quarter walk", "category": "heritage", "time_slot": "Morning", "estimated_cost": 0},
            {"name": "Dudhsagar day trip", "category": "nature", "time_slot": "Morning", "estimated_cost": 1800},
            {"name": "Beach shack seafood dinner at Baga", "category": "food", "time_slot": "Evening", "estimated_cost": 900},
            {"name": "Tito's Lane nightlife", "category": "nightlife", "time_slot": "Evening", "estimated_cost": 1500},
        ],
        "hotels": [
            {"name": "Beach hut in Baga", "tier": "Budget", "nightly": 1800, "area": "Baga", "features": ["Steps from the beach"]},
            {"name": "Boutique stay in Assagao", "tier": "Moderate", "nightly": 5000, "area": "Assagao", "features": ["Pool", "Cafe lane"]},
            {"name": "Resort in Candolim", "tier": "Premium", "nightly": 11000, "area": "Candolim", "features": ["Beach access", "Breakfast"]},
        ],
    },
    "Jaipur": {
        "country": "India",
        "domestic": True,
        "highlights": "Amber Fort, Hawa Mahal, City Palace, Johari Bazaar",
        "food_per_day": 800,
        "local_per_day": 600,
        "activity_per_day": 500,
        "hotel_nightly": {"budget": 1800, "moderate": 4000, "premium": 9000},
        "flight_one_way": {"Delhi": 3500, "Mumbai": 5000, "Bengaluru": 5500, "Chennai": 6000, "Hyderabad": 4800},
        "train_one_way": {"Delhi": 700, "Mumbai": 1400, "Bengaluru": 1800, "Chennai": 2000, "Hyderabad": 1500},
        "bus_one_way": {"Delhi": 800, "Mumbai": 1600, "Bengaluru": 2200, "Chennai": 2400, "Hyderabad": 1700},
        "spots": [
            {"name": "Amber Fort and Maota Lake", "category": "heritage", "time_slot": "Morning", "estimated_cost": 200},
            {"name": "Hawa Mahal and City Palace", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 300},
            {"name": "Johari Bazaar and street food at Masala Chowk", "category": "food", "time_slot": "Evening", "estimated_cost": 400},
            {"name": "Nahargarh sunset", "category": "sightseeing", "time_slot": "Evening", "estimated_cost": 200},
            {"name": "Jantar Mantar", "category": "heritage", "time_slot": "Morning", "estimated_cost": 50},
        ],
        "hotels": [
            {"name": "Haveli guest house in the Old City", "tier": "Budget", "nightly": 1800, "area": "Pink City", "features": ["Walk to Hawa Mahal"]},
            {"name": "Samode Haveli area boutique", "tier": "Moderate", "nightly": 4500, "area": "Gangapole", "features": ["Courtyard", "Rajasthani breakfast"]},
        ],
    },
    "Manali": {
        "country": "India",
        "domestic": True,
        "highlights": "Solang Valley, Old Manali, Hadimba Temple, Beas river",
        "food_per_day": 800,
        "local_per_day": 700,
        "activity_per_day": 1200,
        "hotel_nightly": {"budget": 1800, "moderate": 3800, "premium": 8000},
        "flight_one_way": {"Delhi": 5500, "Mumbai": 8000, "Bengaluru": 9000, "Chennai": 9500, "Hyderabad": 8500},
        "train_one_way": {"Delhi": 900, "Mumbai": 1800, "Bengaluru": 2500, "Chennai": 2800, "Hyderabad": 2200},
        "bus_one_way": {"Delhi": 1200, "Mumbai": 2200, "Bengaluru": 3000, "Chennai": 3200, "Hyderabad": 2600},
        "spots": [
            {"name": "Solang Valley activity morning", "category": "adventure", "time_slot": "Morning", "estimated_cost": 1500},
            {"name": "Hadimba Temple and Old Manali cafes", "category": "nature", "time_slot": "Afternoon", "estimated_cost": 200},
            {"name": "Mall Road evening walk", "category": "food", "time_slot": "Evening", "estimated_cost": 500},
            {"name": "Jogini waterfall trek", "category": "adventure", "time_slot": "Morning", "estimated_cost": 200},
        ],
        "hotels": [
            {"name": "Guesthouse in Vashisht", "tier": "Budget", "nightly": 1600, "area": "Vashisht", "features": ["Hot spring nearby"]},
            {"name": "Riverside cottage in Old Manali", "tier": "Moderate", "nightly": 4000, "area": "Old Manali", "features": ["Cafe lane", "Mountain view"]},
        ],
    },
    "Delhi": {
        "country": "India",
        "domestic": True,
        "highlights": "Humayun's Tomb, India Gate, Chandni Chowk, Qutub Minar, Lodhi Garden",
        "food_per_day": 900,
        "local_per_day": 500,
        "activity_per_day": 400,
        "hotel_nightly": {"budget": 2000, "moderate": 4500, "premium": 10000},
        "flight_one_way": {"Mumbai": 4500, "Bengaluru": 5500, "Chennai": 5500, "Hyderabad": 4500, "Kolkata": 5000},
        "train_one_way": {"Mumbai": 1500, "Bengaluru": 1800, "Chennai": 1800, "Hyderabad": 1400, "Kolkata": 1500},
        "bus_one_way": {"Mumbai": 1800, "Bengaluru": 2400, "Chennai": 2500, "Hyderabad": 1600, "Kolkata": 2000},
        "spots": [
            {"name": "Humayun's Tomb", "category": "heritage", "time_slot": "Morning", "estimated_cost": 250},
            {"name": "India Gate and Lodhi Garden", "category": "sightseeing", "time_slot": "Afternoon", "estimated_cost": 0},
            {"name": "Chandni Chowk food walk", "category": "food", "time_slot": "Evening", "estimated_cost": 400},
            {"name": "Qutub Minar", "category": "heritage", "time_slot": "Morning", "estimated_cost": 250},
            {"name": "Hauz Khas village evening", "category": "nightlife", "time_slot": "Evening", "estimated_cost": 800},
        ],
        "hotels": [
            {"name": "Hotel near Paharganj", "tier": "Budget", "nightly": 1800, "area": "Paharganj", "features": ["Near New Delhi station"]},
            {"name": "Bloomrooms or similar in Janpath", "tier": "Moderate", "nightly": 4500, "area": "Connaught Place", "features": ["Metro access"]},
        ],
    },
    "Mumbai": {
        "country": "India",
        "domestic": True,
        "highlights": "Gateway of India, Marine Drive, Colaba, Bandra, Elephanta",
        "food_per_day": 1100,
        "local_per_day": 500,
        "activity_per_day": 600,
        "hotel_nightly": {"budget": 2500, "moderate": 5500, "premium": 12000},
        "flight_one_way": {"Delhi": 4500, "Bengaluru": 3800, "Chennai": 4000, "Hyderabad": 3500, "Kolkata": 5500},
        "train_one_way": {"Delhi": 1500, "Bengaluru": 1400, "Chennai": 1300, "Hyderabad": 900, "Kolkata": 1800},
        "bus_one_way": {"Delhi": 2000, "Bengaluru": 1600, "Chennai": 1600, "Hyderabad": 1100, "Kolkata": 2200},
        "spots": [
            {"name": "Gateway of India and Colaba walk", "category": "sightseeing", "time_slot": "Morning", "estimated_cost": 0},
            {"name": "Elephanta Caves ferry", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 400},
            {"name": "Marine Drive sunset", "category": "sightseeing", "time_slot": "Evening", "estimated_cost": 0},
            {"name": "Bandra street food and Bandstand", "category": "food", "time_slot": "Evening", "estimated_cost": 500},
        ],
        "hotels": [
            {"name": "Colaba budget hotel", "tier": "Budget", "nightly": 2500, "area": "Colaba", "features": ["Walk to Gateway"]},
            {"name": "Hotel in Bandra West", "tier": "Moderate", "nightly": 5500, "area": "Bandra", "features": ["Cafes", "Sea link access"]},
        ],
    },
}


def party_size(traveler_type: Optional[str]) -> int:
    return {
        "solo": 1,
        "couple": 2,
        "family": 4,
        "friends": 2,
        "business": 1,
    }.get((traveler_type or "solo").lower(), 1)


def rooms_for(party: int) -> int:
    return max(1, math.ceil(party / 2))


def canonical_city(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    key = re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()
    if key in ALIASES:
        return ALIASES[key]
    for alias, canon in sorted(ALIASES.items(), key=lambda item: -len(item[0])):
        if alias in key:
            return canon
    cleaned = name.strip()
    return cleaned[:1].upper() + cleaned[1:] if cleaned else None


def get_city(name: Optional[str]) -> Optional[Dict[str, Any]]:
    canon = canonical_city(name)
    if not canon:
        return None
    profile = CITIES.get(canon)
    if profile:
        return {"name": canon, **profile}
    return {
        "name": canon,
        "country": "India",
        "domestic": True,
        "highlights": f"Main sights, markets, and neighbourhood food in {canon}",
        "food_per_day": 800,
        "local_per_day": 500,
        "activity_per_day": 400,
        "hotel_nightly": {"budget": 2000, "moderate": 4000, "premium": 8000},
        "flight_one_way": {"Delhi": 5000, "Mumbai": 4500, "Bengaluru": 4500, "Chennai": 4000, "Hyderabad": 4000},
        "train_one_way": {"Delhi": 1600, "Mumbai": 1400, "Bengaluru": 1200, "Chennai": 1100, "Hyderabad": 1000},
        "bus_one_way": {"Delhi": 1800, "Mumbai": 1500, "Bengaluru": 1300, "Chennai": 1200, "Hyderabad": 1100},
        "spots": [
            {"name": f"Old-town walking tour in {canon}", "category": "sightseeing", "time_slot": "Morning", "estimated_cost": 200},
            {"name": f"Main museum or landmark in {canon}", "category": "heritage", "time_slot": "Afternoon", "estimated_cost": 200},
            {"name": f"Local market dinner in {canon}", "category": "food", "time_slot": "Evening", "estimated_cost": 400},
            {"name": f"Neighbourhood cafe evening in {canon}", "category": "food", "time_slot": "Evening", "estimated_cost": 500},
            {"name": f"Park or viewpoint morning in {canon}", "category": "nature", "time_slot": "Morning", "estimated_cost": 50},
            {"name": f"Artisan market afternoon in {canon}", "category": "shopping", "time_slot": "Afternoon", "estimated_cost": 300},
        ],
        "hotels": [
            {"name": f"Well-rated budget hotel in central {canon}", "tier": "Budget", "nightly": 2000, "area": "City centre", "features": ["Transit access", "Breakfast optional"]},
            {"name": f"Mid-range business hotel in {canon}", "tier": "Moderate", "nightly": 4200, "area": "Main commercial district", "features": ["Reliable rooms", "Restaurant"]},
            {"name": f"Upper-scale hotel in {canon}", "tier": "Premium", "nightly": 8500, "area": "Prime neighbourhood", "features": ["Pool", "Central location"]},
        ],
    }


def _alias_hits(text: str) -> List[Tuple[int, int, str]]:
    low = text.lower()
    found: List[Tuple[int, int, str, int]] = []
    for alias, canon in ALIASES.items():
        for match in re.finditer(rf"\b{re.escape(alias)}\b", low):
            found.append((match.start(), match.end(), canon, len(alias)))
    found.sort(key=lambda item: (-item[3], item[0]))
    kept: List[Tuple[int, int, str]] = []
    occupied: List[Tuple[int, int]] = []
    for start, end, canon, _length in found:
        if any(not (end <= s or start >= e) for s, e in occupied):
            continue
        occupied.append((start, end))
        kept.append((start, end, canon))
    kept.sort()
    return kept


def extract_trip_ends(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (origin, destination) from phrases like 'from Delhi to Bangalore'."""
    low = text.lower()
    origin = None
    destination = None
    for start, _end, canon in _alias_hits(text):
        window = low[max(0, start - 16):start]
        if re.search(r"\bfrom\s+$", window):
            origin = canon
        elif re.search(r"\b(to|for|in|at|around|visit|visiting)\s+$", window):
            if destination is None:
                destination = canon
    if destination is None:
        for _start, _end, canon in _alias_hits(text):
            if canon != origin:
                destination = canon
                break
    if origin == destination:
        origin = None
    return origin, destination


def extract_duration_days(text: str) -> Optional[int]:
    match = re.search(r"(\d+)\s*(?:-|to\s*)?(?:\d+)?\s*(?:day|days|night|nights)\b", text, re.IGNORECASE)
    if not match:
        return None
    days = int(match.group(1))
    return max(1, min(days, 30))


def extract_budget_amount(text: str) -> Optional[float]:
    """Pull a trip budget. Amounts tied to 'days' or 'nights' are ignored."""
    patterns = [
        r"(?:₹|rs\.?|inr|\$|usd|eur)\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|lac|thousand|million|m)?",
        r"(?:budget|under|within|around|approx(?:imately)?|about|for|in|of)\s*(?:₹|rs\.?|inr|\$)?\s*([\d,]+(?:\.\d+)?)\s*(k|lakh|lac|thousand|million|m)?",
        r"\b([\d,]+(?:\.\d+)?)\s*(k|lakh|lac)\b",
    ]
    found: List[float] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            tail = text[match.end():match.end() + 12]
            if re.match(r"\s*(?:day|days|night|nights)\b", tail, re.IGNORECASE):
                continue
            val = float(match.group(1).replace(",", ""))
            mult = (match.group(2) or "").lower()
            if mult in {"k", "thousand"}:
                val *= 1000
            elif mult in {"lakh", "lac"}:
                val *= 100000
            elif mult in {"m", "million"}:
                val *= 1000000
            if val >= 500:
                found.append(val)
    return found[-1] if found else None


def extract_traveler_type(text: str) -> Optional[str]:
    low = text.lower()
    if any(k in low for k in ["family", "parents", "kids", "children"]):
        return "family"
    if any(k in low for k in ["couple", "honeymoon", "partner", "wife", "husband"]):
        return "couple"
    if any(k in low for k in ["solo", "myself", "alone", "just me"]):
        return "solo"
    if any(k in low for k in ["business", "work trip", "colleagues"]):
        return "business"
    if any(k in low for k in ["friend", "friends", "buddies", "gang"]):
        return "friends"
    return None


def same_city(a: Optional[str], b: Optional[str]) -> bool:
    if not a or not b:
        return False
    return canonical_city(a) == canonical_city(b)


def _round_trip(one_way: Optional[int], party: int) -> Optional[int]:
    if not one_way:
        return None
    # Small return discount versus two one-way tickets.
    return int(round(one_way * 2 * 0.95 * party))


def transport_options(
    origin: Optional[str],
    destination: Optional[str],
    party: int,
) -> Dict[str, Any]:
    """Compare flight, train, and bus for this route. Origin is assumed only when missing."""
    dest_profile = get_city(destination) if destination else None
    assumed = False
    origin_name = canonical_city(origin) if origin else None
    if dest_profile and origin_name and same_city(origin_name, dest_profile["name"]):
        return {
            "options": [],
            "assumed_origin": None,
            "origin_was_assumed": False,
            "local_only": True,
            "note": f"Origin and destination are both {dest_profile['name']}, so the plan spends the budget inside the city.",
        }
    if not dest_profile:
        return {
            "options": [],
            "assumed_origin": None,
            "origin_was_assumed": False,
            "local_only": True,
            "note": "No destination city was named, so intercity transport is not added.",
        }

    hubs = ["Delhi", "Mumbai", "Chennai", "Hyderabad", "Kolkata", "Bengaluru"]
    if origin_name is None:
        assumed = True
        # Conservative hub: the pricier common metro that is not the destination itself.
        candidates = [h for h in hubs if h != dest_profile["name"] and dest_profile.get("flight_one_way", {}).get(h)]
        origin_name = candidates[0] if candidates else "Delhi"

    flight = _round_trip(dest_profile.get("flight_one_way", {}).get(origin_name), party)
    train = _round_trip(dest_profile.get("train_one_way", {}).get(origin_name), party) if dest_profile.get("domestic") else None
    bus = _round_trip(dest_profile.get("bus_one_way", {}).get(origin_name), party) if dest_profile.get("domestic") else None

    options = []
    if flight:
        options.append({
            "mode": "flight",
            "tier": "flight",
            "airline": "IndiGo / Air India (typical economy)",
            "route": f"{origin_name} → {dest_profile['name']} → {origin_name}",
            "class": "Economy",
            "price_estimate": flight,
            "currency": "INR",
            "duration": "2h–3h each way" if dest_profile.get("domestic") else "6h–14h each way",
            "stops": "Non-stop or 1 stop",
            "departure_slots": ["Morning", "Evening"],
            "baggage": "15kg check-in + cabin bag",
            "booking_tip": "These are planning estimates, not live fares. Compare Skyscanner or the airline site 2–4 weeks out.",
            "one_way_reference_inr": dest_profile.get("flight_one_way", {}).get(origin_name),
        })
    if train:
        options.append({
            "mode": "train",
            "tier": "train",
            "airline": "Indian Railways (3A / CC, typical)",
            "route": f"{origin_name} → {dest_profile['name']} → {origin_name}",
            "class": "AC 3-tier or chair car",
            "price_estimate": train,
            "currency": "INR",
            "duration": "Overnight each way" if (dest_profile.get("train_one_way", {}).get(origin_name) or 0) >= 1000 else "Same-day or overnight each way",
            "stops": "Direct or 1 change",
            "departure_slots": ["Evening departure, morning arrival"],
            "baggage": "Generous luggage versus a flight",
            "booking_tip": "Book on IRCTC. Tatkal is a backup, not the plan. Estimate, not a live fare.",
        })
    if bus:
        options.append({
            "mode": "bus",
            "tier": "bus",
            "airline": "Volvo / sleeper bus (typical)",
            "route": f"{origin_name} → {dest_profile['name']} → {origin_name}",
            "class": "AC sleeper or seater",
            "price_estimate": bus,
            "currency": "INR",
            "duration": "Overnight each way",
            "stops": "Direct",
            "departure_slots": ["Night departure"],
            "baggage": "One large bag in the hold",
            "booking_tip": "Useful when the flight would eat the hotel budget. Estimate, not a live fare.",
        })

    note = (
        f"You did not name a departure city, so fares are estimated from {origin_name}. "
        f"If you are already in {dest_profile['name']}, intercity transport is ₹0 and that money stays for hotels and food."
        if assumed
        else f"Fares are round-trip estimates for {party} traveler(s) from {origin_name} to {dest_profile['name']}."
    )
    return {
        "options": options,
        "assumed_origin": origin_name,
        "origin_was_assumed": assumed,
        "local_only": False,
        "note": note,
    }


def choose_transport(
    origin: Optional[str],
    destination: Optional[str],
    party: int,
    rooms: int,
    days: int,
    nights: int,
    user_budget: Optional[float],
    travel_style: str,
) -> Dict[str, Any]:
    """Pick flight, train, or bus so hotels and food still fit the stated budget."""
    profile = get_city(destination) if destination else None
    survey = transport_options(origin, destination, party)
    if survey["local_only"] or not profile:
        return {
            **survey,
            "recommended_mode": "local",
            "recommended_cost": 0,
            "reason": survey.get("note") or "No intercity ticket is required.",
        }

    hotels = profile["hotel_nightly"]
    style_ceiling = {"budget": "budget", "moderate": "moderate", "luxury": "premium"}.get(travel_style, "moderate")
    ceiling_rate = hotels[style_ceiling]
    moderate_rate = hotels["moderate"]

    def hotel_night_from_leftover(leftover: float) -> int:
        if nights <= 0 or rooms <= 0 or leftover <= 0:
            return 0
        raw = int(leftover * 0.42 / (nights * rooms))
        return max(hotels["budget"] // 2, min(ceiling_rate, raw))

    ranked = []
    for opt in survey["options"]:
        cost = opt["price_estimate"]
        if user_budget:
            leftover = user_budget - cost
        else:
            leftover = moderate_rate * nights * rooms * 3
        nightly = hotel_night_from_leftover(leftover)
        comfort = nightly / moderate_rate if moderate_rate else 0
        speed = {"flight": 0.18, "train": 0.06, "bus": 0.0}.get(opt["mode"], 0)
        # A faster mode only wins when the hotel is still at least ~70% of a normal mid-range night.
        score = comfort + (speed if comfort >= 0.70 else 0)
        opt = dict(opt)
        opt["implied_hotel_night"] = nightly
        opt["fit_score"] = round(score, 3)
        ranked.append(opt)

    if not ranked:
        return {
            **survey,
            "recommended_mode": "local",
            "recommended_cost": 0,
            "reason": survey.get("note") or "No intercity ticket is required.",
        }

    ranked.sort(key=lambda item: item["fit_score"], reverse=True)
    best = ranked[0]
    others = [o for o in ranked if o["mode"] != best["mode"]]
    comparison = ", ".join(
        f"{o['mode']} about Rs {o['price_estimate']:,} round trip (about Rs {o['implied_hotel_night']:,} per night for the hotel after that ticket)"
        for o in ranked
    )
    if user_budget:
        reason = (
            f"For a Rs {int(user_budget):,} trip, {comparison}. "
            f"Recommended {best['mode']} at about Rs {best['price_estimate']:,} round trip, "
            f"which leaves room for about Rs {best['implied_hotel_night']:,} per room per night. "
            f"{survey['note']}"
        )
    else:
        reason = (
            f"No budget was stated. Defaulting to {best['mode']} "
            f"(about Rs {best['price_estimate']:,} round trip from {survey['assumed_origin']}) "
            f"and a {travel_style} on-ground plan. {comparison}."
        )
    return {
        **survey,
        "options": ranked,
        "recommended_mode": best["mode"],
        "recommended_cost": best["price_estimate"],
        "reason": reason,
        "other_modes": [o["mode"] for o in others],
    }


def allocate_budget(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Spend the user's budget. Do not replace it with a fixed daily template."""
    days = int(preferences.get("duration_days") or 5)
    days = max(1, min(days, 30))
    nights = max(1, days - 1) if days > 1 else 1
    currency = preferences.get("currency") or "INR"
    style = preferences.get("travel_style") or "moderate"
    traveler = preferences.get("traveler_type") or "solo"
    party = party_size(traveler)
    rooms = rooms_for(party)
    user_budget = preferences.get("budget")
    if user_budget is not None:
        user_budget = float(user_budget)

    dest_name = preferences.get("destination") or destination_info.get("destination")
    profile = get_city(dest_name) if dest_name else None
    origin = preferences.get("origin")

    transport = choose_transport(
        origin=origin,
        destination=dest_name,
        party=party,
        rooms=rooms,
        days=days,
        nights=nights,
        user_budget=user_budget,
        travel_style=style,
    )
    ticket = int(transport.get("recommended_cost") or 0)

    if profile:
        food_day = profile["food_per_day"]
        local_day = profile["local_per_day"]
        act_day = profile["activity_per_day"]
        hotels = profile["hotel_nightly"]
    else:
        benchmark = int(destination_info.get("estimated_daily_cost") or 4000)
        food_day = int(benchmark * 0.28)
        local_day = int(benchmark * 0.14)
        act_day = int(benchmark * 0.18)
        hotels = {
            "budget": int(benchmark * 0.45),
            "moderate": int(benchmark * 0.7),
            "premium": int(benchmark * 1.3),
        }

    style_key = {"budget": "budget", "moderate": "moderate", "luxury": "premium"}.get(style, "moderate")
    target_night = hotels[style_key]

    def package(nightly: int, food: int, acts: int, local: int) -> Dict[str, int]:
        stay = nightly * nights * rooms
        food_total = food * days * party
        act_total = acts * days * party
        local_total = local * days
        core = stay + food_total + act_total + local_total
        misc = int(round(core * 0.08))
        return {
            "accommodation": stay,
            "food_and_dining": food_total,
            "activities_and_entry": act_total,
            "local_transport": local_total,
            "contingency_and_misc": misc,
            "intercity_transport": ticket,
            "nightly_room": nightly,
        }

    ideal = package(target_night, food_day, act_day, local_day)
    ground_ideal = ideal["accommodation"] + ideal["food_and_dining"] + ideal["activities_and_entry"] + ideal["local_transport"] + ideal["contingency_and_misc"]

    if user_budget is None or user_budget <= 0:
        planned = ideal
        estimated = ground_ideal + ticket
        target_budget = float(estimated)
        remaining = 0.0
        feasible = True
        status = "Budget Estimated From City Costs"
        confidence = 0.8
    else:
        target_budget = float(user_budget)
        money_for_ground = user_budget - ticket
        if money_for_ground >= ground_ideal:
            planned = ideal
            estimated = ground_ideal + ticket
            remaining = round(user_budget - estimated, 2)
            feasible = True
            ratio = estimated / user_budget
            if ratio <= 0.9:
                status = "Comfortably Feasible"
                confidence = 0.93
            else:
                status = "Feasible within Target Budget"
                confidence = 0.88
        elif money_for_ground > 0:
            # Scale food, activities, local, and the hotel down so the stated budget still closes.
            scale = money_for_ground / ground_ideal
            nightly = max(800, int(target_night * scale))
            nightly = min(nightly, target_night)
            planned = package(
                nightly,
                max(350, int(food_day * scale)),
                max(150, int(act_day * scale)),
                max(200, int(local_day * scale)),
            )
            # Re-fit misc so the sum does not exceed the user's budget.
            ground_parts = (
                planned["accommodation"]
                + planned["food_and_dining"]
                + planned["activities_and_entry"]
                + planned["local_transport"]
                + planned["contingency_and_misc"]
            )
            if ground_parts > money_for_ground:
                overflow = ground_parts - int(money_for_ground)
                planned["contingency_and_misc"] = max(0, planned["contingency_and_misc"] - overflow)
                ground_parts = (
                    planned["accommodation"]
                    + planned["food_and_dining"]
                    + planned["activities_and_entry"]
                    + planned["local_transport"]
                    + planned["contingency_and_misc"]
                )
            estimated = ground_parts + ticket
            remaining = round(user_budget - estimated, 2)
            floor_night = int(hotels["budget"] * 0.55)
            feasible = planned["nightly_room"] >= floor_night and planned["food_and_dining"] >= 300 * days
            if feasible:
                status = "Feasible within Target Budget"
                confidence = 0.84
            else:
                status = "Tight: ticket plus stay barely fit, simplify hotels or travel by train/bus"
                confidence = 0.7
                feasible = remaining >= -1  # still a plan, but flagged tight only when food collapses
                if planned["food_and_dining"] < 300 * days or ticket > user_budget * 0.65:
                    feasible = False
                    status = "Requires a Cheaper Mode or a Higher Budget"
                    confidence = 0.62
        else:
            planned = package(hotels["budget"], food_day, act_day, local_day)
            estimated = ticket
            remaining = round(user_budget - ticket, 2)
            feasible = False
            status = "Intercity Ticket Alone Exceeds the Budget"
            confidence = 0.55

    estimated = int(round(estimated))
    daily = max(1, round((estimated - ticket) / days / party)) if party else 0
    return {
        "budget": target_budget,
        "estimated_total": estimated,
        "remaining_budget": remaining if user_budget else 0.0,
        "currency": currency,
        "duration_days": days,
        "nights": nights,
        "party_size": party,
        "rooms": rooms,
        "feasible": feasible,
        "feasibility_status": status,
        "confidence": confidence,
        "breakdown": {
            "accommodation": int(planned["accommodation"]),
            "food_and_dining": int(planned["food_and_dining"]),
            "activities_and_entry": int(planned["activities_and_entry"]),
            "local_transport": int(planned["local_transport"]),
            "contingency_and_misc": int(planned["contingency_and_misc"]),
            "intercity_transport": int(planned["intercity_transport"]),
        },
        "daily_average_per_person": daily,
        "target_nightly_room": int(planned.get("nightly_room") or target_night),
        "transport_recommendation": transport.get("recommended_mode"),
        "transport_reason": transport.get("reason"),
        "transport": transport,
        "cost_classification": {
            "estimation_methodology": "User budget is the ceiling. Intercity flight/train/bus is chosen so hotels and food still fit. City price levels set the split.",
            "applied_style": style,
            "destination": dest_name,
        },
    }


def spots_for(destination: str, interests: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    profile = get_city(destination)
    if not profile:
        return []
    spots = list(profile.get("spots") or [])
    if profile["name"] not in CITIES:
        from src.knowledge.osm_places import lookup_places
        mapped = lookup_places(profile["name"])
        if mapped:
            spots = mapped
    if interests:
        preferred = [s for s in spots if s.get("category") in interests or s.get("category") == "sightseeing"]
        others = [s for s in spots if s not in preferred]
        spots = preferred + others
    return spots


def hotels_for(destination: str, nightly_cap: int) -> List[Dict[str, Any]]:
    profile = get_city(destination)
    if not profile:
        return []
    hotels = list(profile.get("hotels") or [])
    if profile["name"] not in CITIES:
        from src.knowledge.osm_places import lookup_hotels
        mapped = lookup_hotels(profile["name"])
        if mapped:
            rates = profile.get("hotel_nightly") or {}
            tiers = [
                ("Budget", int(rates.get("budget") or 2000)),
                ("Moderate", int(rates.get("moderate") or 4000)),
                ("Premium", int(rates.get("premium") or 8000)),
            ]
            hotels = []
            for index, hotel in enumerate(mapped):
                tier, nightly = tiers[min(index, len(tiers) - 1)]
                hotels.append({
                    "name": hotel["name"],
                    "tier": tier,
                    "nightly": nightly,
                    "area": hotel.get("area") or profile["name"],
                    "features": ["Name from OpenStreetMap", "Nightly rate is an estimate"],
                })
    # Keep a spread: cheapest, one near the cap, and one step above if it is close.
    affordable = [h for h in hotels if h["nightly"] <= max(nightly_cap * 1.15, nightly_cap + 500)]
    stretch = [h for h in hotels if h not in affordable][:1]
    chosen = (affordable or hotels[:2]) + stretch
    # Unique by name, cap at 4
    seen = set()
    result = []
    for hotel in chosen:
        if hotel["name"] in seen:
            continue
        seen.add(hotel["name"])
        result.append(hotel)
        if len(result) == 4:
            break
    return result


def text_mentions_other_city(blob: str, destination: str) -> bool:
    """True when the text is clearly about a different city than the one requested."""
    low = blob.lower()
    wanted = canonical_city(destination) or destination
    markers = {
        "Bengaluru": ["lalbagh", "cubbon", "mg road", "indiranagar", "commercial street"],
        "Goa": ["anjuna", "vagator", "baga", "calangute", "fontainhas", "tito"],
        "Jaipur": ["hawa mahal", "amber fort", "johari"],
        "Manali": ["solang", "hadimba", "old manali", "rohtang"],
        "Mumbai": ["marine drive", "gateway of india", "colaba"],
        "Delhi": ["chandni chowk", "qutub", "india gate", "humayun"],
    }
    for city, words in markers.items():
        if city == wanted:
            continue
        if any(word in low for word in words):
            return True
    return False
