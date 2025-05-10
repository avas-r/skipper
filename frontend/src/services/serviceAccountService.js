// frontend/src/services/serviceAccountService.js
import apiClient from './apiClient';

/**
 * Get all service accounts with optional filtering.
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
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach(item => params.append(key, item));
        } else {
          params.append(key, value);
        }
      }
    });
    
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