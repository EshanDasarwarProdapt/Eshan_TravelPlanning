import React, { useState } from 'react';
import { FlightsInfo, FlightOption } from '../types';
import { Plane, Clock, Luggage, ArrowRight, ChevronDown, ChevronUp, Sparkles, Tag } from 'lucide-react';

interface FlightsSectionProps {
  flights: FlightsInfo;
}

const tierColors: Record<string, { bg: string; border: string; badge: string; text: string }> = {
  budget:   { bg: 'bg-emerald-50',  border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800',  text: 'text-emerald-700' },
  standard: { bg: 'bg-blue-50',     border: 'border-blue-200',    badge: 'bg-blue-100 text-blue-800',       text: 'text-blue-700' },
  premium:  { bg: 'bg-amber-50',    border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-800',     text: 'text-amber-700' },
  luxury:   { bg: 'bg-purple-50',   border: 'border-purple-200',  badge: 'bg-purple-100 text-purple-800',   text: 'text-purple-700' },
  flight:   { bg: 'bg-sky-50',      border: 'border-sky-200',     badge: 'bg-sky-100 text-sky-800',         text: 'text-sky-700' },
  train:    { bg: 'bg-emerald-50',  border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800', text: 'text-emerald-700' },
  bus:      { bg: 'bg-amber-50',    border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-800',     text: 'text-amber-700' },
};

function FlightCard({ flight, index }: { flight: FlightOption; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const tier = (flight.tier || 'standard').toLowerCase();
  const colors = tierColors[tier] || tierColors.standard;

  return (
    <div
      className={`rounded-xl border-2 ${colors.border} ${colors.bg} p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-lg ${colors.badge} flex items-center justify-center`}>
            <Plane className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-bold text-ink-900 text-sm">{flight.airline}</h4>
            <p className="text-xs text-ink-500 mt-0.5">{flight.route}</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold ${colors.badge} uppercase tracking-wide`}>
            {tier}
          </span>
        </div>
      </div>

      {/* Price & Key Info */}
      <div className="grid grid-cols-3 gap-3 mb-3">
        <div className="text-center p-2 bg-white/60 rounded-lg">
          <p className="text-xs text-ink-500 font-mono uppercase">Price</p>
          <p className="text-lg font-black text-ink-900">
            ₹{flight.price_estimate?.toLocaleString()}
          </p>
        </div>
        <div className="text-center p-2 bg-white/60 rounded-lg">
          <p className="text-xs text-ink-500 font-mono uppercase">Duration</p>
          <p className="text-sm font-bold text-ink-900 flex items-center justify-center gap-1">
            <Clock className="w-3.5 h-3.5" /> {flight.duration}
          </p>
        </div>
        <div className="text-center p-2 bg-white/60 rounded-lg">
          <p className="text-xs text-ink-500 font-mono uppercase">Stops</p>
          <p className="text-sm font-bold text-ink-900">{flight.stops}</p>
        </div>
      </div>

      {/* Class info */}
      {flight.class && (
        <div className="flex items-center gap-2 mb-2 text-xs text-ink-600">
          <Sparkles className="w-3.5 h-3.5" />
          <span className="font-semibold">Class:</span> {flight.class}
        </div>
      )}

      {/* Expand/Collapse */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`w-full mt-1 py-1.5 text-xs font-semibold ${colors.text} flex items-center justify-center gap-1 hover:underline`}
      >
        {expanded ? 'Less Details' : 'More Details'}
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-2 border-t border-ink-100 pt-3">
          {/* Departure Slots */}
          {flight.departure_slots && flight.departure_slots.length > 0 && (
            <div>
              <p className="text-xs font-bold text-ink-700 mb-1">Departure Slots</p>
              <div className="flex flex-wrap gap-1.5">
                {flight.departure_slots.map((slot, i) => (
                  <span key={i} className="px-2 py-0.5 bg-white rounded text-xs text-ink-700 border border-ink-200">
                    {slot}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Baggage */}
          {flight.baggage && (
            <div className="flex items-center gap-2 text-xs text-ink-600">
              <Luggage className="w-3.5 h-3.5" />
              <span className="font-semibold">Baggage:</span> {flight.baggage}
            </div>
          )}

          {/* Booking Tip */}
          {flight.booking_tip && (
            <div className="flex items-start gap-2 text-xs text-ink-600 bg-white/80 rounded-lg p-2">
              <Tag className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              <span>{flight.booking_tip}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function FlightsSection({ flights }: FlightsSectionProps) {
  if (!flights || !flights.flight_options || flights.flight_options.length === 0) {
    return null;
  }

  return (
    <section className="bg-white rounded-2xl border border-paper-300 shadow-sm overflow-hidden">
      {/* Section Header */}
      <div className="px-6 py-4 bg-gradient-to-r from-sky-50 to-indigo-50 border-b border-paper-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-sky-100 rounded-lg flex items-center justify-center">
              <Plane className="w-5 h-5 text-sky-700" />
            </div>
            <div>
              <h3 className="text-base font-display font-bold text-ink-900">How to Get There</h3>
              <p className="text-xs text-ink-500 mt-0.5">
                {flights.recommended_mode
                  ? `Recommended: ${flights.recommended_mode}`
                  : `${flights.flight_options.length} ways to reach the city`}
              </p>
            </div>
          </div>
          {flights.best_booking_window && (
            <span className="text-xs bg-sky-100 text-sky-800 px-3 py-1 rounded-full font-semibold hidden sm:inline">
              Book: {flights.best_booking_window}
            </span>
          )}
        </div>
      </div>

      {/* Flight Cards */}
      <div className="p-6">
        {flights.mode_reason && (
          <p className="mb-4 text-sm text-ink-700 leading-relaxed">{flights.mode_reason}</p>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {flights.flight_options.map((flight, idx) => (
            <FlightCard key={idx} flight={flight} index={idx} />
          ))}
        </div>

        {/* Bottom Info */}
        <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {flights.origin_suggestion && (
            <div className="bg-paper-50 rounded-lg p-3 border border-paper-200">
              <p className="text-xs font-bold text-ink-700 mb-1">✈️ Suggested Origin</p>
              <p className="text-xs text-ink-600">{flights.origin_suggestion}</p>
            </div>
          )}
          {flights.transit_from_airport && (
            <div className="bg-paper-50 rounded-lg p-3 border border-paper-200">
              <p className="text-xs font-bold text-ink-700 mb-1">🚕 Airport Transit</p>
              <p className="text-xs text-ink-600">{flights.transit_from_airport}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
