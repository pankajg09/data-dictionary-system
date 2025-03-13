import axios from 'axios';
import { User, GoogleLoginResponse } from '../types/auth';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

export const loginWithGoogle = async (response: any): Promise<{ user: User; token: string }> => {
  const { credential } = response;
  
  // Decode the JWT token to get user info
  const base64Url = credential.split('.')[1];
  const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
    return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
  }).join(''));

  const { email, name, picture } = JSON.parse(jsonPayload);

  const { data } = await axios.post<GoogleLoginResponse>(`${API_URL}/api/auth/google-login`, {
    token: credential,
    email,
    name,
    picture
  });

  // Store the token
  localStorage.setItem('token', data.access_token);
  
  return {
    user: data.user,
    token: data.access_token
  };
}; 