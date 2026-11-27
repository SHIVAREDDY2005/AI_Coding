// src/services/testcaseService.ts
import apiClient from './apiClient';
import type { TestcaseGenerateRequest, TestcaseGenerateResponse } from '../types/testcase';

/**
 * Generate AI testcases for a given problem statement.
 * Calls POST /api/v1/testcases/generate
 */
export const generateTestcases = async (
  payload: TestcaseGenerateRequest
): Promise<TestcaseGenerateResponse> => {
  const response = await apiClient.post<TestcaseGenerateResponse>(
    '/testcases/generate',
    payload
  );
  return response.data;
};
