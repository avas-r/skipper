import React, { useState } from 'react';
import { 
  Box, Tab, Tabs, Paper
} from '@mui/material';
import AgentList from '../components/agents/AgentList';
import ServiceAccounts from '../components/agents/ServiceAccounts';

function AgentsPage() {
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>

      {tabIndex === 0 && <AgentList />}
      {tabIndex === 1 && <ServiceAccounts />}
    </Box>
  );
}

export default AgentsPage;