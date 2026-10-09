export interface ScoreBreakdown {
  preference_match: number;
  semantic_relevance: number;
  historical_rating: number;
  evidence_strength: number;
  budget_compatibility: number;
}

export interface DestinationRecommendation {
  destination: string;
  country: string;
  match_score: number;
  why_it_matches: string;
  supporting_evidence: string[];
  relevant_categories: string[];
  average_rating: number;
  estimated_daily_cost: number;
  score_breakdown?: ScoreBreakdown;
}

export interface BudgetBreakdown {
  accommodation: number;
  food_and_dining: number;
  activities_and_entry: number;
  local_transport: number;
  contingency_and_misc: number;
  intercity_transport?: number;
}

export interface BudgetAnalysis {
  budget: number | null;
  estimated_total: number;
  remaining_budget: number;
  currency: string;
  duration_days: number;
  feasible: boolean;
  feasibility_status: string;
  confidence: number;
  breakdown: BudgetBreakdown;
  daily_average_per_person: number;
}

export interface ActivityItem {
  name: string;
  category: string;
  rating: number;
  estimated_cost: number;
  time_slot: string;
  match_score: number;
  why_recommended: string;
  evidence_snippet?: string;
}

export interface LodgingOption {
  category: string;
  tier: string;
  ideal_for: string;
  expected_nightly_rate: string;
  suggested_locations: string[];
  features: string[];
  why_recommended?: string;
}

export interface AccommodationInfo {
  destination: string;
  allocated_stay_budget: number;
  target_nightly_budget: number;
  recommended_lodging_options: LodgingOption[];
  strategic_positioning_advice: string;
  data_grounding_note: string;
  area_guide?: string;
  booking_tips?: string[];
}

export interface FlightOption {
  airline: string;
  route: string;
  class?: string;
  price_estimate: number;
  currency: string;
  duration: string;
  stops: string;
  departure_slots: string[];
  baggage?: string;
  tier: string;
  booking_tip?: string;
}

export interface FlightsInfo {
  flight_options: FlightOption[];
  origin_suggestion?: string;
  best_booking_window?: string;
  transit_from_airport?: string;
}

export interface DayActivitySlot {
  activity: string;
  logistics: string;
  recommended_mode?: string;
  mode_reason?: string;
  estimated_cost: number;
}

export interface DayPlan {
  day_number: number;
  theme: string;
  morning: DayActivitySlot;
  afternoon: DayActivitySlot;
  evening: DayActivitySlot;
  day_budget_estimate: number;
}

export interface ItineraryInfo {
  destination: string;
  trip_title: string;
  total_days: number;
  daily_itinerary: DayPlan[];
  logistical_tips: string[];
}

export interface QualityValidation {
  quality_score: number;
  preference_alignment: number;
  budget_feasibility: number;
  itinerary_coherence: number;
  grounding_quality: number;
  issues: string[];
  improvements: string[];
  approved: boolean;
}

export interface AgentTrace {
  agent: string;
  status: string;
  detail: string;
}

export interface PlanTripResponse {
  query: string;
  preferences: {
    duration_days?: number;
    budget?: number | null;
    currency?: string;
    traveler_type?: string;
    interests?: string[];
    destination?: string | null;
    travel_style?: string;
  };
  destinations: DestinationRecommendation[];
  primary_destination: string;
  budget_analysis: BudgetAnalysis;
  activities: ActivityItem[];
  accommodations: AccommodationInfo;
  flights: FlightsInfo;
  itinerary: ItineraryInfo;
  validation: QualityValidation;
  evidence: Array<{
    id: string;
    text: string;
    score: number;
    metadata: Record<string, any>;
  }>;
  agent_traces: AgentTrace[];
  execution_time_ms: number;
}

export interface TransportChoice {
  mode: string;
  label: string;
  route: string;
  duration: string;
  stops: string;
  per_person_price: number;
  duration_minutes: number;
  fastest: boolean;
  booking_tip?: string;
}

export interface HotelChoice {
  name: string;
  tier: string;
  nightly: number;
  area: string;
  features: string[];
}

export interface TripOptions {
  destination: string;
  origin: string;
  local_only: boolean;
  note: string;
  transport: TransportChoice[];
  hotels: HotelChoice[];
}

export interface CostLine {
  label: string;
  amount: number;
  detail: string;
}

export interface BuiltTrip {
  destination: string;
  origin: string;
  hotel_name: string;
  transport_mode: string;
  trip_days: number;
  stay_days: number;
  nights: number;
  travelers: number;
  rooms: number;
  itinerary: ItineraryInfo;
  cost_lines: CostLine[];
  estimated_total: number;
  currency: string;
  note: string;
}

export interface CategoryRating {
  category: string;
  average_rating: number;
  travelers: number;
}

export interface DayOutline {
  day_number: number;
  sightseeing: string;
  food: string;
  stay: string;
}

export interface ExperiencePlan {
  destination: string;
  display_name?: string;
  country: string;
  available: boolean;
  traveler_count: number;
  average_rating?: number | null;
  daily_cost_inr?: number | null;
  days?: number | null;
  trip_cost_inr?: number | null;
  highlights: string[];
  stay_types: string[];
  category_ratings: CategoryRating[];
  outline: DayOutline[];
  best_season?: string | null;
  note: string;
  price_note?: string | null;
}

export interface ThemeGroup {
  id: string;
  title: string;
  places: ExperiencePlan[];
}

export interface ExploreCatalog {
  themes: ThemeGroup[];
  record_count: number;
}

export interface ExperienceMatch {
  destination: string;
  country: string;
  average_rating?: number | null;
  similar_travelers: number;
  daily_cost_inr: number;
  days: number;
  trip_cost_inr: number;
  within_budget: boolean;
  matched_categories: string[];
}

export interface ExploreRecommendation {
  preferences: string;
  matched_categories: string[];
  budget?: number | null;
  summary: string;
  recommended?: ExperienceMatch | null;
  comparison: ExperienceMatch[];
  best_value?: ExperienceMatch | null;
}
