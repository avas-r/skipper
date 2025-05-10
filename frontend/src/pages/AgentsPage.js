// src/pages/AgentsPage.js
import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import AgentManagementTabs from '../components/agents/AgentManagementTabs';

function AgentsPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Agent Management
      </Typography>
      <Typography variant="body1" paragraph>
        View, add, and manage automation agents and service accounts across your organization.
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <AgentManagementTabs />
      </Paper>
    </Box>
  );
}

export default AgentsPage;