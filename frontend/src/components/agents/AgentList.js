import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Grid,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  Tooltip, MenuItem, Select, FormControl, 
  InputLabel, Switch, FormControlLabel
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import LoginIcon from '@mui/icons-material/Login';
import { 
  getAgents, 
  createAgent, 
  updateAgent,
  deleteAgent,
  enableAgentAutoLogin,
  disableAgentAutoLogin
} from '../../services/agentService';
import { getServiceAccounts } from '../../services/serviceAccountService';

function AgentList() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [agentFormData, setAgentFormData] = useState({
    name: '',
    machine_id: '',
    ip_address: '',
    tags: [],
    capabilities: {}
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState(null);
  
  // Auto login dialog
  const [autoLoginDialogOpen, setAutoLoginDialogOpen] = useState(false);
  const [currentAutoLoginAgent, setCurrentAutoLoginAgent] = useState(null);
  const [autoLoginEnabled, setAutoLoginEnabled] = useState(false);
  const [selectedServiceAccount, setSelectedServiceAccount] = useState('');
  const [sessionType, setSessionType] = useState('windows');

  const queryClient = useQueryClient();

  // Fetch agents
  const { data: agents, isLoading, error, refetch } = useQuery('agents', getAgents);
  
  // Fetch service accounts for auto-login
  const { data: serviceAccounts, isLoading: isLoadingAccounts } = useQuery(
    'serviceAccounts', 
    getServiceAccounts
  );

  // Create mutation
  const createMutation = useMutation(createAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries('agents');
      handleCloseDialog();
    }
  });

  // Update mutation
  const updateMutation = useMutation(
    (data) => updateAgent(data.id, data.agentData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('agents');
        handleCloseDialog();
      }
    }
  );

  // Delete mutation
  const deleteMutation = useMutation(deleteAgent, {
    onSuccess: () => {
      queryClient.invalidateQueries('agents');
      setDeleteDialogOpen(false);
    }
  });
  
  // Enable auto-login mutation
  const enableAutoLoginMutation = useMutation(
    (data) => enableAgentAutoLogin(data.agentId, data.serviceAccountId, data.sessionType),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('agents');
        handleCloseAutoLoginDialog();
      }
    }
  );
  
  // Disable auto-login mutation
  const disableAutoLoginMutation = useMutation(
    (agentId) => disableAgentAutoLogin(agentId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('agents');
        handleCloseAutoLoginDialog();
      }
    }
  );

  const handleOpenDialog = (agent = null) => {
    if (agent) {
      setEditMode(true);
      setCurrentAgent(agent);
      setAgentFormData({
        name: agent.name,
        machine_id: agent.machine_id,
        ip_address: agent.ip_address || '',
        tags: agent.tags || [],
        capabilities: agent.capabilities || {}
      });
    } else {
      setEditMode(false);
      setCurrentAgent(null);
      setAgentFormData({
        name: '',
        machine_id: '',
        ip_address: '',
        tags: [],
        capabilities: {}
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditMode(false);
    setCurrentAgent(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAgentFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = () => {
    if (editMode) {
      updateMutation.mutate({ 
        id: currentAgent.agent_id, 
        agentData: agentFormData 
      });
    } else {
      createMutation.mutate(agentFormData);
    }
  };

  const handleDeleteClick = (agent) => {
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (agentToDelete) {
      deleteMutation.mutate(agentToDelete.agent_id);
    }
  };
  
  const handleOpenAutoLoginDialog = (agent) => {
    setCurrentAutoLoginAgent(agent);
    setAutoLoginEnabled(agent.auto_login_enabled || false);
    setSelectedServiceAccount(agent.service_account_id || '');
    setSessionType(agent.session_type || 'windows');
    setAutoLoginDialogOpen(true);
  };
  
  const handleCloseAutoLoginDialog = () => {
    setAutoLoginDialogOpen(false);
    setCurrentAutoLoginAgent(null);
    setSelectedServiceAccount('');
    setAutoLoginEnabled(false);
  };
  
  const handleAutoLoginToggle = () => {
    setAutoLoginEnabled(!autoLoginEnabled);
  };
  
  const handleSaveAutoLogin = () => {
    if (!currentAutoLoginAgent) return;
    
    if (autoLoginEnabled) {
      if (!selectedServiceAccount) {
        // Show error - need to select a service account
        return;
      }
      
      enableAutoLoginMutation.mutate({
        agentId: currentAutoLoginAgent.agent_id,
        serviceAccountId: selectedServiceAccount,
        sessionType
      });
    } else {
      disableAutoLoginMutation.mutate(currentAutoLoginAgent.agent_id);
    }
  };

  // Filter agents based on search term
  const filteredAgents = agents?.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.machine_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (agent.ip_address && agent.ip_address.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getStatusColor = (status) => {
    switch (status) {
      case 'online':
        return 'success';
      case 'offline':
        return 'error';
      case 'busy':
        return 'warning';
      default:
        return 'default';
    }
  };

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
            onClick={() => refetch()}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => handleOpenDialog()}
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

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3 }}>
          <Typography color="error">Error loading agents: {error.message}</Typography>
        </Paper>
      ) : filteredAgents?.length ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Auto-Login</TableCell>
                <TableCell>Last Heartbeat</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAgents.map((agent) => (
                <TableRow key={agent.agent_id}>
                  <TableCell>{agent.name}</TableCell>
                  <TableCell>{agent.ip_address}</TableCell>
                  <TableCell>
                    <Chip 
                      label={agent.status} 
                      color={getStatusColor(agent.status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={agent.auto_login_enabled ? "Enabled" : "Disabled"} 
                      color={agent.auto_login_enabled ? "success" : "default"}
                      size="small" 
                      variant={agent.auto_login_enabled ? "filled" : "outlined"}
                    />
                  </TableCell>
                  <TableCell>
                    {agent.last_heartbeat 
                      ? new Date(agent.last_heartbeat).toLocaleString() 
                      : 'Never'
                    }
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Configure Auto-Login">
                      <IconButton 
                        onClick={() => handleOpenAutoLoginDialog(agent)} 
                        size="small"
                        color="primary"
                      >
                        <LoginIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit Agent">
                      <IconButton onClick={() => handleOpenDialog(agent)} size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Agent">
                      <IconButton onClick={() => handleDeleteClick(agent)} size="small" color="error">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
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

      {/* Create/Edit Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editMode ? 'Edit Agent' : 'Add Agent'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Agent Name"
                name="name"
                value={agentFormData.name}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Machine ID"
                name="machine_id"
                value={agentFormData.machine_id}
                onChange={handleInputChange}
                required
                disabled={editMode}
                helperText={editMode ? "Machine ID cannot be changed" : ""}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="IP Address"
                name="ip_address"
                value={agentFormData.ip_address}
                onChange={handleInputChange}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            color="primary"
            disabled={createMutation.isLoading || updateMutation.isLoading}
          >
            {createMutation.isLoading || updateMutation.isLoading ? (
              <CircularProgress size={24} />
            ) : (
              editMode ? 'Save Changes' : 'Create Agent'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the agent <strong>{agentToDelete?.name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleConfirmDelete} 
            color="error" 
            variant="contained"
            disabled={deleteMutation.isLoading}
          >
            {deleteMutation.isLoading ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Auto-Login Configuration Dialog */}
      <Dialog 
        open={autoLoginDialogOpen} 
        onClose={handleCloseAutoLoginDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Configure Auto-Login</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Agent: {currentAutoLoginAgent?.name}
            </Typography>
            
            <FormControlLabel
              control={
                <Switch
                  checked={autoLoginEnabled}
                  onChange={handleAutoLoginToggle}
                  name="auto_login_enabled"
                  color="primary"
                />
              }
              label="Enable Auto-Login"
              sx={{ mb: 2, display: 'block' }}
            />
            
            {autoLoginEnabled && (
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel id="service-account-label">Service Account</InputLabel>
                    <Select
                      labelId="service-account-label"
                      label="Service Account"
                      value={selectedServiceAccount}
                      onChange={(e) => setSelectedServiceAccount(e.target.value)}
                      disabled={isLoadingAccounts}
                    >
                      {serviceAccounts?.map((account) => (
                        <MenuItem key={account.account_id} value={account.account_id}>
                          {account.display_name} ({account.username})
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel id="session-type-label">Session Type</InputLabel>
                    <Select
                      labelId="session-type-label"
                      label="Session Type"
                      value={sessionType}
                      onChange={(e) => setSessionType(e.target.value)}
                    >
                      <MenuItem value="windows">Windows</MenuItem>
                      <MenuItem value="web">Web</MenuItem>
                      <MenuItem value="remote">Remote Session</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAutoLoginDialog}>Cancel</Button>
          <Button 
            onClick={handleSaveAutoLogin} 
            variant="contained" 
            color="primary"
            disabled={enableAutoLoginMutation.isLoading || disableAutoLoginMutation.isLoading}
          >
            {enableAutoLoginMutation.isLoading || disableAutoLoginMutation.isLoading ? (
              <CircularProgress size={24} />
            ) : 'Save Configuration'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AgentList;