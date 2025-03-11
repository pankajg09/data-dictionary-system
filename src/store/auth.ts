import { create } from 'zustand';
import api from '../config/api';
import { AuthResponse } from '../types/api';

interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  loginWithGoogle: (credential: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, name: string) => Promise<void>;
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<AuthResponse>('/api/auth/login', {
        email,
        password,
      });
      localStorage.setItem('token', response.data.access_token);
      const userResponse = await api.get<User>('/api/auth/me');
      set({
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: 'Invalid credentials',
        isLoading: false,
      });
    }
  },

  loginWithGoogle: async (credential: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<AuthResponse>('/api/auth/google', {
        credential,
      });
      localStorage.setItem('token', response.data.access_token);
      const userResponse = await api.get<User>('/api/auth/me');
      set({
        user: userResponse.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({
        error: 'Google authentication failed',
        isLoading: false,
      });
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({
      user: null,
      isAuthenticated: false,
    });
  },

  register: async (email: string, password: string, name: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/api/auth/register', {
        email,
        password,
        name,
      });
      set({ isLoading: false });
    } catch (error) {
      set({
        error: 'Registration failed',
        isLoading: false,
      });
    }
  },
}));

export default useAuthStore; 