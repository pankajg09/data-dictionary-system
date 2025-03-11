import { useState, useCallback } from 'react';
import { ApiErrorResponse } from '../types/api';

interface ErrorState {
  message: string;
  code?: string;
  details?: any;
}

export const useErrorHandler = () => {
  const [error, setError] = useState<ErrorState | null>(null);

  const handleError = useCallback((err: unknown) => {
    // Handle API error responses
    if (typeof err === 'object' && err !== null && 'response' in err) {
      const apiError = (err as ApiErrorResponse).response?.data;
      if (apiError) {
        setError({
          message: apiError.message || 'An unexpected API error occurred',
          code: apiError.code || 'API_ERROR',
          details: apiError.details || null
        });
        return;
      }
    }

    // Handle standard Error objects
    if (err instanceof Error) {
      setError({
        message: err.message,
        code: 'ERROR'
      });
      return;
    }

    // Handle unknown errors
    setError({
      message: 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR'
    });
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    handleError,
    clearError
  };
};

export default useErrorHandler; 