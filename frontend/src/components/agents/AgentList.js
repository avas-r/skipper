// frontend/src/components/agents/AgentList.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  TextField, Dialog, DialogTitle,
  DialogContent, DialogActions,
  FormControl, InputLabel, Select,
  MenuItem, Alert
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import { 
  getAgents, 
  createAgent, 
  updateAgent, 
  deleteAgent,
  sendAgentCommand 
} from '../../services/agentService';

const AgentList = ({ onSelectAgent, refreshTrigger }) => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Form state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    machine_id: '',
    hostname: '',  // Add hostname field
    tags: [],
    status: 'offline',
    version: ''
  });
  const [formError, setFormError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  useEffect(() => {
    fetchAgents();
  }, [refreshTrigger]);
  
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
  
  const handleOpenAddDialog = () => {
    setIsEditing(false);
    setFormData({
      name: '',
      machine_id: '',
      hostname: ``,
      tags: [],
      status: 'offline',
      version: ''
    });
    setFormError('');
    setDialogOpen(true);
  };

  const handleOpenEditDialog = (agent) => {
    setIsEditing(true);
    setFormData({
      name: agent.name,
      machine_id: agent.machine_id,
      hostname: agent.hostname,
      tags: agent.tags || [],
      status: agent.status,
      version: agent.version || ''
    });
    setFormError('');
    setDialogOpen(true);
  };
  
  const handleCloseDialog = () => {
    setDialogOpen(false);
  };
  
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  const handleTagsChange = (e) => {
    const tagsString = e.target.value;
    const tagsArray = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    setFormData({
      ...formData,
      tags: tagsArray
    });
  };
  
  const handleSubmit = async () => {
    setFormError('');
    setActionLoading(true);
    
    // Validate form
    if (!formData.name) {
      setFormError('Name is required');
      setActionLoading(false);
      return;
    }
    
    if (!formData.machine_id) {
      setFormError('Machine ID is required');
      setActionLoading(false);
      return;
    }
    
    try {
      let updatedAgent;
      
      if (isEditing) {
        // Get the agent being edited
        const agentToUpdate = agents.find(agent => agent.machine_id === formData.machine_id);
        
        if (!agentToUpdate) {
          setFormError('Agent not found');
          setActionLoading(false);
          return;
        }
        
        // Update agent
        updatedAgent = await updateAgent(agentToUpdate.agent_id, formData);
        
        // Update the agents list
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.agent_id === agentToUpdate.agent_id ? updatedAgent : agent
          )
        );
      } else {
        // Create new agent
        updatedAgent = await createAgent(formData);
        
        // Add to agents list
        setAgents(prevAgents => [...prevAgents, updatedAgent]);
      }
      
      setDialogOpen(false);
    } catch (err) {
      console.error('Failed to save agent:', err);
      setFormError('Error saving agent: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleDeleteClick = (agent) => {
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };
  
  const handleConfirmDelete = async () => {
    if (!agentToDelete) return;
    
    setActionLoading(true);
    try {
      await deleteAgent(agentToDelete.agent_id);
      // Remove agent from the list
      setAgents(prevAgents => 
        prevAgents.filter(agent => agent.agent_id !== agentToDelete.agent_id)
      );
      setDeleteDialogOpen(false);
    } catch (err) {
      console.error('Failed to delete agent:', err);
      setError('Error deleting agent: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
      setAgentToDelete(null);
    }
  };
  
  const handleSendCommand = async (agent, command) => {
    setActionLoading(true);
    try {
      const commandData = {
        command_type: command,
        parameters: {}
      };
      
      const updatedAgent = await sendAgentCommand(agent.agent_id, commandData);
      
      // Update agent in the list
      setAgents(prevAgents => 
        prevAgents.map(a => 
          a.agent_id === agent.agent_id ? updatedAgent : a
        )
      );
    } catch (err) {
      console.error(`Failed to send ${command} command:`, err);
      setError(`Error sending ${command} command: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoading(false);
    }
  };

  const renderAgentStatus = (status) => {
    let color, icon;
    
    switch (status) {
      case 'online':
        color = 'success';
        icon = <CheckCircleIcon fontSize="small" />;
        break;
      case 'offline':
        color = 'error';
        icon = <ErrorIcon fontSize="small" />;
        break;
      case 'busy':
      case 'running':
        color = 'warning';
        icon = <WarningIcon fontSize="small" />;
        break;
      case 'starting':
        color = 'info';
        icon = <PlayArrowIcon fontSize="small" />;
        break;
      case 'stopping':
        color = 'warning';
        icon = <PauseIcon fontSize="small" />;
        break;
      default:
        color = 'default';
        icon = null;
    }
    
    return (
      <Chip 
        icon={icon}
        label={status} 
        color={color} 
        size="small" 
      />
    );
  };
  
  const filteredAgents = agents?.filter(agent => 
    !searchTerm || 
    agent.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.machine_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (agent.hostname && agent.hostname.toLowerCase().includes(searchTerm.toLowerCase()))
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
            disabled={loading || actionLoading}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            color="primary"
            onClick={handleOpenAddDialog}
            disabled={actionLoading}
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
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : filteredAgents?.length ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Machine ID</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Hostname</TableCell>
                <TableCell>Version</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAgents.map((agent) => (
                <TableRow key={agent.agent_id} 
                  hover 
                  onClick={() => onSelectAgent && onSelectAgent(agent.agent_id)}
                  sx={{ cursor: onSelectAgent ? 'pointer' : 'default' }}
                >
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>{agent.machine_id}</TableCell>
                  <TableCell>{renderAgentStatus(agent.status)}</TableCell>
                  <TableCell>{agent.hostname || '-'}</TableCell>
                  <TableCell>{agent.version || '-'}</TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    {agent.status === 'online' || agent.status === 'busy' ? (
                      <IconButton 
                        size="small" 
                        color="warning"
                        onClick={() => handleSendCommand(agent, 'stop')}
                        disabled={actionLoading}
                        title="Stop Agent"
                      >
                        <PauseIcon fontSize="small" />
                      </IconButton>
                    ) : (
                      <IconButton 
                        size="small"
                        color="success"
                        onClick={() => handleSendCommand(agent, 'start')}
                        disabled={actionLoading}
                        title="Start Agent"
                      >
                        <PlayArrowIcon fontSize="small" />
                      </IconButton>
                    )}
                    <IconButton 
                      size="small"
                      onClick={() => handleOpenEditDialog(agent)}
                      disabled={actionLoading}
                      title="Edit Agent"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      color="error"
                      onClick={() => handleDeleteClick(agent)}
                      disabled={actionLoading}
                      title="Delete Agent"
                    >
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
      
      {/* Create/Edit Agent Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Edit Agent' : 'Add New Agent'}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {formError}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="normal"
            name="name"
            label="Agent Name"
            fullWidth
            value={formData.name}
            onChange={handleInputChange}
            required
          />
          
          <TextField
            margin="normal"
            name="machine_id"
            label="Machine ID"
            fullWidth
            value={formData.machine_id}
            onChange={handleInputChange}
            required
            disabled={isEditing} // Can't change machine ID when editing
          />
          
          {/* Add Hostname field */}
          <TextField
            margin="normal"
            name="hostname"
            label="Hostname"
            fullWidth
            value={formData.hostname || ''}
            onChange={handleInputChange}
            required
            helperText="The machine's network hostname"
          />       

          <TextField
            margin="normal"
            name="version"
            label="Version"
            fullWidth
            value={formData.version || ''}
            onChange={handleInputChange}
          />
          
          <TextField
            margin="normal"
            name="tags"
            label="Tags (comma-separated)"
            fullWidth
            value={formData.tags ? formData.tags.join(', ') : ''}
            onChange={handleTagsChange}
            helperText="Enter tags separated by commas (e.g., production, windows, database)"
          />
          
          {isEditing && (
            <FormControl fullWidth margin="normal">
              <InputLabel>Status</InputLabel>
              <Select
                name="status"
                value={formData.status}
                label="Status"
                onChange={handleInputChange}
              >
                <MenuItem value="online">Online</MenuItem>
                <MenuItem value="offline">Offline</MenuItem>
                <MenuItem value="busy">Busy</MenuItem>
              </Select>
            </FormControl>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            color="primary" 
            variant="contained"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : isEditing ? 'Save Changes' : 'Create Agent'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !actionLoading && setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Agent</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete agent "{agentToDelete?.name}"?
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            This action cannot be undone and will remove all agent logs and configurations.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setDeleteDialogOpen(false)} 
            disabled={actionLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmDelete} 
            color="error" 
            variant="contained"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentList;