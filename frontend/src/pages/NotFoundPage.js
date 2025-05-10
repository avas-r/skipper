// frontend/src/pages/NotFoundPage.js
import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

function NotFoundPage() {
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
        <Typography variant="h1" color="primary" sx={{ mb: 2, fontSize: '8rem' }}>
          404
        </Typography>
        <Typography variant="h4" sx={{ mb: 2 }}>
          Page Not Found
        </Typography>
        <Typography variant="body1" color="textSecondary" sx={{ mb: 4, textAlign: 'center' }}>
          The page you're looking for doesn't exist or has been moved.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          component={RouterLink}
          to="/"
        >
          Back to Home
        </Button>
      </Paper>
    </Box>
  );
}

export default NotFoundPage;