import { create } from 'zustand';
import api from '../config/api';
import type { AuthResponse } from '../types/api';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  register: (username: string, email: string, password: string) => Promise<void>;
}

const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await api.post<AuthResponse>('/api/auth/token', { username, password });
      localStorage.setItem('token', response.data.access_token);
      set({ isAuthenticated: true, isLoading: false });
    } catch (error) {
      set({ error: 'Invalid credentials', isLoading: false });
      throw error;
    }
  },

  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, isAuthenticated: false });
  },

  register: async (username: string, email: string, password: string) => {
    set({ isLoading: true, error: null });
    try {
      await api.post('/api/auth/register', { username, email, password });
      set({ isLoading: false });
    } catch (error) {
      set({ error: 'Registration failed', isLoading: false });
      throw error;
    }
  },
}));

export default useAuthStore; 