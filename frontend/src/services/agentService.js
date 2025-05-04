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
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token expiration
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token is invalid or expired, redirect to login page
      localStorage.removeItem('token');
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