/**
 * Agent service for interacting with the agent management API.
 * 
 * This service provides functions to manage agents:
 * - List, create, update, delete agents
 * - Get agent logs
 * - Send commands to agents
 * - Configure auto-login
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
          // OAuth2 refresh token flow requires form data
          const refreshData = new URLSearchParams();
          refreshData.append('refresh_token', refreshToken);
          refreshData.append('grant_type', 'refresh_token');  // Required by OAuth2
          
          const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, refreshData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          });
          
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
              // Continue with error handling below
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
 * Get all agents with optional filtering.
 * 
 * @param {Object} filters - Optional filter parameters
 * @param {string} filters.status - Filter by agent status
 * @param {string} filters.search - Search term
 * @param {Array<string>} filters.tags - Filter by tags
 * @param {number} filters.skip - Number of records to skip (pagination)
 * @param {number} filters.limit - Maximum records to return (pagination)
 * @returns {Promise<Array>} List of agents
 */
export const getAgents = async (filters = {}) => {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    
    if (filters.status) {
      params.append('status', filters.status);
    }
    
    if (filters.search) {
      params.append('search', filters.search);
    }
    
    if (filters.tags && filters.tags.length > 0) {
      filters.tags.forEach(tag => {
        params.append('tags', tag);
      });
    }
    
    if (filters.skip !== undefined) {
      params.append('skip', filters.skip);
    }
    
    if (filters.limit !== undefined) {
      params.append('limit', filters.limit);
    }
    
    const response = await apiClient.get('/api/v1/agents', { params });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch agents'
    );
  }
};

/**
 * Get a single agent by ID.
 * 
 * @param {string} agentId - Agent ID
 * @returns {Promise<Object>} Agent data
 */
export const getAgentById = async (agentId) => {
  try {
    const response = await apiClient.get(`/api/v1/agents/${agentId}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch agent'
    );
  }
};

/**
 * Create a new agent.
 * 
 * @param {Object} agentData - Agent data
 * @returns {Promise<Object>} Created agent
 */
export const createAgent = async (agentData) => {
  try {
    const response = await apiClient.post('/api/v1/agents', agentData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to create agent'
    );
  }
};

/**
 * Update an existing agent.
 * 
 * @param {string} agentId - Agent ID
 * @param {Object} agentData - Agent update data
 * @returns {Promise<Object>} Updated agent
 */
export const updateAgent = async (agentId, agentData) => {
  try {
    const response = await apiClient.put(`/api/v1/agents/${agentId}`, agentData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to update agent'
    );
  }
};

/**
 * Delete an agent.
 * 
 * @param {string} agentId - Agent ID
 * @returns {Promise<boolean>} True if deletion successful
 */
export const deleteAgent = async (agentId) => {
  try {
    await apiClient.delete(`/api/v1/agents/${agentId}`);
    return true;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to delete agent'
    );
  }
};

/**
 * Get agent logs.
 * 
 * @param {string} agentId - Agent ID
 * @param {Object} options - Optional parameters
 * @param {string} options.logLevel - Filter by log level
 * @param {number} options.skip - Number of records to skip (pagination)
 * @param {number} options.limit - Maximum records to return (pagination)
 * @returns {Promise<Array>} List of agent logs
 */
export const getAgentLogs = async (agentId, options = {}) => {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    
    if (options.logLevel) {
      params.append('log_level', options.logLevel);
    }
    
    if (options.skip !== undefined) {
      params.append('skip', options.skip);
    }
    
    if (options.limit !== undefined) {
      params.append('limit', options.limit);
    }
    
    const response = await apiClient.get(`/api/v1/agents/${agentId}/logs`, { params });
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch agent logs'
    );
  }
};

/**
 * Send a command to an agent.
 * 
 * @param {string} agentId - Agent ID
 * @param {Object} commandData - Command data
 * @param {string} commandData.command_type - Command type
 * @param {Object} commandData.parameters - Command parameters
 * @returns {Promise<Object>} Updated agent
 */
export const sendAgentCommand = async (agentId, commandData) => {
  try {
    const response = await apiClient.post(`/api/v1/agents/${agentId}/command`, commandData);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to send command to agent'
    );
  }
};

/**
 * Enable auto-login for an agent.
 * 
 * @param {string} agentId - Agent ID
 * @param {string} serviceAccountId - Service account ID to use for auto-login
 * @param {string} sessionType - Session type (windows, web, etc.)
 * @returns {Promise<Object>} Updated agent
 */
export const enableAgentAutoLogin = async (agentId, serviceAccountId, sessionType = 'windows') => {
  try {
    const url = `/api/v1/agents/${agentId}/auto-login/enable?service_account_id=${serviceAccountId}&session_type=${sessionType}`;
    const response = await apiClient.post(url);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to enable agent auto-login'
    );
  }
};

/**
 * Disable auto-login for an agent.
 * 
 * @param {string} agentId - Agent ID
 * @returns {Promise<Object>} Updated agent
 */
export const disableAgentAutoLogin = async (agentId) => {
  try {
    const response = await apiClient.post(`/api/v1/agents/${agentId}/auto-login/disable`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to disable agent auto-login'
    );
  }
};

/**
 * Check for stale agents and mark them as offline.
 * 
 * @param {number} maxSilenceMinutes - Maximum silence time in minutes
 * @returns {Promise<Object>} Result
 */
export const checkStaleAgents = async (maxSilenceMinutes = 5) => {
  try {
    const response = await apiClient.post(`/api/v1/agents/check-stale?max_silence_minutes=${maxSilenceMinutes}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to check stale agents'
    );
  }
};