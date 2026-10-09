import time
from fastapi import APIRouter, HTTPException, Depends
from src.api.schemas import (
    HealthResponse,
    PlanTripRequest,
    PlanTripResponse,
    SearchRequest,
    SearchResponse,
    RecommendRequest,
    RecommendResponse,
    DirectItineraryRequest,
    ItineraryResponse,
    ChatRequest,
    ChatResponse,
    TripOptionsRequest,
    TripOptionsResponse,
    BuildTripRequest,
    BuiltTripResponse,
    ExploreCatalogResponse,
    ExploreRecommendRequest,
    ExploreRecommendResponse,
)
from src.services.langgraph_workflow import travel_graph
from src.services.recommendation_service import recommendation_service
from src.rag.vector_store import vector_store
from src.utils.config import settings
from src.utils.logging import get_logger
from src.agents.itinerary_planner import plan_itinerary
from src.agents.budget_analyst import calculate_budget_feasibility
from src.agents.activity_recommender import recommend_activities
from src.agents.accommodation_finder import find_accommodations
from src.agents.flight_finder import find_flights
from src.utils.llm import gemini_client
from src.services.trip_builder import build_trip, list_trip_options
from src.services.explore_catalog import explore_catalog, recommend_experiences

logger = get_logger("api_routes")
router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System Health & Status")
async def health_check():
    """
    Returns operational status, vector store indexing count, and Gemini connectivity mode.
    """
    count = vector_store.count()
    llm_mode = (
        f"AI Credits ({settings.LLM_MODEL})"
        if settings.LLM_API_KEY
        else "Local Grounded Engine (No Key Set)"
    )
    return HealthResponse(
        status="healthy",
        version=settings.PROJECT_VERSION,
        database_records_indexed=count,
        llm_status=llm_mode,
        embedding_model=settings.EMBEDDING_MODEL_NAME
    )


@router.post("/api/v1/plan-trip", response_model=PlanTripResponse, summary="End-to-End Multi-Agent Trip Planning")
async def plan_trip_endpoint(req: PlanTripRequest):
    """
    Executes the 8-Agent LangGraph workflow:
    Input Guardrails -> Preference Classifier -> Destination Analyzer -> Budget Analyst ->
    Activity Recommender -> Accommodation Finder -> Flight Finder -> Itinerary Planner -> Quality Validator
    (with conditional refinement loop back to Itinerary Planner if needed).
    """
    start_time = time.perf_counter()
    logger.info(f"Incoming trip planning request: {req.query}")

    # Overrides have to be in the query. Applying them after the graph
    # used to change only the summary, while the itinerary stayed on the old city.
    query = req.query
    constraints = []
    if req.destination_override:
        constraints.append(f"The destination is {req.destination_override}.")
    if req.budget_override:
        constraints.append(f"The total budget is {int(req.budget_override)}.")
    if req.duration_override:
        constraints.append(f"The trip is {req.duration_override} days.")
    if constraints:
        query = f"{req.query} {' '.join(constraints)}"

    initial_state = {
        "user_query": query,
        "sanitized_query": "",
        "guardrail_status": {},
        "preferences": {},
        "retrieved_documents": [],
        "destinations": {},
        "budget_analysis": {},
        "activities": {},
        "accommodations": {},
        "flights": {},
        "itinerary": {},
        "validation": {},
        "refinement_count": 0,
        "refinement_feedback": "",
        "agent_traces": [],
        "errors": []
    }
    
    try:
        final_state = travel_graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Multi-Agent Workflow Error: {str(e)}")

    if final_state.get("errors"):
        raise HTTPException(status_code=400, detail=" ; ".join(final_state["errors"]))

    # Apply overrides if provided in request
    prefs = final_state.get("preferences", {})
    if req.destination_override:
        prefs["destination"] = req.destination_override
    if req.budget_override:
        prefs["budget"] = req.budget_override
    if req.duration_override:
        prefs["duration_days"] = req.duration_override

    dests_info = final_state.get("destinations", {})
    dests_list = dests_info.get("recommended_destinations", [])
    primary_dest = dests_info.get("primary_recommendation", dests_list[0]["destination"] if dests_list else "Goa")
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    return PlanTripResponse(
        query=req.query,
        preferences=prefs,
        destinations=dests_list,
        primary_destination=primary_dest,
        budget_analysis=final_state.get("budget_analysis", {}),
        activities=final_state.get("activities", {}).get("recommended_activities", []),
        accommodations=final_state.get("accommodations", {}),
        flights=final_state.get("flights", {}),
        itinerary=final_state.get("itinerary", {}),
        validation=final_state.get("validation", {}),
        evidence=final_state.get("retrieved_documents", []),
        agent_traces=final_state.get("agent_traces", []),
        execution_time_ms=round(elapsed_ms, 2)
    )


