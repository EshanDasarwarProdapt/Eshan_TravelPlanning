import React from 'react';
import { Wallet, CheckCircle2, AlertTriangle, PieChart, ShieldCheck } from 'lucide-react';
import { BudgetAnalysis } from '../types';

interface BudgetBreakdownCardProps {
  budget: BudgetAnalysis;
}

export const BudgetBreakdownCard: React.FC<BudgetBreakdownCardProps> = ({ budget }) => {
  const {
    estimated_total,
    remaining_budget,
    budget: targetBudget,
    feasible,
    feasibility_status,
    confidence,
    breakdown,
    daily_average_per_person,
    duration_days
  } = budget;

  const total = estimated_total || 1;
  const share = (amount: number) => Math.round((amount / total) * 100);
  const categories = [
    { label: "Accommodation & Lodging", amount: breakdown.accommodation, pct: share(breakdown.accommodation), color: "bg-ink-900" },
    { label: "Food, Dining & Cafes", amount: breakdown.food_and_dining, pct: share(breakdown.food_and_dining), color: "bg-accent" },
    { label: "Activities & Sightseeing", amount: breakdown.activities_and_entry, pct: share(breakdown.activities_and_entry), color: "bg-amber-600" },
    { label: "Getting There (flight / train / bus)", amount: breakdown.intercity_transport || 0, pct: share(breakdown.intercity_transport || 0), color: "bg-sky-700" },
    { label: "Local Transport & Cabs", amount: breakdown.local_transport, pct: share(breakdown.local_transport), color: "bg-emerald-700" },
    { label: "Contingency & Misc", amount: breakdown.contingency_and_misc, pct: share(breakdown.contingency_and_misc), color: "bg-ink-400" },
  ].filter((cat) => cat.amount > 0);

  return (
    <section className="py-6">
      <div className="bg-paper-50 rounded-lg border border-paper-300 p-6 shadow-subtle">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-paper-200">
          <div>
            <span className="text-xs font-mono text-ink-500 uppercase tracking-wider">
              Agent 03 · Budget Analyst
            </span>
            <h2 className="font-display text-2xl font-bold text-ink-900 flex items-center space-x-2">
              <span>Financial Feasibility & Expense Allocation</span>
            </h2>
          </div>

          <div className="flex items-center space-x-3">
            <div className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded text-xs font-mono font-semibold ${
              feasible ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-amber-50 text-amber-800 border border-amber-200'
            }`}>
              {feasible ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <AlertTriangle className="w-4 h-4 text-amber-600" />}
              <span>{feasibility_status}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 py-6 border-b border-paper-200">
          <div>
            <span className="text-xs font-mono text-ink-500 block uppercase">Target Budget</span>
            <span className="text-2xl font-display font-bold text-ink-900">
              {targetBudget ? `₹${targetBudget.toLocaleString()}` : 'Flexible'}
            </span>
            <span className="text-[11px] text-ink-400 block mt-0.5">Stated in query</span>
          </div>

          <div>
            <span className="text-xs font-mono text-ink-500 block uppercase">Estimated Total Cost</span>
            <span className="text-2xl font-display font-bold text-accent">
              ₹{estimated_total.toLocaleString()}
            </span>
            <span className="text-[11px] text-ink-400 block mt-0.5">₹{daily_average_per_person.toLocaleString()} / day per traveler</span>
          </div>

          <div>
            <span className="text-xs font-mono text-ink-500 block uppercase">Surplus / Deficit</span>
            <span className={`text-2xl font-display font-bold ${remaining_budget >= 0 ? 'text-emerald-700' : 'text-amber-600'}`}>
              {remaining_budget >= 0 ? `+₹${remaining_budget.toLocaleString()}` : `-₹${Math.abs(remaining_budget).toLocaleString()}`}
            </span>
            <span className="text-[11px] text-ink-400 block mt-0.5">Deterministic arithmetic calculation</span>
          </div>
        </div>

        {/* Expense Category Progress Bar */}
        <div className="pt-6">
          <div className="flex items-center justify-between text-xs font-mono text-ink-700 mb-2">
            <span>Itemized Allocation Breakdown</span>
            <span className="text-ink-400">Model Confidence: {Math.round(confidence * 100)}%</span>
          </div>

          <div className="w-full h-3 bg-paper-200 rounded-full overflow-hidden flex mb-4">
            {categories.map((cat, idx) => (
              <div
                key={idx}
                style={{ width: `${cat.pct}%` }}
                className={`${cat.color} h-full transition-all`}
                title={`${cat.label}: ₹${cat.amount.toLocaleString()} (${cat.pct}%)`}
              />
            ))}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
            {categories.map((cat, idx) => (
              <div key={idx} className="bg-paper-100 rounded p-2.5 border border-paper-200">
                <div className="flex items-center space-x-1.5 mb-1">
                  <span className={`w-2 h-2 rounded-full ${cat.color}`} />
                  <span className="text-[11px] text-ink-600 font-medium truncate">{cat.label}</span>
                </div>
                <div className="text-sm font-bold font-mono text-ink-900">₹{cat.amount.toLocaleString()}</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
