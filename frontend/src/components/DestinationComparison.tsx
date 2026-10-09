import React from 'react';
import { Award, Star, CheckCircle, Compass, BarChart2 } from 'lucide-react';
import { DestinationRecommendation } from '../types';

interface DestinationComparisonProps {
  destinations: DestinationRecommendation[];
  primaryDestination: string;
}

export const DestinationComparison: React.FC<DestinationComparisonProps> = ({
  destinations,
  primaryDestination
}) => {
  if (!destinations || destinations.length === 0) return null;

  return (
    <section className="py-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
            Agent 02 · Destination Analysis
          </span>
          <h2 className="font-display text-2xl font-bold text-ink-900">
            Recommended Destinations & Empirical Grounding
          </h2>
        </div>
        <span className="text-xs font-mono text-ink-400">
          Ranked by Multi-Factor Hybrid RAG Scoring
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {destinations.map((dest, idx) => {
          const isPrimary = dest.destination.toLowerCase() === primaryDestination.toLowerCase() || idx === 0;

          return (
            <div
              key={idx}
              className={`rounded-lg border p-5 transition-all text-left flex flex-col justify-between ${
                isPrimary
                  ? 'bg-paper-50 border-ink-900 shadow-card ring-1 ring-ink-900/5'
                  : 'bg-paper-50/70 border-paper-300 hover:border-paper-400'
              }`}
            >
              <div>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-ink-400">0{idx + 1}</span>
                      <h3 className="font-display text-xl font-bold text-ink-900">
                        {dest.destination}
                      </h3>
                    </div>
                    <span className="text-xs text-ink-500 font-medium">{dest.country}</span>
                  </div>

                  {/* Match Score Badge */}
                  <div className="text-right">
                    <div className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-paper-200 text-ink-900 font-mono text-xs font-bold">
                      <Award className="w-3.5 h-3.5 text-accent" />
                      <span>{dest.match_score}%</span>
                    </div>
                    {isPrimary && (
                      <span className="block text-[10px] font-mono text-accent font-semibold mt-0.5">
                        Selected Primary
                      </span>
                    )}
                  </div>
                </div>

                <p className="text-xs text-ink-700 font-serif leading-relaxed mt-3 mb-4">
                  {dest.why_it_matches}
                </p>

                {/* Score Factor Breakdown */}
                {dest.score_breakdown && (
                  <div className="bg-paper-100 rounded p-2.5 mb-4 border border-paper-200 text-[11px] font-mono space-y-1">
                    <div className="flex justify-between text-ink-600">
                      <span>Preference Alignment:</span>
                      <span className="text-ink-900 font-semibold">{Math.round(dest.score_breakdown.preference_match * 100)}%</span>
                    </div>
                    <div className="flex justify-between text-ink-600">
                      <span>Semantic Relevance:</span>
                      <span className="text-ink-900 font-semibold">{Math.round(dest.score_breakdown.semantic_relevance * 100)}%</span>
                    </div>
                    <div className="flex justify-between text-ink-600">
                      <span>Historical Rating:</span>
                      <span className="text-ink-900 font-semibold">{Math.round(dest.score_breakdown.historical_rating * 100)}%</span>
                    </div>
                    <div className="flex justify-between text-ink-600">
                      <span>Budget Compatibility:</span>
                      <span className="text-ink-900 font-semibold">{Math.round(dest.score_breakdown.budget_compatibility * 100)}%</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Grounded Evidence Snippets */}
              <div className="pt-3 border-t border-paper-200">
                <span className="text-[10px] font-mono text-ink-400 uppercase block mb-1.5">
                  Dataset 485 Evidence:
                </span>
                <div className="space-y-1">
                  {dest.supporting_evidence.map((ev, evIdx) => (
                    <div key={evIdx} className="flex items-start space-x-1.5 text-[11px] text-ink-600">
                      <CheckCircle className="w-3 h-3 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <span className="line-clamp-2">{ev}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};
