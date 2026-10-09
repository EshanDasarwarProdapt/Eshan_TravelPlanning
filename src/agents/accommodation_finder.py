import json
from typing import Dict, Any, List
from src.knowledge.travel_facts import hotels_for, text_mentions_other_city
from src.utils.llm import gemini_client
from src.utils.logging import log_agent_execution

ACCOMMODATION_PROMPT = """You are the Accommodation Finder Agent in an AI Travel Planning System.
Your job is to recommend realistic accommodation options for the traveler's destination, considering their budget, travel style, and traveler type.

CRITICAL RULES:
1. Generate 3-4 accommodation options across different tiers (budget, moderate, premium, luxury).
2. Use realistic hotel/stay categories and pricing for the specific destination.
3. Include specific neighborhood/area suggestions that are strategically located near attractions.
4. Provide realistic nightly rates in the traveler's currency.
5. Ground recommendations in the actual geography and hospitality landscape of the destination.
6. Name real hotels or well-known stays in this city. Nightly rates must sit near the nightly budget. Include a cheaper option and a mid-range option. Offer a expensive option only if it is close to the nightly budget.
7. Include practical features relevant to the traveler type.
8. Return valid JSON matching this schema:
{
  "recommended_lodging_options": [
    {
      "category": "Boutique Heritage Haveli",
      "tier": "Moderate",
      "ideal_for": "couples & cultural travelers",
      "expected_nightly_rate": "₹4,500 - ₹8,000 / night",
      "suggested_locations": ["Old City Quarter", "Near Main Palace"],
      "features": ["Traditional architecture", "Rooftop restaurant", "Walking distance to attractions"],
      "why_recommended": "Perfect balance of cultural immersion and comfort for heritage-focused travelers."
    }
  ],
  "area_guide": "Brief guide to the best neighborhoods for staying",
  "booking_tips": ["Book early for peak season", "Check for meal inclusions"]
}"""


