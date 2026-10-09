import React from 'react';
import { Compass, Sparkles, Database, CheckCircle2, AlertCircle } from 'lucide-react';

interface HeaderProps {
  backendHealth: {
    status: string;
    version: string;
    database_records_indexed: number;
    llm_status: string;
  } | null;
  page: 'explore' | 'plan';
  onNavigate: (page: 'explore' | 'plan') => void;
}

export const Header: React.FC<HeaderProps> = ({ backendHealth, page, onNavigate }) => {
  return (
    <header className="border-b border-paper-300 bg-paper-50 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Title */}
        <div 
          onClick={() => onNavigate('explore')}
          className="cursor-pointer flex items-center space-x-3 group"
        >
          <div className="w-8 h-8 rounded-sm bg-ink-900 flex items-center justify-center text-paper-50 group-hover:bg-accent transition-colors">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-display tracking-tight text-xl font-bold text-ink-900">WAYPOINT</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-paper-200 text-ink-700 font-mono font-medium">v1.0</span>
            </div>
            <p className="text-[11px] text-ink-500 font-medium tracking-wider uppercase">Travel Intelligence & Multi-Agent Planning</p>
          </div>
        </div>

        <nav className="flex items-center gap-2 text-sm">
          <button
            type="button"
            onClick={() => onNavigate('explore')}
            className={`px-3 py-1 rounded ${page === 'explore' ? 'bg-ink-900 text-paper-50' : 'text-ink-700'}`}
          >
            Explore
          </button>
          <button
            type="button"
            onClick={() => onNavigate('plan')}
            className={`px-3 py-1 rounded ${page === 'plan' ? 'bg-ink-900 text-paper-50' : 'text-ink-700'}`}
          >
            Plan
          </button>
        </nav>

        {/* Backend & Grounding Status Indicators */}
        <div className="hidden md:flex items-center space-x-6 text-xs">
          <div className="flex items-center space-x-1.5 text-ink-700 bg-paper-100 px-2.5 py-1 rounded border border-paper-300">
            <Database className="w-3.5 h-3.5 text-accent" />
            <span>UCI 485 Grounded:</span>
            <span className="font-mono font-semibold text-ink-900">
              {backendHealth ? `${backendHealth.database_records_indexed.toLocaleString()} vectors` : 'Connecting...'}
            </span>
          </div>

          <div className="flex items-center space-x-1.5 text-ink-700 bg-paper-100 px-2.5 py-1 rounded border border-paper-300">
            <Sparkles className="w-3.5 h-3.5 text-ink-500" />
            <span>LangGraph:</span>
            <span className="font-semibold text-ink-900">7-Agent Loop</span>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className={`w-2 h-2 rounded-full ${backendHealth?.status === 'healthy' ? 'bg-emerald-500' : 'bg-amber-500 animate-pulse'}`} />
            <span className="text-ink-500 font-mono text-[11px]">
              {backendHealth?.llm_status || 'System Ready'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
