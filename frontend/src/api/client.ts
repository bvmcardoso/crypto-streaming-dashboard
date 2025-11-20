import axios from 'axios';

// Simple axios instance so we don't repeat the base URL everywhere.
// If you ever need to point to a different backend, change only here.
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 5000,
});
