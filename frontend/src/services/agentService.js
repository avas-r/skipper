// frontend/src/services/agentService.js
import apiClient from './apiClient';

/**
 * Get all agents with optional filtering.
 */
export const getAgents = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => params.append(key, item));
        } else {
          params.append(key, value);
        }
      }
    });
    
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
 */
export const getAgentLogs = async (agentId, options = {}) => {
  try {
    const params = new URLSearchParams();
    
    Object.entries(options).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value);
      }
    });
    
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
 */
export const enableAgentAutoLogin = async (agentId, serviceAccountId, sessionType = 'windows') => {
  try {
    const params = new URLSearchParams({
      service_account_id: serviceAccountId,
      session_type: sessionType
    });
    
    const response = await apiClient.post(`/api/v1/agents/${agentId}/auto-login/enable?${params.toString()}`);
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to enable agent auto-login'
    );
  }
};

/**
 * Disable auto-login for an agent.
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