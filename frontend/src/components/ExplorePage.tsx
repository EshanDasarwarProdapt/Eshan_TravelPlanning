import React, { useEffect, useState } from 'react';
import { ArrowRight, Star } from 'lucide-react';
import { fetchExplore, recommendExperiences } from '../services/api';
import { ExperiencePlan, ExploreCatalog, ExploreRecommendation } from '../types';

interface ExplorePageProps {
  onPlan: (destination: string) => void;
}

function inr(amount?: number | null) {
  if (amount == null) return '';
  return `₹${amount.toLocaleString('en-IN')}`;
}

export const ExplorePage: React.FC<ExplorePageProps> = ({ onPlan }) => {
  const [catalog, setCatalog] = useState<ExploreCatalog | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [preferences, setPreferences] = useState('5 day trip for beaches, sightseeing, and local food');
  const [budget, setBudget] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [result, setResult] = useState<ExploreRecommendation | null>(null);
  const [open, setOpen] = useState<ExperiencePlan | null>(null);

  useEffect(() => {
    fetchExplore()
      .then(setCatalog)
      .catch((err) => setLoadError(err.message || 'Could not load experiences.'));
  }, []);

  const search = async (event: React.FormEvent) => {
    event.preventDefault();
    setSearching(true);
    setSearchError(null);
    try {
      const parsed = budget.trim() ? Number(budget) : undefined;
      setResult(await recommendExperiences(preferences, parsed));
    } catch (err: any) {
      setSearchError(err.message || 'Could not match traveler scores.');
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 pb-32 text-left">
      <p className="text-xs font-mono uppercase tracking-wider text-ink-500">Explore</p>
      <h1 className="font-display text-4xl sm:text-5xl text-ink-900 mt-2">Trips rated by past travelers</h1>
      <p className="text-ink-500 mt-3 max-w-3xl">
        Each score is the average of traveler records in the database
        {catalog ? ` (${catalog.record_count.toLocaleString()} records)` : ''}.
        Places with no records are shown without a rating. Use Plan when you want to choose a hotel, a route, and a final cost.
      </p>

      <form onSubmit={search} className="mt-8 bg-paper-50 border border-paper-300 rounded-lg p-4 sm:p-5 space-y-3">
        <label className="block">
          <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">What kind of trip?</span>
          <input
            value={preferences}
            onChange={(event) => setPreferences(event.target.value)}
            className="w-full border border-paper-300 rounded px-3 py-3 bg-transparent focus:outline-none focus:border-ink-900"
          />
        </label>
        <label className="block max-w-xs">
          <span className="block text-xs font-mono uppercase tracking-wider text-ink-500 mb-2">Trip budget in INR, optional</span>
          <input
            value={budget}
            onChange={(event) => setBudget(event.target.value.replace(/[^\d]/g, ''))}
            placeholder="40000"
            className="w-full border border-paper-300 rounded px-3 py-3 bg-transparent focus:outline-none focus:border-ink-900"
          />
        </label>
        <button
          type="submit"
          disabled={searching || preferences.trim().length < 2}
          className="inline-flex items-center space-x-2 bg-ink-900 text-paper-50 px-5 py-2 rounded text-sm disabled:opacity-50"
        >
          <span>{searching ? 'Matching travelers...' : 'Match similar travelers'}</span>
          <ArrowRight className="w-4 h-4" />
        </button>
        {searchError && <p className="text-sm text-amber-900">{searchError}</p>}
      </form>

      {result && (
        <section className="mt-6 bg-paper-50 border border-paper-300 rounded-lg p-4 sm:p-5">
          <h2 className="font-display text-2xl text-ink-900">Best match</h2>
          <p className="text-sm text-ink-600 mt-2">{result.summary}</p>
          {result.comparison.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs font-mono uppercase text-ink-500">
                  <tr>
                    <th className="py-2 pr-3">Destination</th>
                    <th className="py-2 pr-3">Rating</th>
                    <th className="py-2 pr-3">Similar travelers</th>
                    <th className="py-2 pr-3">Stored trip cost</th>
                    <th className="py-2">Budget</th>
                  </tr>
                </thead>
                <tbody>
                  {result.comparison.map((row) => (
                    <tr key={row.destination} className="border-t border-paper-200">
                      <td className="py-2 pr-3 font-semibold">{row.destination}</td>
                      <td className="py-2 pr-3">{row.average_rating == null ? 'Not rated' : `${row.average_rating.toFixed(2)} / 5`}</td>
                      <td className="py-2 pr-3">{row.similar_travelers}</td>
                      <td className="py-2 pr-3">{inr(row.trip_cost_inr)} for {row.days} days</td>
                      <td className="py-2">{row.within_budget ? 'Inside' : 'Over'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {result.recommended && (
            <button
              type="button"
              onClick={() => onPlan(result.recommended!.destination)}
              className="mt-4 text-sm underline"
            >
              Plan {result.recommended.destination}
            </button>
          )}
        </section>
      )}

      {loadError && <p className="mt-6 text-sm text-amber-900">{loadError}</p>}

      <div className="mt-10 space-y-10">
        {catalog?.themes.map((theme) => (
          <section key={theme.id}>
            <h2 className="font-display text-2xl text-ink-900">{theme.title}</h2>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
              {theme.places.map((place) => (
                <button
                  key={`${theme.id}-${place.destination}`}
                  type="button"
                  onClick={() => setOpen(place)}
                  className={`text-left rounded-lg border p-4 ${open?.destination === place.destination && open?.display_name === place.display_name ? 'border-ink-900 bg-paper-100' : 'border-paper-300 bg-paper-50'}`}
                >
                  <p className="font-bold text-ink-900">{place.display_name || place.destination}</p>
                  {place.available ? (
                    <>
                      <p className="mt-2 flex items-center gap-1 text-sm">
                        <Star className="w-3.5 h-3.5" />
                        {place.average_rating?.toFixed(2)} / 5 from {place.traveler_count} travelers
                      </p>
                      <p className="text-xs text-ink-500 mt-1">
                        {place.days} days from Delhi · about {inr(place.trip_cost_inr)} a person
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="mt-2 text-sm text-ink-500">{place.note}</p>
                      {place.trip_cost_inr ? (
                        <p className="text-xs text-ink-500 mt-1">
                          {place.days} days from Delhi · about {inr(place.trip_cost_inr)} a person
                        </p>
                      ) : null}
                    </>
                  )}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>

      {open && (
        <section className="mt-8 bg-paper-50 border border-paper-300 rounded-lg p-4 sm:p-5">
          <h2 className="font-display text-2xl text-ink-900">{open.display_name || open.destination}</h2>
          <p className="text-sm text-ink-500 mt-1">{open.note}</p>
          {open.price_note && <p className="text-sm text-ink-700 mt-2">{open.price_note}</p>}
          {open.available && (
            <>
              <p className="text-sm text-ink-700 mt-3">
                Stored stays: {open.stay_types.join(', ')}. Season on the records: {open.best_season}.
              </p>
              <ul className="mt-4 space-y-3">
                {open.outline.map((day) => (
                  <li key={day.day_number} className="border-t border-paper-200 pt-3">
                    <p className="font-semibold">Day {day.day_number}</p>
                    <p className="text-sm mt-1">{day.sightseeing}</p>
                    <p className="text-sm text-ink-600 mt-1">{day.food}</p>
                    <p className="text-xs text-ink-500 mt-1">Stay recorded for this place: {day.stay}</p>
                  </li>
                ))}
              </ul>
              <button
                type="button"
                onClick={() => onPlan(open.destination)}
                className="mt-4 inline-flex items-center space-x-2 bg-ink-900 text-paper-50 px-4 py-2 rounded text-sm"
              >
                <span>Plan this trip</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}
        </section>
      )}
    </div>
  );
};
