// src/hooks/useSimilarProblems.ts
import { useState, useCallback, useRef, useEffect } from 'react';
import { findSimilarProblems } from '../services/similarService';
import { extractApiErrorMessage } from '../services/apiClient';
import type { PlatformKey, SimilarProblemsResponse } from '../types/similar';

const SOLVED_STORAGE_KEY = 'similar-problems:solved-urls';

function readSolvedUrlsFromStorage(): string[] {
  try {
    const raw = localStorage.getItem(SOLVED_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((x): x is string => typeof x === 'string') : [];
  } catch {
    return [];
  }
}

export const useSimilarProblems = (sessionId: string) => {
  const [data, setData] = useState<SimilarProblemsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshingPlatform, setRefreshingPlatform] = useState<PlatformKey | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  useEffect(() => {
    setData(null);
    setError(null);
    setRefreshingPlatform(null);
  }, [sessionId]);

  const fetchSimilar = useCallback(
    async (problem: string, refresh = false, platform?: PlatformKey) => {
      const trimmed = problem.trim();
      if (trimmed.length < 5) {
        setError('Problem statement must be at least 5 characters to find similar problems.');
        return;
      }
      if (inFlightRef.current) return;

      inFlightRef.current = true;
      setLoading(true);
      setRefreshingPlatform(platform ?? null);
      setError(null);

      try {
        const solvedUrls = readSolvedUrlsFromStorage();
        const res = await findSimilarProblems(trimmed, { refresh, platform, solvedUrls });
        if (platform) {
          setData((prev) => {
            if (!prev) return res;
            return {
              ...prev,
              [platform]: res[platform],
              platform_status: {
                ...(prev.platform_status ?? {}),
                ...(res.platform_status ?? {}),
              },
              model_used: res.model_used ?? prev.model_used,
            };
          });
        } else {
          setData(res);
        }
      } catch (err: unknown) {
        setError(extractApiErrorMessage(err, 'Failed to find similar problems'));
      } finally {
        inFlightRef.current = false;
        setLoading(false);
        setRefreshingPlatform(null);
      }
    },
    []
  );

  const resetSimilar = useCallback(() => {
    setData(null);
    setError(null);
    setRefreshingPlatform(null);
  }, []);

  return { data, loading, refreshingPlatform, error, fetchSimilar, resetSimilar };
};
