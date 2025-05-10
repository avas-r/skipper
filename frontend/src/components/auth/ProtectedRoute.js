// frontend/src/components/auth/ProtectedRoute.js
import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import apiClient from '../../services/apiClient';

const ProtectedRoute = ({ children, requiredPermissions = [], requiredRoles = [] }) => {
  const location = useLocation();
  const { authenticated, loading, user, hasPermission, hasAnyRole } = useAuth();
  const [verifyingAuth, setVerifyingAuth] = useState(true);
  const [isAuthorized, setIsAuthorized] = useState(false);

  console.log('User permissions:', user?.permissions);
  console.log('User roles:', user?.roles);
  console.log('Required permissions:', requiredPermissions);

  // Verify token by making an API call
  useEffect(() => {
    const verifyToken = async () => {
      if (!authenticated) {
        setVerifyingAuth(false);
        return;
      }

      try {
        // Try to call the /auth/me endpoint to verify token
        await apiClient.get('/api/v1/auth/me');
        
        // Check permissions and roles
        let authorized = true;
        
        // If we have specific permission requirements, check them
        if (requiredPermissions.length > 0) {
          // If the user is admin or superuser, allow access regardless of specific permissions
          const isAdmin = user?.roles?.some(role => 
            role === 'admin' || role === 'superuser' || role === 'Admin' || role === 'Superuser'
          );
          
          if (isAdmin) {
            authorized = true;
          } else {
            // Otherwise check for specific permissions
            authorized = requiredPermissions.every(permission => {
              const hasPermissionValue = user?.permissions?.includes(permission);
              console.log(`Checking permission ${permission}: ${hasPermissionValue}`);
              return hasPermissionValue;
            });
          }
        }
        
        // If we have role requirements and permission check passed, check roles
        if (authorized && requiredRoles.length > 0) {
          authorized = user?.roles?.some(role => requiredRoles.includes(role));
        }
        
        console.log('Authorization result:', authorized);
        setIsAuthorized(authorized);
      } catch (error) {
        console.error('Token verification failed', error);
        setIsAuthorized(false);
      } finally {
        setVerifyingAuth(false);
      }
    };

    verifyToken();
  }, [authenticated, user, requiredPermissions, requiredRoles]);

  // Show loading state while verifying auth
  if (loading || verifyingAuth) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body1" sx={{ mt: 2 }}>
          Verifying authentication...
        </Typography>
      </Box>
    );
  }

  // If user is not authenticated, redirect to login
  if (!authenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  // If user doesn't have required permissions/roles
  if (!isAuthorized && (requiredPermissions.length > 0 || requiredRoles.length > 0)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
};

export default ProtectedRoute;