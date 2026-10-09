import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.knowledge.travel_facts import (
    extract_budget_amount,
    extract_duration_days,
    extract_traveler_type,
    extract_trip_ends,
)
from src.utils.llm import gemini_client
from src.utils.logging import log_agent_execution

class StructuredPreferences(BaseModel):
    duration_days: Optional[int] = Field(default=5, description="Trip duration in days")
    budget: Optional[float] = Field(default=None, description="Total budget amount")
    currency: str = Field(default="INR", description="Currency symbol/code")
    traveler_type: Optional[str] = Field(default="friends", description="friends, couple, family, solo, business")
    interests: List[str] = Field(default_factory=list, description="Extracted interest tags (beaches, nightlife, etc.)")
    destination: Optional[str] = Field(default=None, description="Explicit destination name if stated, else null")
    accommodation_preference: Optional[str] = Field(default=None, description="Specific stay type preference")
    travel_style: str = Field(default="moderate", description="budget, moderate, luxury")
    constraints: List[str] = Field(default_factory=list, description="Any hard constraints")


SYSTEM_PROMPT = """You are the Preference Classifier Agent in an AI Travel Planning System.
Your job is to convert natural-language travel requirements into structured travel intent.
CRITICAL RULES:
1. Do NOT invent information.
2. If the user does not specify a destination, set destination = null. If they name a city, keep that city even when it is misspelled (banglore, bengaluru, and bangalore all mean Bengaluru). Never swap their city for a different one.
3. If the user does not specify a budget, set budget = null. A bare amount such as "in 40000" or "40k" is the total trip budget.
4. Extract interests accurately. ALWAYS use the most SPECIFIC interest tag possible from this list:
   - "beaches" (beach, coast, sea, ocean, sand, watersports)
   - "nightlife" (party, clubs, pubs, bars, DJ)
   - "adventure" (trek, rafting, paragliding, snow, hiking, mountains, skiing)
   - "heritage" (history, forts, palace, monument, culture, museum, architecture)
   - "nature" (scenic, greenery, backwaters, tea gardens, waterfall, national parks)
   - "wildlife" (wildlife, zoo, zoos, safari, animals, sanctuary, jungle, tiger, elephant, national park)
   - "food" (culinary, cuisine, dining, seafood, street food, restaurants)
   - "wellness" (spa, massage, ayurveda, yoga, meditation, relax, retreat)
   - "luxury" (resort, 5-star, fine dining, premium, private villa)
   - "spiritual" (temple, ghat, aarti, pilgrimage, sacred, church, cathedral)
   - "shopping" (mall, retail, market, bazaar, souvenirs)
   - "sightseeing" (general sightseeing, city tour, landmarks)
5. IMPORTANT: If the user mentions "wildlife", "zoo", "zoos", "safari", "animals", "sanctuary", "tiger", "jungle", "national park" — you MUST include "wildlife" as an interest. Do NOT classify these as just "nature".
6. Extract duration in days as an integer.
7. Extract traveler_type (friends, couple, family, solo, business). If the user does not mention who is travelling, set traveler_type to "solo".
8. If the user mentions a specific country (e.g. Germany, Japan, Thailand), set destination to that country name.
9. If the user mentions a specific city (e.g. Berlin, Munich, Tokyo), set destination to that city name.
10. Return strictly valid JSON adhering to the schema:
{
  "duration_days": int or null,
  "budget": float or null,
  "currency": "INR",
  "traveler_type": "friends" | "couple" | "family" | "solo" | "business",
  "interests": ["beaches", "nightlife", ...],
  "origin": string or null,
  "destination": string or null,
  "accommodation_preference": string or null,
  "travel_style": "budget" | "moderate" | "luxury",
  "constraints": []
}"""

