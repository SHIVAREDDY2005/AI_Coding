// src/services/languageService.ts
import apiClient from './apiClient';
import type { LanguagesResponse } from '../types/language';

export const fetchLanguages = async (): Promise<LanguagesResponse> => {
  const response = await apiClient.get<LanguagesResponse>('/languages');
  return response.data;
};
