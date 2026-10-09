from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from src.utils.guardrails import validate_and_sanitize_input
from src.agents.preference_classifier import classify_preferences
from src.agents.destination_analyzer import analyze_destinations
from src.agents.budget_analyst import calculate_budget_feasibility
from src.agents.activity_recommender import recommend_activities
from src.agents.accommodation_finder import find_accommodations
from src.agents.flight_finder import find_flights
from src.agents.itinerary_planner import plan_itinerary
from src.agents.quality_validator import evaluate_plan_quality
from src.agents.stay_plan import compose_stay_plan
from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger("workflow")

class TravelPlanningState(TypedDict):
    user_query: str
    sanitized_query: str
    guardrail_status: Dict[str, Any]
    preferences: Dict[str, Any]
    retrieved_documents: List[Dict[str, Any]]
    destinations: Dict[str, Any]
    budget_analysis: Dict[str, Any]
    activities: Dict[str, Any]
    accommodations: Dict[str, Any]
    flights: Dict[str, Any]
    itinerary: Dict[str, Any]
    validation: Dict[str, Any]
    prepared_lodging: Optional[Dict[str, Any]]
    prepared_itinerary: Optional[Dict[str, Any]]
    refinement_count: int
    refinement_feedback: str
    agent_traces: List[Dict[str, Any]]
    errors: List[str]


# Node Functions
def node_input_guardrails(state: TravelPlanningState) -> Dict[str, Any]:
    query = state["user_query"]
    check = validate_and_sanitize_input(query)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Input Guardrails",
        "status": "passed" if check.is_valid else "failed",
        "detail": f"Sanitized query length: {len(check.sanitized_query)} chars. Warnings: {len(check.warnings)}"
    })
    
    return {
        "sanitized_query": check.sanitized_query,
        "guardrail_status": {
            "is_valid": check.is_valid,
            "errors": check.errors,
            "warnings": check.warnings,
            "metadata": check.metadata
        },
        "agent_traces": traces,
        "errors": check.errors
    }


def node_preference_classifier(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    query = state["sanitized_query"]
    prefs = classify_preferences(query)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Preference Classifier",
        "status": "completed",
        "detail": f"Extracted {len(prefs.get('interests', []))} interests, {prefs.get('duration_days', 5)} days, budget: {prefs.get('budget', 'unspecified')}"
    })
    return {"preferences": prefs, "agent_traces": traces}


def node_destination_analyzer(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    query = state["sanitized_query"]
    prefs = state["preferences"]
    dest_res = analyze_destinations(query, prefs)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Destination Analyzer",
        "status": "completed",
        "detail": f"Compared candidates. Primary recommendation: {dest_res.get('primary_recommendation')} ({dest_res.get('recommended_destinations', [{}])[0].get('match_score', 90)}% match)"
    })
    return {
        "destinations": dest_res,
        "retrieved_documents": dest_res.get("retrieved_evidence", []),
        "agent_traces": traces
    }


def node_budget_analyst(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dests = state["destinations"]
    dest = dict((dests.get("recommended_destinations") or [{}])[0] or {})
    if dests.get("primary_recommendation"):
        dest["destination"] = dests["primary_recommendation"]
    budget_res = calculate_budget_feasibility(prefs, dest)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Budget Analyst",
        "status": "completed",
        "detail": f"Status: {budget_res.get('feasibility_status')}. Est Total: ₹{budget_res.get('estimated_total'):,} (Confidence: {int(budget_res.get('confidence', 0.8)*100)}%)"
    })
    return {"budget_analysis": budget_res, "agent_traces": traces}


def node_activity_recommender(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dest_info = state["destinations"]
    budget_info = state["budget_analysis"]
    draft = compose_stay_plan(prefs, dest_info, budget_info)
    activities_res = draft.get("activities") or recommend_activities(prefs, dest_info, budget_info, use_model=False)

    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Activity Recommender",
        "status": "completed",
        "detail": f"Ranked {len(activities_res.get('recommended_activities', []))} curated activities aligned with {prefs.get('interests')}"
    })
    return {
        "activities": activities_res,
        "prepared_lodging": draft.get("accommodations") or {},
        "prepared_itinerary": draft.get("itinerary") or {},
        "agent_traces": traces,
    }


def node_accommodation_finder(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dest_info = state["destinations"]
    budget_info = state["budget_analysis"]
    prepared = state.get("prepared_lodging")
    if prepared:
        accom_res = prepared
    elif isinstance(prepared, dict):
        accom_res = find_accommodations(prefs, dest_info, budget_info, use_model=False)
    else:
        accom_res = find_accommodations(prefs, dest_info, budget_info)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Accommodation Finder",
        "status": "completed",
        "detail": f"Positioned {len(accom_res.get('recommended_lodging_options', []))} lodging tiers within ₹{budget_info.get('breakdown', {}).get('accommodation', 0):,} stay allocation"
    })
    return {"accommodations": accom_res, "agent_traces": traces}