def fallback_preference_extractor(user_query: str) -> Dict[str, Any]:
    """Deterministic rule-based extractor if LLM is offline or unconfigured."""
    text = user_query.lower()
    
    # 1. Duration
    duration = extract_duration_days(user_query) or 5

    # 2. Budget — currency symbol, "40k", "in 40000", or "budget 40000"
    budget = extract_budget_amount(user_query)
    currency = "INR"
    if "dollar" in text or "$" in text or "usd" in text:
        currency = "USD"
    elif "euro" in text or "eur" in text or "€" in text:
        currency = "EUR"

    # 3. Traveler Type — solo unless the query says otherwise
    traveler_type = extract_traveler_type(user_query) or "solo"

    # 4. Interests — wildlife MUST be its own category, checked FIRST
    interest_pool = {
        "wildlife": ["wildlife", "zoo", "zoos", "safari", "animals", "animal", "sanctuary", "tiger", "elephant", "jungle", "national park"],
        "beaches": ["beach", "beaches", "coast", "coastal", "sea", "ocean", "sand", "watersports"],
        "nightlife": ["nightlife", "party", "parties", "club", "clubs", "pub", "pubs", "bars", "dj"],
        "adventure": ["adventure", "trek", "trekking", "rafting", "paragliding", "snow", "hiking", "mountains", "skiing", "bungee"],
        "heritage": ["heritage", "history", "historical", "fort", "palace", "monument", "culture", "museum", "architecture", "ruins"],
        "nature": ["nature", "scenic", "greenery", "backwaters", "tea gardens", "waterfall"],
        "food": ["food", "culinary", "cuisine", "dining", "seafood", "tapas", "bistro", "street food", "restaurants"],
        "wellness": ["wellness", "spa", "massage", "ayurveda", "yoga", "meditation", "relax", "retreat"],
        "luxury": ["luxury", "resort", "5-star", "fine dining", "premium", "private villa"],
        "spiritual": ["spiritual", "temple", "temples", "ghat", "aarti", "pilgrimage", "sacred", "church", "cathedral"],
        "shopping": ["mall", "shopping", "retail", "market", "bazaar", "souvenirs"]
    }
    interests = []
    for tag, keywords in interest_pool.items():
        if any(kw in text for kw in keywords):
            interests.append(tag)

    if not interests:
        interests = ["sightseeing", "food"]

    # 5. Destination detection — cities, including common misspellings such as "banglore"
    origin, destination = extract_trip_ends(user_query)
    known_destinations = {
        # Countries
        "germany": "Germany", "japan": "Japan", "france": "France", "italy": "Italy",
        "spain": "Spain", "thailand": "Thailand", "indonesia": "Indonesia", "australia": "Australia",
        "switzerland": "Switzerland", "turkey": "Turkey", "greece": "Greece", "vietnam": "Vietnam",
        "singapore": "Singapore", "malaysia": "Malaysia", "sri lanka": "Sri Lanka", "nepal": "Nepal",
        "uae": "Dubai", "usa": "United States", "uk": "United Kingdom", "mexico": "Mexico",
        "south africa": "South Africa", "kenya": "Kenya", "tanzania": "Tanzania",
        "new zealand": "New Zealand", "egypt": "Egypt", "morocco": "Morocco", "portugal": "Portugal",
        "croatia": "Croatia", "czech republic": "Czech Republic", "austria": "Austria",
        # Cities
        "goa": "Goa", "manali": "Manali", "jaipur": "Jaipur", "kerala": "Kerala",
        "bali": "Bali", "kyoto": "Kyoto", "paris": "Paris", "dubai": "Dubai",
        "rome": "Rome", "barcelona": "Barcelona", "phuket": "Phuket", "varanasi": "Varanasi",
        "shimla": "Shimla", "berlin": "Berlin", "munich": "Munich", "amsterdam": "Amsterdam",
        "london": "London", "tokyo": "Tokyo", "bangkok": "Bangkok", "istanbul": "Istanbul",
        "prague": "Prague", "vienna": "Vienna", "lisbon": "Lisbon", "zurich": "Zurich",
        "sydney": "Sydney", "cape town": "Cape Town", "new york": "New York",
        "maldives": "Maldives", "santorini": "Santorini", "udaipur": "Udaipur",
        "rishikesh": "Rishikesh", "leh ladakh": "Leh Ladakh", "andaman": "Andaman",
        "jim corbett": "Jim Corbett", "ranthambore": "Ranthambore",
        "nairobi": "Kenya", "masai mara": "Kenya",
    }
    if destination is None:
        for key, val in known_destinations.items():
            if re.search(rf"\b{re.escape(key)}\b", text):
                destination = val
                break

    # 6. Travel style
    travel_style = "moderate"
    if "luxury" in text or "5-star" in text or (budget and budget > 100000):
        travel_style = "luxury"
    elif "budget" in text or "cheap" in text or "economical" in text or "hostel" in text:
        travel_style = "budget"

    return {
        "duration_days": duration,
        "budget": budget,
        "currency": currency,
        "traveler_type": traveler_type,
        "interests": interests,
        "origin": origin,
        "destination": destination,
        "accommodation_preference": None,
        "travel_style": travel_style,
        "constraints": []
    }


def classify_preferences(user_query: str) -> Dict[str, Any]:
    """
    Agent 1 (Preference Classifier): Converts natural language requirements
    into verified structured travel intent.
    """
    with log_agent_execution("preference_classifier", user_query):
        stated_budget = extract_budget_amount(user_query)
        stated_days = extract_duration_days(user_query)
        stated_party = extract_traveler_type(user_query)
        _origin, stated_destination = extract_trip_ends(user_query)
        # The sentence already names the city, length, budget, and who is going.
        if stated_destination and stated_budget is not None and stated_days is not None and stated_party:
            result = fallback_preference_extractor(user_query)
        else:
            prompt = f"Extract structured travel intent for this query: '{user_query}'"
            result = gemini_client.generate_json(
                prompt=prompt,
                system_instruction=SYSTEM_PROMPT,
                fallback_handler=lambda: fallback_preference_extractor(user_query)
            )
        
        # Post-processing: enforce wildlife interest if query mentions wildlife/zoo terms
        query_lower = user_query.lower()
        wildlife_keywords = ["wildlife", "zoo", "zoos", "safari", "animals", "sanctuary", "tiger", "jungle"]
        if any(kw in query_lower for kw in wildlife_keywords):
            interests = result.get("interests", [])
            if "wildlife" not in interests:
                interests.insert(0, "wildlife")
                result["interests"] = interests
            # Remove "nature" as primary if wildlife should be primary
            if "nature" in interests and interests.index("nature") < interests.index("wildlife"):
                interests.remove("nature")
                interests.append("nature")
                result["interests"] = interests

        # Explicit facts in the sentence win over a model guess.
        # This is what stops "banglore" from being planned as Goa.
        origin, destination = extract_trip_ends(user_query)
        if destination:
            result["destination"] = destination
        elif not result.get("destination"):
            result["destination"] = None
        if origin:
            result["origin"] = origin
        stated_budget = extract_budget_amount(user_query)
        if stated_budget is not None:
            result["budget"] = stated_budget
        stated_days = extract_duration_days(user_query)
        if stated_days is not None:
            result["duration_days"] = stated_days
        stated_party = extract_traveler_type(user_query)
        result["traveler_type"] = stated_party or "solo"
        if not result.get("interests"):
            result["interests"] = ["sightseeing", "food"]
        if "beach" in query_lower and not any("beach" in str(i) for i in result.get("interests", [])):
            result["interests"] = ["beaches", *result.get("interests", [])]
        if not result.get("currency"):
            result["currency"] = "INR"
        if not result.get("travel_style"):
            result["travel_style"] = "moderate"

        return result
