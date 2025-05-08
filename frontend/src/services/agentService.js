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

// Get all agents
export const getAgents = async () => {
  try {
    const response = await apiClient.get('/api/v1/agents');
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch agents'
    );
  }
};

// Get a single agent by ID
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

// Create a new agent
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

// Update an existing agent
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

// Delete an agent
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

// Send a command to an agent
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

// Enable auto-login for an agent
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

// Disable auto-login for an agent
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