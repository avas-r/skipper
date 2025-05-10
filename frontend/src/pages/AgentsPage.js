// frontend/src/pages/AgentsPage.js
import React, { useState } from 'react';
import { Box, Typography, Paper, Tab, Tabs } from '@mui/material';
import AgentManagement from '../components/agents/AgentManagement';

function AgentsPage() {
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Agent Management
      </Typography>
      <Typography variant="body1" paragraph>
        View, add, and manage automation agents and service accounts across your organization.
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>
      
      <AgentManagement initialTab={tabIndex} />
    </Box>
  );
}

export default AgentsPage;