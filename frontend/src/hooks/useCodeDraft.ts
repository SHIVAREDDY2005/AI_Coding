// src/hooks/useCodeDraft.ts
import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Manages a code draft persisted to localStorage per workspace session and language.
 * Key format: workspace-code:<sessionId>:<languageId>
 * Uses a ref to avoid overwriting a newly selected language's draft with the previous language's code.
 */
export const useCodeDraft = (sessionId: string, languageId: number | null) => {
  const storageKey = languageId !== null ? `workspace-code:${sessionId}:${languageId}` : null;
  const loadedKeyRef = useRef<string | null>(null);

  const [code, setCodeState] = useState<string>(() => {
    if (!storageKey) return '';
    try {
      return localStorage.getItem(storageKey) ?? '';
    } catch {
      return '';
    }
  });

  useEffect(() => {
    loadedKeyRef.current = storageKey;
    if (!storageKey) {
      setCodeState('');
      return;
    }
    try {
      const saved = localStorage.getItem(storageKey);
      setCodeState(saved ?? '');
    } catch {
      setCodeState('');
    }
  }, [storageKey]);

  const setCode = useCallback(
    (nextCode: string) => {
      setCodeState(nextCode);
      const key = loadedKeyRef.current;
      if (key) {
        try {
          if (nextCode === '') {
            localStorage.removeItem(key);
          } else {
            localStorage.setItem(key, nextCode);
          }
        } catch {
          // Ignore storage quota errors
        }
      }
    },
    []
  );

  const resetDraft = useCallback(() => {
    setCodeState('');
    if (storageKey) {
      try {
        localStorage.removeItem(storageKey);
      } catch {
        // Ignore storage errors
      }
    }
  }, [storageKey]);

  return { code, setCode, resetDraft };
};
