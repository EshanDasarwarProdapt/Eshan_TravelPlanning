from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# Health
class HealthResponse(BaseModel):
    status: str
    version: str
    database_records_indexed: int
    llm_status: str
    embedding_model: str


# Plan Trip
class PlanTripRequest(BaseModel):
    query: str = Field(..., example="I have 5 days and around ₹40,000. I'm travelling with friends and want beaches, good food, nightlife and some adventure.")
    destination_override: Optional[str] = Field(default=None, example="Goa")
    budget_override: Optional[float] = Field(default=None, example=40000.0)
    duration_override: Optional[int] = Field(default=None, example=5)


class ScoreBreakdown(BaseModel):
    preference_match: float
    semantic_relevance: float
    historical_rating: float
    evidence_strength: float
    budget_compatibility: float


class DestinationRecommendation(BaseModel):
    destination: str
    country: str
    match_score: float
    why_it_matches: str
    supporting_evidence: List[str]
    relevant_categories: List[str]
    average_rating: float
    estimated_daily_cost: int
    score_breakdown: Optional[ScoreBreakdown] = None


class BudgetBreakdown(BaseModel):
    accommodation: int
    food_and_dining: int
    activities_and_entry: int
    local_transport: int
    contingency_and_misc: int
    intercity_transport: int = 0


class BudgetAnalysisResponse(BaseModel):
    budget: Optional[float]
    estimated_total: int
    remaining_budget: float
    currency: str
    duration_days: int
    feasible: bool
    feasibility_status: str
    confidence: float
    breakdown: BudgetBreakdown
    daily_average_per_person: int


class ActivityItem(BaseModel):
    name: str
    category: str
    rating: float
    estimated_cost: int
    time_slot: str
    match_score: float
    why_recommended: str
    evidence_snippet: Optional[str] = None


class LodgingOption(BaseModel):
    category: str
    tier: str
    ideal_for: str
    expected_nightly_rate: str
    suggested_locations: List[str]
    features: List[str]
    why_recommended: Optional[str] = None


class AccommodationResponse(BaseModel):
    destination: str
    allocated_stay_budget: int
    target_nightly_budget: int
    recommended_lodging_options: List[LodgingOption]
    strategic_positioning_advice: str
    data_grounding_note: str
    area_guide: Optional[str] = None
    booking_tips: Optional[List[str]] = None


class FlightOption(BaseModel):
    airline: str
    route: str
    class_: Optional[str] = Field(default=None, alias="class")
    price_estimate: int
    currency: str
    duration: str
    stops: str
    departure_slots: List[str]
    baggage: Optional[str] = None
    tier: str
    booking_tip: Optional[str] = None

    class Config:
        populate_by_name = True


class FlightsResponse(BaseModel):
    flight_options: List[FlightOption]
    origin_suggestion: Optional[str] = None
    best_booking_window: Optional[str] = None
    transit_from_airport: Optional[str] = None


class DayActivitySlot(BaseModel):
    activity: str
    logistics: str
    estimated_cost: int


class DayPlan(BaseModel):
    day_number: int
    theme: str
    morning: DayActivitySlot
    afternoon: DayActivitySlot
    evening: DayActivitySlot
    day_budget_estimate: int


class ItineraryResponse(BaseModel):
    destination: str
    trip_title: str
    total_days: int
    daily_itinerary: List[DayPlan]
    logistical_tips: List[str]


class QualityValidationResponse(BaseModel):
    quality_score: float
    preference_alignment: float
    budget_feasibility: float
    itinerary_coherence: float
    grounding_quality: float
    issues: List[str]
    improvements: List[str]
    approved: bool


class AgentTraceItem(BaseModel):
    agent: str
    status: str
    detail: str


class PlanTripResponse(BaseModel):
    query: str
    preferences: Dict[str, Any]
    destinations: List[DestinationRecommendation]
    primary_destination: str
    budget_analysis: BudgetAnalysisResponse
    activities: List[ActivityItem]
    accommodations: AccommodationResponse
    flights: FlightsResponse
    itinerary: ItineraryResponse
    validation: QualityValidationResponse
    evidence: List[Dict[str, Any]]
    agent_traces: List[AgentTraceItem]
    execution_time_ms: float


