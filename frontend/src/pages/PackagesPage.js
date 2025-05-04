import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function PackagesPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Packages
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>
          This page will allow you to manage automation packages. Coming soon!
        </Typography>
      </Paper>
    </Box>
  );
}

export default PackagesPage;