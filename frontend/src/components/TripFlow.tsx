import React, { useState } from 'react';
import { ArrowRight, BedDouble, Bus, MapPin, Plane, Train, Users } from 'lucide-react';
import { buildTrip, fetchTripOptions } from '../services/api';
import { BuiltTrip, HotelChoice, TransportChoice, TripOptions } from '../types';

interface TripFlowProps {
  onPlanned: (trip: BuiltTrip) => void;
  initialDestination?: string;
}

type Step = 'where' | 'route' | 'hotel' | 'details';

const STEPS: { id: Step; label: string }[] = [
  { id: 'where', label: 'Where' },
  { id: 'route', label: 'How to get there' },
  { id: 'hotel', label: 'Hotel' },
  { id: 'details', label: 'Trip details' },
];

function inr(amount: number) {
  return `₹${amount.toLocaleString('en-IN')}`;
}

function ModeIcon({ mode }: { mode: string }) {
  if (mode === 'train') return <Train className="w-5 h-5" />;
  if (mode === 'bus') return <Bus className="w-5 h-5" />;
  return <Plane className="w-5 h-5" />;
}

export const TripFlow: React.FC<TripFlowProps> = ({ onPlanned, initialDestination = '' }) => {
  const [step, setStep] = useState<Step>('where');
  const [destination, setDestination] = useState(initialDestination);
  const [origin, setOrigin] = useState('');
  const [options, setOptions] = useState<TripOptions | null>(null);
  const [transportMode, setTransportMode] = useState('');
  const [hotelName, setHotelName] = useState('');
  const [tripDays, setTripDays] = useState(3);
  const [stayDays, setStayDays] = useState(3);
  const [travelers, setTravelers] = useState(2);
  const [preferences, setPreferences] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadOptions = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!destination.trim() || !origin.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchTripOptions(destination.trim(), origin.trim());
      setOptions(data);
      const fastest = data.transport.find((item) => item.fastest) || data.transport[0];
      setTransportMode(data.local_only || !fastest ? 'local' : fastest.mode);
      setHotelName('');
      setStep(data.local_only || data.transport.length === 0 ? 'hotel' : 'route');
    } catch (err: any) {
      setError(err.message || 'Could not load routes for that city.');
    } finally {
      setLoading(false);
    }
  };

  const generate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!options || !hotelName) return;
    if (stayDays > tripDays) {
      setError('Days in the city cannot be longer than the whole trip.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const plan = await buildTrip({
        destination: options.destination,
        origin: options.origin,
        transport_mode: transportMode || 'local',
        hotel_name: hotelName,
        trip_days: Math.min(30, Math.max(1, tripDays || 1)),
        travelers: Math.min(20, Math.max(1, travelers || 1)),
        stay_days: Math.min(30, Math.max(1, stayDays || 1)),
        preferences,
      });
      onPlanned(plan);
    } catch (err: any) {
      setError(err.message || 'Could not build the plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 md:py-16 pb-32">
      <div className="text-center mb-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-paper-200 border border-paper-300 text-ink-700 text-xs font-mono uppercase tracking-wider mb-4">
          <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          <span>Plan the trip, then see the cost</span>
        </div>
        <h1 className="font-display text-4xl sm:text-5xl text-ink-900 tracking-tight leading-[1.15] mb-4">
          Where are you going?
        </h1>
        <p className="text-ink-500 text-base sm:text-lg max-w-2xl mx-auto">
          Start with the destination and the city you are in. Pick how you want to get there and where you want to stay, then tell us who is traveling. The estimated cost is added up at the end.
        </p>
      </div>

      <ol className="flex flex-wrap gap-2 mb-6 text-xs font-mono uppercase tracking-wider">
        {STEPS.map((item, index) => {
          const active = item.id === step;
          const done = STEPS.findIndex((entry) => entry.id === step) > index;
          return (
            <li
              key={item.id}
              className={`px-3 py-1 rounded border ${active ? 'bg-ink-900 text-paper-50 border-ink-900' : done ? 'bg-paper-200 text-ink-800 border-paper-300' : 'text-ink-400 border-paper-300'}`}
            >
              {index + 1}. {item.label}
            </li>
          );
        })}
      </ol>

      {error && (
        <p className="mb-4 text-sm text-amber-900 bg-amber-50 border border-amber-300 rounded px-3 py-2">{error}</p>
      )}

      {step === 'where' && (
        <form onSubmit={loadOptions} className="bg-paper-50 rounded-lg border border-paper-300 shadow-card p-5 sm:p-6 space-y-4">
          <label className="block text-left">
            <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">Destination</span>
            <input
              value={destination}
              onChange={(event) => setDestination(event.target.value)}
              placeholder="Jaipur"
              className="w-full bg-transparent border border-paper-300 rounded px-3 py-3 text-lg focus:outline-none focus:border-ink-900"
              disabled={loading}
            />
          </label>
          <label className="block text-left">
            <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">Your current city</span>
            <input
              value={origin}
              onChange={(event) => setOrigin(event.target.value)}
              placeholder="Delhi"
              className="w-full bg-transparent border border-paper-300 rounded px-3 py-3 text-lg focus:outline-none focus:border-ink-900"
              disabled={loading}
            />
          </label>
          <button
            type="submit"
            disabled={loading || !destination.trim() || !origin.trim()}
            className="inline-flex items-center space-x-2 bg-ink-900 hover:bg-accent text-paper-50 px-6 py-3 rounded text-sm font-medium disabled:opacity-50"
          >
            <span>{loading ? 'Looking up routes...' : 'Show ways to get there'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      )}

      {step === 'route' && options && (
        <section className="text-left">
          <h2 className="font-display text-2xl text-ink-900 mb-1">How to get there</h2>
          <p className="text-sm text-ink-500 mb-4">{options.note}</p>
          <div className="space-y-3">
            {options.transport.map((option) => (
              <TransportCard
                key={option.mode}
                option={option}
                selected={transportMode === option.mode}
                onSelect={() => setTransportMode(option.mode)}
              />
            ))}
          </div>
          <div className="mt-5 flex gap-3">
            <button type="button" onClick={() => setStep('where')} className="px-4 py-2 text-sm border border-paper-300 rounded">Back</button>
            <button
              type="button"
              disabled={!transportMode}
              onClick={() => setStep('hotel')}
              className="inline-flex items-center space-x-2 bg-ink-900 text-paper-50 px-5 py-2 rounded text-sm disabled:opacity-50"
            >
              <span>See hotels in {options.destination}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </section>
      )}

      {step === 'hotel' && options && (
        <section className="text-left">
          <h2 className="font-display text-2xl text-ink-900 mb-1">Where do you want to stay?</h2>
          <p className="text-sm text-ink-500 mb-4">
            Nightly rates are planning estimates for {options.destination}. Pick the stay the rest of the trip should use.
          </p>
          {options.local_only && <p className="text-sm text-ink-700 mb-4">{options.note}</p>}
          <div className="space-y-3">
            {options.hotels.map((hotel) => (
              <HotelCard
                key={hotel.name}
                hotel={hotel}
                selected={hotelName === hotel.name}
                onSelect={() => setHotelName(hotel.name)}
              />
            ))}
          </div>
          {options.hotels.length === 0 && (
            <p className="text-sm text-amber-900">No stays were found for this city yet.</p>
          )}
          <div className="mt-5 flex gap-3">
            <button
              type="button"
              onClick={() => setStep(options.transport.length ? 'route' : 'where')}
              className="px-4 py-2 text-sm border border-paper-300 rounded"
            >
              Back
            </button>
            <button
              type="button"
              disabled={!hotelName}
              onClick={() => setStep('details')}
              className="inline-flex items-center space-x-2 bg-ink-900 text-paper-50 px-5 py-2 rounded text-sm disabled:opacity-50"
            >
              <span>Enter trip details</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </section>
      )}

      {step === 'details' && options && (
        <form onSubmit={generate} className="bg-paper-50 rounded-lg border border-paper-300 shadow-card p-5 sm:p-6 text-left space-y-4">
          <h2 className="font-display text-2xl text-ink-900">Trip details</h2>
          <p className="text-sm text-ink-500">
            {options.origin} to {options.destination} by {transportMode}, staying at {hotelName}.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <NumberField label="Days of the trip" value={tripDays} min={1} max={30} onChange={setTripDays} />
            <NumberField label="Travelers" value={travelers} min={1} max={20} onChange={setTravelers} />
            <NumberField label="Days in this city" value={stayDays} min={1} max={30} onChange={setStayDays} />
          </div>
          <p className="text-xs text-ink-500">
            Hotel nights are one less than the days in the city, because the last day is checkout. A 3-day stay is 2 nights.
          </p>
          <label className="block">
            <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">What do you want to do?</span>
            <textarea
              rows={3}
              value={preferences}
              onChange={(event) => setPreferences(event.target.value)}
              placeholder="Forts, markets, and Rajasthani food"
              className="w-full bg-transparent border border-paper-300 rounded px-3 py-3 focus:outline-none focus:border-ink-900"
            />
          </label>
          <div className="flex gap-3">
            <button type="button" onClick={() => setStep('hotel')} className="px-4 py-2 text-sm border border-paper-300 rounded">Back</button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center space-x-2 bg-ink-900 text-paper-50 px-5 py-2 rounded text-sm disabled:opacity-50"
            >
              <Users className="w-4 h-4" />
              <span>{loading ? 'Building the plan...' : 'Generate the plan'}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

function NumberField({
  label,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">{label}</span>
      <input
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-full border border-paper-300 rounded px-3 py-3 bg-transparent focus:outline-none focus:border-ink-900"
      />
    </label>
  );
}

function TransportCard({
  option,
  selected,
  onSelect,
}: {
  option: TransportChoice;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-4 ${selected ? 'border-ink-900 bg-paper-100' : 'border-paper-300 bg-paper-50'}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <ModeIcon mode={option.mode} />
          <div>
            <p className="font-bold text-ink-900">{option.label}</p>
            <p className="text-xs text-ink-500">{option.route}</p>
          </div>
        </div>
        <div className="text-right">
          {option.fastest && <span className="block text-[10px] font-mono uppercase text-accent">Fastest</span>}
          <p className="font-black text-ink-900">{inr(option.per_person_price)}</p>
          <p className="text-[11px] text-ink-500">per person, round trip</p>
        </div>
      </div>
      <p className="mt-2 text-xs text-ink-600">{option.duration} · {option.stops}</p>
    </button>
  );
}

function HotelCard({
  hotel,
  selected,
  onSelect,
}: {
  hotel: HotelChoice;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-4 ${selected ? 'border-ink-900 bg-paper-100' : 'border-paper-300 bg-paper-50'}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <BedDouble className="w-5 h-5" />
          <div>
            <p className="font-bold text-ink-900">{hotel.name}</p>
            <p className="text-xs text-ink-500 flex items-center gap-1"><MapPin className="w-3 h-3" /> {hotel.area} · {hotel.tier}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="font-black text-ink-900">{inr(hotel.nightly)}</p>
          <p className="text-[11px] text-ink-500">a night, estimate</p>
        </div>
      </div>
    </button>
  );
}
