// src/hooks/useCodeExecution.ts
import { useState, useCallback } from 'react';
import type { JudgeExecutionRequest, JudgeExecutionResponse } from '../types/judge';
import { evaluateCode } from '../services/judgeService';
import { extractApiErrorMessage } from '../services/apiClient';

export interface UseCodeExecutionReturn {
  result: JudgeExecutionResponse | null;
  loading: boolean;
  error: string | null;
  run: (request: JudgeExecutionRequest) => Promise<JudgeExecutionResponse | null>;
  reset: () => void;
}

export const useCodeExecution = (): UseCodeExecutionReturn => {
  const [result, setResult] = useState<JudgeExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (request: JudgeExecutionRequest): Promise<JudgeExecutionResponse | null> => {
    setLoading(true);
    setError(null);
    try {
      const data = await evaluateCode(request);
      setResult(data);
      return data;
    } catch (err: unknown) {
      setError(extractApiErrorMessage(err, 'Code execution failed'));
      setResult(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, run, reset };
};
