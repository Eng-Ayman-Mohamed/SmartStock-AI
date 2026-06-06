interface ApiResponse<T> {
  data: T;
  message?: string;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface ApiError {
  error: string;
  type: string;
}

interface LoginPayload {
  email: string;
  password: string;
}

interface LoginResponse {
  access: string;
  refresh?: string;
  user: {
    id: number;
    email: string;
    name: string;
    role: 'viewer' | 'manager' | 'admin';
  };
}

interface RefreshResponse {
  access: string;
}
