import axios from 'axios';
import { useAuthStore } from '../store/authStore';

declare module 'axios' {
  interface AxiosResponse {
    _meta?: Record<string, unknown> | null;
  }
}

export class ApiResponseError extends Error {
  type: string;
  code: number;
  response: { status: number; headers: Record<string, string>; data: unknown };

  constructor(
    envelope: { message?: string; error?: string; code?: number },
    response: { status: number; headers: Record<string, string>; data: unknown },
  ) {
    super(envelope.message ?? 'API error');
    this.name = 'ApiResponseError';
    this.type = envelope.error ?? 'UnknownError';
    this.code = envelope.code ?? 500;
    this.response = response;
  }
}

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let lastRefreshedToken: string | null = null;
let pendingQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

function processQueue(error: unknown, token: string | null) {
  pendingQueue.forEach((p) => {
    if (token) {
      p.resolve(token);
    } else {
      p.reject(error);
    }
  });
  pendingQueue = [];
}

const AUTH_EXEMPT_PATHS = ['/auth/login/', '/auth/register/', '/auth/refresh/'];

api.interceptors.request.use((config) => {
  const url = config.url || '';
  if (AUTH_EXEMPT_PATHS.some((p) => url.includes(p))) {
    return config;
  }
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object' && ('data' in response.data || response.data.status === 'error')) {
      if (response.data.status === 'error') {
        return Promise.reject(
          new ApiResponseError(response.data, {
            status: response.status,
            headers: response.headers as Record<string, string>,
            data: response.data,
          }),
        );
      }
      if (response.data.status === 'success') {
        const envelope = response.data;
        response.data = envelope.data;
        response._meta = envelope.meta ?? null;
      }
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    if (!originalRequest) return Promise.reject(error);

    if (error.response?.status === 401 && !originalRequest._retry && !AUTH_EXEMPT_PATHS.some((p) => originalRequest.url?.includes(p))) {
      const currentToken = useAuthStore.getState().token;

      // Prevent refresh loop: if we already refreshed this exact token and it still fails, bail
      if (currentToken && currentToken === lastRefreshedToken) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({
            resolve: (token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              resolve(api(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const { data } = await axios.post<{ access: string }>(
          '/api/auth/refresh/',
          {},
          { withCredentials: true }
        );
        const newToken = data.access;
        lastRefreshedToken = newToken;
        useAuthStore.getState().setToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().clearAuth();
        console.warn('Session expired. Please log in again.');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
