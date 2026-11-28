// src/features/workspace/similarUtils.ts
import type { PlatformKey, SimilarProblemItem, SimilarProblemsResponse } from '../../types/similar';

export type DifficultyFilter = 'all' | 'easy' | 'medium' | 'hard';

export interface SimilarFilterOptions {
  difficulty: DifficultyFilter;
  topic: string;
  hideSolved: boolean;
  solvedUrls: Set<string>;
}

/**
 * Maps platform-specific difficulty labels or numeric ratings (e.g. Codeforces 1200)
 * into uniform Easy / Medium / Hard buckets for UI filtering.
 */
export function normalizeDifficultyBucket(difficulty?: string | null): Exclude<DifficultyFilter, 'all'> | null {
  if (!difficulty) return null;
  const trimmed = difficulty.trim().toLowerCase();
  if (trimmed === 'easy' || trimmed === 'medium' || trimmed === 'hard') {
    return trimmed;
  }
  const numeric = Number(trimmed);
  if (Number.isFinite(numeric) && numeric > 0) {
    if (numeric <= 1200) return 'easy';
    if (numeric <= 1700) return 'medium';
    return 'hard';
  }
  return null;
}

/** Returns deduplicated problem items for the selected platform tab. */
export function getPlatformItems(
  data: SimilarProblemsResponse | null,
  platform: PlatformKey
): SimilarProblemItem[] {
  if (!data) return [];
  const raw = data[platform] ?? [];
  const seen = new Set<string>();
  return raw.filter((item) => {
    if (seen.has(item.url)) return false;
    seen.add(item.url);
    return true;
  });
}

export function extractTopicOptions(items: SimilarProblemItem[]): string[] {
  const tags = new Set<string>();
  for (const item of items) {
    for (const tag of item.tags) {
      const clean = tag.trim();
      if (clean) tags.add(clean);
    }
  }
  return Array.from(tags).sort((a, b) => a.localeCompare(b));
}

/** Filters problems by difficulty bucket, selected topic tag, and solved state. */
export function filterSimilarProblems(
  items: SimilarProblemItem[],
  filters: SimilarFilterOptions
): SimilarProblemItem[] {
  return items.filter((item) => {
    if (filters.hideSolved && filters.solvedUrls.has(item.url)) {
      return false;
    }
    if (filters.difficulty !== 'all') {
      const bucket = normalizeDifficultyBucket(item.difficulty);
      if (bucket !== filters.difficulty) return false;
    }
    if (filters.topic) {
      const target = filters.topic.toLowerCase();
      const hasTopic = item.tags.some((t) => t.toLowerCase() === target);
      if (!hasTopic) return false;
    }
    return true;
  });
}

export function toggleSolvedUrl(current: Set<string>, url: string): Set<string> {
  const next = new Set(current);
  if (next.has(url)) {
    next.delete(url);
  } else {
    next.add(url);
  }
  return next;
}
