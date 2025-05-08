import React, { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../../services/authService';
import { Box, CircularProgress, Typography } from '@mui/material';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    // Check authentication
    const checkAuth = async () => {
      try {
        // Check if we have a token
        const auth = isAuthenticated();
        console.log('Authentication check result:', auth);
        
        if (auth) {
          // Verify we have user data
          const user = getCurrentUser();
          console.log('User data:', user ? 'Present' : 'Missing');
          
          // Only consider authenticated if we have both a token and user data
          setAuthenticated(!!user);
        } else {
          setAuthenticated(false);
        }
      } catch (error) {
        console.error('Auth check error:', error);
        setAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  if (loading) {
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

  if (!authenticated) {
    console.log('Not authenticated, redirecting to login');
    // Redirect to login page, but save the current location to redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  console.log('Authentication verified, rendering protected content');
  return children;
};

export default ProtectedRoute;