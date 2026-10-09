import React from 'react';
import { MapPin, Calendar, Users, Wallet, CheckCircle, Clock } from 'lucide-react';
import { PlanTripResponse } from '../types';

interface TripSummaryHeaderProps {
  plan: PlanTripResponse;
  onNewPlan: () => void;
}

export const TripSummaryHeader: React.FC<TripSummaryHeaderProps> = ({ plan, onNewPlan }) => {
  const { primary_destination, preferences, budget_analysis, validation, execution_time_ms } = plan;
  
  return (
    <div className="bg-paper-50 border-b border-paper-300 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-ink-500 uppercase tracking-wider mb-2">
            <span>Synthesized Travel Plan</span>
            <span>·</span>
            <span className="flex items-center text-emerald-700">
              <CheckCircle className="w-3.5 h-3.5 mr-1" />
              Verified by 7 Agents
            </span>
            <span>·</span>
            <span className="flex items-center text-ink-400">
              <Clock className="w-3.5 h-3.5 mr-1" />
              {execution_time_ms}ms
            </span>
          </div>

          <h1 className="font-display text-3xl sm:text-4xl text-ink-900 tracking-tight font-bold">
            {plan.itinerary.trip_title || `${primary_destination} Travel Plan`}
          </h1>

          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs">
            <span className="inline-flex items-center px-3 py-1 rounded bg-paper-200 text-ink-900 font-medium">
              <MapPin className="w-3.5 h-3.5 mr-1.5 text-accent" />
              {primary_destination}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded bg-paper-200 text-ink-900 font-medium">
              <Calendar className="w-3.5 h-3.5 mr-1.5 text-ink-500" />
              {preferences.duration_days || 5} Days
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded bg-paper-200 text-ink-900 font-medium capitalize">
              <Users className="w-3.5 h-3.5 mr-1.5 text-ink-500" />
              {preferences.traveler_type || 'Travelers'}
            </span>
            <span className="inline-flex items-center px-3 py-1 rounded bg-paper-200 text-ink-900 font-medium font-mono">
              <Wallet className="w-3.5 h-3.5 mr-1.5 text-ink-500" />
              {preferences.budget ? `Target: ₹${preferences.budget.toLocaleString()}` : `Est: ₹${budget_analysis.estimated_total.toLocaleString()}`}
            </span>
            {preferences.interests && preferences.interests.length > 0 && (
              <span className="inline-flex items-center px-3 py-1 rounded bg-accent-light border border-accent-border text-accent font-medium">
                {preferences.interests.join(' · ')}
              </span>
            )}
          </div>
        </div>

        {/* Action button */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onNewPlan}
            className="px-4 py-2 border border-paper-300 hover:border-ink-900 text-ink-700 hover:text-ink-900 text-xs font-mono rounded bg-paper-50 transition-colors"
          >
            ← Modify / New Query
          </button>
        </div>
      </div>
    </div>
  );
};
