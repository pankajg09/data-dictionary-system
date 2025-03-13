import React from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { Container, Box, Typography, Alert, Button } from '@mui/material';
import { Google as GoogleIcon } from '@mui/icons-material';
import useAuthStore from '../store/auth';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { loginWithGoogle, error, clearError, isLoading, login } = useAuthStore();

  const handleGoogleSuccess = async (credentialResponse: any) => {
    try {
      await loginWithGoogle(credentialResponse.credential);
      navigate('/');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const handleGoogleError = () => {
    console.error('Google login failed');
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 3,
        }}
      >
        <Typography component="h1" variant="h4">
          Data Dictionary System
        </Typography>
        
        <Typography component="h2" variant="h5">
          Sign In
        </Typography>

        {error && (
          <Alert severity="error" onClose={clearError}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 2 }}>
          <GoogleLogin
            onSuccess={handleGoogleSuccess}
            onError={handleGoogleError}
            useOneTap
          />
        </Box>
      </Box>
    </Container>
  );
};

export default Login; 