import axios from 'axios';

// Get API URL from environment variable, with fallback
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Login user
export const login = async (email, password) => {
  // OAuth2 password flow requires form data
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  formData.append('grant_type', 'password');  // Required by OAuth2

  const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  // Store tokens in localStorage
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);

  // Get user information
  const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
    headers: {
      'Authorization': `Bearer ${response.data.access_token}`
    }
  });

  // Store user info in localStorage
  localStorage.setItem('user', JSON.stringify(userResponse.data));

  return userResponse.data;
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
  
  // OAuth2 refresh token flow requires form data
  const refreshData = new URLSearchParams();
  refreshData.append('refresh_token', refreshToken);
  refreshData.append('grant_type', 'refresh_token');  // Required by OAuth2
  
  const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, refreshData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  
  console.log('Token refresh response:', response.data);
  
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('refresh_token', response.data.refresh_token);
  
  return response.data;
};

// Get current user
export const getCurrentUser = () => {
  const userJson = localStorage.getItem('user');
  return userJson ? JSON.parse(userJson) : null;
};

// Check if user is authenticated
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token') && !!localStorage.getItem('user');
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