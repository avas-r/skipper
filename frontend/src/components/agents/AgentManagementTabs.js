// src/components/agents/AgentManagementTabs.js
import React, { useState } from 'react';
import { Box, Paper, Tabs, Tab } from '@mui/material';
import AgentList from './AgentList';
import AgentDetail from './AgentDetail';
import ServiceAccounts from './ServiceAccounts';

function AgentManagementTabs() {
  const [tabIndex, setTabIndex] = useState(0);
  const [selectedAgentId, setSelectedAgentId] = useState(null);

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
    // Reset selected agent when switching to service accounts tab
    if (newValue === 1) {
      setSelectedAgentId(null);
    }
  };

  const handleSelectAgent = (agent) => {
    setSelectedAgentId(agent.agent_id);
  };

  const handleBackToList = () => {
    setSelectedAgentId(null);
  };

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>

      {tabIndex === 0 && (
        selectedAgentId ? (
          <AgentDetail agentId={selectedAgentId} onBack={handleBackToList} />
        ) : (
          <AgentList onSelectAgent={handleSelectAgent} />
        )
      )}

      {tabIndex === 1 && (
        <ServiceAccounts />
      )}
    </Box>
  );
}

export default AgentManagementTabs;