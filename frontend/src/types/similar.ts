// src/types/similar.ts

export type PlatformKey = 'leetcode' | 'codechef' | 'codeforces';

export interface SimilarProblemItem {
  title: string;
  platform: PlatformKey | string;
  url: string;
  similarity_score: number;
  difficulty?: string | null;
  tags: string[];
  reason: string;
}

export interface SimilarProblemsResponse {
  leetcode: SimilarProblemItem[];
  codechef: SimilarProblemItem[];
  codeforces: SimilarProblemItem[];
  platform_status?: Record<string, string>;
  model_used?: string | null;
}