@router.post("/api/v1/search", response_model=SearchResponse, summary="Hybrid Travel Experience Search")
async def search_endpoint(req: SearchRequest):
    """
    Direct Hybrid Search combining BM25 keyword matching and ChromaDB semantic similarity with metadata filters.
    """
    results = recommendation_service.search_travel_experiences(
        query=req.query,
        n_results=req.n_results,
        destination=req.destination,
        category=req.category,
        travel_type=req.travel_type,
        min_rating=req.min_rating
    )
    return SearchResponse(
        query=req.query,
        total_matches=len(results),
        results=results
    )


@router.post("/api/v1/recommend", response_model=RecommendResponse, summary="Destination Recommendations")
async def recommend_endpoint(req: RecommendRequest):
    """
    Extracts preferences and evaluates top matching destinations with full score breakdowns.
    """
    rec_data = recommendation_service.get_ranked_recommendations(req.query)
    prefs = rec_data["preferences"]
    
    from src.agents.destination_analyzer import analyze_destinations
    analysis = analyze_destinations(req.query, prefs)
    
    dests = analysis.get("recommended_destinations", [])
    primary = analysis.get("primary_recommendation", dests[0]["destination"] if dests else "Goa")
    
    return RecommendResponse(
        query=req.query,
        preferences=prefs,
        destinations=dests,
        primary_destination=primary,
        reasoning_summary=analysis.get("reasoning_summary", "")
    )


@router.post("/api/v1/itinerary", response_model=ItineraryResponse, summary="Direct Itinerary Generation")
async def itinerary_endpoint(req: DirectItineraryRequest):
    """
    Generates a structured day-by-day itinerary given destination parameters.
    """
    prefs = {
        "destination": req.destination,
        "duration_days": req.duration_days,
        "traveler_type": req.traveler_type,
        "budget": req.budget,
        "interests": req.interests,
        "travel_style": "moderate"
    }
    dest_info = {"primary_recommendation": req.destination, "estimated_daily_cost": 4500}
    budget_info = calculate_budget_feasibility(prefs, dest_info)
    activities_info = recommend_activities(prefs, dest_info, budget_info)
    accom_info = find_accommodations(prefs, dest_info, budget_info)
    
    itin = plan_itinerary(
        preferences=prefs,
        destination_info=dest_info,
        budget_info=budget_info,
        activities_info=activities_info,
        accommodation_info=accom_info
    )
    return itin


CHAT_SYSTEM_PROMPT = """You are Waypoint, a concise travel assistant on a trip-planning site.
Answer only travel questions: destinations, seasons, budgets, flights, trains, buses, hotels, food, sights, packing, visas at a high level, and how to shape a day plan.
If the user asks about anything that is not travel, say you only help with travel and invite a travel question.
Prices and schedules are planning estimates, not live bookings. Say so when you quote a number.
Keep replies short: a few sentences or a short list. Do not invent a full multi-day itinerary unless the user asks for one.
The site's main planner builds the detailed itinerary, so you can suggest they use it for a full day-by-day plan."""


@router.get("/api/v1/explore", response_model=ExploreCatalogResponse, summary="Database-rated destination experiences")
async def explore_catalog_endpoint():
    """5–7 day experiences whose ratings are means of stored traveler scores."""
    return explore_catalog()


@router.post("/api/v1/explore/recommend", response_model=ExploreRecommendResponse, summary="Match similar traveler scores")
async def explore_recommend_endpoint(req: ExploreRecommendRequest):
    """Rank destinations by the scores of travelers with the same preference tags."""
    try:
        return recommend_experiences(req.preferences, req.budget)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/v1/trip-options", response_model=TripOptionsResponse, summary="Ways to get there and hotels")
async def trip_options_endpoint(req: TripOptionsRequest):
    """Fares and hotels for a destination from the traveler's current city. No budget split."""
    try:
        return list_trip_options(req.destination, req.origin)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/v1/build-trip", response_model=BuiltTripResponse, summary="Plan from the traveler's choices")
async def build_trip_endpoint(req: BuildTripRequest):
    """Day plan and an estimated total from the selected route, hotel, party, and stay."""
    try:
        return build_trip(
            destination=req.destination,
            origin=req.origin,
            transport_mode=req.transport_mode,
            hotel_name=req.hotel_name,
            trip_days=req.trip_days,
            travelers=req.travelers,
            stay_days=req.stay_days,
            preferences=req.preferences,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/v1/chat", response_model=ChatResponse, summary="Travel chatbot")
async def chat_endpoint(req: ChatRequest):
    """Short travel Q&A. Does not run the full itinerary workflow."""
    history = []
    for turn in req.history[-8:]:
        role = turn.role if turn.role in {"user", "assistant"} else "user"
        text = turn.content.strip()
        if text:
            history.append({"role": role, "content": text[:1000]})
    history.append({"role": "user", "content": req.message.strip()})

    reply = gemini_client.chat(
        messages=history,
        system_instruction=CHAT_SYSTEM_PROMPT,
        fallback_text="I can't reach the travel assistant right now. Use the planner above for a full itinerary.",
    )
    if not reply or not reply.strip():
        reply = "I couldn't form a reply. Try asking about a city, a budget, or how to get there."
    return ChatResponse(reply=reply.strip())
