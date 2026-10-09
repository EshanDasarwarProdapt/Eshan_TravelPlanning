import React from 'react';
import { Compass, Home, Star, MapPin, Tag, ShieldCheck, Check } from 'lucide-react';
import { ActivityItem, AccommodationInfo } from '../types';

interface ActivitiesLodgingSectionProps {
  activities: ActivityItem[];
  accommodations: AccommodationInfo;
}

export const ActivitiesLodgingSection: React.FC<ActivitiesLodgingSectionProps> = ({
  activities,
  accommodations
}) => {
  return (
    <section className="py-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Activities Column */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
              Agent 04 · Activity Recommender
            </span>
            <h2 className="font-display text-2xl font-bold text-ink-900">
              Curated Experiences
            </h2>
          </div>
          <span className="text-xs font-mono text-ink-400">
            Ranked by Preference Match
          </span>
        </div>

        <div className="space-y-3">
          {activities.map((act, idx) => (
            <div
              key={idx}
              className="bg-paper-50 rounded-lg border border-paper-300 p-4 hover:border-ink-900/30 transition-all text-left"
            >
              <div className="flex items-start justify-between gap-2 mb-1.5">
                <h3 className="font-semibold text-ink-900 text-sm">{act.name}</h3>
                <span className="text-xs font-mono font-bold text-accent bg-accent-light px-2 py-0.5 rounded">
                  {act.match_score}% Match
                </span>
              </div>

              <p className="text-xs text-ink-600 font-serif mb-3 leading-relaxed">
                {act.why_recommended}
              </p>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-paper-200 text-[11px] font-mono text-ink-500">
                <div className="flex items-center space-x-3">
                  {act.rating > 0 && (
                    <span className="flex items-center text-amber-700">
                      <Star className="w-3 h-3 fill-amber-500 text-amber-500 mr-1" />
                      {act.rating}/5.0
                    </span>
                  )}
                  <span className="capitalize bg-paper-200 px-1.5 py-0.5 rounded text-ink-700">
                    {act.category}
                  </span>
                  <span>{act.time_slot}</span>
                </div>
                <span className="font-semibold text-ink-900">
                  ₹{act.estimated_cost.toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lodging & Accommodation Column */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
              Agent 05 · Accommodation Finder
            </span>
            <h2 className="font-display text-2xl font-bold text-ink-900">
              Lodging & Neighborhood Strategy
            </h2>
          </div>
          <span className="text-xs font-mono text-ink-400">
            Target: ₹{accommodations.target_nightly_budget?.toLocaleString()}/night
          </span>
        </div>

        <div className="space-y-4">
          {/* Strategic Advice Card */}
          <div className="bg-paper-200/60 rounded-lg p-4 border border-paper-300">
            <span className="text-[10px] font-mono uppercase tracking-wider text-ink-500 block mb-1 font-semibold">
              Strategic Neighborhood Positioning:
            </span>
            <p className="text-xs text-ink-800 font-serif leading-relaxed">
              {accommodations.strategic_positioning_advice}
            </p>
          </div>

          {/* Lodging Tiers */}
          {accommodations.recommended_lodging_options?.map((tier, idx) => (
            <div
              key={idx}
              className="bg-paper-50 rounded-lg border border-paper-300 p-4 text-left"
            >
              <div className="flex items-start justify-between mb-1">
                <div>
                  <span className="text-[10px] font-mono uppercase text-accent font-semibold block">
                    {tier.tier}
                  </span>
                  <h3 className="font-semibold text-ink-900 text-sm">{tier.category}</h3>
                </div>
                <span className="text-xs font-mono text-ink-700 font-medium bg-paper-200 px-2 py-0.5 rounded">
                  {tier.expected_nightly_rate}
                </span>
              </div>

              <div className="text-[11px] text-ink-500 mb-2">
                Ideal for: <span className="text-ink-800 capitalize font-medium">{tier.ideal_for}</span>
              </div>

              <div className="space-y-1 mb-3">
                {tier.features?.map((f, fIdx) => (
                  <div key={fIdx} className="flex items-center space-x-1.5 text-xs text-ink-700">
                    <Check className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                    <span>{f}</span>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-paper-200 flex items-center space-x-1 text-[11px] text-ink-500">
                <MapPin className="w-3 h-3 text-ink-400" />
                <span>Prime Hubs: {tier.suggested_locations?.join(', ')}</span>
              </div>
            </div>
          ))}

          {/* Data Grounding Notice */}
          <div className="p-3 rounded border border-dashed border-paper-400 bg-paper-100 text-[11px] text-ink-500">
            <span className="font-semibold text-ink-700">Transparency Note: </span>
            {accommodations.data_grounding_note}
          </div>
        </div>
      </div>
    </section>
  );
};
