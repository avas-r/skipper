//skipper/frontend/src/pages/AgentsPage.js

import React, { useState, useMemo } from 'react';
import { Box, Tab, Tabs, Paper } from '@mui/material';
import AgentManagement from '../components/agents/AgentManagement';
import MockServiceAccounts from '../components/agents/MockServiceAccounts';

export default function AgentsPage() {
  const [tabIndex, setTabIndex] = useState(0);

  // Mock data for agents
  const mockAgents = useMemo(() => [
    { 
      agent_id: '1', 
      name: 'Agent-WS01', 
      machine_id: 'WS01-1234', 
      status: 'online', 
      ip_address: '192.168.1.101',
      version: '1.2.0',
      last_heartbeat: new Date().toISOString(),
      capabilities: { os: 'Windows 10', memory: '16GB', cpu: '4 cores' },
      tags: ['finance', 'billing'],
      auto_login_enabled: true,
      service_account: { username: 'robot_fin1', display_name: 'Finance Robot 1' }
    },
    { 
      agent_id: '2', 
      name: 'Agent-WS02', 
      machine_id: 'WS02-5678', 
      status: 'offline', 
      ip_address: '192.168.1.102',
      version: '1.1.5',
      last_heartbeat: '2023-06-15T14:30:00Z',
      capabilities: { os: 'Windows 11', memory: '32GB', cpu: '8 cores' },
      tags: ['hr', 'onboarding'],
      auto_login_enabled: false
    },
    { 
      agent_id: '3', 
      name: 'Agent-WS03', 
      machine_id: 'WS03-9012', 
      status: 'busy', 
      ip_address: '192.168.1.103',
      version: '1.2.0',
      last_heartbeat: new Date().toISOString(),
      capabilities: { os: 'Windows 10', memory: '8GB', cpu: '2 cores' },
      tags: ['sales', 'reporting'],
      auto_login_enabled: true,
      service_account: { username: 'robot_sales', display_name: 'Sales Robot' }
    }
  ], []);

  // Mock data for service accounts
  const mockServiceAccounts = useMemo(() => [
    { 
      account_id: '1',
      username: 'robot_fin1', 
      display_name: 'Finance Robot 1', 
      account_type: 'robot',
      description: 'Robot account for finance automation',
      status: 'active',
      created_at: '2023-01-15T10:30:00Z'
    },
    { 
      account_id: '2',
      username: 'robot_hr', 
      display_name: 'HR Robot', 
      account_type: 'robot',
      description: 'Robot account for HR processes',
      status: 'active',
      created_at: '2023-02-20T14:15:00Z'
    },
    { 
      account_id: '3',
      username: 'robot_sales', 
      display_name: 'Sales Robot', 
      account_type: 'robot',
      description: 'Robot account for sales automation',
      status: 'active',
      created_at: '2023-03-05T09:45:00Z'
    }
  ], []);

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabIndex}
          onChange={(_e, v) => setTabIndex(v)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>

      {tabIndex === 0 && (
        <AgentManagement
          agents={mockAgents}
          serviceAccounts={mockServiceAccounts}
        />
      )}
      {tabIndex === 1 && (
        <MockServiceAccounts 
          serviceAccounts={mockServiceAccounts}
        />
      )}
    </Box>
  );
}
