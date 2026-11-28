// src/features/workspace/SimilarProblemsPanel.tsx
import React, { useState, useMemo } from 'react';
import { ExternalLink, RefreshCw, Sparkles, AlertTriangle, CheckCircle2, Circle } from 'lucide-react';
import Button from '../../components/ui/Button';
import type { PlatformKey, SimilarProblemsResponse } from '../../types/similar';
import {
  extractTopicOptions,
  filterSimilarProblems,
  getPlatformItems,
  toggleSolvedUrl,
  type DifficultyFilter,
} from './similarUtils';

interface SimilarProblemsPanelProps {
  problem: string;
  data: SimilarProblemsResponse | null;
  loading: boolean;
  refreshingPlatform: PlatformKey | null;
  error: string | null;
  onFindSimilar: (refresh?: boolean, platform?: PlatformKey) => void;
}

const SOLVED_STORAGE_KEY = 'similar-problems:solved-urls';

const PLATFORMS: Array<{ key: PlatformKey; label: string }> = [
  { key: 'codeforces', label: 'Codeforces' },
  { key: 'codechef', label: 'CodeChef' },
  { key: 'leetcode', label: 'LeetCode' },
];

function loadSolvedUrls(): Set<string> {
  try {
    const raw = localStorage.getItem(SOLVED_STORAGE_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? new Set(parsed.filter((x) => typeof x === 'string')) : new Set();
  } catch {
    return new Set();
  }
}

function scoreBadgeClass(score: number): string {
  if (score >= 80) return 'bg-accent/15 text-accent border-accent/30';
  if (score >= 60) return 'bg-primary/15 text-primary-light border-primary/30';
  return 'bg-surface-elevated text-text-muted border-border';
}

function scoreBarClass(score: number): string {
  if (score >= 80) return 'bg-accent';
  if (score >= 60) return 'bg-primary';
  return 'bg-text-muted';
}

export const SimilarProblemsPanel: React.FC<SimilarProblemsPanelProps> = ({
  problem,
  data,
  loading,
  refreshingPlatform,
  error,
  onFindSimilar,
}) => {
  const [platform, setPlatform] = useState<PlatformKey>('codeforces');
  const [difficulty, setDifficulty] = useState<DifficultyFilter>('all');
  const [topic, setTopic] = useState<string>('');
  const [hideSolved, setHideSolved] = useState<boolean>(false);
  const [solvedUrls, setSolvedUrls] = useState<Set<string>>(() => loadSolvedUrls());

  const rawItems = useMemo(() => getPlatformItems(data, platform), [data, platform]);
  const topicOptions = useMemo(() => extractTopicOptions(rawItems), [rawItems]);

  const filteredItems = useMemo(
    () =>
      filterSimilarProblems(rawItems, {
        difficulty,
        topic: topicOptions.includes(topic) ? topic : '',
        hideSolved,
        solvedUrls,
      }),
    [rawItems, difficulty, topic, topicOptions, hideSolved, solvedUrls]
  );

  const platformStatus = data?.platform_status?.[platform];

  const handleToggleSolved = (e: React.MouseEvent, url: string) => {
    e.preventDefault();
    e.stopPropagation();
    setSolvedUrls((prev) => {
      const next = toggleSolvedUrl(prev, url);
      try {
        localStorage.setItem(SOLVED_STORAGE_KEY, JSON.stringify(Array.from(next)));
      } catch {
        // Ignore storage errors
      }
      return next;
    });
  };

  const resetFilters = () => {
    setDifficulty('all');
    setTopic('');
    setHideSolved(false);
  };

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      {/* Platform Sub-Tabs + Search Action */}
      <div className="px-3 py-2.5 border-b border-border bg-surface-dark space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div role="tablist" aria-label="Coding platforms" className="flex items-center gap-1">
            {PLATFORMS.map((p) => {
              const count = data ? getPlatformItems(data, p.key).length : 0;
              const active = platform === p.key;
              const isRefreshingThis = loading && refreshingPlatform === p.key;
              return (
                <div key={p.key} className="inline-flex items-center gap-0.5">
                  <button
                    type="button"
                    role="tab"
                    aria-selected={active}
                    onClick={() => {
                      setPlatform(p.key);
                      setTopic('');
                    }}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors inline-flex items-center gap-1.5 ${
                      active
                        ? 'bg-surface-elevated text-white'
                        : 'text-text-muted hover:text-text'
                    }`}
                  >
                    <span>{p.label}</span>
                    {data && (
                      <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-surface text-text-muted">
                        {count}
                      </span>
                    )}
                  </button>
                  {data && (
                    <button
                      type="button"
                      disabled={loading || !problem.trim()}
                      onClick={() => {
                        setPlatform(p.key);
                        onFindSimilar(true, p.key);
                      }}
                      title={`Refresh ${p.label}`}
                      aria-label={`Refresh ${p.label}`}
                      className="p-1 rounded text-text-muted hover:text-primary-light disabled:opacity-40 transition-colors"
                    >
                      <RefreshCw className={`w-3 h-3 ${isRefreshingThis ? 'animate-spin text-primary-light' : ''}`} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <Button
            type="button"
            variant={data ? 'secondary' : 'primary'}
            size="sm"
            loading={loading && !refreshingPlatform}
            disabled={loading || !problem.trim()}
            onClick={() => onFindSimilar(Boolean(data))}
          >
            {data ? <RefreshCw className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
            {loading && !refreshingPlatform ? 'Searching...' : data ? 'Refresh All' : 'Find Similar'}
          </Button>
        </div>

        {/* Filters */}
        {data && (
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <select
              aria-label="Filter by difficulty"
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value as DifficultyFilter)}
              className="px-2 py-1 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="all">All Difficulties</option>
              <option value="easy">Easy (≤1200)</option>
              <option value="medium">Medium (1201–1700)</option>
              <option value="hard">Hard (&gt;1700)</option>
            </select>

            <select
              aria-label="Filter by topic"
              value={topicOptions.includes(topic) ? topic : ''}
              onChange={(e) => setTopic(e.target.value)}
              className="px-2 py-1 text-xs rounded-md border border-border bg-surface text-text focus:outline-none focus:ring-1 focus:ring-primary max-w-[150px]"
            >
              <option value="">All Topics</option>
              {topicOptions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>

            <label className="inline-flex items-center gap-1.5 text-xs text-text-muted cursor-pointer select-none ml-auto">
              <input
                type="checkbox"
                checked={hideSolved}
                onChange={(e) => setHideSolved(e.target.checked)}
                className="rounded border-border bg-surface text-primary focus:ring-primary"
              />
              Hide solved
            </label>
          </div>
        )}
      </div>

      {/* Results Body */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar p-4 space-y-3">
        {error && (
          <div className="flex items-start gap-2 text-xs text-danger p-3 rounded-lg bg-danger/10 border border-danger/30">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {loading && (
          <div className="py-8 text-center text-xs text-primary-light">
            Querying live catalogs and computing similarity scores...
          </div>
        )}

        {!loading && !data && !error && (
          <div className="py-10 text-center text-xs text-text-muted space-y-3">
            <Sparkles className="w-5 h-5 text-primary-light mx-auto" />
            <p className="text-text font-medium">Find Verified Similar Problems</p>
            <p className="max-w-xs mx-auto">
              Matches real problems from live platform catalogs using semantic similarity, topic overlap, and algorithm matching.
            </p>
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={!problem.trim()}
              onClick={() => onFindSimilar(false)}
            >
              <Sparkles className="w-3.5 h-3.5" />
              Find Similar Problems
            </Button>
          </div>
        )}

        {!loading &&
          data &&
          platformStatus &&
          !platformStatus.startsWith('live') &&
          !platformStatus.startsWith('imported') && (
          <div className="flex items-start gap-2 text-xs text-warning p-3 rounded-lg bg-warning/10 border border-warning/30">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>
              <strong>{PLATFORMS.find((p) => p.key === platform)?.label}:</strong> {platformStatus}
            </span>
          </div>
        )}

        {!loading && data && rawItems.length > 0 && filteredItems.length === 0 && (
          <div className="py-8 text-center text-xs text-text-muted space-y-2">
            <p>No problems match your current filters.</p>
            <Button type="button" variant="secondary" size="sm" onClick={resetFilters}>
              Clear filters
            </Button>
          </div>
        )}

        {!loading &&
          data &&
          rawItems.length === 0 &&
          !error &&
          (!platformStatus || platformStatus.startsWith('live') || platformStatus.startsWith('imported')) && (
          <div className="py-8 text-center text-xs text-text-muted">
            No matching problems found for {PLATFORMS.find((p) => p.key === platform)?.label}.
          </div>
        )}

        {!loading && filteredItems.length > 0 && (
          <div className="space-y-2.5">
            {filteredItems.map((item) => {
              const isSolved = solvedUrls.has(item.url);
              return (
                <a
                  key={`${platform}-${item.url}`}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block p-3 rounded-xl border transition-colors group ${
                    isSolved
                      ? 'border-accent/40 bg-accent/5'
                      : 'border-border bg-surface-dark hover:border-primary/60 hover:bg-surface-elevated/60'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className="text-sm font-semibold text-white group-hover:text-primary-light truncate">
                        {item.title}
                      </span>
                      <ExternalLink className="w-3.5 h-3.5 text-text-muted group-hover:text-primary-light shrink-0" />
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <button
                        type="button"
                        onClick={(e) => handleToggleSolved(e, item.url)}
                        title={isSolved ? 'Marked as solved (click to unmark)' : 'Mark as solved'}
                        aria-label={isSolved ? `Unmark ${item.title} as solved` : `Mark ${item.title} as solved`}
                        className={`p-0.5 rounded transition-colors ${
                          isSolved ? 'text-accent' : 'text-text-muted hover:text-text'
                        }`}
                      >
                        {isSolved ? <CheckCircle2 className="w-4 h-4" /> : <Circle className="w-4 h-4" />}
                      </button>
                      <span
                        className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${scoreBadgeClass(
                          item.similarity_score
                        )}`}
                        title="Similarity score out of 100"
                      >
                        {item.similarity_score}/100
                      </span>
                    </div>
                  </div>

                  {/* Similarity Progress Bar */}
                  <div className="w-full h-1.5 rounded-full bg-surface overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full ${scoreBarClass(item.similarity_score)}`}
                      style={{ width: `${item.similarity_score}%` }}
                    />
                  </div>

                  <p className="text-xs text-text-muted leading-relaxed mb-2">{item.reason}</p>

                  <div className="flex flex-wrap items-center gap-1.5">
                    {item.difficulty && (
                      <span className="px-2 py-0.5 rounded bg-surface border border-border text-[11px] font-medium text-text">
                        {item.difficulty}
                      </span>
                    )}
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-0.5 rounded bg-surface border border-border text-[11px] text-text-muted"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </a>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
