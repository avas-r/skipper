import React, { createContext, useState, useEffect, useContext } from 'react';
import { 
  getCurrentUser, 
  isAuthenticated, 
  getUserTenant, 
  getUserRoles, 
  hasRole, 
  logout 
} from '../services/authService';

// Create context
const AuthContext = createContext();

// Provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    // Initialize auth state
    const initAuth = () => {
      try {
        const isAuth = isAuthenticated();
        setAuthenticated(isAuth);
        
        if (isAuth) {
          const currentUser = getCurrentUser();
          setUser(currentUser);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        setAuthenticated(false);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  // Provide login state update function
  const updateAuthState = () => {
    const isAuth = isAuthenticated();
    setAuthenticated(isAuth);
    setUser(isAuth ? getCurrentUser() : null);
  };

  // Logout function
  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setUser(null);
  };

  // Check if user has specific role
  const checkRole = (role) => {
    return hasRole(role);
  };

  // Get user's tenant ID
  const getTenant = () => {
    return getUserTenant();
  };

  // Get user's roles
  const getRoles = () => {
    return getUserRoles();
  };

  return (
    <AuthContext.Provider
      value={{
        authenticated,
        loading,
        user,
        updateAuthState,
        logout: handleLogout,
        hasRole: checkRole,
        getTenant,
        getRoles
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;