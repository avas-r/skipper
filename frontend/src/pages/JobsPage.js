import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function JobsPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Jobs
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>
          This page will show all automation jobs and their status. Coming soon!
        </Typography>
      </Paper>
    </Box>
  );
}

export default JobsPage;