def fallback_accommodation_finder(
    dest_name: str,
    country: str,
    duration: int,
    nightly_budget: int,
    travel_style: str,
    traveler_type: str,
    interests: List[str]
) -> Dict[str, Any]:
    """Hotel list priced against the nightly budget when the model is unavailable."""
    catalog = hotels_for(dest_name, nightly_budget or 4000)
    if catalog:
        options = []
        for hotel in catalog:
            options.append({
                "category": hotel["name"],
                "tier": hotel.get("tier") or "Moderate",
                "ideal_for": traveler_type,
                "expected_nightly_rate": f"₹{hotel['nightly']:,} / night",
                "suggested_locations": [hotel.get("area") or dest_name],
                "features": hotel.get("features") or ["Central location"],
                "why_recommended": f"About ₹{hotel['nightly']:,} a night in {hotel.get('area', dest_name)}, against a target of ₹{nightly_budget:,}.",
            })
        return {
            "recommended_lodging_options": options,
            "area_guide": f"Stay near the sights you will actually visit in {dest_name}, so cab rides do not eat the daily budget.",
            "booking_tips": [
                "Rates below are planning estimates, not live availability.",
                "Match the nightly rate to the stay budget before you book.",
            ],
        }

    # Determine pricing tier based on country/destination
    price_multiplier = 1.0
    high_cost_countries = ["france", "united kingdom", "switzerland", "japan", "australia", "united states", "maldives"]
    mid_cost_countries = ["germany", "italy", "spain", "singapore", "netherlands", "greece", "turkey", "united arab emirates", "kenya", "tanzania"]
    low_cost_countries = ["india", "thailand", "indonesia", "vietnam", "sri lanka", "nepal", "malaysia"]
    
    country_lower = country.lower()
    if country_lower in high_cost_countries:
        price_multiplier = 2.5
    elif country_lower in mid_cost_countries:
        price_multiplier = 1.8
    elif country_lower in low_cost_countries:
        price_multiplier = 1.0
    
    base_budget = int(1500 * price_multiplier)
    base_moderate = int(4000 * price_multiplier)
    base_premium = int(8000 * price_multiplier)
    base_luxury = int(15000 * price_multiplier)
    
    # Determine ideal stay types based on interests
    stay_theme = "general"
    if "wildlife" in interests:
        stay_theme = "wildlife"
    elif "beaches" in interests:
        stay_theme = "beach"
    elif "adventure" in interests:
        stay_theme = "adventure"
    elif "heritage" in interests:
        stay_theme = "heritage"
    elif "wellness" in interests:
        stay_theme = "wellness"
    
    theme_descriptions = {
        "wildlife": {
            "budget": f"Forest Guest House near {dest_name}",
            "moderate": f"Wildlife Eco-Lodge with Safari Access in {dest_name}",
            "premium": f"Luxury Tented Safari Camp in {dest_name}",
            "luxury": f"Private Game Reserve Villa in {dest_name}",
            "locations_budget": ["Near park entrance gate", "Local village area"],
            "locations_mod": ["Inside buffer zone", "Overlooking river/waterhole"],
            "locations_prem": ["Inside national park perimeter", "Elevated jungle view"],
            "locations_lux": ["Private conservancy", "Exclusive wilderness estate"],
        },
        "beach": {
            "budget": f"Beachside Hostel & Shack Stay in {dest_name}",
            "moderate": f"Boutique Coastal Resort in {dest_name}",
            "premium": f"Oceanfront Villa with Pool in {dest_name}",
            "luxury": f"Private Beach Resort & Spa in {dest_name}",
            "locations_budget": ["Near main beach strip", "Backpacker quarter"],
            "locations_mod": ["Quiet beach cove", "Coastal promenade area"],
            "locations_prem": ["Private beachfront", "Cliffside ocean view"],
            "locations_lux": ["Secluded private beach", "Island resort"],
        },
        "heritage": {
            "budget": f"Old City Guest House in {dest_name}",
            "moderate": f"Heritage Boutique Hotel in {dest_name}",
            "premium": f"Restored Palace Hotel in {dest_name}",
            "luxury": f"Royal Heritage Suite & Spa in {dest_name}",
            "locations_budget": ["Near old town market", "Walking distance to monuments"],
            "locations_mod": ["Historic quarter", "Near main palace/fort"],
            "locations_prem": ["Converted heritage mansion", "City center landmark area"],
            "locations_lux": ["Former royal estate", "Exclusive heritage wing"],
        },
        "adventure": {
            "budget": f"Mountain Hostel & Base Camp in {dest_name}",
            "moderate": f"Adventure Lodge & Chalet in {dest_name}",
            "premium": f"Premium Mountain Resort in {dest_name}",
            "luxury": f"Luxury Alpine Retreat in {dest_name}",
            "locations_budget": ["Trekking trailhead area", "Activity center zone"],
            "locations_mod": ["Valley viewpoint", "River/lakeside"],
            "locations_prem": ["Mountain ridge resort", "Scenic valley estate"],
            "locations_lux": ["Private mountain estate", "Helipad-accessible resort"],
        },
        "wellness": {
            "budget": f"Yoga Ashram & Guest House in {dest_name}",
            "moderate": f"Wellness Retreat & Spa Hotel in {dest_name}",
            "premium": f"Ayurvedic Spa Resort in {dest_name}",
            "luxury": f"Holistic Luxury Wellness Estate in {dest_name}",
            "locations_budget": ["Ashram district", "Near yoga centers"],
            "locations_mod": ["Peaceful countryside", "Garden setting"],
            "locations_prem": ["Secluded spa estate", "Forest retreat"],
            "locations_lux": ["Private wellness villa", "Exclusive resort"],
        },
        "general": {
            "budget": f"Central Budget Hotel & Hostel in {dest_name}",
            "moderate": f"Boutique City Hotel in {dest_name}",
            "premium": f"Premium Hotel & Suites in {dest_name}",
            "luxury": f"Luxury Five-Star Hotel in {dest_name}",
            "locations_budget": ["City center", "Near transit hub"],
            "locations_mod": ["Prime neighborhood", "Near key attractions"],
            "locations_prem": ["Upscale district", "Waterfront / scenic area"],
            "locations_lux": ["Landmark property", "Exclusive address"],
        }
    }
    
    theme = theme_descriptions.get(stay_theme, theme_descriptions["general"])
    
    lodgings = [
        {
            "category": theme["budget"],
            "tier": "Budget",
            "ideal_for": "solo travelers & backpackers",
            "expected_nightly_rate": f"₹{base_budget:,} - ₹{int(base_budget * 1.8):,} / night",
            "suggested_locations": theme["locations_budget"],
            "features": ["Free WiFi", "Common lounge area", "Tour desk", "Breakfast available"],
            "why_recommended": f"Most affordable option for {dest_name} while staying close to key attractions."
        },
        {
            "category": theme["moderate"],
            "tier": "Moderate",
            "ideal_for": f"{traveler_type} travelers",
            "expected_nightly_rate": f"₹{base_moderate:,} - ₹{int(base_moderate * 1.8):,} / night",
            "suggested_locations": theme["locations_mod"],
            "features": ["Ensuite bathroom", "Restaurant on-site", "Daily housekeeping", "Concierge service"],
            "why_recommended": f"Best value for {traveler_type} travelers with comfort and convenience at {dest_name}."
        },
        {
            "category": theme["premium"],
            "tier": "Premium",
            "ideal_for": "couples & families",
            "expected_nightly_rate": f"₹{base_premium:,} - ₹{int(base_premium * 1.8):,} / night",
            "suggested_locations": theme["locations_prem"],
            "features": ["Swimming pool", "Spa access", "Room service", "Private balcony", "Airport transfers"],
            "why_recommended": f"Elevated comfort with premium amenities and prime location in {dest_name}."
        },
        {
            "category": theme["luxury"],
            "tier": "Luxury",
            "ideal_for": "luxury seekers & honeymooners",
            "expected_nightly_rate": f"₹{base_luxury:,} - ₹{int(base_luxury * 1.8):,} / night",
            "suggested_locations": theme["locations_lux"],
            "features": ["Butler service", "Private pool/jacuzzi", "Fine dining", "Exclusive experiences", "Limousine transfers"],
            "why_recommended": f"Ultimate luxury experience in {dest_name} with world-class amenities and service."
        }
    ]
    
    return {
        "recommended_lodging_options": lodgings,
        "area_guide": f"In {dest_name}, the best areas to stay depend on your priorities. Budget travelers should stay near transit hubs for easy access. Mid-range travelers benefit from neighborhoods near primary attractions. Premium travelers should look for properties with scenic views or historical character.",
        "booking_tips": [
            f"Peak season in {dest_name} requires booking 4-6 weeks in advance.",
            "Compare prices on multiple platforms — direct booking often offers better cancellation policies.",
            "Check if breakfast and airport transfers are included in the rate."
        ]
    }


