// src/features/workspace/AiMentorChat.tsx
import React, { useEffect, useRef } from 'react';
import { Sparkles, AlertTriangle } from 'lucide-react';
import Button from '../../components/ui/Button';
import type { AiMentorMessage } from '../../types/ai';

interface AiMentorChatProps {
  messages: AiMentorMessage[];
  loading: boolean;
  languageName?: string;
  testcaseCount: number;
  hasCode: boolean;
  feedbackFocus: string;
  customPrompt: string;
  onChangeCustomPrompt: (val: string) => void;
  onSelectMode: (modeId: string) => void;
  onSend: () => void;
}

const FOCUS_MODES = [
  { id: 'auto', label: 'Auto' },
  { id: 'optimize', label: 'Optimize' },
  { id: 'debug', label: 'Fix Errors' },
  { id: 'edge_cases', label: 'Edge Cases' },
];

export const AiMentorChat: React.FC<AiMentorChatProps> = ({
  messages,
  loading,
  languageName,
  testcaseCount,
  hasCode,
  feedbackFocus,
  customPrompt,
  onChangeCustomPrompt,
  onSelectMode,
  onSend,
}) => {
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      {/* Scrollable Chat Thread */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4 space-y-3">
        {messages.length === 0 && !loading ? (
          <div className="py-8 text-center text-xs text-text-muted space-y-2">
            <Sparkles className="w-5 h-5 text-primary-light mx-auto" />
            <p className="text-text font-medium">AI Mentor Chat</p>
            <p>
              Ask a question below or pick a quick action to get feedback on your{' '}
              {languageName ?? 'code'} and {testcaseCount} test case
              {testcaseCount === 1 ? '' : 's'}.
            </p>
          </div>
        ) : (
          messages.map((msg) =>
            msg.role === 'user' ? (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-[85%] px-3 py-2 rounded-xl rounded-br-sm bg-primary/20 border border-primary/40 text-xs text-white">
                  {msg.text}
                </div>
              </div>
            ) : msg.error ? (
              <div
                key={msg.id}
                className="flex items-start gap-2 text-xs text-danger p-3 rounded-xl bg-danger/10 border border-danger/30"
              >
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{msg.error}</span>
              </div>
            ) : msg.suggestion ? (
              <div
                key={msg.id}
                className="p-3 rounded-xl rounded-bl-sm bg-surface-dark border border-border space-y-2.5 text-xs leading-relaxed"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-text-muted font-semibold">Focus:</span>
                  <span className="px-2 py-0.5 rounded bg-primary/15 text-primary-light font-medium">
                    {msg.suggestion.mistake_type}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-surface border border-border">
                  <p className="text-text-muted font-semibold mb-1">Analysis</p>
                  <p className="text-text">{msg.suggestion.issue}</p>
                </div>
                <div className="p-2.5 rounded-lg bg-accent/10 border border-accent/30">
                  <p className="text-accent font-semibold mb-1">Guidance</p>
                  <p className="text-text">{msg.suggestion.hint}</p>
                </div>
                {msg.suggestion.complexity && (
                  <div className="p-2.5 rounded-lg bg-surface border border-border">
                    <p className="text-text-muted font-semibold mb-1">Complexity</p>
                    <p className="text-text">{msg.suggestion.complexity}</p>
                  </div>
                )}
                {msg.suggestion.optimization && (
                  <div className="p-2.5 rounded-lg bg-primary/10 border border-primary/30">
                    <p className="text-primary-light font-semibold mb-1">Optimization</p>
                    <p className="text-text">{msg.suggestion.optimization}</p>
                  </div>
                )}
              </div>
            ) : null
          )
        )}

        {loading && (
          <div className="p-3 rounded-xl bg-surface-dark border border-border text-xs text-primary-light">
            Analyzing your {languageName ?? 'code'} and {testcaseCount} test case
            {testcaseCount === 1 ? '' : 's'}...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Pinned Chat Composer */}
      <div className="p-3 border-t border-border bg-surface-dark space-y-2">
        <div className="flex flex-wrap gap-1.5">
          {FOCUS_MODES.map((mode) => (
            <button
              key={mode.id}
              type="button"
              onClick={() => onSelectMode(mode.id)}
              disabled={loading || !hasCode}
              className={`px-2 py-0.5 rounded text-[11px] font-medium border transition-colors ${
                feedbackFocus === mode.id && !customPrompt.trim()
                  ? 'bg-primary/20 border-primary text-white'
                  : 'bg-surface border-border text-text-muted hover:text-text'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onSend();
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={customPrompt}
            onChange={(e) => onChangeCustomPrompt(e.target.value)}
            placeholder="Ask a follow-up or how you want feedback..."
            className="flex-1 px-3 py-1.5 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-text-muted/60 focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Button
            type="submit"
            variant="primary"
            size="sm"
            loading={loading}
            disabled={loading || !hasCode}
          >
            Send
          </Button>
        </form>
      </div>
    </div>
  );
};
