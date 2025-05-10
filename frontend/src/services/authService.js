// frontend/src/services/authService.js
import axios from 'axios';
import apiClient from './apiClient';

// Get API URL from environment variable, with fallback
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Login user and get access token
 * 
 * @param {string} email User email
 * @param {string} password User password
 * @returns {Promise<Object>} User data
 */
export const login = async (email, password) => {
  try {
    // OAuth2 password flow requires form data
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    formData.append('grant_type', 'password');
    
    // Direct axios request for login
    const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    // Store tokens in localStorage
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    // Get user info
    const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${response.data.access_token}`
      }
    });
    
    // Store user data
    localStorage.setItem('user', JSON.stringify(userResponse.data));
    
    return userResponse.data;
  } catch (error) {
    console.error('Login error:', error);
    
    // Extract error details for better error messages
    let errorMessage = 'Authentication failed';
    
    if (error.response) {
      if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response.status === 401) {
        errorMessage = 'Invalid email or password';
      } else if (error.response.status === 403) {
        errorMessage = 'Account locked or disabled';
      }
    }
    
    throw new Error(errorMessage);
  }
};

/**
 * Logout user
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

/**
 * Refresh access token
 * 
 * @returns {Promise<Object>} New tokens
 */
export const refreshToken = async () => {
  try {
    const refreshToken = localStorage.getItem('refresh_token');
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    // Prepare form data for the refresh request
    const formData = new URLSearchParams();
    formData.append('refresh_token', refreshToken);
    
    const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    return response.data;
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
};

/**
 * Get current user data
 * 
 * @returns {Promise<Object>} Current user data
 */
export const getCurrentUser = async () => {
  const userJson = localStorage.getItem('user');
  
  if (userJson) {
    // Return cached user data
    return JSON.parse(userJson);
  }
  
  // If no cached data, fetch from API
  try {
    const response = await apiClient.get('/api/v1/auth/me');
    
    // Store user data
    localStorage.setItem('user', JSON.stringify(response.data));
    
    return response.data;
  } catch (error) {
    console.error('Failed to get current user:', error);
    throw error;
  }
};

/**
 * Check if user is authenticated
 * 
 * @returns {boolean} True if authenticated
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

/**
 * Get user tenant ID
 * 
 * @returns {string|null} Tenant ID or null
 */
export const getUserTenant = () => {
  const userJson = localStorage.getItem('user');
  if (!userJson) return null;
  
  const user = JSON.parse(userJson);
  return user?.tenant_id || null;
};

/**
 * Get user roles
 * 
 * @returns {Array<string>} List of role names
 */
export const getUserRoles = () => {
  const userJson = localStorage.getItem('user');
  if (!userJson) return [];
  
  const user = JSON.parse(userJson);
  return user?.roles || [];
};

/**
 * Check if user has a specific role
 * 
 * @param {string} roleName Role name to check
 * @returns {boolean} True if user has the role
 */
export const hasRole = (roleName) => {
  const roles = getUserRoles();
  return roles.includes(roleName);
};