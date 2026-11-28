// src/services/similarService.ts
import apiClient from './apiClient';
import type { PlatformKey, SimilarProblemsResponse } from '../types/similar';

export interface FindSimilarOptions {
  refresh?: boolean;
  platform?: PlatformKey;
  solvedUrls?: string[];
  attemptedUrls?: string[];
  excludeSolved?: boolean;
  targetDifficulty?: string;
}

/**
 * Find similar problems on LeetCode, CodeChef, and Codeforces.
 * Calls POST /api/v1/problems/similar
 */
export const findSimilarProblems = async (
  problem: string,
  options: FindSimilarOptions = {}
): Promise<SimilarProblemsResponse> => {
  const response = await apiClient.post<SimilarProblemsResponse>(
    '/problems/similar',
    {
      problem,
      refresh: options.refresh ?? false,
      platform: options.platform,
      solved_urls: options.solvedUrls ?? [],
      attempted_urls: options.attemptedUrls ?? [],
      exclude_solved: options.excludeSolved ?? false,
      target_difficulty: options.targetDifficulty,
    }
  );
  return response.data;
};
