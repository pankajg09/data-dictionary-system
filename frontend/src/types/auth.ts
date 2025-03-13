export interface User {
  id: number;
  email: string;
  name: string;
  picture?: string;
  role: string;
  login_count: number;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

export interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (credential: string) => Promise<void>;
  logout: () => void;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface GoogleLoginResponse extends LoginResponse {}

export interface GoogleLoginRequest {
  token: string;
  email: string;
  name: string;
  picture?: string;
} 