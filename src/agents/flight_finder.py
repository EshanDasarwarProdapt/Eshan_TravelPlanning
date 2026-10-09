import json
from typing import Dict, Any, List
from src.knowledge.travel_facts import text_mentions_other_city, transport_options
from src.utils.llm import gemini_client
from src.utils.logging import log_agent_execution

FLIGHT_FINDER_PROMPT = """You are the Flight Finder Agent in an AI Travel Planning System.
Your job is to recommend realistic flight options for the traveler's trip based on their destination, budget, and travel style.

CRITICAL RULES:
1. Generate 3-4 realistic flight options with different price tiers (budget, standard, premium).
2. Include realistic airline names that actually operate on that route.
3. Provide estimated prices in the user's currency.
4. Include flight duration, number of stops, and departure time slots.
5. Ground your recommendations in real-world airline routes and typical pricing.
6. If the destination is within the same country (domestic), suggest appropriate domestic carriers.
7. If the destination is international, suggest appropriate international carriers.
8. DO NOT fabricate flight numbers. Use realistic airline names and route patterns.
9. Return valid JSON matching this schema:
{
  "flight_options": [
    {
      "airline": "Air India",
      "route": "Delhi (DEL) → Goa (GOI)",
      "class": "Economy",
      "price_estimate": 4500,
      "currency": "INR",
      "duration": "2h 30m",
      "stops": "Non-stop",
      "departure_slots": ["Morning (6:00-9:00)", "Afternoon (12:00-15:00)"],
      "baggage": "15kg check-in + 7kg cabin",
      "tier": "budget",
      "booking_tip": "Book 2-3 weeks in advance for best fares on this route."
    }
  ],
  "origin_suggestion": "Major metro city hub nearest to traveler",
  "best_booking_window": "2-4 weeks before departure for domestic, 4-8 weeks for international",
  "transit_from_airport": "Pre-paid taxi or shuttle service to hotel area (₹800-1200)"
}"""


