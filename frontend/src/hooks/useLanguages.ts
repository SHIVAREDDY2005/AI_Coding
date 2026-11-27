// src/hooks/useLanguages.ts
import { useState, useEffect, useCallback } from 'react';
import type { LanguageInfo } from '../types/language';
import { fetchLanguages } from '../services/languageService';
import { extractApiErrorMessage } from '../services/apiClient';

export const useLanguages = () => {
  const [languages, setLanguages] = useState<LanguageInfo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLanguages();
      setLanguages(Array.isArray(data.languages) ? data.languages : []);
    } catch (e: unknown) {
      setError(extractApiErrorMessage(e, 'Failed to load supported languages'));
      setLanguages([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { languages, loading, error, refetch: load };
};
