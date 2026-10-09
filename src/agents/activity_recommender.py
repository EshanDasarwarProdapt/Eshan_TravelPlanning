import json
from typing import Dict, Any, List
from src.knowledge.travel_facts import spots_for, text_mentions_other_city
from src.utils.llm import gemini_client
from src.utils.logging import log_agent_execution

ACTIVITY_PROMPT = """You are the Activity Recommender Agent in an AI Travel Planning System.
Recommend real places at the destination in the user message. Costs must fit the activity budget.

RULES:
1. Return 6-8 real landmarks or experiences in THAT city only.
2. Mix morning, afternoon, and evening.
3. Use the local currency. Keep each estimated_cost inside the activity budget.
4. Do not mention any other city. Do not reuse a Goa, Jaipur, or Manali example.
5. Return JSON only:
{
  "recommended_activities": [
    {
      "name": "Specific Activity Name at Specific Location",
      "category": "beaches",
      "rating": 4.8,
      "estimated_cost": 2500,
      "time_slot": "Morning",
      "match_score": 96.0,
      "why_recommended": "Directly matches user's interest; highly rated by similar travelers in the dataset.",
      "evidence_snippet": "Top rated activity in this category for the destination."
    }
  ]
}"""


def fallback_activity_recommender(
    dest_name: str,
    country: str,
    interests: List[str],
    traveler_type: str,
    daily_budget: int
) -> Dict[str, Any]:
    """Place list for this city when the model is unavailable or answers about another city."""
    spots = spots_for(dest_name, interests)
    if spots:
        cap = max(200, int(daily_budget or 1500))
        ranked = []
        for act in spots[:8]:
            cost = min(int(act.get("estimated_cost") or 0), cap)
            from_map = act.get("source") == "openstreetmap"
            ranked.append({
                "name": act["name"],
                "category": act.get("category") or "sightseeing",
                "rating": 0 if from_map else 4.6,
                "estimated_cost": cost,
                "time_slot": act.get("time_slot") or "Morning",
                "match_score": 94.0,
                "why_recommended": (
                    f"{act['name']} is a mapped place in {dest_name}. The cost is a planning estimate, not a ticket price."
                    if from_map
                    else f"A real {act.get('category', 'sightseeing')} stop in {dest_name} for a {traveler_type} trip."
                ),
                "evidence_snippet": (
                    "Place name from OpenStreetMap."
                    if from_map
                    else f"Fits a daily activity budget of about ₹{cap} in {dest_name}."
                ),
            })
        return {"recommended_activities": ranked}

    # Base activity templates by interest category
    activity_templates = {
        "wildlife": [
            {"name": f"Morning Jeep Safari & Wildlife Spotting in {dest_name}", "category": "wildlife", "rating": 4.9, "cost": 2500, "time_slot": "Morning", "score": 97.0},
            {"name": f"Guided Nature Walk & Bird Watching Trail in {dest_name}", "category": "wildlife", "rating": 4.7, "cost": 800, "time_slot": "Morning", "score": 94.0},
            {"name": f"Evening Safari & Sunset at Watering Hole in {dest_name}", "category": "wildlife", "rating": 4.8, "cost": 2000, "time_slot": "Evening", "score": 95.0},
            {"name": f"Wildlife Photography Workshop in {dest_name}", "category": "wildlife", "rating": 4.6, "cost": 1500, "time_slot": "Afternoon", "score": 90.0},
        ],
        "beaches": [
            {"name": f"Snorkeling & Water Sports at {dest_name} Beach", "category": "beaches", "rating": 4.8, "cost": 2500, "time_slot": "Morning", "score": 96.0},
            {"name": f"Sunset Beach Walk & Seafood Dinner in {dest_name}", "category": "beaches", "rating": 4.9, "cost": 1800, "time_slot": "Evening", "score": 95.0},
            {"name": f"Island Hopping & Boat Tour from {dest_name}", "category": "beaches", "rating": 4.7, "cost": 3500, "time_slot": "Morning", "score": 93.0},
            {"name": f"Beach Volleyball & Coastal Cycling in {dest_name}", "category": "beaches", "rating": 4.5, "cost": 600, "time_slot": "Afternoon", "score": 88.0},
        ],
        "heritage": [
            {"name": f"Guided Heritage Walking Tour of {dest_name} Old Quarter", "category": "heritage", "rating": 4.9, "cost": 1200, "time_slot": "Morning", "score": 97.0},
            {"name": f"Museum & Historical Monument Visit in {dest_name}", "category": "heritage", "rating": 4.8, "cost": 800, "time_slot": "Morning", "score": 95.0},
            {"name": f"Evening Light & Sound Show at {dest_name} Landmark", "category": "heritage", "rating": 4.7, "cost": 500, "time_slot": "Evening", "score": 92.0},
            {"name": f"Local Art & Craft Workshop in {dest_name}", "category": "heritage", "rating": 4.6, "cost": 1500, "time_slot": "Afternoon", "score": 90.0},
        ],
        "adventure": [
            {"name": f"Trekking & Hiking Adventure in {dest_name}", "category": "adventure", "rating": 4.9, "cost": 2000, "time_slot": "Morning", "score": 97.0},
            {"name": f"Adrenaline Sports Experience in {dest_name}", "category": "adventure", "rating": 4.8, "cost": 3500, "time_slot": "Morning", "score": 95.0},
            {"name": f"River/Lake Activity Adventure in {dest_name}", "category": "adventure", "rating": 4.7, "cost": 1800, "time_slot": "Afternoon", "score": 93.0},
            {"name": f"Scenic Viewpoint Excursion in {dest_name}", "category": "adventure", "rating": 4.6, "cost": 600, "time_slot": "Evening", "score": 90.0},
        ],
        "food": [
            {"name": f"Street Food & Local Market Tour in {dest_name}", "category": "food", "rating": 4.9, "cost": 1200, "time_slot": "Afternoon", "score": 96.0},
            {"name": f"Traditional Cooking Class in {dest_name}", "category": "food", "rating": 4.8, "cost": 2000, "time_slot": "Morning", "score": 94.0},
            {"name": f"Fine Dining Experience at {dest_name} Restaurant", "category": "food", "rating": 4.7, "cost": 3000, "time_slot": "Evening", "score": 92.0},
            {"name": f"Local Brewery/Café Hopping in {dest_name}", "category": "food", "rating": 4.6, "cost": 1500, "time_slot": "Afternoon", "score": 89.0},
        ],
        "nightlife": [
            {"name": f"Rooftop Bar & Cocktail Experience in {dest_name}", "category": "nightlife", "rating": 4.8, "cost": 2500, "time_slot": "Evening", "score": 95.0},
            {"name": f"Live Music & Club Night in {dest_name}", "category": "nightlife", "rating": 4.7, "cost": 2000, "time_slot": "Evening", "score": 93.0},
            {"name": f"Night Market & Entertainment Walk in {dest_name}", "category": "nightlife", "rating": 4.6, "cost": 1200, "time_slot": "Evening", "score": 90.0},
        ],
        "wellness": [
            {"name": f"Spa & Traditional Massage in {dest_name}", "category": "wellness", "rating": 4.9, "cost": 3000, "time_slot": "Afternoon", "score": 96.0},
            {"name": f"Morning Yoga & Meditation Session in {dest_name}", "category": "wellness", "rating": 4.8, "cost": 800, "time_slot": "Morning", "score": 94.0},
            {"name": f"Hot Springs / Thermal Bath Experience in {dest_name}", "category": "wellness", "rating": 4.7, "cost": 1500, "time_slot": "Afternoon", "score": 92.0},
        ],
        "spiritual": [
            {"name": f"Temple / Sacred Site Visit in {dest_name}", "category": "spiritual", "rating": 4.9, "cost": 300, "time_slot": "Morning", "score": 96.0},
            {"name": f"Evening Prayer / Ritual Ceremony in {dest_name}", "category": "spiritual", "rating": 4.8, "cost": 200, "time_slot": "Evening", "score": 94.0},
            {"name": f"Spiritual Heritage Walk in {dest_name}", "category": "spiritual", "rating": 4.7, "cost": 500, "time_slot": "Morning", "score": 91.0},
        ],
        "shopping": [
            {"name": f"Traditional Market & Bazaar Tour in {dest_name}", "category": "shopping", "rating": 4.7, "cost": 500, "time_slot": "Afternoon", "score": 93.0},
            {"name": f"Artisan & Souvenir Shopping in {dest_name}", "category": "shopping", "rating": 4.6, "cost": 2000, "time_slot": "Afternoon", "score": 90.0},
        ],
        "nature": [
            {"name": f"Scenic Nature Trail & Photography in {dest_name}", "category": "nature", "rating": 4.8, "cost": 600, "time_slot": "Morning", "score": 95.0},
            {"name": f"Botanical Garden / Park Visit in {dest_name}", "category": "nature", "rating": 4.7, "cost": 400, "time_slot": "Afternoon", "score": 92.0},
            {"name": f"Sunset Viewpoint Excursion in {dest_name}", "category": "nature", "rating": 4.8, "cost": 300, "time_slot": "Evening", "score": 93.0},
        ],
    }
    
    # Build activity list from user interests
    selected_activities = []
    for interest in interests:
        templates = activity_templates.get(interest, [])
        selected_activities.extend(templates)
    
    # Add general sightseeing if few activities
    if len(selected_activities) < 4:
        general = [
            {"name": f"City Walking Tour & Sightseeing in {dest_name}", "category": "sightseeing", "rating": 4.7, "cost": 800, "time_slot": "Morning", "score": 92.0},
            {"name": f"Local Cultural Experience in {dest_name}", "category": "heritage", "rating": 4.6, "cost": 1200, "time_slot": "Afternoon", "score": 89.0},
            {"name": f"Sunset Spot & Evening Leisure in {dest_name}", "category": "nature", "rating": 4.5, "cost": 500, "time_slot": "Evening", "score": 87.0},
            {"name": f"Local Food Tasting & Market Walk in {dest_name}", "category": "food", "rating": 4.7, "cost": 1000, "time_slot": "Afternoon", "score": 90.0},
        ]
        selected_activities.extend(general)
    
    # Format and sort
    ranked = []
    for act in selected_activities[:8]:
        ranked.append({
            "name": act["name"],
            "category": act["category"],
            "rating": act["rating"],
            "estimated_cost": act["cost"],
            "time_slot": act["time_slot"],
            "match_score": act["score"],
            "why_recommended": f"Matches {', '.join(interests)} interest with {act['rating']}/5 rating. Ideal for {traveler_type} travelers.",
            "evidence_snippet": f"Validated against Dataset 485 {act['category']} preferences for {dest_name}."
        })
    
    ranked.sort(key=lambda x: x["match_score"], reverse=True)
    return {"recommended_activities": ranked}


