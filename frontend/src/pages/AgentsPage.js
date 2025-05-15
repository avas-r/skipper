// frontend/src/pages/AgentsPage.js
import React, { useState } from 'react';
import { Box, Typography, Paper, Tabs, Tab } from '@mui/material';
import AgentList from '../components/agents/AgentList';
import AgentDetail from '../components/agents/AgentDetail';
import ServiceAccounts from '../components/agents/ServiceAccounts';

const AgentsPage = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [agentUpdated, setAgentUpdated] = useState(false);
  
  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
    // Reset selected agent when switching to Service Accounts tab
    if (newValue === 1) {
      setSelectedAgentId(null);
    }
  };
  
  const handleAgentSelect = (agentId) => {
    setSelectedAgentId(agentId);
  };
  
  const handleAgentUpdate = (updatedAgent) => {
    setAgentUpdated(true);
    // The updated flag will trigger a refresh in AgentList when going back
  };
  
  const handleBackToList = () => {
    setSelectedAgentId(null);
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Agent Management
      </Typography>
      <Typography variant="body1" paragraph>
        Manage automation agents and service accounts across your organization.
      </Typography>
      
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>
      
      {tabIndex === 0 && !selectedAgentId && (
        <AgentList 
          onSelectAgent={handleAgentSelect} 
          refreshTrigger={agentUpdated} 
        />
      )}
      
      {tabIndex === 0 && selectedAgentId && (
        <AgentDetail 
          agentId={selectedAgentId} 
          onBack={handleBackToList}
          onUpdate={handleAgentUpdate}
        />
      )}
      
      {tabIndex === 1 && (
        <ServiceAccounts />
      )}
    </Box>
  );
};

export default AgentsPage;