// frontend/src/services/agentService.js
import apiClient from './apiClient';

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