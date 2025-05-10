/**
 * Service account service for interacting with the service account API.
 * 
 * This service provides functions to manage service accounts:
 * - List, create, update, delete service accounts
 */

import axios from 'axios';

// Get API URL from environment variable, with fallback
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Adding auth header to request:', config.url);
    } else {
      console.warn('No token found for request:', config.url);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token expiration and refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If 401 error and we haven't tried to refresh yet
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.log('Attempting to refresh token...');
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (refreshToken) {
          // The refresh endpoint expects refresh_token as a query parameter
          const encodedToken = encodeURIComponent(refreshToken);
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh?refresh_token=${encodedToken}`);
          
          console.log('Token refresh successful');
          
          if (response.data) {
            try {
              // Store new tokens
              localStorage.setItem('access_token', response.data.access_token);
              localStorage.setItem('refresh_token', response.data.refresh_token);
              
              // Also update the user data to keep it in sync
              try {
                const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
                  headers: {
                    'Authorization': `Bearer ${response.data.access_token}`
                  }
                });
                localStorage.setItem('user', JSON.stringify(userResponse.data));
              } catch (userError) {
                console.error('Error refreshing user data:', userError);
              }
              
              // Update header and retry request
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
              return axios(originalRequest);
            } catch (storageError) {
              console.error('Error storing tokens:', storageError);
            }
          }
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        if (refreshError.response) {
          console.error('Refresh error status:', refreshError.response.status);
          console.error('Refresh error data:', refreshError.response.data);
        }
      }
      
      console.log('Clearing auth data and redirecting to login');
      // If refresh fails or no refresh token, clear session and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

/**
 * Get all service accounts.
 * 
 * @param {Object} filters - Optional filter parameters
 * @param {string} filters.status - Filter by account status
 * @param {string} filters.search - Search term
 * @param {number} filters.skip - Number of records to skip (pagination)
 * @param {number} filters.limit - Maximum records to return (pagination)
 * @returns {Promise<Array>} List of service accounts
 */
export const getServiceAccounts = async (filters = {}) => {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    
    if (filters.status) {
      params.append('status', filters.status);
    }
    
    if (filters.search) {
      params.append('search', filters.search);
    }
    
    if (filters.skip !== undefined) {
      params.append('skip', filters.skip);
    }
    
    if (filters.limit !== undefined) {
      params.append('limit', filters.limit);
    }
    
    const response = await apiClient.get('/api/v1/service-accounts', { params });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch service accounts'
    );
  }
};

/**
 * Get a single service account by ID.
 * 
 * @param {string} accountId - Service account ID
 * @returns {Promise<Object>} Service account data
 */
export const getServiceAccountById = async (accountId) => {
  try {
    const response = await apiClient.get(`/api/v1/service-accounts/${accountId}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch service account'
    );
  }
};

/**
 * Create a new service account.
 * 
 * @param {Object} accountData - Service account data
 * @returns {Promise<Object>} Created service account
 */
export const createServiceAccount = async (accountData) => {
  try {
    const response = await apiClient.post('/api/v1/service-accounts', accountData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to create service account'
    );
  }
};

/**
 * Update an existing service account.
 * 
 * @param {string} accountId - Service account ID
 * @param {Object} accountData - Service account update data
 * @returns {Promise<Object>} Updated service account
 */
export const updateServiceAccount = async (accountId, accountData) => {
  try {
    const response = await apiClient.put(`/api/v1/service-accounts/${accountId}`, accountData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to update service account'
    );
  }
};

/**
 * Delete a service account.
 * 
 * @param {string} accountId - Service account ID
 * @returns {Promise<boolean>} True if deletion successful
 */
export const deleteServiceAccount = async (accountId) => {
  try {
    await apiClient.delete(`/api/v1/service-accounts/${accountId}`);
    return true;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to delete service account'
    );
  }
};