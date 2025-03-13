import React, { createContext, useContext, useState, useEffect } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import type { User, AuthState, AuthContextType, GoogleLoginResponse } from '../types/auth';
import api from '../config/api';

interface ConfigResponse {
  key: string;
  value: string;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  loading: true,
  error: null,
  login: async () => {},
  logout: () => {},
});

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null,
  });
  const [clientId, setClientId] = useState<string>('');

  useEffect(() => {
    const fetchClientId = async () => {
      try {
        const response = await api.get<ConfigResponse>('/api/config/public/google-client-id');
        setClientId(response.data.value);
      } catch (error) {
        console.error('Failed to fetch Google Client ID:', error);
        setState(prev => ({ ...prev, error: 'Failed to load authentication configuration' }));
      }
    };

    fetchClientId();
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setState((prev) => ({ ...prev, loading: false }));
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await api.get<User>('/api/auth/me');
      setState((prev) => ({
        ...prev,
        isAuthenticated: true,
        user: response.data,
        loading: false,
        error: null,
      }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: 'Failed to fetch user',
      }));
    }
  };

  const login = async (credential: string) => {
    try {
      const response = await api.post<GoogleLoginResponse>('/api/auth/google-login', { token: credential });
      
      localStorage.setItem('token', response.data.access_token);
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      setState((prev) => ({
        ...prev,
        isAuthenticated: true,
        user: response.data.user,
        loading: false,
        error: null,
      }));
    } catch (error: any) {
      setState((prev) => ({
        ...prev,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: error.response?.data?.detail || 'Login failed',
      }));
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setState((prev) => ({
      ...prev,
      isAuthenticated: false,
      user: null,
      loading: false,
      error: null,
    }));
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
  };

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <AuthContext.Provider value={value}>
        {children}
      </AuthContext.Provider>
    </GoogleOAuthProvider>
  );
};

export { AuthContext };

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 