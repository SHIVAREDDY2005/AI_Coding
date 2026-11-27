// src/data/problems.ts
/**
 * Placeholder for real problem data.
 * The backend does not currently provide a problem catalogue endpoint, 
 * so this file exports an empty array. When a proper API becomes available, 
 * it should be replaced with a data fetch or generated list.
 */
export interface Problem {
  id: string;
  title: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  tags: string[];
  description: string;
}

export const problems: Problem[] = [];
