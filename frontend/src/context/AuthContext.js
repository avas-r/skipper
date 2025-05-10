// frontend/src/context/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import * as authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [error, setError] = useState(null);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        try {
          // Verify token by fetching user data
          const userData = await authService.getCurrentUser();
          setUser(userData);
          setAuthenticated(true);
          setError(null);
        } catch (error) {
          console.error('Token verification failed:', error);
          
          try {
            // Try to refresh the token
            const refreshResult = await authService.refreshToken();
            
            if (refreshResult) {
              // Get user data with new token
              const userData = await authService.getCurrentUser();
              setUser(userData);
              setAuthenticated(true);
              setError(null);
            } else {
              // Clear invalid auth state
              logout();
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError);
            logout();
          }
        }
      } else {
        setAuthenticated(false);
        setUser(null);
      }
      
      setLoading(false);
    };
    
    initAuth();
  }, []);
  
  const login = async (email, password) => {
    setLoading(true);
    setError(null);
    
    try {
      const userData = await authService.login(email, password);
      setUser(userData);
      setAuthenticated(true);
      return userData;
    } catch (error) {
      console.error('Login failed:', error);
      setError(error.message || 'Authentication failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = () => {
    authService.logout();
    setAuthenticated(false);
    setUser(null);
    setError(null);
  };
  
  // Add a function to check if user has specific permission
  const hasPermission = (permission) => {
    if (!user || !user.permissions) return false;
    return user.permissions.includes(permission);
  };
  
  // Add a function to check if user has one of the specified roles
  const hasAnyRole = (roles) => {
    if (!user || !user.roles) return false;
    return roles.some(role => user.roles.includes(role));
  };
  
  return (
    <AuthContext.Provider value={{ 
      user, 
      authenticated, 
      loading, 
      error,
      hasPermission,
      hasAnyRole,
      login, 
      logout 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

export default AuthContext;