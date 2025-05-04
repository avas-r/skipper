import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function QueuesPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Queues
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>
          This page will show job queues and their status. Coming soon!
        </Typography>
      </Paper>
    </Box>
  );
}

export default QueuesPage;