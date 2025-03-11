import React from 'react';
import { render, screen, fireEvent, waitFor } from '../../utils/test-utils';
import Login from '../Login';
import useAuthStore from '../../store/auth';

// Mock the auth store
const mockStore = jest.fn();
jest.mock('../../store/auth', () => ({
  __esModule: true,
  default: () => mockStore(),
}));

describe('Login Component', () => {
  const mockLogin = jest.fn();
  const mockLoginWithGoogle = jest.fn();
  
  beforeEach(() => {
    mockStore.mockImplementation(() => ({
      login: mockLogin,
      loginWithGoogle: mockLoginWithGoogle,
      isLoading: false,
      error: null,
    }));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders login form', () => {
    render(<Login />);
    
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByTestId('google-login')).toBeInTheDocument();
  });

  it('handles form submission', async () => {
    render(<Login />);
    
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('displays error message when login fails', () => {
    mockStore.mockImplementation(() => ({
      login: mockLogin,
      loginWithGoogle: mockLoginWithGoogle,
      isLoading: false,
      error: 'Invalid credentials',
    }));

    render(<Login />);
    
    expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
  });

  it('shows loading state during authentication', () => {
    mockStore.mockImplementation(() => ({
      login: mockLogin,
      loginWithGoogle: mockLoginWithGoogle,
      isLoading: true,
      error: null,
    }));

    render(<Login />);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });
}); 