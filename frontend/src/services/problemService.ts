// src/services/problemService.ts
import { problems } from '../data/problems';
import type { Problem } from '../data/problems';

/**
 * Simple client-side service for problem catalogue.
 * All operations are performed on the static in-memory list.
 */
export const getAllProblems = (): Problem[] => {
  return [...problems];
};

export const getProblemById = (id: string): Problem | undefined => {
  return problems.find((p) => p.id === id);
};

export const getUniqueTags = (): string[] => {
  const tags = new Set<string>();
  problems.forEach((p) => p.tags.forEach((t) => tags.add(t)));
  return Array.from(tags).sort();
};

export const getUniqueDifficulties = (): ('Easy' | 'Medium' | 'Hard')[] => {
  const diffs: ('Easy' | 'Medium' | 'Hard')[] = ['Easy', 'Medium', 'Hard'];
  return diffs;
};