# Search
class SearchRequest(BaseModel):
    query: str = Field(..., example="beaches with nightlife and seafood")
    n_results: int = Field(default=10, le=50)
    destination: Optional[str] = None
    category: Optional[str] = None
    travel_type: Optional[str] = None
    min_rating: Optional[float] = None


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[Dict[str, Any]]


# Recommend
class RecommendRequest(BaseModel):
    query: str = Field(..., example="5 days trip with family for heritage and nature")


class RecommendResponse(BaseModel):
    query: str
    preferences: Dict[str, Any]
    destinations: List[DestinationRecommendation]
    primary_destination: str
    reasoning_summary: str


# Itinerary Direct Request
class DirectItineraryRequest(BaseModel):
    destination: str = Field(..., example="Goa")
    duration_days: int = Field(default=5, ge=1, le=30)
    traveler_type: str = Field(default="friends", example="friends")
    budget: Optional[float] = Field(default=40000.0)
    interests: List[str] = Field(default=["beaches", "nightlife"])


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    history: List[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str


class TransportChoice(BaseModel):
    mode: str
    label: str
    route: str
    duration: str
    stops: str
    per_person_price: int
    duration_minutes: int
    fastest: bool = False
    booking_tip: Optional[str] = None


class HotelChoice(BaseModel):
    name: str
    tier: str
    nightly: int
    area: str
    features: List[str]


class TripOptionsRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=80)
    origin: str = Field(..., min_length=2, max_length=80)


class TripOptionsResponse(BaseModel):
    destination: str
    origin: str
    local_only: bool
    note: str
    transport: List[TransportChoice]
    hotels: List[HotelChoice]


class BuildTripRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=80)
    origin: str = Field(..., min_length=2, max_length=80)
    transport_mode: str
    hotel_name: str = Field(..., min_length=2, max_length=120)
    trip_days: int = Field(..., ge=1, le=30)
    travelers: int = Field(..., ge=1, le=20)
    stay_days: int = Field(..., ge=1, le=30)
    preferences: str = Field(default="", max_length=500)


class CostLine(BaseModel):
    label: str
    amount: int
    detail: str


class BuiltTripResponse(BaseModel):
    destination: str
    origin: str
    hotel_name: str
    transport_mode: str
    trip_days: int
    stay_days: int
    nights: int
    travelers: int
    rooms: int
    itinerary: ItineraryResponse
    cost_lines: List[CostLine]
    estimated_total: int
    currency: str = "INR"
    note: str


class CategoryRating(BaseModel):
    category: str
    average_rating: float
    travelers: int


class DayOutline(BaseModel):
    day_number: int
    sightseeing: str
    food: str
    stay: str


class ExperiencePlan(BaseModel):
    destination: str
    display_name: Optional[str] = None
    country: str = ""
    available: bool
    traveler_count: int = 0
    average_rating: Optional[float] = None
    daily_cost_inr: Optional[int] = None
    days: Optional[int] = None
    trip_cost_inr: Optional[int] = None
    highlights: List[str] = Field(default_factory=list)
    stay_types: List[str] = Field(default_factory=list)
    category_ratings: List[CategoryRating] = Field(default_factory=list)
    outline: List[DayOutline] = Field(default_factory=list)
    best_season: Optional[str] = None
    note: str = ""
    price_note: Optional[str] = None


class ThemeGroup(BaseModel):
    id: str
    title: str
    places: List[ExperiencePlan]


class ExploreCatalogResponse(BaseModel):
    themes: List[ThemeGroup]
    record_count: int


class ExploreRecommendRequest(BaseModel):
    preferences: str = Field(..., min_length=2, max_length=400)
    budget: Optional[int] = Field(default=None, ge=0)


class ExperienceMatch(BaseModel):
    destination: str
    country: str
    average_rating: Optional[float] = None
    similar_travelers: int
    daily_cost_inr: int
    days: int
    trip_cost_inr: int
    within_budget: bool
    matched_categories: List[str]


class ExploreRecommendResponse(BaseModel):
    preferences: str
    matched_categories: List[str]
    budget: Optional[int] = None
    summary: str
    recommended: Optional[ExperienceMatch] = None
    comparison: List[ExperienceMatch]
    best_value: Optional[ExperienceMatch] = None
