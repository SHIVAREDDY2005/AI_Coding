import axios from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.toString() ?? '';

if (!apiBaseUrl) {
  console.warn('VITE_API_BASE_URL is not defined. API client may not work.');
}

const apiClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

export function extractApiErrorMessage(err: unknown, fallback = 'Request failed'): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((item: { msg?: string; loc?: (string | number)[] }) => {
          const path = Array.isArray(item.loc) ? item.loc.join('.') : '';
          return path ? `${path}: ${item.msg ?? 'Invalid value'}` : (item.msg ?? 'Validation error');
        })
        .join('; ');
    }
    if (err.code === 'ECONNABORTED') {
      return 'Request timed out. The server took too long to respond.';
    }
    if (!err.response) {
      return 'Cannot reach the backend server. Ensure FastAPI is running on http://localhost:8000.';
    }
    return err.message || fallback;
  }
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
}

export default apiClient;
