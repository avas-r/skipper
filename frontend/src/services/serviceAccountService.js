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

// Get all service accounts
export const getServiceAccounts = async () => {
  try {
    const response = await apiClient.get('/api/v1/service-accounts');
    return response.data;
  } catch (error) {
    throw new Error(
      error.response?.data?.detail || 'Failed to fetch service accounts'
    );
  }
};

// Get a single service account by ID
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

// Create a new service account
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

// Update an existing service account
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

// Delete a service account
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