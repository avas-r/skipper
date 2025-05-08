import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  TextField
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { getAgents } from '../../services/agentService';

function AgentList() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    fetchAgents();
  }, []);
  
  const fetchAgents = async () => {
    setLoading(true);
    setError('');
    try {
      const agentsData = await getAgents();
      setAgents(agentsData);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      setError('Error loading agents: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };
  
  const filteredAgents = agents?.filter(agent => 
    agent.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.machine_id?.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" component="h2">
          Agents
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={fetchAgents}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            color="primary"
          >
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
      ) : filteredAgents?.length ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Machine ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Version</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAgents.map((agent) => (
                <TableRow key={agent.agent_id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>{agent.machine_id}</TableCell>
                  <TableCell>
                    <Chip 
                      label={agent.status} 
                      color={agent.status === 'online' ? 'success' : 'error'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{agent.ip_address}</TableCell>
                  <TableCell>{agent.version}</TableCell>
                  <TableCell align="right">
                    <IconButton size="small">
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
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
    </Box>
  );
}

export default AgentList;