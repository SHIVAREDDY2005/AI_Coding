// src/hooks/useTestcases.ts
import { useState, useEffect, useCallback, useRef } from 'react';
import { generateTestcases } from '../services/testcaseService';
import { extractApiErrorMessage } from '../services/apiClient';
import type { JudgeTestCase } from '../types/judge';

export interface EditableTestcase {
  id: string;
  inputText: string;
  expectedText: string;
}

function serializeValue(val: unknown): string {
  if (val === undefined) return '';
  try {
    return JSON.stringify(val);
  } catch {
    return String(val);
  }
}

function createId(): string {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export const useTestcases = (sessionId: string) => {
  const storageKey = `workspace-testcases:${sessionId}`;

  const [testcases, setTestcases] = useState<EditableTestcase[]>(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) return parsed;
      }
    } catch {
      // Ignore invalid storage
    }
    return [];
  });

  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [modelUsed, setModelUsed] = useState<string | null>(null);
  const generatingRef = useRef(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        setTestcases(Array.isArray(parsed) ? parsed : []);
      } else {
        setTestcases([]);
      }
    } catch {
      setTestcases([]);
    }
    setGenerationError(null);
    setModelUsed(null);
  }, [storageKey]);

  useEffect(() => {
    try {
      if (testcases.length === 0) {
        localStorage.removeItem(storageKey);
      } else {
        localStorage.setItem(storageKey, JSON.stringify(testcases));
      }
    } catch {
      // Ignore storage quota errors
    }
  }, [testcases, storageKey]);

  const addTestcase = useCallback(() => {
    setTestcases((prev) => [
      ...prev,
      { id: createId(), inputText: '', expectedText: '' },
    ]);
  }, []);

  const updateTestcase = useCallback(
    (id: string, field: 'inputText' | 'expectedText', value: string) => {
      setTestcases((prev) =>
        prev.map((tc) => (tc.id === id ? { ...tc, [field]: value } : tc))
      );
    },
    []
  );

  const removeTestcase = useCallback((id: string) => {
    setTestcases((prev) => prev.filter((tc) => tc.id !== id));
  }, []);

  const clearTestcases = useCallback(() => {
    setTestcases([]);
    setGenerationError(null);
    setModelUsed(null);
  }, []);

  const generateFromProblem = useCallback(async (problem: string): Promise<boolean> => {
    const trimmed = problem.trim();
    if (trimmed.length < 5) {
      setGenerationError('Problem statement must be at least 5 characters to generate test cases.');
      return false;
    }
    if (generatingRef.current) {
      return false;
    }

    generatingRef.current = true;
    setGenerating(true);
    setGenerationError(null);

    try {
      const res = await generateTestcases({ problem: trimmed });
      if (!res.testcases || res.testcases.length === 0) {
        setGenerationError('The backend returned zero test cases for this problem.');
        return false;
      }
      const mapped: EditableTestcase[] = res.testcases.map((tc) => ({
        id: createId(),
        inputText: serializeValue(tc.input),
        expectedText: serializeValue(tc.expected_output),
      }));
      setTestcases(mapped);
      setModelUsed(res.model_used || null);
      return true;
    } catch (err: unknown) {
      setGenerationError(extractApiErrorMessage(err, 'Failed to generate test cases'));
      return false;
    } finally {
      generatingRef.current = false;
      setGenerating(false);
    }
  }, []);

  const validateAndBuildPayload = useCallback((): {
    valid: boolean;
    error?: string;
    payload?: JudgeTestCase[];
  } => {
    if (testcases.length === 0) {
      return {
        valid: false,
        error: 'Add at least one test case or click "Generate Test Cases" before running.',
      };
    }

    const payload: JudgeTestCase[] = [];
    for (let i = 0; i < testcases.length; i++) {
      const tc = testcases[i];
      if (!tc.inputText.trim()) {
        return { valid: false, error: `Test case #${i + 1}: Input cannot be empty.` };
      }
      if (!tc.expectedText.trim()) {
        return { valid: false, error: `Test case #${i + 1}: Expected output cannot be empty.` };
      }
      let parsedInput: unknown;
      let parsedExpected: unknown;
      try {
        parsedInput = JSON.parse(tc.inputText);
      } catch {
        return {
          valid: false,
          error: `Test case #${i + 1}: Input must be valid JSON (e.g. [1, 2], {"nums": [2,7], "target": 9}, "abc", or 42).`,
        };
      }
      try {
        parsedExpected = JSON.parse(tc.expectedText);
      } catch {
        return {
          valid: false,
          error: `Test case #${i + 1}: Expected output must be valid JSON (e.g. [0, 1], true, "result", or 42).`,
        };
      }
      payload.push({ input: parsedInput, expected_output: parsedExpected });
    }

    return { valid: true, payload };
  }, [testcases]);

  return {
    testcases,
    generating,
    generationError,
    modelUsed,
    addTestcase,
    updateTestcase,
    removeTestcase,
    clearTestcases,
    generateFromProblem,
    validateAndBuildPayload,
  };
};