def node_flight_finder(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dest_info = state["destinations"]
    budget_info = state["budget_analysis"]
    flight_res = find_flights(prefs, dest_info, budget_info)
    
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Flight Finder",
        "status": "completed",
        "detail": f"Found {len(flight_res.get('flight_options', []))} flight options across budget/standard/premium tiers"
    })
    return {"flights": flight_res, "agent_traces": traces}


def node_itinerary_planner(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dest_info = state["destinations"]
    budget_info = state["budget_analysis"]
    activities_info = state["activities"]
    accom_info = state["accommodations"]
    refinement = state.get("refinement_feedback", "")
    prepared = state.get("prepared_itinerary")

    if refinement:
        itin_res = plan_itinerary(
            preferences=prefs,
            destination_info=dest_info,
            budget_info=budget_info,
            activities_info=activities_info,
            accommodation_info=accom_info,
            refinement_feedback=refinement
        )
    elif prepared:
        itin_res = prepared
    elif isinstance(prepared, dict):
        itin_res = plan_itinerary(
            preferences=prefs,
            destination_info=dest_info,
            budget_info=budget_info,
            activities_info=activities_info,
            accommodation_info=accom_info,
            use_model=False,
        )
    else:
        itin_res = plan_itinerary(
            preferences=prefs,
            destination_info=dest_info,
            budget_info=budget_info,
            activities_info=activities_info,
            accommodation_info=accom_info,
            refinement_feedback=refinement
        )
    
    traces = list(state.get("agent_traces", []))
    refine_count = state.get("refinement_count", 0)
    traces.append({
        "agent": "Itinerary Planner",
        "status": "completed",
        "detail": f"Generated {len(itin_res.get('daily_itinerary', []))}-day chronological plan (Iteration {refine_count + 1})"
    })
    return {"itinerary": itin_res, "agent_traces": traces}


def node_quality_validator(state: TravelPlanningState) -> Dict[str, Any]:
    if state.get("errors"):
        return {}
    prefs = state["preferences"]
    dest_info = state["destinations"]
    budget_info = state["budget_analysis"]
    act_info = state["activities"]
    itin_info = state["itinerary"]
    
    val_res = evaluate_plan_quality(
        preferences=prefs,
        destination_info=dest_info,
        budget_info=budget_info,
        activities_info=act_info,
        itinerary_info=itin_info
    )
    
    refinement_feedback = ""
    if not val_res.get("approved", True) and val_res.get("issues"):
        refinement_feedback = " ; ".join(val_res["issues"])
        
    traces = list(state.get("agent_traces", []))
    traces.append({
        "agent": "Quality Validator",
        "status": "completed",
        "detail": f"Overall Quality Score: {int(val_res.get('quality_score', 0.9)*100)}% | Approved: {val_res.get('approved')}"
    })
    return {
        "validation": val_res,
        "refinement_count": state.get("refinement_count", 0) + 1,
        "refinement_feedback": refinement_feedback,
        "agent_traces": traces
    }


def should_continue(state: TravelPlanningState) -> str:
    """Conditional Edge routing logic."""
    if state.get("errors"):
        return END
        
    val = state.get("validation", {})
    approved = val.get("approved", True)
    refinement_count = state.get("refinement_count", 0)
    
    if approved or refinement_count >= settings.MAX_REFINEMENT_LOOPS:
        logger.info(f"LangGraph Workflow completed successfully with score {val.get('quality_score')}")
        return END
    else:
        logger.info(f"Quality score {val.get('quality_score')} below threshold. Routing back to Itinerary Planner (Refinement loop {refinement_count})...")
        return "itinerary_planner"


# Build the Graph
def build_travel_planning_graph():
    builder = StateGraph(TravelPlanningState)
    
    # Add Nodes (8 Agents + Guardrails)
    builder.add_node("input_guardrails", node_input_guardrails)
    builder.add_node("preference_classifier", node_preference_classifier)
    builder.add_node("destination_analyzer", node_destination_analyzer)
    builder.add_node("budget_analyst", node_budget_analyst)
    builder.add_node("activity_recommender", node_activity_recommender)
    builder.add_node("accommodation_finder", node_accommodation_finder)
    builder.add_node("flight_finder", node_flight_finder)
    builder.add_node("itinerary_planner", node_itinerary_planner)
    builder.add_node("quality_validator", node_quality_validator)
    
    # Set Entry Point
    builder.set_entry_point("input_guardrails")
    
    # Linear Edges (8-agent pipeline)
    builder.add_edge("input_guardrails", "preference_classifier")
    builder.add_edge("preference_classifier", "destination_analyzer")
    builder.add_edge("destination_analyzer", "budget_analyst")
    builder.add_edge("budget_analyst", "activity_recommender")
    builder.add_edge("activity_recommender", "accommodation_finder")
    builder.add_edge("accommodation_finder", "flight_finder")
    builder.add_edge("flight_finder", "itinerary_planner")
    builder.add_edge("itinerary_planner", "quality_validator")
    
    # Conditional Edge from Quality Validator
    builder.add_conditional_edges(
        "quality_validator",
        should_continue,
        {
            END: END,
            "itinerary_planner": "itinerary_planner"
        }
    )
    
    return builder.compile()


travel_graph = build_travel_planning_graph()