def find_accommodations(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any],
    use_model: bool = True,
) -> Dict[str, Any]:
    """
    Agent 5 (Accommodation Finder): Generates dynamic, LLM-powered lodging recommendations
    tailored to the specific destination, budget, and traveler profile.
    """
    with log_agent_execution("accommodation_finder"):
        dest_name = destination_info.get("primary_recommendation", "Goa")
        travel_style = preferences.get("travel_style", "moderate")
        traveler_type = preferences.get("traveler_type", "friends")
        interests = preferences.get("interests", [])
        duration = int(preferences.get("duration_days", 5) or 5)
        
        # Extract country
        dest_list = destination_info.get("recommended_destinations", [])
        country = "India"
        for d in dest_list:
            if d.get("destination", "").lower() == dest_name.lower():
                country = d.get("country", "India")
                break
        
        # Accommodation budget from budget analyst
        allocated_stay_budget = budget_info.get("breakdown", {}).get("accommodation", 15000)
        nightly_budget = round(allocated_stay_budget / max(1, duration - 1)) if duration > 1 else allocated_stay_budget

        def fallback_handler():
            return fallback_accommodation_finder(dest_name, country, duration, nightly_budget, travel_style, traveler_type, interests)

        if not use_model:
            result = fallback_handler()
        else:
            gemini_prompt = (
                f"Destination: {dest_name}, {country}\n"
                f"Trip Duration: {duration} days / {duration - 1} nights\n"
                f"Traveler Type: {traveler_type}\n"
                f"Travel Style: {travel_style}\n"
                f"Interests: {interests}\n"
                f"Nightly Budget Target: ₹{nightly_budget:,}\n"
                f"Total Accommodation Budget: ₹{allocated_stay_budget:,}\n\n"
                f"Generate 3-4 realistic accommodation options at different price tiers "
                f"(budget, moderate, premium, luxury) specifically for {dest_name}, {country}. "
                f"Include specific neighborhoods/areas to stay in, realistic nightly rates, "
                f"and features relevant for {traveler_type} travelers interested in {', '.join(interests)}. "
                f"Consider the local hospitality landscape and typical accommodation types available in {dest_name}."
            )
            result = gemini_client.generate_json(
                prompt=gemini_prompt,
                system_instruction=ACCOMMODATION_PROMPT,
                fallback_handler=fallback_handler
            )
            if "recommended_lodging_options" not in result or not result["recommended_lodging_options"]:
                result = fallback_handler()
            elif text_mentions_other_city(json.dumps(result), dest_name):
                result = fallback_handler()

        # Enrich with budget metadata
        result["destination"] = dest_name
        result["allocated_stay_budget"] = allocated_stay_budget
        result["target_nightly_budget"] = nightly_budget
        if "strategic_positioning_advice" not in result:
            result["strategic_positioning_advice"] = f"For {duration} days with {traveler_type} in {dest_name}, staying near primary activity hubs reduces local transit costs by up to 25%."
        if "data_grounding_note" not in result:
            result["data_grounding_note"] = "Lodging recommendations are generated dynamically based on destination characteristics, traveler profile, and Dataset 485 patterns."

        return result
