// frontend/src/components/agents/AgentManagement.js
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, Typography, Paper, Button, CircularProgress, 
  Chip, IconButton, TextField, Dialog, DialogActions, 
  DialogContent, DialogTitle, FormControl, InputLabel, 
  Select, MenuItem, Alert, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Tabs, Tab
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';

// Import services
import { 
  getAgents, 
  createAgent, 
  updateAgent, 
  deleteAgent, 
  getAgentLogs, 
  sendAgentCommand,
  enableAgentAutoLogin,
  disableAgentAutoLogin
} from '../../services/agentService';

import { getServiceAccounts } from '../../services/serviceAccountService';

function AgentManagement({ initialTab = 0 }) {
  const [tabIndex, setTabIndex] = useState(initialTab);
  const [agents, setAgents] = useState([]);
  const [serviceAccounts, setServiceAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [agentFormData, setAgentFormData] = useState({
    name: '',
    machine_id: '',
    tags: [],
    status: 'offline'
  });
  
  // Auto-login dialog
  const [autoLoginDialogOpen, setAutoLoginDialogOpen] = useState(false);
  const [autoLoginData, setAutoLoginData] = useState({
    agent_id: '',
    service_account_id: '',
    session_type: 'windows'
  });

  // Function to fetch agents data
  const fetchAgents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const filters = {};
      if (searchTerm) {
        filters.search = searchTerm;
      }
      const agentsData = await getAgents(filters);
      setAgents(agentsData);
    } catch (err) {
      console.error('Failed to fetch agents:', err);
      setError('Failed to load agents. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [searchTerm]);

  // Function to fetch service accounts
  const fetchServiceAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const serviceAccountsData = await getServiceAccounts();
      setServiceAccounts(serviceAccountsData);
    } catch (err) {
      console.error('Failed to fetch service accounts:', err);
      setError('Failed to load service accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data on component mount or when dependencies change
  useEffect(() => {
    if (tabIndex === 0) {
      fetchAgents();
    } else if (tabIndex === 1) {
      fetchServiceAccounts();
    }
  }, [tabIndex, fetchAgents, fetchServiceAccounts]);

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };

  const toggleRowExpand = (agentId) => {
    setExpandedRows(prev => ({
      ...prev,
      [agentId]: !prev[agentId]
    }));
  };

  const handleRefresh = () => {
    if (tabIndex === 0) {
      fetchAgents();
    } else if (tabIndex === 1) {
      fetchServiceAccounts();
    }
  };

  const handleOpenDialog = (agent = null) => {
    if (agent) {
      // Edit mode
      setSelectedAgent(agent);
      setAgentFormData({
        name: agent.name,
        machine_id: agent.machine_id,
        tags: agent.tags || [],
        status: agent.status
      });
    } else {
      // Create mode
      setSelectedAgent(null);
      setAgentFormData({
        name: '',
        machine_id: '',
        tags: [],
        status: 'offline'
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedAgent(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAgentFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleTagsChange = (e) => {
    setAgentFormData(prev => ({
      ...prev,
      tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
    }));
  };

  const handleSubmitAgent = async () => {
    try {
      if (selectedAgent) {
        // Update existing agent
        const updatedAgent = await updateAgent(selectedAgent.agent_id, agentFormData);
        setAgents(prevAgents => 
          prevAgents.map(agent => 
            agent.agent_id === selectedAgent.agent_id ? updatedAgent : agent
          )
        );
      } else {
        // Create new agent
        const newAgent = await createAgent(agentFormData);
        setAgents(prev => [...prev, newAgent]);
      }
      handleCloseDialog();
    } catch (err) {
      console.error('Failed to save agent:', err);
      setError(err.message || 'Failed to save agent. Please try again.');
    }
  };

  const handleDeleteClick = (agent) => {
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    try {
      await deleteAgent(agentToDelete.agent_id);
      setAgents(prevAgents => 
        prevAgents.filter(agent => agent.agent_id !== agentToDelete.agent_id)
      );
      setDeleteDialogOpen(false);
    } catch (err) {
      console.error('Failed to delete agent:', err);
      setError(err.message || 'Failed to delete agent. Please try again.');
    }
  };

  // Agent commands
  const handleSendCommand = async (agent, commandType) => {
    try {
      const commandData = {
        command_type: commandType,
        parameters: {}
      };
      
      // Add additional parameters for specific commands
      if (commandType === 'start') {
        commandData.parameters.force = false;
      } else if (commandType === 'stop') {
        commandData.parameters.graceful = true;
      }
      
      const updatedAgent = await sendAgentCommand(agent.agent_id, commandData);
      
      // Update agent in state
      setAgents(prevAgents => 
        prevAgents.map(a => 
          a.agent_id === agent.agent_id ? updatedAgent : a
        )
      );
      
    } catch (err) {
      console.error(`Failed to send ${commandType} command:`, err);
      setError(err.message || `Failed to send ${commandType} command. Please try again.`);
    }
  };

  // Auto-login handlers
  const handleOpenAutoLoginDialog = (agent) => {
    setAutoLoginData({
      agent_id: agent.agent_id,
      service_account_id: '',
      session_type: 'windows'
    });
    setAutoLoginDialogOpen(true);
  };

  const handleCloseAutoLoginDialog = () => {
    setAutoLoginDialogOpen(false);
  };

  const handleAutoLoginChange = (e) => {
    const { name, value } = e.target;
    setAutoLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmitAutoLogin = async () => {
    try {
      const updatedAgent = await enableAgentAutoLogin(
        autoLoginData.agent_id,
        autoLoginData.service_account_id,
        autoLoginData.session_type
      );
      
      // Update agent in state
      setAgents(prevAgents => 
        prevAgents.map(agent => 
          agent.agent_id === autoLoginData.agent_id ? updatedAgent : agent
        )
      );
      
      handleCloseAutoLoginDialog();
    } catch (err) {
      console.error('Failed to enable auto-login:', err);
      setError(err.message || 'Failed to enable auto-login. Please try again.');
    }
  };

  const handleDisableAutoLogin = async (agent) => {
    try {
      const updatedAgent = await disableAgentAutoLogin(agent.agent_id);
      
      // Update agent in state
      setAgents(prevAgents => 
        prevAgents.map(a => 
          a.agent_id === agent.agent_id ? updatedAgent : a
        )
      );
    } catch (err) {
      console.error('Failed to disable auto-login:', err);
      setError(err.message || 'Failed to disable auto-login. Please try again.');
    }
  };

  // Filter agents based on search term
  const filteredAgents = agents.filter(agent => 
    !searchTerm || 
    agent.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.machine_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (agent.ip_address && agent.ip_address.includes(searchTerm))
  );

  // Filter service accounts based on search term
  const filteredAccounts = serviceAccounts.filter(account => 
    !searchTerm ||
    account.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (account.description && account.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Render agent status badge with appropriate color
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
    
    return (
      <Chip 
        label={status} 
        color={color} 
        size="small"
      />
    );
  };

  return (
    <Box className="w-full">
      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>

      {/* Agent Tab Content */}
      {tabIndex === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h5" component="h2">
              Agent Management
            </Typography>
            <Box>
              <Button 
                variant="outlined" 
                startIcon={<RefreshIcon />} 
                onClick={handleRefresh}
                sx={{ mr: 2 }}
              >
                Refresh
              </Button>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                onClick={() => handleOpenDialog()}
              >
                Add Agent
              </Button>
            </Box>
          </Box>

          {/* Search */}
          <TextField
            fullWidth
            label="Search agents"
            variant="outlined"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 3 }}
          />

          {/* Error message */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading, Error, and Empty States */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredAgents.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography>No agents found. Add a new agent to get started.</Typography>
            </Paper>
          ) : (
            /* Agents Table */
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox"></TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Machine ID</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>IP Address</TableCell>
                    <TableCell>Version</TableCell>
                    <TableCell>Last Heartbeat</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAgents.map((agent) => (
                    <React.Fragment key={agent.agent_id}>
                      <TableRow hover>
                        <TableCell padding="checkbox">
                          <IconButton
                            onClick={() => toggleRowExpand(agent.agent_id)}
                            size="small"
                          >
                            {expandedRows[agent.agent_id] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                          </IconButton>
                        </TableCell>
                        <TableCell>{agent.name}</TableCell>
                        <TableCell>{agent.machine_id}</TableCell>
                        <TableCell>{renderAgentStatus(agent.status)}</TableCell>
                        <TableCell>{agent.ip_address || '-'}</TableCell>
                        <TableCell>{agent.version || '-'}</TableCell>
                        <TableCell>
                          {agent.last_heartbeat 
                            ? new Date(agent.last_heartbeat).toLocaleString() 
                            : 'Never'
                          }
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            onClick={() => handleOpenDialog(agent)}
                            title="Edit Agent"
                          >
                            <EditIcon />
                          </IconButton>
                          {agent.status === 'online' || agent.status === 'busy' ? (
                            <IconButton
                              onClick={() => handleSendCommand(agent, 'stop')}
                              title="Stop Agent"
                            >
                              <PauseIcon />
                            </IconButton>
                          ) : (
                            <IconButton
                              onClick={() => handleSendCommand(agent, 'start')}
                              title="Start Agent"
                            >
                              <PlayArrowIcon />
                            </IconButton>
                          )}
                          <IconButton
                            onClick={() => handleDeleteClick(agent)}
                            title="Delete Agent"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      {/* Expanded Row Content */}
                      {expandedRows[agent.agent_id] && (
                        <TableRow>
                          <TableCell colSpan={8} sx={{ p: 3, backgroundColor: 'rgba(0, 0, 0, 0.02)' }}>
                            <Box sx={{ display: 'flex', gap: 2 }}>
                              {/* Capabilities Card */}
                              <Paper sx={{ flex: 1, p: 3 }}>
                                <Typography variant="h6" gutterBottom>
                                  Capabilities
                                </Typography>
                                {agent.capabilities && Object.keys(agent.capabilities).length > 0 ? (
                                  <Box component="ul" sx={{ pl: 2 }}>
                                    {Object.entries(agent.capabilities).map(([key, value]) => (
                                      <Box component="li" key={key} sx={{ mb: 1 }}>
                                        <Typography variant="body2">
                                          <strong>{key}:</strong> {typeof value === 'object' ? JSON.stringify(value) : value.toString()}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Box>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    No capabilities reported
                                  </Typography>
                                )}
                              </Paper>
                              
                              {/* Auto-Login Card */}
                              <Paper sx={{ flex: 1, p: 3 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                  <Typography variant="h6">
                                    Auto-Login Configuration
                                  </Typography>
                                  {agent.auto_login_enabled ? (
                                    <Button 
                                      variant="outlined" 
                                      color="error"
                                      startIcon={<LogoutIcon />}
                                      onClick={() => handleDisableAutoLogin(agent)}
                                    >
                                      Disable
                                    </Button>
                                  ) : (
                                    <Button 
                                      variant="outlined" 
                                      color="primary"
                                      startIcon={<LoginIcon />}
                                      onClick={() => handleOpenAutoLoginDialog(agent)}
                                    >
                                      Enable
                                    </Button>
                                  )}
                                </Box>
                                
                                {agent.auto_login_enabled && agent.service_account ? (
                                  <Alert severity="info" sx={{ mb: 2 }}>
                                    <Typography variant="body2">
                                      <strong>Account:</strong> {agent.service_account.display_name} ({agent.service_account.username})
                                    </Typography>
                                    <Typography variant="body2">
                                      <strong>Session Type:</strong> {agent.session_type || 'windows'}
                                    </Typography>
                                  </Alert>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    Auto-login is not configured for this agent.
                                  </Typography>
                                )}
                                
                                {agent.tags && agent.tags.length > 0 && (
                                  <Box sx={{ mt: 3 }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                      Tags
                                    </Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                      {agent.tags.map(tag => (
                                        <Chip 
                                          key={tag} 
                                          label={tag}
                                          size="small"
                                        />
                                      ))}
                                    </Box>
                                  </Box>
                                )}
                              </Paper>
                            </Box>
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          
          {/* Agent Form Dialog */}
          <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
            <DialogTitle>
              {selectedAgent ? 'Edit Agent' : 'Add Agent'}
            </DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="normal"
                name="name"
                label="Agent Name"
                fullWidth
                value={agentFormData.name}
                onChange={handleInputChange}
                required
              />
              
              <TextField
                margin="normal"
                name="machine_id"
                label="Machine ID"
                fullWidth
                value={agentFormData.machine_id}
                onChange={handleInputChange}
                required
              />
              
              <TextField
                margin="normal"
                name="tags"
                label="Tags (comma-separated)"
                fullWidth
                value={agentFormData.tags.join(', ')}
                onChange={handleTagsChange}
              />
              
              {selectedAgent && (
                <FormControl fullWidth margin="normal">
                  <InputLabel>Status</InputLabel>
                  <Select
                    name="status"
                    value={agentFormData.status}
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
              <Button onClick={handleCloseDialog}>Cancel</Button>
              <Button onClick={handleSubmitAgent} variant="contained">
                {selectedAgent ? 'Save Changes' : 'Create Agent'}
              </Button>
            </DialogActions>
          </Dialog>
          
          {/* Delete Confirmation Dialog */}
          <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
            <DialogTitle>Delete Agent</DialogTitle>
            <DialogContent>
              <Typography>
                Are you sure you want to delete the agent{' '}
                <strong>{agentToDelete?.name}</strong>? This action cannot be undone.
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleConfirmDelete} variant="contained" color="error">
                Delete
              </Button>
            </DialogActions>
          </Dialog>
          
          {/* Auto Login Dialog */}
          <Dialog open={autoLoginDialogOpen} onClose={handleCloseAutoLoginDialog} maxWidth="sm" fullWidth>
            <DialogTitle>Enable Auto-Login</DialogTitle>
            <DialogContent>
              <FormControl fullWidth margin="normal">
                <InputLabel>Service Account</InputLabel>
                <Select
                  name="service_account_id"
                  value={autoLoginData.service_account_id}
                  label="Service Account"
                  onChange={handleAutoLoginChange}
                  required
                >
                  <MenuItem value="">Select a service account</MenuItem>
                  {serviceAccounts.map(account => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.display_name} ({account.username})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>Session Type</InputLabel>
                <Select
                  name="session_type"
                  value={autoLoginData.session_type}
                  label="Session Type"
                  onChange={handleAutoLoginChange}
                >
                  <MenuItem value="windows">Windows</MenuItem>
                  <MenuItem value="web">Web</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
              
              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Auto-login will allow the agent to run background processes with the
                  configured service account credentials. Make sure to follow proper
                  security protocols.
                </Typography>
              </Alert>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseAutoLoginDialog}>Cancel</Button>
              <Button onClick={handleSubmitAutoLogin} variant="contained">
                Enable Auto-Login
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      )}

      {/* Service Accounts Tab Content */}
      {tabIndex === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h5" component="h2">
              Service Accounts
            </Typography>
            <Box>
              <Button 
                variant="outlined" 
                startIcon={<RefreshIcon />} 
                onClick={handleRefresh}
                sx={{ mr: 2 }}
              >
                Refresh
              </Button>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                // This would open a form to create service accounts
                // which would need to be implemented
              >
                Add Account
              </Button>
            </Box>
          </Box>

          {/* Search */}
          <TextField
            fullWidth
            label="Search service accounts"
            variant="outlined"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            sx={{ mb: 3 }}
          />

          {/* Error message */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading, Error, and Empty States */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredAccounts.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Typography>No service accounts found. Add a new account to get started.</Typography>
            </Paper>
          ) : (
            /* Service Accounts Table */
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Username</TableCell>
                    <TableCell>Display Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAccounts.map((account) => (
                    <TableRow key={account.account_id} hover>
                      <TableCell>{account.username}</TableCell>
                      <TableCell>{account.display_name}</TableCell>
                      <TableCell>{account.account_type}</TableCell>
                      <TableCell>{account.description || '-'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={account.status} 
                          color={account.status === 'active' ? 'success' : 'error'} 
                          size="small" 
                        />
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          title="Edit Account"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          title="Delete Account"
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Box>
      )}
    </Box>
  );
}

export default AgentManagement;