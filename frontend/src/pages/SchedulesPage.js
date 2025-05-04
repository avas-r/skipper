import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

function SchedulesPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Schedules
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Typography>
          This page will show all job schedules. Coming soon!
        </Typography>
      </Paper>
    </Box>
  );
}

export default SchedulesPage;