// src/components/auth/ProtectedRoute.js
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const { authenticated, loading } = useAuth();

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