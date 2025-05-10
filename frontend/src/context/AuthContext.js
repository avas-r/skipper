import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import apiClient from '../services/apiClient';
import * as authService from '../services/authService';
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  // Initialize auth state
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token');
      const userStr = localStorage.getItem('user');
      
      if (token && userStr) {
        try {
          // Verify token by making a direct axios request with the token
          console.log('Verifying token on init');
          const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
          
          // Directly fetch with axios for more control
          console.log('Using token for auth:', token);
          const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          console.log('Token verified, user data:', userResponse.data);
          setUser(userResponse.data);
          localStorage.setItem('user', JSON.stringify(userResponse.data));
          setAuthenticated(true);
        } catch (error) {
          console.error('Token verification failed:', error);
          
          try {
            // Try to refresh the token
            console.log('Attempting to refresh token');
            const refreshResult = await authService.refreshToken();
            
            if (refreshResult) {
              // Try again with the new token
              const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
              const newToken = refreshResult.access_token;
              
              const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
                headers: {
                  'Authorization': `Bearer ${newToken}`
                }
              });
              
              console.log('Token refresh successful, user data:', userResponse.data);
              setUser(userResponse.data);
              localStorage.setItem('user', JSON.stringify(userResponse.data));
              setAuthenticated(true);
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError);
            logout();
          }
        }
      } else {
        console.log('No token or user data found in localStorage');
        setAuthenticated(false);
        setUser(null);
      }
      
      setLoading(false);
    };
    
    initAuth();
  }, []);
  
  const login = async (username, password) => {
    setLoading(true);
    try {
      console.log('AuthContext: Logging in user', username);
      
      // Use the authService to login
      const userData = await authService.login(username, password);
      
      console.log('AuthContext: Login successful, user data:', userData);
      
      // Update state with user data
      setUser(userData);
      setAuthenticated(true);
      
      return userData;
    } catch (error) {
      console.error('AuthContext: Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = () => {
    console.log('AuthContext: Logging out user');
    
    // Use the authService to logout
    authService.logout();
    
    // Update state
    setAuthenticated(false);
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ user, authenticated, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

export default AuthContext;