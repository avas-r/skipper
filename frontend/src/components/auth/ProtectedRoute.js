// src/components/auth/ProtectedRoute.js
import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import apiClient from '../../services/apiClient';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { authenticated, loading, user } = useAuth();
  const [verifyingAuth, setVerifyingAuth] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Verify token by making an API call
  useEffect(() => {
    const verifyToken = async () => {
      if (!authenticated) {
        setVerifyingAuth(false);
        return;
      }

      try {
        console.log('ProtectedRoute: Verifying token...');
        // Try to call the /auth/me endpoint to verify token
        await apiClient.get('/api/v1/auth/me');
        
        console.log('ProtectedRoute: Token is valid');
        setIsAuthenticated(true);
      } catch (error) {
        console.error('ProtectedRoute: Token verification failed', error);
        setIsAuthenticated(false);
      } finally {
        setVerifyingAuth(false);
      }
    };

    verifyToken();
  }, [authenticated]);

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

  // If user is not authenticated after verification, redirect to login
  if (!authenticated || !isAuthenticated) {
    console.log('Not authenticated, redirecting to login');
    // Redirect to login page, but save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  console.log('Authentication verified, rendering protected content for user:', user?.email);
  return children;
};

export default ProtectedRoute;