// src/services/healthService.ts
import apiClient from './apiClient';

export interface BackendHealthResponse {
  status: string;
  version: string;
}

export const fetchHealth = async (): Promise<BackendHealthResponse> => {
  const response = await apiClient.get<BackendHealthResponse>('/health', { timeout: 5000 });
  return response.data;
};
