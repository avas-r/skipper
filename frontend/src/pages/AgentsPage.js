// src/pages/AgentsPage.js
import React from 'react';
import { Box, Typography, Paper, Divider } from '@mui/material';
import AgentList from '../components/agents/AgentList';
import AgentManagementSimple from '../components/agents/AgentManagementSimple';

function AgentsPage() {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Agent Management
      </Typography>
      <Typography variant="body1" paragraph>
        View, add, and manage automation agents across your organization.
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <AgentList />
      </Paper>
      
      <Divider sx={{ my: 4 }} />
      
      <Typography variant="h5" component="h2" gutterBottom>
        Advanced Management
      </Typography>
      
      <Paper sx={{ p: 3 }}>
        <AgentManagementSimple />
      </Paper>
    </Box>
  );
}

export default AgentsPage;