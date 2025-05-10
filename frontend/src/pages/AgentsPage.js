// src/pages/AgentsPage.js
import React from 'react';
import { Box, Typography, Paper, Button, TextField, Chip, CircularProgress } from '@mui/material';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

function AgentsPage() {
  const [agents, setAgents] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [searchTerm, setSearchTerm] = React.useState('');

  React.useEffect(() => {
    // Simulate loading agents
    setLoading(true);
    setTimeout(() => {
      // Mock data
      const mockAgents = [
        { 
          agent_id: '1', 
          name: 'Agent 001', 
          machine_id: 'DESKTOP-A1B2C3', 
          status: 'online',
          ip_address: '192.168.1.101',
          version: '1.0.5'
        },
        { 
          agent_id: '2', 
          name: 'Agent 002', 
          machine_id: 'SERVER-X9Y8Z7', 
          status: 'offline',
          ip_address: '192.168.1.102',
          version: '1.0.4'
        },
        { 
          agent_id: '3', 
          name: 'Agent 003', 
          machine_id: 'LAPTOP-Q7W9E5', 
          status: 'busy',
          ip_address: '192.168.1.103',
          version: '1.0.5'
        }
      ];
      setAgents(mockAgents);
      setLoading(false);
    }, 1000);
  }, []);

  // Filter agents based on search term
  const filteredAgents = agents.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    agent.machine_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Render agent status chip
  const renderAgentStatus = (status) => {
    let color;
    
    switch (status) {
      case 'online':
        color = 'success';
        break;
      case 'offline':
        color = 'error';
        break;
      case 'busy':
        color = 'warning';
        break;
      default:
        color = 'default';
    }
    
    return <Chip label={status} color={color} size="small" />;
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Agent Management
      </Typography>
      <Typography variant="body1" paragraph>
        View, add, and manage automation agents across your organization.
      </Typography>
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h5" component="h2">
            Agents
          </Typography>
          <Box>
            <Button variant="contained" color="primary">
              Add Agent
            </Button>
          </Box>
        </Box>
        
        <TextField
          fullWidth
          label="Search agents"
          variant="outlined"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ mb: 3 }}
        />
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Paper sx={{ p: 3 }}>
            <Typography color="error">{error}</Typography>
          </Paper>
        ) : filteredAgents.length ? (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Machine ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>IP Address</TableCell>
                  <TableCell>Version</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAgents.map((agent) => (
                  <TableRow key={agent.agent_id}>
                    <TableCell>{agent.name}</TableCell>
                    <TableCell>{agent.machine_id}</TableCell>
                    <TableCell>{renderAgentStatus(agent.status)}</TableCell>
                    <TableCell>{agent.ip_address}</TableCell>
                    <TableCell>{agent.version}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Paper sx={{ p: 3 }}>
            <Typography>No agents found. Add a new agent to get started.</Typography>
          </Paper>
        )}
      </Paper>
    </Box>
  );
}

export default AgentsPage;