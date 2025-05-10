// src/services/authService.js
import axios from 'axios';
import apiClient from './apiClient';

// Get API URL from environment variable, with fallback
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Login user
export const login = async (email, password) => {
  // OAuth2 password flow requires form data
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  formData.append('grant_type', 'password');  // Required by OAuth2

  console.log('Sending login request to:', `${API_URL}/api/v1/auth/login`);
  
  // We don't use apiClient here because we don't have a token yet
  const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  console.log('Login response:', response.data);
  
  // Store tokens in localStorage
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);

  try {
    // Get user information with the token we just received
    console.log('Fetching user info with new token');
    const accessToken = response.data.access_token;
    
    // Debug token by decoding it (only for UI info - no security validation)
    try {
      const tokenParts = accessToken.split('.');
      if (tokenParts.length === 3) {
        const payloadBase64 = tokenParts[1].replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(atob(payloadBase64));
        console.log('Token payload:', payload);
        
        // Check expiration
        const exp = payload.exp;
        const iat = payload.iat || 0;
        const now = Math.floor(Date.now() / 1000);
        console.log(`Token issued at: ${new Date(iat * 1000).toISOString()}`);
        console.log(`Token expires at: ${new Date(exp * 1000).toISOString()}`);
        console.log(`Current time: ${new Date(now * 1000).toISOString()}`);
        console.log(`Time until expiration: ${exp - now} seconds (${Math.round((exp - now) / 60)} minutes)`);
      }
    } catch (e) {
      console.error('Error decoding token:', e);
    }
    
    const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    console.log('User info response:', userResponse.data);
    
    // Store user info in localStorage
    localStorage.setItem('user', JSON.stringify(userResponse.data));
    return userResponse.data;
  } catch (error) {
    console.error('Error fetching user info:', error);
    
    // Log the error details
    if (error.response) {
      console.error('Error response:', error.response.status, error.response.data);
      console.error('Request headers:', error.config.headers);
    }
    
    // Clear invalid auth if user fetch fails
    if (error.response && error.response.status === 401) {
      logout();
    }
    
    throw error;
  }
};

// Logout user
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

// Refresh token
export const refreshToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  console.log('Refreshing token via authService');
  
  // Prepare form data for the refresh request
  const formData = new URLSearchParams();
  formData.append('refresh_token_form', refreshToken);

  try {
    const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    console.log('Token refresh response:', response.data);
    
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    return response.data;
  } catch (error) {
    console.error('Token refresh error:', error);
    
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
      console.error('Request URL:', error.config.url);
    }
    
    throw error;
  }
};

// Get current user
export const getCurrentUser = () => {
  const userJson = localStorage.getItem('user');
  return userJson ? JSON.parse(userJson) : null;
};

// Check if user is authenticated
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

// Get user tenant
export const getUserTenant = () => {
  const user = getCurrentUser();
  return user ? user.tenant_id : null;
};

// Get user roles
export const getUserRoles = () => {
  const user = getCurrentUser();
  return user ? user.roles : [];
};

// Check if user has a specific role
export const hasRole = (roleName) => {
  const roles = getUserRoles();
  return roles.includes(roleName);
};