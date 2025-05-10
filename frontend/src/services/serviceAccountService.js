// frontend/src/services/serviceAccountService.js
import apiClient from './apiClient';

/**
 * Get all service accounts with optional filtering.
 */
export const getServiceAccounts = async (filters = {}) => {
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