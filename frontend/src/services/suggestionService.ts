// src/services/suggestionService.ts
import apiClient from './apiClient';
import type { SuggestionRequest, SuggestionResponse } from '../types/ai';

/**
 * Explicitly request an AI mentoring hint based on user code and evaluation results.
 * Calls POST /api/v1/suggestions/generate
 */
export const generateSuggestion = async (
  payload: SuggestionRequest
): Promise<SuggestionResponse> => {
  const response = await apiClient.post<SuggestionResponse>(
    '/suggestions/generate',
    payload
  );
  return response.data;
};
