// frontend/src/pages/UnauthorizedPage.js
import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import LockIcon from '@mui/icons-material/Lock';

function UnauthorizedPage() {
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
      }}
    >
      <Paper 
        elevation={3}
        sx={{
          p: 5,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          maxWidth: 500,
        }}
      >
        <LockIcon color="error" sx={{ fontSize: 100, mb: 2 }} />
        <Typography variant="h4" sx={{ mb: 2 }}>
          Access Denied
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4, textAlign: 'center' }}>
          You don't have permission to access this resource. Please contact your administrator
          if you believe this is an error.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/"
          >
            Back to Home
          </Button>
          <Button
            variant="outlined"
            component={RouterLink}
            to="/login"
          >
            Log in with different account
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

export default UnauthorizedPage;