import React from 'react';
import '@testing-library/jest-dom';
import 'jest-fetch-mock';

// Mock Google OAuth
jest.mock('@react-oauth/google', () => ({
  GoogleLogin: () => React.createElement('div', { 'data-testid': 'google-login' }, 'Google Login'),
  GoogleOAuthProvider: ({ children }: { children: React.ReactNode }) => React.createElement(React.Fragment, null, children),
}));

// Mock zustand
jest.mock('zustand');

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
})); 