import React, { useEffect, useRef, useState } from 'react';
import { MessageCircle, Send, X } from 'lucide-react';
import { sendChat, ChatTurn } from '../services/api';

const STARTERS = [
  'Best time to visit Assam?',
  'Flight or train on a tight budget?',
  'How should I split ₹40,000 for 5 days?',
];

export function TravelChat() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatTurn[]>([
    {
      role: 'assistant',
      content: 'Ask me anything about a trip: cities, seasons, budgets, trains, flights, or hotels. For a full day-by-day plan, use the planner on this page.',
    },
  ]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open, busy]);

  const ask = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    const history = messages.filter((turn) => turn.role === 'user' || turn.role === 'assistant').slice(-8);
    setMessages((prev) => [...prev, { role: 'user', content: message }]);
    setDraft('');
    setError(null);
    setBusy(true);
    try {
      const reply = await sendChat(message, history);
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch (err: any) {
      setError(err.message || 'The travel assistant could not reply.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end">
      {open && (
        <div className="mb-3 w-[min(22rem,calc(100vw-2.5rem))] h-[28rem] bg-paper-50 border border-paper-300 rounded-2xl shadow-lg flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-paper-200 flex items-center justify-between bg-ink-900 text-paper-50">
            <div>
              <p className="text-sm font-display font-bold">Travel chat</p>
              <p className="text-[11px] text-paper-200">Questions about trips, not a full itinerary</p>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="p-1 rounded hover:bg-white/10"
              aria-label="Close travel chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2">
            {messages.map((turn, index) => (
              <div
                key={index}
                className={`max-w-[90%] rounded-xl px-3 py-2 text-sm leading-relaxed ${
                  turn.role === 'user'
                    ? 'ml-auto bg-ink-900 text-paper-50'
                    : 'mr-auto bg-paper-100 text-ink-800 border border-paper-200'
                }`}
              >
                {turn.content}
              </div>
            ))}
            {busy && (
              <div className="mr-auto bg-paper-100 text-ink-500 border border-paper-200 rounded-xl px-3 py-2 text-sm">
                Thinking…
              </div>
            )}
            {error && <p className="text-xs text-amber-800">{error}</p>}
            <div ref={bottomRef} />
          </div>

          {messages.length < 3 && (
            <div className="px-3 pb-2 flex flex-wrap gap-1.5">
              {STARTERS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => ask(prompt)}
                  className="text-[11px] px-2 py-1 rounded-full border border-paper-300 bg-white text-ink-700 hover:border-ink-900"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          <form
            className="border-t border-paper-200 p-2 flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              ask(draft);
            }}
          >
            <input
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask a travel question"
              className="min-w-0 flex-1 text-sm bg-white border border-paper-300 rounded-lg px-3 py-2 focus:outline-none focus:border-ink-900"
              disabled={busy}
            />
            <button
              type="submit"
              disabled={busy || !draft.trim()}
              className="px-3 rounded-lg bg-ink-900 text-paper-50 disabled:opacity-40"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="h-12 px-4 rounded-full bg-ink-900 text-paper-50 shadow-lg flex items-center gap-2 hover:bg-ink-800"
      >
        <MessageCircle className="w-5 h-5" />
        <span className="text-sm font-semibold">{open ? 'Close' : 'Travel chat'}</span>
      </button>
    </div>
  );
}
