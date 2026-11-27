// src/hooks/useAiMentor.ts
import { useState, useCallback, useRef } from 'react';
import { generateSuggestion } from '../services/suggestionService';
import { extractApiErrorMessage } from '../services/apiClient';
import type { SuggestionResponse } from '../types/ai';
import type { JudgeExecutionResponse } from '../types/judge';

export const useAiMentor = () => {
  const [suggestion, setSuggestion] = useState<SuggestionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inFlightRef = useRef(false);

  const requestHelp = useCallback(
    async (
      problem: string,
      userCode: string,
      evalResult: JudgeExecutionResponse | null
    ) => {
      if (!problem.trim() || problem.trim().length < 3) {
        setError('A problem statement is required for AI Help.');
        return;
      }
      if (!userCode.trim()) {
        setError('Write some code in the editor first before requesting AI Help.');
        return;
      }
      if (inFlightRef.current) return;

      inFlightRef.current = true;
      setLoading(true);
      setError(null);

      try {
        const payloadEval: Record<string, unknown> = evalResult
          ? {
              summary: evalResult.summary,
              results: evalResult.results,
              detected_function: evalResult.detected_function,
            }
          : { status: 'Not yet executed; user requested guidance on current draft.' };

        const res = await generateSuggestion({
          problem: problem.trim(),
          user_code: userCode,
          eval_result: payloadEval,
        });
        setSuggestion(res);
      } catch (err: unknown) {
        setError(extractApiErrorMessage(err, 'Failed to get AI mentoring feedback'));
      } finally {
        inFlightRef.current = false;
        setLoading(false);
      }
    },
    []
  );

  const clearSuggestion = useCallback(() => {
    setSuggestion(null);
    setError(null);
  }, []);

  return { suggestion, loading, error, requestHelp, clearSuggestion };
};
