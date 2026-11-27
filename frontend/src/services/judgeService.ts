// src/services/judgeService.ts
import apiClient from './apiClient';
import type { JudgeExecutionRequest, JudgeExecutionResponse } from '../types/judge';

/**
 * Evaluate user code against supplied testcases.
 * Calls POST /api/v1/judge/evaluate
 */
export const evaluateCode = async (
  payload: JudgeExecutionRequest
): Promise<JudgeExecutionResponse> => {
  const response = await apiClient.post<JudgeExecutionResponse>(
    '/judge/evaluate',
    payload
  );
  return response.data;
};
