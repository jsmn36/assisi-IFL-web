import axios from 'axios';

// Health/database-info endpoints are mounted at the root, not under /api/v1.
// Strip a trailing /api/v1 from VITE_API_URL so this works with the same env
// var the rest of the app uses, while still allowing an explicit override
// via VITE_API_ROOT_URL.
const fromEnv = (import.meta.env.VITE_API_URL ?? '').toString();
const ROOT_URL =
  (import.meta.env.VITE_API_ROOT_URL as string | undefined) ??
  (fromEnv ? fromEnv.replace(/\/?api\/v1\/?$/, '') : '');

const apiClient = axios.create({
  baseURL: ROOT_URL,
});

export const api = {
  getDatabaseInfo: () => apiClient.get('/database/info'),
  healthCheck: () => apiClient.get('/health'),
};