def fallback_flight_finder(
    destination: str,
    country: str,
    duration: int,
    budget: float,
    currency: str,
    travel_style: str,
    traveler_type: str
) -> Dict[str, Any]:
    """Deterministic rule-based flight recommendation when LLM is unavailable."""
    
    # Determine if domestic (India) or international
    indian_destinations = [
        "goa", "manali", "jaipur", "kerala", "varanasi", "shimla", "udaipur",
        "leh ladakh", "andaman", "jim corbett", "ranthambore", "rishikesh",
        "kerala (munnar & alleppey)", "kerala (periyar & wayanad)", "jim corbett & ranthambore"
    ]
    is_domestic = destination.lower() in indian_destinations or country.lower() == "india"
    
    style_multiplier = {"budget": 0.7, "moderate": 1.0, "luxury": 1.6}.get(travel_style, 1.0)
    
    if is_domestic:
        base_price = 4500
        options = [
            {
                "airline": "IndiGo",
                "route": f"Delhi (DEL) → {destination}",
                "class": "Economy",
                "price_estimate": int(base_price * 0.8 * style_multiplier),
                "currency": currency,
                "duration": "2h 15m",
                "stops": "Non-stop",
                "departure_slots": ["Early Morning (5:30-7:00)", "Afternoon (13:00-15:00)", "Evening (18:00-20:00)"],
                "baggage": "15kg check-in + 7kg cabin",
                "tier": "budget",
                "booking_tip": "IndiGo offers the most frequent flights. Book 2-3 weeks ahead for best fares."
            },
            {
                "airline": "Air India",
                "route": f"Mumbai (BOM) → {destination}",
                "class": "Economy",
                "price_estimate": int(base_price * 1.0 * style_multiplier),
                "currency": currency,
                "duration": "2h 30m",
                "stops": "Non-stop",
                "departure_slots": ["Morning (8:00-10:00)", "Evening (17:00-19:00)"],
                "baggage": "25kg check-in + 7kg cabin",
                "tier": "standard",
                "booking_tip": "Air India includes more baggage allowance. Good for travelers with extra luggage."
            },
            {
                "airline": "Vistara",
                "route": f"Delhi (DEL) → {destination}",
                "class": "Premium Economy",
                "price_estimate": int(base_price * 1.5 * style_multiplier),
                "currency": currency,
                "duration": "2h 20m",
                "stops": "Non-stop",
                "departure_slots": ["Morning (7:00-9:00)", "Afternoon (14:00-16:00)"],
                "baggage": "25kg check-in + 7kg cabin",
                "tier": "premium",
                "booking_tip": "Vistara Premium Economy offers extra legroom and complimentary meals."
            },
            {
                "airline": "SpiceJet",
                "route": f"Bangalore (BLR) → {destination}",
                "class": "Economy",
                "price_estimate": int(base_price * 0.7 * style_multiplier),
                "currency": currency,
                "duration": "2h 45m",
                "stops": "Non-stop",
                "departure_slots": ["Morning (6:00-8:00)", "Night (21:00-23:00)"],
                "baggage": "15kg check-in + 7kg cabin",
                "tier": "budget",
                "booking_tip": "SpiceJet often has flash sales. Check their website for last-minute deals."
            }
        ]
        origin_suggestion = "Delhi (DEL), Mumbai (BOM), or Bangalore (BLR)"
        transit_tip = f"Pre-paid taxi or app cab from airport to {destination} hotel area (₹500-1500)"
    else:
        # International flights
        base_price = 25000
        if country.lower() in ["japan", "australia", "new zealand", "united states", "kenya", "tanzania", "south africa"]:
            base_price = 45000
        elif country.lower() in ["france", "germany", "united kingdom", "italy", "spain", "switzerland", "netherlands", "greece", "turkey", "croatia", "czech republic", "austria", "portugal"]:
            base_price = 35000
        elif country.lower() in ["thailand", "indonesia", "singapore", "malaysia", "vietnam", "sri lanka", "nepal", "maldives"]:
            base_price = 18000
        elif country.lower() in ["united arab emirates"]:
            base_price = 20000
        
        options = [
            {
                "airline": "IndiGo / AirAsia",
                "route": f"Delhi (DEL) → {destination}",
                "class": "Economy",
                "price_estimate": int(base_price * 0.75 * style_multiplier),
                "currency": currency,
                "duration": "5h-8h",
                "stops": "Non-stop / 1 stop",
                "departure_slots": ["Early Morning (4:00-7:00)", "Late Night (22:00-01:00)"],
                "baggage": "20kg check-in + 7kg cabin",
                "tier": "budget",
                "booking_tip": "Budget carriers often have limited luggage. Book 4-6 weeks ahead for international routes."
            },
            {
                "airline": "Air India",
                "route": f"Mumbai (BOM) → {destination}",
                "class": "Economy",
                "price_estimate": int(base_price * 1.0 * style_multiplier),
                "currency": currency,
                "duration": "6h-10h",
                "stops": "Non-stop / 1 stop",
                "departure_slots": ["Morning (8:00-11:00)", "Evening (19:00-22:00)"],
                "baggage": "30kg check-in + 7kg cabin",
                "tier": "standard",
                "booking_tip": "Air India offers generous baggage for international routes. Star Alliance partner for connecting flights."
            },
            {
                "airline": "Emirates / Qatar Airways",
                "route": f"Delhi (DEL) → {destination} (via Dubai/Doha)",
                "class": "Economy Plus",
                "price_estimate": int(base_price * 1.4 * style_multiplier),
                "currency": currency,
                "duration": "8h-14h",
                "stops": "1 stop (hub connection)",
                "departure_slots": ["Morning (6:00-9:00)", "Afternoon (14:00-17:00)", "Night (22:00-01:00)"],
                "baggage": "30kg check-in + 7kg cabin",
                "tier": "premium",
                "booking_tip": "Gulf carriers offer excellent in-flight service and generous transit lounge access."
            },
            {
                "airline": "Singapore Airlines / Lufthansa",
                "route": f"Mumbai (BOM) → {destination}",
                "class": "Business",
                "price_estimate": int(base_price * 2.5 * style_multiplier),
                "currency": currency,
                "duration": "7h-12h",
                "stops": "Non-stop / 1 stop",
                "departure_slots": ["Morning (9:00-12:00)", "Evening (20:00-23:00)"],
                "baggage": "40kg check-in + 2x 7kg cabin",
                "tier": "luxury",
                "booking_tip": "Business class includes lounge access, priority boarding, and lie-flat seats on long-haul routes."
            }
        ]
        origin_suggestion = "Delhi (DEL) or Mumbai (BOM) — major international hubs"
        transit_tip = f"Airport shuttle, metro, or pre-booked transfer to {destination} accommodation area"
    
    return {
        "flight_options": options,
        "origin_suggestion": origin_suggestion,
        "best_booking_window": "2-3 weeks for domestic, 4-8 weeks for international flights",
        "transit_from_airport": transit_tip
    }


