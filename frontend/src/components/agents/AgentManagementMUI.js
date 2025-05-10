import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Paper, Tabs, Tab, Button, IconButton,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, Collapse, Divider, Alert, CircularProgress, Grid
} from '@mui/material';
import LucideIcon from '../common/LucideIcon';
import LucideIconFallback from '../common/LucideIconFallback';
// Import specific icons from Lucide for fallback usage
import { 
  RefreshCw, Plus, Edit, Trash2, Play, Pause, 
  CheckCircle, AlertTriangle, X, LogIn, LogOut, 
  ChevronUp, ChevronDown, Search
} from 'lucide-react';
import { getAgents, createAgent, updateAgent, deleteAgent, sendAgentCommand, enableAgentAutoLogin, disableAgentAutoLogin } from '../../services/agentService';
import { getServiceAccounts } from '../../services/serviceAccountService';

function AgentManagementMUI() {
  // State variables
  const [tabIndex, setTabIndex] = useState(0);
  const [agents, setAgents] = useState([]);
  const [serviceAccounts, setServiceAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [agentDialog, setAgentDialog] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [expandedRows, setExpandedRows] = useState({});
  const [agentToDelete, setAgentToDelete] = useState(null);
  const [agentFormData, setAgentFormData] = useState({
    name: '',
    machine_id: '',
    tags: [],
    status: 'offline'
  });
  
  // Service account dialog
  const [accountDialog, setAccountDialog] = useState(false);
  const [serviceAccountFormData, setServiceAccountFormData] = useState({
    username: '',
    display_name: '',
    description: '',
    password: '',
    account_type: 'robot'
  });
  
  // Auto-login dialog
  const [autoLoginDialog, setAutoLoginDialog] = useState(false);
  const [autoLoginData, setAutoLoginData] = useState({
    agent_id: '',
    service_account_id: '',
    session_type: 'windows'
  });

  // Fetch agents data
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

  // Fetch service accounts
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

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };

  // Toggle row expansion
  const toggleRowExpand = (agentId) => {
    setExpandedRows(prev => ({
      ...prev,
      [agentId]: !prev[agentId]
    }));
  };

  // Refresh data
  const handleRefresh = () => {
    if (tabIndex === 0) {
      fetchAgents();
    } else if (tabIndex === 1) {
      fetchServiceAccounts();
    }
  };

  // Open agent dialog for create/edit
  const handleOpenAgentDialog = (agent = null) => {
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
    setAgentDialog(true);
  };

  // Close agent dialog
  const handleCloseAgentDialog = () => {
    setAgentDialog(false);
    setSelectedAgent(null);
  };

  // Handle form input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAgentFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle tags input change
  const handleTagsChange = (e) => {
    setAgentFormData(prev => ({
      ...prev,
      tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)
    }));
  };

  // Submit agent form
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
      handleCloseAgentDialog();
    } catch (err) {
      console.error('Failed to save agent:', err);
      setError(err.message || 'Failed to save agent. Please try again.');
    }
  };

  // Open delete confirmation dialog
  const handleDeleteClick = (agent) => {
    setAgentToDelete(agent);
    setDeleteDialog(true);
  };

  // Confirm agent deletion
  const handleConfirmDelete = async () => {
    try {
      await deleteAgent(agentToDelete.agent_id);
      setAgents(prevAgents => 
        prevAgents.filter(agent => agent.agent_id !== agentToDelete.agent_id)
      );
      setDeleteDialog(false);
    } catch (err) {
      console.error('Failed to delete agent:', err);
      setError(err.message || 'Failed to delete agent. Please try again.');
    }
  };

  // Open service account dialog
  const handleOpenAccountDialog = () => {
    setServiceAccountFormData({
      username: '',
      display_name: '',
      description: '',
      password: '',
      account_type: 'robot'
    });
    setAccountDialog(true);
  };

  // Close service account dialog
  const handleCloseAccountDialog = () => {
    setAccountDialog(false);
  };

  // Handle service account form input change
  const handleAccountInputChange = (e) => {
    const { name, value } = e.target;
    setServiceAccountFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Send command to agent
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

  // Open auto-login dialog
  const handleOpenAutoLoginDialog = (agent) => {
    setAutoLoginData({
      agent_id: agent.agent_id,
      service_account_id: '',
      session_type: 'windows'
    });
    setAutoLoginDialog(true);
  };

  // Close auto-login dialog
  const handleCloseAutoLoginDialog = () => {
    setAutoLoginDialog(false);
  };

  // Handle auto-login form input change
  const handleAutoLoginChange = (e) => {
    const { name, value } = e.target;
    setAutoLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Submit auto-login configuration
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

  // Disable auto-login for agent
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

  // Render agent status chip
  const renderAgentStatus = (status) => {
    let color;
    let iconComponent;
    
    switch (status) {
      case 'online':
        color = 'success';
        iconComponent = CheckCircle;
        break;
      case 'offline':
        color = 'error';
        iconComponent = X;
        break;
      case 'busy':
        color = 'warning';
        iconComponent = AlertTriangle;
        break;
      default:
        color = 'default';
        iconComponent = null;
    }
    
    return (
      <Chip 
        icon={iconComponent && <LucideIconFallback icon={iconComponent} size="small" />}
        label={status} 
        color={color}
        size="small" 
      />
    );
  };

  return (
    <Box>
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
            <Typography variant="h6">
              Agent Management
            </Typography>
            <Box>
              <Button 
                variant="outlined" 
                startIcon={<LucideIconFallback icon={RefreshCw} />} 
                onClick={handleRefresh}
                sx={{ mr: 2 }}
              >
                Refresh
              </Button>
              <Button 
                variant="contained" 
                startIcon={<LucideIconFallback icon={Plus} />}
                onClick={() => handleOpenAgentDialog()}
              >
                Add Agent
              </Button>
            </Box>
          </Box>

          {/* Search field */}
          <TextField
            fullWidth
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <LucideIconFallback icon={Search} sx={{ mr: 1, color: 'action.active' }} />
            }}
            sx={{ mb: 3 }}
          />

          {/* Error message */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading state */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredAgents.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No agents found. Add a new agent to get started.
              </Typography>
            </Paper>
          ) : (
            /* Agents Table */
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell width="50"></TableCell>
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
                        <TableCell>
                          <IconButton 
                            size="small" 
                            onClick={() => toggleRowExpand(agent.agent_id)}
                          >
                            <LucideIconFallback 
                              icon={expandedRows[agent.agent_id] ? ChevronUp : ChevronDown} 
                            />
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
                            size="small" 
                            color="primary"
                            onClick={() => handleOpenAgentDialog(agent)}
                          >
                            <LucideIconFallback icon={Edit} />
                          </IconButton>
                          {agent.status === 'online' || agent.status === 'busy' ? (
                            <IconButton 
                              size="small" 
                              color="warning"
                              onClick={() => handleSendCommand(agent, 'stop')}
                            >
                              <LucideIconFallback icon={Pause} />
                            </IconButton>
                          ) : (
                            <IconButton 
                              size="small" 
                              color="success"
                              onClick={() => handleSendCommand(agent, 'start')}
                            >
                              <LucideIconFallback icon={Play} />
                            </IconButton>
                          )}
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleDeleteClick(agent)}
                          >
                            <LucideIconFallback icon={Trash2} />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                      {/* Expanded Row Content */}
                      <TableRow>
                        <TableCell colSpan={8} style={{ paddingTop: 0, paddingBottom: 0 }}>
                          <Collapse in={expandedRows[agent.agent_id]} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 3 }}>
                              <Grid container spacing={3}>
                                {/* Capabilities Card */}
                                <Grid item xs={12} md={6}>
                                  <Paper sx={{ p: 2, height: '100%' }}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                      Capabilities
                                    </Typography>
                                    {agent.capabilities && Object.keys(agent.capabilities).length > 0 ? (
                                      <Box>
                                        {Object.entries(agent.capabilities).map(([key, value]) => (
                                          <Box key={key} sx={{ mb: 1 }}>
                                            <Typography variant="subtitle2" component="span">
                                              {key}:
                                            </Typography>{' '}
                                            <Typography component="span" color="text.secondary">
                                              {value}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Box>
                                    ) : (
                                      <Typography color="text.secondary">
                                        No capabilities reported
                                      </Typography>
                                    )}
                                  </Paper>
                                </Grid>
                                
                                {/* Auto-Login Card */}
                                <Grid item xs={12} md={6}>
                                  <Paper sx={{ p: 2, height: '100%' }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                                      <Typography variant="h6">
                                        Auto-Login Configuration
                                      </Typography>
                                      {agent.auto_login_enabled ? (
                                        <Button 
                                          variant="outlined" 
                                          color="error"
                                          size="small"
                                          startIcon={<LucideIconFallback icon={LogOut} />}
                                          onClick={() => handleDisableAutoLogin(agent)}
                                        >
                                          Disable
                                        </Button>
                                      ) : (
                                        <Button 
                                          variant="outlined" 
                                          color="primary"
                                          size="small"
                                          startIcon={<LucideIconFallback icon={LogIn} />}
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
                                      <Typography color="text.secondary">
                                        Auto-login is not configured for this agent.
                                      </Typography>
                                    )}
                                    
                                    {agent.tags && agent.tags.length > 0 && (
                                      <Box sx={{ mt: 2 }}>
                                        <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                          Tags
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                          {agent.tags.map(tag => (
                                            <Chip key={tag} label={tag} size="small" />
                                          ))}
                                        </Box>
                                      </Box>
                                    )}
                                  </Paper>
                                </Grid>
                              </Grid>
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Agent Form Dialog */}
          <Dialog 
            open={agentDialog} 
            onClose={handleCloseAgentDialog}
            maxWidth="sm"
            fullWidth
          >
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
              />
              <TextField
                margin="normal"
                name="machine_id"
                label="Machine ID"
                fullWidth
                value={agentFormData.machine_id}
                onChange={handleInputChange}
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
              <Button onClick={handleCloseAgentDialog}>Cancel</Button>
              <Button onClick={handleSubmitAgent} variant="contained">
                {selectedAgent ? 'Save Changes' : 'Create Agent'}
              </Button>
            </DialogActions>
          </Dialog>

          {/* Delete Confirmation Dialog */}
          <Dialog
            open={deleteDialog}
            onClose={() => setDeleteDialog(false)}
          >
            <DialogTitle>Delete Agent</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Are you sure you want to delete the agent <strong>{agentToDelete?.name}</strong>?
                This action cannot be undone.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
              <Button onClick={handleConfirmDelete} color="error" variant="contained">
                Delete
              </Button>
            </DialogActions>
          </Dialog>

          {/* Auto Login Dialog */}
          <Dialog
            open={autoLoginDialog}
            onClose={handleCloseAutoLoginDialog}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Enable Auto-Login</DialogTitle>
            <DialogContent>
              <FormControl fullWidth margin="normal">
                <InputLabel>Service Account</InputLabel>
                <Select
                  name="service_account_id"
                  value={autoLoginData.service_account_id}
                  label="Service Account"
                  onChange={handleAutoLoginChange}
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
            <Typography variant="h6">
              Service Accounts
            </Typography>
            <Box>
              <Button 
                variant="outlined" 
                startIcon={<LucideIcon icon="RefreshCw" />} 
                onClick={handleRefresh}
                sx={{ mr: 2 }}
              >
                Refresh
              </Button>
              <Button 
                variant="contained" 
                startIcon={<LucideIconFallback icon={Plus} />}
                onClick={handleOpenAccountDialog}
              >
                Add Account
              </Button>
            </Box>
          </Box>

          {/* Search field */}
          <TextField
            fullWidth
            placeholder="Search service accounts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <LucideIconFallback icon={Search} sx={{ mr: 1, color: 'action.active' }} />
            }}
            sx={{ mb: 3 }}
          />

          {/* Error message */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Loading state */}
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredAccounts.length === 0 ? (
            <Paper sx={{ p: 3, textAlign: 'center' }}>
              <Typography color="text.secondary">
                No service accounts found. Add a new account to get started.
              </Typography>
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
                        <IconButton size="small" color="primary">
                          <LucideIconFallback icon={Edit} />
                        </IconButton>
                        <IconButton size="small" color="error">
                          <LucideIconFallback icon={Trash2} />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {/* Create Service Account Dialog */}
          <Dialog
            open={accountDialog}
            onClose={handleCloseAccountDialog}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Add Service Account</DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="normal"
                name="username"
                label="Username"
                fullWidth
                value={serviceAccountFormData.username}
                onChange={handleAccountInputChange}
              />
              <TextField
                margin="normal"
                name="display_name"
                label="Display Name"
                fullWidth
                value={serviceAccountFormData.display_name}
                onChange={handleAccountInputChange}
              />
              <TextField
                margin="normal"
                name="password"
                label="Password"
                type="password"
                fullWidth
                value={serviceAccountFormData.password}
                onChange={handleAccountInputChange}
              />
              <TextField
                margin="normal"
                name="description"
                label="Description"
                fullWidth
                multiline
                rows={3}
                value={serviceAccountFormData.description}
                onChange={handleAccountInputChange}
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Account Type</InputLabel>
                <Select
                  name="account_type"
                  value={serviceAccountFormData.account_type}
                  label="Account Type"
                  onChange={handleAccountInputChange}
                >
                  <MenuItem value="robot">Robot</MenuItem>
                  <MenuItem value="service">Service</MenuItem>
                </Select>
              </FormControl>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseAccountDialog}>Cancel</Button>
              <Button variant="contained">
                Create Account
              </Button>
            </DialogActions>
          </Dialog>
        </Box>
      )}
    </Box>
  );
}

export default AgentManagementMUI;