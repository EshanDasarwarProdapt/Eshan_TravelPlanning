import React, { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, Sparkles, ShieldCheck, Search, Calculator, Calendar, Award } from 'lucide-react';

interface AgentProgressModalProps {
  isOpen: boolean;
}

const AGENT_STEPS = [
  { id: 'guardrails', name: 'Input Guardrails', desc: 'Sanitizing query and verifying safety bounds' },
  { id: 'classifier', name: 'Preference Classifier', desc: 'Extracting structured intent, duration, and interests' },
  { id: 'destination', name: 'Destination Analyzer', desc: 'Hybrid RAG retrieval and multi-factor candidate scoring' },
  { id: 'budget', name: 'Budget Analyst', desc: 'Deterministic expense allocation and feasibility modeling' },
  { id: 'activity', name: 'Activity Recommender', desc: 'Ranking destination-specific activities by interest match' },
  { id: 'lodging', name: 'Accommodation Finder', desc: 'Positioning lodging tiers and neighborhood guidance' },
  { id: 'flights', name: 'Flight Finder', desc: 'Recommending flight options across budget, standard, and premium tiers' },
  { id: 'itinerary', name: 'Itinerary Planner', desc: 'Building chronological morning, afternoon, and evening schedule' },
  { id: 'validator', name: 'Quality Validator', desc: 'LLM-as-a-judge score evaluation and refinement loop check' },
];

export const AgentProgressModal: React.FC<AgentProgressModalProps> = ({ isOpen }) => {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setCurrentStep(0);
      return;
    }
    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev < AGENT_STEPS.length - 1 ? prev + 1 : prev));
    }, 600);
    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-ink-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-paper-50 border border-paper-300 rounded-lg shadow-2xl max-w-md w-full p-6 text-left">
        <div className="flex items-center space-x-2.5 pb-4 border-b border-paper-200">
          <div className="w-6 h-6 rounded bg-ink-900 text-paper-50 flex items-center justify-center animate-spin">
            <Loader2 className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="font-display font-bold text-ink-900 text-lg">Orchestrating Agents</h3>
            <p className="text-[11px] font-mono text-ink-500 uppercase">LangGraph Execution In Progress</p>
          </div>
        </div>

        <div className="py-4 space-y-3">
          {AGENT_STEPS.map((step, idx) => {
            const isDone = idx < currentStep;
            const isCurrent = idx === currentStep;

            return (
              <div
                key={step.id}
                className={`flex items-start space-x-3 transition-opacity duration-300 ${
                  isDone ? 'opacity-100' : isCurrent ? 'opacity-100' : 'opacity-40'
                }`}
              >
                <div className="mt-0.5">
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-accent animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-paper-300 bg-paper-100" />
                  )}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-semibold ${isCurrent ? 'text-accent' : 'text-ink-900'}`}>
                      {step.name}
                    </span>
                    <span className="text-[10px] font-mono text-ink-400">0{idx + 1}</span>
                  </div>
                  <p className="text-[11px] text-ink-500 leading-tight mt-0.5">{step.desc}</p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-3 border-t border-paper-200 text-center">
          <span className="text-[11px] font-mono text-ink-400">Grounding against 5,456 UCI 485 vectors...</span>
        </div>
      </div>
    </div>
  );
};