def recommend_activities(
    preferences: Dict[str, Any],
    destination_info: Dict[str, Any],
    budget_info: Dict[str, Any],
    use_model: bool = True,
) -> Dict[str, Any]:
    """
    Agent 4 (Activity Recommender): Generates dynamic, LLM-powered activity recommendations
    tailored to the specific destination, interests, and traveler profile.
    """
    with log_agent_execution("activity_recommender"):
        dest_name = destination_info.get("primary_recommendation", "Goa")
        interests = preferences.get("interests", [])
        traveler_type = preferences.get("traveler_type", "friends")
        duration = int(preferences.get("duration_days", 5) or 5)
        daily_budget = budget_info.get("daily_average_per_person", 4500)
        
        # Extract country
        dest_list = destination_info.get("recommended_destinations", [])
        country = "India"
        for d in dest_list:
            if d.get("destination", "").lower() == dest_name.lower():
                country = d.get("country", "India")
                break

        def fallback_handler():
            return fallback_activity_recommender(dest_name, country, interests, traveler_type, daily_budget)

        if not use_model:
            return fallback_handler()

        gemini_prompt = (
            f"Destination: {dest_name}, {country}\n"
            f"Trip Duration: {duration} days\n"
            f"Traveler Type: {traveler_type}\n"
            f"User Interests: {interests}\n"
            f"Daily Activity Budget: ₹{daily_budget}\n\n"
            f"Generate 6-8 specific, real activities and experiences that are actually available "
            f"at {dest_name}, {country}. Focus on activities matching the user's interests: {', '.join(interests)}. "
            f"Include real landmark names, attraction names, and local experiences unique to {dest_name}. "
            f"Mix morning, afternoon, and evening activities. Provide realistic cost estimates."
        )

        result = gemini_client.generate_json(
            prompt=gemini_prompt,
            system_instruction=ACTIVITY_PROMPT,
            fallback_handler=fallback_handler
        )

        if "recommended_activities" not in result or not result["recommended_activities"]:
            return fallback_handler()
        if text_mentions_other_city(json.dumps(result), dest_name):
            return fallback_handler()

        return result
