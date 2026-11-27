// src/pages/HomePage.tsx
import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  ArrowRight,
  Code2,
  Sparkles,
  Terminal,
  Trash2,
  CheckCircle2,
  Circle,
  LayoutList,
} from 'lucide-react';
import Button from '../components/ui/Button';

interface LocalSession {
  id: string;
  preview: string;
}

function loadLocalSessions(): LocalSession[] {
  const sessions: LocalSession[] = [];
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith('workspace:')) {
        const id = key.slice('workspace:'.length);
        const content = localStorage.getItem(key) ?? '';
        if (id && content.trim()) {
          sessions.push({
            id,
            preview: content.trim().split('\n')[0].slice(0, 100),
          });
        }
      }
    }
  } catch {
    // Ignore storage access errors
  }
  return sessions;
}

const STRUCTURE_SCAFFOLD = `Problem:


Input Format:


Output Format:


Constraints:
`;

const HomePage: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [error, setError] = useState('');
  const [recentSessions, setRecentSessions] = useState<LocalSession[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    setRecentSessions(loadLocalSessions());
  }, []);

  // Live readiness hints so the AI testcase generator has what it requires
  const readiness = useMemo(() => {
    const lower = question.toLowerCase();
    return {
      hasDescription: question.trim().length >= 20,
      hasInput: /\b(input|given|array|list|string|integer|tree|graph|matrix|nums|params?)\b/.test(lower),
      hasOutput: /\b(output|return|find|determine|print|count|indices)\b/.test(lower),
      hasConstraints: /\b(constraint|<=|>=|<|>|10\^|bounds?|length|range)\b/.test(lower),
    };
  }, [question]);

  const insertStructure = () => {
    setQuestion((prev) => {
      if (!prev.trim()) return STRUCTURE_SCAFFOLD;
      return `Problem:\n${prev.trim()}\n\nInput Format:\n\n\nOutput Format:\n\n\nConstraints:\n`;
    });
    if (error) setError('');
  };

  const startSession = () => {
    const trimmed = question.trim();
    if (!trimmed) {
      setError('Please enter a DSA problem statement before starting.');
      return;
    }
    setError('');
    const sessionId =
      typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID()
        : Date.now().toString();
    try {
      localStorage.setItem(`workspace:${sessionId}`, trimmed);
    } catch {
      // ignore storage errors
    }
    navigate(`/problems/${sessionId}`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    startSession();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      startSession();
    }
  };

  const deleteSession = (id: string) => {
    try {
      localStorage.removeItem(`workspace:${id}`);
      localStorage.removeItem(`workspace-testcases:${id}`);
      localStorage.removeItem(`workspace-lang:${id}`);
    } catch {
      // Ignore storage errors
    }
    setRecentSessions((prev) => prev.filter((s) => s.id !== id));
  };

  const checklistItems = [
    { label: 'Problem goal', met: readiness.hasDescription },
    { label: 'Input format', met: readiness.hasInput },
    { label: 'Expected output', met: readiness.hasOutput },
    { label: 'Constraints', met: readiness.hasConstraints },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 md:py-16">
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/15 border border-primary/30 text-primary-light text-xs font-medium mb-5">
          <Sparkles className="w-3.5 h-3.5" />
          <span>AI Test Generation · Monaco Editor · Judge0 Execution</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-bold tracking-tight text-white mb-4">
          What problem are we solving today?
        </h1>
        <p className="text-sm md:text-base text-text-muted max-w-xl mx-auto">
          Paste or describe your DSA problem statement below. Including the input format, expected output, and constraints lets the AI generate accurate test cases.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-surface border border-border rounded-2xl p-4 shadow-xl shadow-black/30"
      >
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <label htmlFor="problem-composer" className="text-xs font-medium text-text-muted">
            Problem Specification
          </label>
          <button
            type="button"
            onClick={insertStructure}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-surface-elevated border border-border text-text-muted hover:text-white hover:border-border-light transition-colors"
            title="Insert empty section headings to organize your problem"
          >
            <LayoutList className="w-3.5 h-3.5 text-primary-light" />
            Insert Structure
          </button>
        </div>

        <textarea
          id="problem-composer"
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value);
            if (error) setError('');
          }}
          onKeyDown={handleKeyDown}
          placeholder={`Describe your problem with input, output, and constraints.\n\nFor example:\nGiven an array of integers nums and an integer target, return indices of the two numbers that add up to target.\nInput: dict {"nums": list[int], "target": int}\nOutput: list[int] of two indices\nConstraints: 2 <= len(nums) <= 10^4`}
          rows={8}
          className="w-full p-3 rounded-xl border border-border bg-surface-dark text-text text-sm md:text-base leading-relaxed placeholder:text-text-muted/55 focus:outline-none focus:ring-2 focus:ring-primary resize-y"
        />

        {/* Readiness checklist for AI test case generation */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 mt-3 px-1">
          <span className="text-xs text-text-muted">AI test generation readiness:</span>
          {checklistItems.map((item) => (
            <span
              key={item.label}
              className={`inline-flex items-center gap-1 text-xs ${
                item.met ? 'text-accent' : 'text-text-muted'
              }`}
            >
              {item.met ? (
                <CheckCircle2 className="w-3.5 h-3.5" />
              ) : (
                <Circle className="w-3.5 h-3.5 opacity-60" />
              )}
              {item.label}
            </span>
          ))}
        </div>

        {error && (
          <p role="alert" className="text-danger text-sm mt-2.5">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center justify-between gap-3 mt-4 pt-3 border-t border-border">
          <span className="text-xs text-text-muted">
            Tip: Press <kbd className="px-1.5 py-0.5 rounded bg-surface-elevated border border-border text-text">Ctrl</kbd> +{' '}
            <kbd className="px-1.5 py-0.5 rounded bg-surface-elevated border border-border text-text">Enter</kbd> to launch
          </span>
          <Button type="submit" variant="primary" size="lg">
            Start Coding
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </form>

      {/* Capability overview (real platform features, no fabricated stats) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-8">
        <div className="p-4 rounded-xl border border-border bg-surface/60">
          <Code2 className="w-4 h-4 text-primary-light mb-2" />
          <h2 className="text-sm font-semibold text-white mb-1">Monaco Code Editor</h2>
          <p className="text-xs text-text-muted">
            Multi-language syntax highlighting with automatic per-language browser drafts.
          </p>
        </div>
        <div className="p-4 rounded-xl border border-border bg-surface/60">
          <Sparkles className="w-4 h-4 text-primary-light mb-2" />
          <h2 className="text-sm font-semibold text-white mb-1">AI Test Case Synthesis</h2>
          <p className="text-xs text-text-muted">
            Explicitly generate edge cases and boundary inputs from your problem statement.
          </p>
        </div>
        <div className="p-4 rounded-xl border border-border bg-surface/60">
          <Terminal className="w-4 h-4 text-primary-light mb-2" />
          <h2 className="text-sm font-semibold text-white mb-1">Judge0 Evaluation</h2>
          <p className="text-xs text-text-muted">
            Sandboxed execution returning real verdicts, outputs, timing, and memory.
          </p>
        </div>
      </div>

      {/* Real user-created sessions from localStorage (only shown when non-empty) */}
      {recentSessions.length > 0 && (
        <section className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-text-muted mb-3">
            Your Local Workspace Sessions
          </h2>
          <div className="space-y-2">
            {recentSessions.map((s) => (
              <div
                key={s.id}
                className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl border border-border bg-surface hover:border-border-light transition-colors"
              >
                <Link
                  to={`/problems/${s.id}`}
                  className="text-sm text-text hover:text-primary-light truncate flex-1"
                >
                  {s.preview}
                </Link>
                <div className="flex items-center gap-2 shrink-0">
                  <Button as={Link} to={`/problems/${s.id}`} variant="secondary" size="sm">
                    Resume
                  </Button>
                  <button
                    type="button"
                    onClick={() => deleteSession(s.id)}
                    aria-label="Delete local session"
                    className="p-1.5 rounded-md text-text-muted hover:text-danger hover:bg-surface-elevated"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default HomePage;
