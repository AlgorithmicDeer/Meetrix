/**
 * Ask Page - Natural language insights chat interface.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useSession } from '@/contexts/SessionContext';
import { queryInsights } from '@/lib/api';
import { Spinner } from '@/components/ui/Spinner';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const SUGGESTIONS = [
  'Which meetings cost the most?',
  'Who is most overloaded?',
  'What should I cancel first?',
  'Show me cascade chains',
  'What are my worst recurring meetings?',
  'What is the total cost of status update meetings?',
];

export function Ask() {
  const { sessionId, results } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (!sessionId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="font-mono text-6xl">✦(•‿•)✦</div>
        <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black">
          RUN AN ANALYSIS FIRST
        </p>
        <Link
          to="/settings"
          className="border-2 border-kb-black bg-kb-pink px-6 py-3 font-mono font-bold text-sm uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          Go to Settings
        </Link>
      </div>
    );
  }

  const handleSubmit = async (query: string) => {
    const trimmed = query.trim();
    if (!trimmed || isLoading) return;

    const userMessage: Message = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await queryInsights({
        session_id: sessionId,
        query: trimmed,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        role: 'assistant',
        content:
          err instanceof Error
            ? `Error: ${err.message}`
            : 'Sorry, I could not process your query. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-10rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="font-display font-black text-3xl uppercase">ASK MEETRIX</h1>
        {results && (
          <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
            {results.summary_stats.total_meetings} MEETINGS IN CONTEXT
          </span>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 py-4 pr-2">
        {/* Suggestion chips */}
        {messages.length === 0 && (
          <div className="mb-6">
            <p className="font-mono text-xs uppercase tracking-widest text-kb-black/50 mb-4">
              TRY ASKING:
            </p>
            <div className="flex flex-wrap gap-3">
              {SUGGESTIONS.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => handleSubmit(suggestion)}
                  className="border-2 border-kb-black bg-kb-lavender px-4 py-2 font-mono font-bold text-xs uppercase shadow-brutal-sm hover:bg-kb-pink hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none cursor-pointer transition-all duration-75"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat messages */}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'user' ? (
              <div className="bg-kb-lavender border-2 border-kb-black shadow-brutal-sm p-4 ml-12 max-w-[80%]">
                <p className="font-sans text-sm text-kb-black">{msg.content}</p>
              </div>
            ) : (
              <div className="bg-kb-white border-2 border-kb-black shadow-brutal-md p-6 mr-12 max-w-[85%]">
                <div className="flex items-center gap-2 mb-3">
                  <span className="font-mono text-xs text-kb-black/50">✦(•‿•)✦</span>
                  <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50">
                    MEETRIX
                  </span>
                </div>
                <p className="font-sans text-sm text-kb-black leading-relaxed whitespace-pre-wrap">
                  {msg.content}
                </p>
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-kb-white border-2 border-kb-black shadow-brutal-md p-6 mr-12 max-w-[85%]">
              <div className="flex items-center gap-2 mb-3">
                <span className="font-mono text-xs text-kb-black/50">✦(•‿•)✦</span>
                <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50">
                  MEETRIX
                </span>
              </div>
              <div className="flex items-center gap-3">
                <Spinner className="w-5 h-5" />
                <span className="font-mono font-bold text-xs uppercase tracking-widest animate-pulse text-kb-black/60">
                  THINKING...
                </span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="sticky bottom-0 border-t-3 border-kb-black bg-kb-cream pt-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your meetings... (Enter to send, Shift+Enter for newline)"
            className="flex-1 border-3 border-kb-black bg-kb-white p-4 font-sans text-base resize-none focus:outline-none focus:shadow-brutal-sm transition-all duration-75 h-16"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSubmit(input)}
            disabled={isLoading || !input.trim()}
            className="bg-kb-pink border-3 border-kb-black shadow-brutal-sm px-8 py-4 font-mono font-bold text-sm uppercase tracking-widest hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-kb-muted flex-shrink-0"
          >
            SEND
          </button>
        </div>
      </div>
    </div>
  );
}

// Made with Bob
