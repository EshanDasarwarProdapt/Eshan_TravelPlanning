import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Terminal, Database, CheckCircle2, ShieldCheck, Clock } from 'lucide-react';
import { AgentTrace } from '../types';

interface AgentTraceInspectorProps {
  traces: AgentTrace[];
  evidence: Array<{
    id: string;
    text: string;
    score: number;
    metadata: Record<string, any>;
  }>;
  executionTimeMs: number;
}

export const AgentTraceInspector: React.FC<AgentTraceInspectorProps> = ({
  traces,
  evidence,
  executionTimeMs
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'agents' | 'evidence'>('agents');

  return (
    <section className="py-6 border-t border-paper-300">
      <div className="bg-paper-50 rounded-lg border border-paper-300 overflow-hidden text-left">
        {/* Toggle Bar */}
        <div
          onClick={() => setIsOpen(!isOpen)}
          className="cursor-pointer p-4 flex items-center justify-between hover:bg-paper-100 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <div className="w-7 h-7 rounded bg-ink-900 text-paper-50 flex items-center justify-center">
              <Terminal className="w-3.5 h-3.5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold uppercase text-ink-900 tracking-wider">
                  How Your Plan Was Built
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-paper-200 text-ink-700">
                  LangGraph Orchestration Trace
                </span>
              </div>
              <span className="text-xs text-ink-500">
                Inspect the 7 agents' deterministic execution metadata and retrieved dataset vectors
              </span>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <span className="text-xs font-mono text-ink-500">
              {traces.length} steps · {executionTimeMs}ms
            </span>
            {isOpen ? <ChevronUp className="w-5 h-5 text-ink-500" /> : <ChevronDown className="w-5 h-5 text-ink-500" />}
          </div>
        </div>

        {/* Expanded Content */}
        {isOpen && (
          <div className="border-t border-paper-200 p-5 bg-paper-100/50">
            <div className="flex items-center space-x-4 mb-4 border-b border-paper-300 pb-2 text-xs font-mono">
              <button
                onClick={() => setActiveTab('agents')}
                className={`pb-1 ${activeTab === 'agents' ? 'border-b-2 border-ink-900 font-bold text-ink-900' : 'text-ink-500'}`}
              >
                Agent Execution Sequence ({traces.length})
              </button>
              <button
                onClick={() => setActiveTab('evidence')}
                className={`pb-1 ${activeTab === 'evidence' ? 'border-b-2 border-ink-900 font-bold text-ink-900' : 'text-ink-500'}`}
              >
                Retrieved Dataset 485 Vectors ({evidence.length})
              </button>
            </div>

            {activeTab === 'agents' ? (
              <div className="space-y-3 font-mono text-xs">
                {traces.map((t, idx) => (
                  <div
                    key={idx}
                    className="bg-paper-50 rounded p-3 border border-paper-200 flex items-start justify-between gap-4"
                  >
                    <div className="flex items-start space-x-2.5">
                      <span className="text-ink-400 font-bold">0{idx + 1}</span>
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-ink-900">{t.agent}</span>
                          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.2 rounded border border-emerald-200">
                            {t.status}
                          </span>
                        </div>
                        <p className="text-ink-600 mt-1 text-[11px] font-sans leading-relaxed">{t.detail}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3 font-mono text-xs max-h-96 overflow-y-auto">
                {evidence.map((ev, idx) => (
                  <div key={idx} className="bg-paper-50 rounded p-3 border border-paper-200 text-left">
                    <div className="flex items-center justify-between text-[11px] text-ink-500 mb-1">
                      <span className="font-bold text-ink-800">
                        {ev.metadata?.destination} · {ev.metadata?.category_name || ev.metadata?.category}
                      </span>
                      <span className="text-accent font-bold">Score: {Math.round(ev.score * 100)}%</span>
                    </div>
                    <p className="text-[11px] font-sans text-ink-700 leading-relaxed">{ev.text}</p>
                    <div className="mt-2 text-[10px] text-ink-400 flex items-center space-x-3">
                      <span>User ID: {ev.metadata?.user_id}</span>
                      <span>Rating: {ev.metadata?.rating}/5.0</span>
                      <span>Cost: ₹{ev.metadata?.estimated_daily_cost_inr}/day</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
