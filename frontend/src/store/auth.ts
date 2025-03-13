import { create } from 'zustand';
import api from '../config/api';
import type { User, LoginResponse, GoogleLoginResponse } from '../types/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (credential: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.post<LoginResponse>('/api/auth/login', { email, password });
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false,
      });
      throw error;
    }
  },

  loginWithGoogle: async (credential: string) => {
    try {
      set({ isLoading: true, error: null });
      
      // Decode the JWT token to get user info
      const tokenParts = credential.split('.');
      const payload = JSON.parse(atob(tokenParts[1]));
      
      const response = await api.post<GoogleLoginResponse>('/api/auth/google-login', { 
        token: credential,
        email: payload.email,
        name: payload.name,
        picture: payload.picture,
        sub: payload.sub  // Add the Google ID
      });
      
      const { access_token, user } = response.data;
      localStorage.setItem('token', access_token);
      set({ user, isAuthenticated: true, isLoading: false });
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'Google login failed',
        isLoading: false,
      });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, isAuthenticated: false });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore; 