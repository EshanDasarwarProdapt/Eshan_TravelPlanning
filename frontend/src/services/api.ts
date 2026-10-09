import { BuiltTrip, ExploreCatalog, ExploreRecommendation, PlanTripResponse, TripOptions } from '../types';

const API_BASE = '';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Backend health check failed');
  return res.json();
}

export async function planTrip(query: string, destinationOverride?: string, budgetOverride?: number, durationOverride?: number): Promise<PlanTripResponse> {
  const payload: any = { query };
  if (destinationOverride) payload.destination_override = destinationOverride;
  if (budgetOverride) payload.budget_override = budgetOverride;
  if (durationOverride) payload.duration_override = durationOverride;

  const res = await fetch(`${API_BASE}/api/v1/plan-trip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${res.status}`);
  }

  return res.json();
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export async function fetchExplore(): Promise<ExploreCatalog> {
  const res = await fetch(`${API_BASE}/api/v1/explore`);
  if (!res.ok) throw new Error('Could not load destination experiences.');
  return res.json();
}

export async function recommendExperiences(preferences: string, budget?: number): Promise<ExploreRecommendation> {
  const res = await fetch(`${API_BASE}/api/v1/explore/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ preferences, budget: budget || null }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${res.status}`);
  }
  return res.json();
}

export async function fetchTripOptions(destination: string, origin: string): Promise<TripOptions> {
  const res = await fetch(`${API_BASE}/api/v1/trip-options`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ destination, origin }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${res.status}`);
  }
  return res.json();
}

export async function buildTrip(input: {
  destination: string;
  origin: string;
  transport_mode: string;
  hotel_name: string;
  trip_days: number;
  travelers: number;
  stay_days: number;
  preferences: string;
}): Promise<BuiltTrip> {
  const res = await fetch(`${API_BASE}/api/v1/build-trip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${res.status}`);
  }
  return res.json();
}

export async function sendChat(message: string, history: ChatTurn[]): Promise<string> {
  const res = await fetch(`${API_BASE}/api/v1/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server responded with status ${res.status}`);
  }
  const data = await res.json();
  return data.reply as string;
}