def find_flights(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent 8 (Flight Finder): Recommends flight options with pricing tiers,
    airlines, duration, and booking tips for the selected destination.
    """
    with log_agent_execution("flight_finder"):
        dest_name = destination_info.get("primary_recommendation", "Goa")
        
        # Extract country from destination recommendations
        dest_list = destination_info.get("recommended_destinations", [])
        country = "India"
        for d in dest_list:
            if d.get("destination", "").lower() == dest_name.lower():
                country = d.get("country", "India")
                break
        
        duration = int(preferences.get("duration_days", 5) or 5)
        budget = preferences.get("budget") or budget_info.get("estimated_total", 50000)
        currency = preferences.get("currency", "INR")
        travel_style = preferences.get("travel_style", "moderate")
        traveler_type = preferences.get("traveler_type", "friends")
        interests = preferences.get("interests", [])

        planned = _options_from_budget(preferences, dest_name, country, budget_info, currency)
        # Prices come from the budget decision so a flight card cannot disagree with the total.
        # The model still writes hotels, activities, and the day plan.
        if planned["flight_options"]:
            return planned

        def fallback_handler():
            return fallback_flight_finder(dest_name, country, duration, budget, currency, travel_style, traveler_type)

        gemini_prompt = (
            f"Destination city: {dest_name}, {country}\n"
            f"Origin: {preferences.get('origin') or 'a major Indian city, say which one you assume'}\n"
            f"Trip Duration: {duration} days\n"
            f"Total trip budget: {currency} {budget}\n"
            f"Traveler Type: {traveler_type}\n"
            f"Interests: {interests}\n\n"
            f"Compare flight, train, and bus for reaching {dest_name} only. "
            f"Do not suggest a route to any other city. Mark prices as estimates."
        )

        result = gemini_client.generate_json(
            prompt=gemini_prompt,
            system_instruction=FLIGHT_FINDER_PROMPT,
            fallback_handler=fallback_handler
        )

        if "flight_options" not in result or not result["flight_options"]:
            return fallback_handler()
        blob = json.dumps(result)
        if text_mentions_other_city(blob, dest_name):
            return fallback_handler()
        return result


def _options_from_budget(
    preferences: Dict[str, Any],
    dest_name: str,
    country: str,
    budget_info: Dict[str, Any],
    currency: str,
) -> Dict[str, Any]:
    """Use the budget agent's flight-vs-train decision so the prices match the plan."""
    transport = budget_info.get("transport") or {}
    options = transport.get("options") or []
    if not options:
        survey = transport_options(preferences.get("origin"), dest_name, 1)
        options = survey.get("options") or []
        transport = {**survey, "recommended_mode": (options[0]["mode"] if options else "local"), "reason": survey.get("note")}

    flight_options: List[Dict[str, Any]] = []
    for opt in options:
        flight_options.append({
            "airline": opt.get("airline") or opt.get("mode"),
            "route": opt.get("route") or dest_name,
            "class": opt.get("class") or "Standard",
            "price_estimate": int(opt.get("price_estimate") or 0),
            "currency": opt.get("currency") or currency,
            "duration": opt.get("duration") or "",
            "stops": opt.get("stops") or "",
            "departure_slots": opt.get("departure_slots") or [],
            "baggage": opt.get("baggage"),
            "tier": opt.get("tier") or opt.get("mode") or "standard",
            "booking_tip": opt.get("booking_tip"),
        })

    recommended = transport.get("recommended_mode") or "local"
    return {
        "flight_options": flight_options,
        "origin_suggestion": transport.get("assumed_origin") or preferences.get("origin") or f"Name your departure city for exact fares to {dest_name}",
        "best_booking_window": "2–4 weeks ahead for domestic flights; trains as soon as the chart opens",
        "transit_from_airport": f"App cab or prepaid taxi from the {dest_name} station or airport into the hotel area",
        "recommended_mode": recommended,
        "mode_reason": transport.get("reason") or budget_info.get("transport_reason") or "",
    }
