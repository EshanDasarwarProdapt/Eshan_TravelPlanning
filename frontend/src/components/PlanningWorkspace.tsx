import React, { useState } from 'react';
import { ArrowRight, Sparkles, MapPin, Calendar, Wallet, Users, Compass } from 'lucide-react';

interface PlanningWorkspaceProps {
  onSubmit: (query: string) => void;
  isLoading: boolean;
}

const SAMPLE_PROMPTS = [
  {
    title: "5 Days Goa Coastal & Nightlife",
    query: "I have 5 days and around ₹40,000. I'm travelling with friends and want beaches, good food, nightlife and some adventure.",
    tags: ["5 Days", "₹40,000", "Friends", "Beaches + Nightlife"]
  },
  {
    title: "4 Days Manali Mountain Thrill",
    query: "4 days mountain adventure in Manali with friends for paragliding, river rafting, and scenic trekking under ₹30,000.",
    tags: ["4 Days", "₹30,000", "Friends", "Paragliding + Trekking"]
  },
  {
    title: "7 Days Bali Wellness & Retreat",
    query: "7 days romantic couple trip in Bali with yoga retreats, rice terrace walks, and sunset beach clubs with ₹1,20,000 budget.",
    tags: ["7 Days", "₹1,20,000", "Couple", "Wellness + Ocean"]
  },
  {
    title: "3 Days Jaipur Royal Cultural Heritage",
    query: "3 days family heritage tour in Jaipur exploring royal forts, palace architecture, and traditional Rajasthani dining for ₹35,000.",
    tags: ["3 Days", "₹35,000", "Family", "Forts + Culture"]
  }
];

export const PlanningWorkspace: React.FC<PlanningWorkspaceProps> = ({ onSubmit, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handleSelectSample = (sampleQuery: string) => {
    setQuery(sampleQuery);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 md:py-16">
      {/* Workspace Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-paper-200 border border-paper-300 text-ink-700 text-xs font-mono uppercase tracking-wider mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          <span>Multi-Agent Travel Intelligence Workspace</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl text-ink-900 tracking-tight leading-[1.15] mb-4">
          Where should you travel next?
        </h1>
        <p className="text-ink-500 text-base sm:text-lg max-w-2xl mx-auto font-normal">
          Enter your natural-language travel intent. Our 7-agent LangGraph engine classifies your preferences, evaluates historical evidence from Dataset 485, and builds an itemized, validated itinerary.
        </p>
      </div>

      {/* Input Console Box */}
      <div className="bg-paper-50 rounded-lg border border-paper-300 shadow-card p-4 sm:p-6 mb-8 transition-all focus-within:border-ink-900 focus-within:ring-1 focus-within:ring-ink-900">
        <form onSubmit={handleSubmit}>
          <label htmlFor="travel-query" className="block text-xs font-mono font-medium text-ink-500 uppercase tracking-wider mb-2">
            Natural-Language Travel Requirement
          </label>
          <textarea
            id="travel-query"
            rows={3}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. I have 5 days and ₹40,000 for a trip with friends. Looking for beaches, seafood, nightlife and some scuba diving..."
            className="w-full bg-transparent border-0 resize-none text-ink-900 placeholder:text-ink-400 text-lg sm:text-xl font-serif focus:outline-none leading-relaxed"
            disabled={isLoading}
          />

          <div className="mt-4 pt-4 border-t border-paper-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-4 text-xs font-mono text-ink-500">
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-ink-400" />
                <span>Days</span>
              </span>
              <span className="flex items-center space-x-1">
                <Wallet className="w-3.5 h-3.5 text-ink-400" />
                <span>Budget</span>
              </span>
              <span className="flex items-center space-x-1">
                <Users className="w-3.5 h-3.5 text-ink-400" />
                <span>Group Type</span>
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="inline-flex items-center justify-center space-x-2 bg-ink-900 hover:bg-accent text-paper-50 px-6 py-3 rounded text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-subtle"
            >
              <span>{isLoading ? 'Agents Analyzing...' : 'Generate Plan'}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      </div>

      {/* Preset Curated Prompts */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
            Verified Travel Scenarios (Dataset 485 Grounded)
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {SAMPLE_PROMPTS.map((sample, idx) => (
            <div
              key={idx}
              onClick={() => handleSelectSample(sample.query)}
              className="group cursor-pointer bg-paper-50 hover:bg-paper-200/60 border border-paper-300 rounded p-3.5 transition-all text-left"
            >
              <div className="flex items-center justify-between mb-1.5">
                <h3 className="text-sm font-semibold text-ink-900 group-hover:text-accent transition-colors">
                  {sample.title}
                </h3>
                <span className="text-[11px] font-mono text-ink-400 group-hover:text-ink-700">Select →</span>
              </div>
              <p className="text-xs text-ink-500 line-clamp-2 mb-2 font-serif italic">
                "{sample.query}"
              </p>
              <div className="flex flex-wrap gap-1.5">
                {sample.tags.map((tag, tIdx) => (
                  <span
                    key={tIdx}
                    className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-paper-200 text-ink-700"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
