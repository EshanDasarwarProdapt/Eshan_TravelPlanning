import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ExplorePage } from './components/ExplorePage';
import { TripFlow } from './components/TripFlow';
import { ItineraryTimeline } from './components/ItineraryTimeline';
import { TravelChat } from './components/TravelChat';
import { checkHealth } from './services/api';
import { BuiltTrip } from './types';

export function App() {
  const [backendHealth, setBackendHealth] = useState<any>(null);
  const [page, setPage] = useState<'explore' | 'plan'>('explore');
  const [currentPlan, setCurrentPlan] = useState<BuiltTrip | null>(null);
  const [flowKey, setFlowKey] = useState(0);
  const [planDestination, setPlanDestination] = useState('');

  useEffect(() => {
    checkHealth()
      .then((data) => setBackendHealth(data))
      .catch((err) => console.log('Backend health check error:', err));
  }, []);

  const handleReset = () => {
    setCurrentPlan(null);
    setPlanDestination('');
    setFlowKey((key) => key + 1);
  };

  const openPlanner = (destination: string) => {
    setPlanDestination(destination);
    setCurrentPlan(null);
    setFlowKey((key) => key + 1);
    setPage('plan');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-paper-100 flex flex-col font-sans text-ink-900">
      <Header backendHealth={backendHealth} page={page} onNavigate={setPage} />

      <main className="flex-1">
        {page === 'explore' ? (
          <ExplorePage onPlan={openPlanner} />
        ) : !currentPlan ? (
          <TripFlow key={flowKey} initialDestination={planDestination} onPlanned={(plan) => {
            setCurrentPlan(plan);
            window.scrollTo({ top: 0, behavior: 'smooth' });
          }} />
        ) : (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-4 text-left">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <p className="text-xs font-mono uppercase tracking-wider text-ink-500">Your plan</p>
                <h1 className="font-display text-3xl sm:text-4xl text-ink-900">{currentPlan.itinerary.trip_title}</h1>
                <p className="text-sm text-ink-600 mt-2">
                  {currentPlan.origin} to {currentPlan.destination} by {currentPlan.transport_mode}. {currentPlan.travelers} travelers, {currentPlan.stay_days} days in the city, {currentPlan.nights} nights at {currentPlan.hotel_name}.
                </p>
              </div>
              <button
                onClick={handleReset}
                className="px-4 py-2 text-sm border border-paper-300 rounded bg-paper-50"
              >
                Start over
              </button>
            </div>

            <ItineraryTimeline itinerary={currentPlan.itinerary} />

            <section className="bg-paper-50 rounded-lg border border-paper-300 p-5 sm:p-6">
              <h2 className="font-display text-2xl text-ink-900 mb-1">Estimated cost</h2>
              <p className="text-sm text-ink-500 mb-4">{currentPlan.note}</p>
              <ul className="divide-y divide-paper-200">
                {currentPlan.cost_lines.map((line) => (
                  <li key={line.label} className="py-3 flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-ink-900">{line.label}</p>
                      <p className="text-xs text-ink-500">{line.detail}</p>
                    </div>
                    <p className="font-mono font-bold text-ink-900">₹{line.amount.toLocaleString('en-IN')}</p>
                  </li>
                ))}
              </ul>
              <div className="mt-4 pt-4 border-t border-ink-900 flex items-center justify-between">
                <p className="font-display text-xl text-ink-900">Estimated total</p>
                <p className="font-mono text-2xl font-black text-ink-900">₹{currentPlan.estimated_total.toLocaleString('en-IN')}</p>
              </div>
            </section>
          </div>
        )}
      </main>

      <TravelChat />

      {/* Footer */}
      <footer className="border-t border-paper-300 bg-paper-50 py-8 text-center text-xs text-ink-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <span className="font-display font-bold text-ink-900">WAYPOINT</span>
            <span>·</span>
            <span>AI-Powered Travel Planning & Itinerary Assistant</span>
          </div>
          <div>
            <span>Grounded on UCI Dataset 485 (5,456 Vectors) · LangGraph 8-Agent Loop · FastAPI & React</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
