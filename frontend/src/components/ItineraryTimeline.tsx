import React, { useState } from 'react';
import { Calendar, Sun, CloudSun, Moon, Compass, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { ItineraryInfo } from '../types';

interface ItineraryTimelineProps {
  itinerary: ItineraryInfo;
}

export const ItineraryTimeline: React.FC<ItineraryTimelineProps> = ({ itinerary }) => {
  const [expandedDays, setExpandedDays] = useState<Record<number, boolean>>({ 1: true, 2: true });

  const toggleDay = (dayNum: number) => {
    setExpandedDays((prev) => ({ ...prev, [dayNum]: !prev[dayNum] }));
  };

  const expandAll = () => {
    const all: Record<number, boolean> = {};
    itinerary.daily_itinerary.forEach((d) => (all[d.day_number] = true));
    setExpandedDays(all);
  };

  const collapseAll = () => {
    setExpandedDays({});
  };

  return (
    <section className="py-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
            Agent 06 · Itinerary Planner
          </span>
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-ink-900">
            Day-by-Day Chronological Itinerary
          </h2>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono">
          <button
            onClick={expandAll}
            className="px-3 py-1 bg-paper-200 hover:bg-paper-300 text-ink-800 rounded transition-colors"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1 bg-paper-200 hover:bg-paper-300 text-ink-800 rounded transition-colors"
          >
            Collapse All
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {itinerary.daily_itinerary?.map((day) => {
          const isExpanded = expandedDays[day.day_number] ?? true;

          return (
            <div
              key={day.day_number}
              className="bg-paper-50 rounded-lg border border-paper-300 overflow-hidden shadow-subtle text-left transition-all"
            >
              {/* Day Header */}
              <div
                onClick={() => toggleDay(day.day_number)}
                className="cursor-pointer p-4 sm:p-5 flex items-center justify-between bg-paper-50 hover:bg-paper-100 transition-colors border-b border-paper-200"
              >
                <div className="flex items-center space-x-3 sm:space-x-4">
                  <div className="w-10 h-10 rounded bg-ink-900 text-paper-50 font-display text-lg font-bold flex items-center justify-center flex-shrink-0">
                    {day.day_number < 10 ? `0${day.day_number}` : day.day_number}
                  </div>
                  <div>
                    <span className="text-xs font-mono text-accent font-semibold uppercase tracking-wider">
                      Day {day.day_number}
                    </span>
                    <h3 className="text-base sm:text-lg font-bold text-ink-900">{day.theme}</h3>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <span className="hidden sm:inline-block text-xs font-mono text-ink-500">
                    Est: ₹{day.day_budget_estimate?.toLocaleString()}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-ink-500" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-ink-500" />
                  )}
                </div>
              </div>

              {/* Day Body (Morning, Afternoon, Evening) */}
              {isExpanded && (
                <div className="p-5 grid grid-cols-1 md:grid-cols-3 gap-4 bg-paper-50/60">
                  {/* Morning */}
                  <div className="bg-paper-100/70 rounded p-4 border border-paper-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center space-x-1.5 text-xs font-mono uppercase text-amber-800 font-semibold mb-2">
                        <Sun className="w-3.5 h-3.5 text-amber-600" />
                        <span>Morning</span>
                      </div>
                      <p className="text-xs sm:text-sm font-serif text-ink-900 font-medium mb-3">
                        {day.morning?.activity}
                      </p>
                    </div>
                    <div className="pt-3 border-t border-paper-200/80 text-[11px] text-ink-500">
                      <span className="block font-mono text-ink-400 uppercase text-[9px]">Logistics & Transit</span>
                      <span>{day.morning?.logistics}</span>
                    </div>
                  </div>

                  {/* Afternoon */}
                  <div className="bg-paper-100/70 rounded p-4 border border-paper-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center space-x-1.5 text-xs font-mono uppercase text-amber-700 font-semibold mb-2">
                        <CloudSun className="w-3.5 h-3.5 text-amber-600" />
                        <span>Afternoon</span>
                      </div>
                      <p className="text-xs sm:text-sm font-serif text-ink-900 font-medium mb-3">
                        {day.afternoon?.activity}
                      </p>
                    </div>
                    <div className="pt-3 border-t border-paper-200/80 text-[11px] text-ink-500">
                      <span className="block font-mono text-ink-400 uppercase text-[9px]">Logistics & Transit</span>
                      <span>{day.afternoon?.logistics}</span>
                    </div>
                  </div>

                  {/* Evening */}
                  <div className="bg-paper-100/70 rounded p-4 border border-paper-200 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center space-x-1.5 text-xs font-mono uppercase text-indigo-900 font-semibold mb-2">
                        <Moon className="w-3.5 h-3.5 text-indigo-700" />
                        <span>Evening</span>
                      </div>
                      <p className="text-xs sm:text-sm font-serif text-ink-900 font-medium mb-3">
                        {day.evening?.activity}
                      </p>
                    </div>
                    <div className="pt-3 border-t border-paper-200/80 text-[11px] text-ink-500">
                      <span className="block font-mono text-ink-400 uppercase text-[9px]">Logistics & Dining</span>
                      <span>{day.evening?.logistics}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Logistical Tips Banner */}
      {itinerary.logistical_tips && itinerary.logistical_tips.length > 0 && (
        <div className="mt-6 bg-paper-200/70 rounded-lg p-5 border border-paper-300 text-left">
          <div className="flex items-center space-x-2 text-xs font-mono font-semibold uppercase text-ink-800 mb-2">
            <AlertCircle className="w-4 h-4 text-accent" />
            <span>Local Operational & Transit Guidelines</span>
          </div>
          <ul className="space-y-1.5 text-xs text-ink-700 font-serif">
            {itinerary.logistical_tips.map((tip, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <span className="text-accent font-bold">·</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
};
