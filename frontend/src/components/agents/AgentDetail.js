// frontend/src/components/agents/AgentDetail.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Tabs, Tab, Card, CardContent, 
  CardHeader, Grid, Button, Divider, Chip, Alert, CircularProgress,
  List, ListItem, ListItemText, IconButton, Dialog, DialogTitle,
  DialogContent, DialogActions, TextField, FormControl, InputLabel,
  Select, MenuItem
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import { 
  getAgentById, 
  getAgentLogs, 
  sendAgentCommand,
  enableAgentAutoLogin,
  disableAgentAutoLogin,
  updateAgent
} from '../../services/agentService';
import { getServiceAccounts } from '../../services/serviceAccountService';

const AgentDetail = ({ agentId, onBack, onUpdate }) => {
  const [agent, setAgent] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logsLoading, setLogsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');
  const [tabIndex, setTabIndex] = useState(0);
  
  // Auto-login dialog
  const [autoLoginDialogOpen, setAutoLoginDialogOpen] = useState(false);
  const [serviceAccounts, setServiceAccounts] = useState([]);
  const [autoLoginData, setAutoLoginData] = useState({
    service_account_id: '',
    session_type: 'windows'
  });
  const [autoLoginError, setAutoLoginError] = useState('');
  
  // Edit agent dialog
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: '',
    tags: [],
    status: '',
    version: ''
  });
  const [editFormError, setEditFormError] = useState('');

  useEffect(() => {
    if (agentId) {
      fetchAgentDetails();
      fetchServiceAccounts();
    }
  }, [agentId]);

  const fetchAgentDetails = async () => {
    setLoading(true);
    setError('');
    try {
      const agentData = await getAgentById(agentId);
      setAgent(agentData);
      
      // Initialize edit form data
      setEditFormData({
        name: agentData.name,
        tags: agentData.tags || [],
        status: agentData.status,
        version: agentData.version || ''
      });
      
      if (tabIndex === 1) {
        fetchAgentLogs();
      }
    } catch (err) {
      console.error('Failed to fetch agent details:', err);
      setError('Error loading agent details: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentLogs = async () => {
    if (!agentId) return;
    
    setLogsLoading(true);
    try {
      const logsData = await getAgentLogs(agentId);
      setLogs(logsData);
    } catch (err) {
      console.error('Failed to fetch agent logs:', err);
      setError('Error fetching logs: ' + (err.message || 'Unknown error'));
    } finally {
      setLogsLoading(false);
    }
  };

  const fetchServiceAccounts = async () => {
    try {
      const accounts = await getServiceAccounts();
      setServiceAccounts(accounts);
    } catch (err) {
      console.error('Failed to fetch service accounts:', err);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
    if (newValue === 1 && logs.length === 0) {
      fetchAgentLogs();
    }
  };

  const handleSendCommand = async (commandType) => {
    if (!agentId) return;
    
    setActionLoading(true);
    try {
      const commandData = {
        command_type: commandType,
        parameters: {}
      };
      
      const updatedAgent = await sendAgentCommand(agentId, commandData);
      setAgent(updatedAgent);
      
      // Notify parent component of update
      if (onUpdate) {
        onUpdate(updatedAgent);
      }
    } catch (err) {
      console.error(`Failed to send ${commandType} command:`, err);
      setError(`Failed to send command: ${err.message || 'Unknown error'}`);
    } finally {
      setActionLoading(false);
    }
  };
  
  // Auto-login handlers
  const handleOpenAutoLoginDialog = () => {
    setAutoLoginData({
      service_account_id: '',
      session_type: 'windows'
    });
    setAutoLoginError('');
    setAutoLoginDialogOpen(true);
  };
  
  const handleAutoLoginChange = (e) => {
    const { name, value } = e.target;
    setAutoLoginData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleEnableAutoLogin = async () => {
    setAutoLoginError('');
    setActionLoading(true);
    
    // Validate form
    if (!autoLoginData.service_account_id) {
      setAutoLoginError('Please select a service account');
      setActionLoading(false);
      return;
    }
    
    try {
      const updatedAgent = await enableAgentAutoLogin(
        agentId,
        autoLoginData.service_account_id,
        autoLoginData.session_type
      );
      
      setAgent(updatedAgent);
      setAutoLoginDialogOpen(false);
      
      // Notify parent component of update
      if (onUpdate) {
        onUpdate(updatedAgent);
      }
    } catch (err) {
      console.error('Failed to enable auto-login:', err);
      setAutoLoginError('Error enabling auto-login: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };
  
  const handleDisableAutoLogin = async () => {
    setActionLoading(true);
    try {
      const updatedAgent = await disableAgentAutoLogin(agentId);
      setAgent(updatedAgent);
      
      // Notify parent component of update
      if (onUpdate) {
        onUpdate(updatedAgent);
      }
    } catch (err) {
      console.error('Failed to disable auto-login:', err);
      setError('Error disabling auto-login: ' + (err.message || 'Unknown error'));
    } finally {
      setActionLoading(false);
    }
  };
  
  // Edit agent handlers
  const handleOpenEditDialog = () => {
    setEditFormData({
      name: agent.name,
      tags: agent.tags || [],
      status: agent.status,
      version: agent.version || ''
    });
    setEditFormError('');
    setEditDialogOpen(true);
  };
  
  const handleEditInputChange = (e) => {
    const { name, value } = e.target;
    setEditFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleTagsChange = (e) => {
    const tagsString = e.target.value;
    const tagsArray = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    setEditFormData(prev => ({
      ...prev,
      tags: tagsArray
    }));
  };
  
  const handleUpdateAgent = async () => {
    setEditFormError('');
    setActionLoading(true);
    
    // Validate form
    if (!editFormData.name) {
      setEditFormError('Name is required');
      setActionLoading(false);
      return;
    }
    
    try {
      const updatedAgent = await updateAgent(agentId, editFormData);
      setAgent(updatedAgent);
      setEditDialogOpen(false);
      
      // Notify parent component of update
      if (onUpdate) {
        onUpdate(updatedAgent);
      }
    } catch (err) {
      console.error('Failed to update agent:', err);
      setEditFormError('Error updating agent: ' + (err.message || 'Unknown error'));
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        sx={{ mb: 3 }}
        action={
          <Button color="inherit" size="small" onClick={fetchAgentDetails}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  if (!agent) {
    return (
      <Alert severity="info">No agent selected</Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton onClick={onBack} sx={{ mr: 1 }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h5">{agent.name}</Typography>
        {renderAgentStatus(agent.status)}
        <Button 
          variant="outlined" 
          size="small" 
          startIcon={<RefreshIcon />} 
          sx={{ ml: 'auto' }}
          onClick={fetchAgentDetails}
          disabled={actionLoading}
        >
          Refresh
        </Button>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Details" />
          <Tab label="Logs" />
          <Tab label="Jobs" />
        </Tabs>
      </Paper>

      {/* Agent Actions */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button 
          variant="outlined" 
          startIcon={<RefreshIcon />}
          onClick={fetchAgentDetails}
          disabled={actionLoading}
        >
          Refresh
        </Button>
        {agent.status === 'online' || agent.status === 'busy' ? (
          <Button 
            variant="outlined" 
            color="warning"
            startIcon={<PauseIcon />}
            onClick={() => handleSendCommand('stop')}
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Stop Agent'}
          </Button>
        ) : (
          <Button 
            variant="outlined" 
            color="success"
            startIcon={<PlayArrowIcon />}
            onClick={() => handleSendCommand('start')}
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Start Agent'}
          </Button>
        )}
        <Button
          variant="outlined"
          color="primary"
          onClick={handleOpenEditDialog}
          disabled={actionLoading}
        >
          Edit Agent
        </Button>
        {agent.auto_login_enabled ? (
          <Button 
            variant="outlined" 
            color="error"
            startIcon={<LogoutIcon />}
            onClick={handleDisableAutoLogin}
            disabled={actionLoading}
          >
            Disable Auto-Login
          </Button>
        ) : (
          <Button 
            variant="outlined" 
            color="primary"
            startIcon={<LoginIcon />}
            onClick={handleOpenAutoLoginDialog}
            disabled={actionLoading}
          >
            Configure Auto-Login
          </Button>
        )}
      </Box>

      {/* Tab Content */}
      {tabIndex === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Agent Information" />
              <Divider />
              <CardContent>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Machine ID" secondary={agent.machine_id} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="IP Address" secondary={agent.ip_address || 'Not Available'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Version" secondary={agent.version || 'Unknown'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Last Heartbeat" secondary={agent.last_heartbeat ? new Date(agent.last_heartbeat).toLocaleString() : 'Never'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Created At" secondary={agent.created_at ? new Date(agent.created_at).toLocaleString() : 'Unknown'} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardHeader title="Capabilities" />
              <Divider />
              <CardContent>
                {agent.capabilities ? (
                  <List dense>
                    {Object.entries(agent.capabilities).map(([key, value]) => (
                      <ListItem key={key}>
                        <ListItemText 
                          primary={key} 
                          secondary={typeof value === 'object' ? JSON.stringify(value) : String(value)} 
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">No capabilities reported</Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          {agent.tags && agent.tags.length > 0 && (
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Tags" />
                <Divider />
                <CardContent>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {agent.tags.map(tag => (
                      <Chip key={tag} label={tag} />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          )}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Auto-Login Configuration" />
              <Divider />
              <CardContent>
                {agent.auto_login_enabled ? (
                  <>
                    <Typography variant="subtitle1" gutterBottom>
                      Auto-login is enabled for this agent
                    </Typography>
                    {agent.service_account && (
                      <List dense>
                        <ListItem>
                          <ListItemText 
                            primary="Service Account" 
                            secondary={`${agent.service_account.display_name} (${agent.service_account.username})`} 
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemText 
                            primary="Session Type" 
                            secondary={agent.session_type || 'windows'} 
                          />
                        </ListItem>
                      </List>
                    )}
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<LogoutIcon />}
                      onClick={handleDisableAutoLogin}
                      disabled={actionLoading}
                      sx={{ mt: 2 }}
                    >
                      Disable Auto-Login
                    </Button>
                  </>
                ) : (
                  <>
                    <Typography variant="body2" color="text.secondary">
                      Auto-login is not configured for this agent.
                    </Typography>
                    <Button
                      variant="outlined"
                      color="primary"
                      startIcon={<LoginIcon />}
                      onClick={handleOpenAutoLoginDialog}
                      disabled={actionLoading}
                      sx={{ mt: 2 }}
                    >
                      Configure Auto-Login
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {tabIndex === 1 && (
        <Box>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchAgentLogs}
              disabled={logsLoading || actionLoading}
            >
              Refresh Logs
            </Button>
          </Box>
          
          {logsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : logs.length === 0 ? (
            <Paper sx={{ p: 3 }}>
              <Typography>No logs available for this agent.</Typography>
            </Paper>
          ) : (
            <Paper>
              <List>
                {logs.map((log) => (
                  <ListItem key={log.log_id} divider>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip 
                            label={log.log_level} 
                            color={log.log_level === 'error' ? 'error' : log.log_level === 'warning' ? 'warning' : 'info'} 
                            size="small" 
                          />
                          <Typography variant="body1">{log.message}</Typography>
                        </Box>
                      }
                      secondary={log.created_at ? new Date(log.created_at).toLocaleString() : 'Unknown'}
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          )}
        </Box>
      )}

      {tabIndex === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography>Job history will be displayed here.</Typography>
        </Paper>
      )}
      
      {/* Auto Login Dialog */}
      <Dialog open={autoLoginDialogOpen} onClose={() => !actionLoading && setAutoLoginDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Auto-Login</DialogTitle>
        <DialogContent>
          {autoLoginError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {autoLoginError}
            </Alert>
          )}
          
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
          <Button onClick={() => setAutoLoginDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleEnableAutoLogin} 
            color="primary" 
            variant="contained"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Enable Auto-Login'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Edit Agent Dialog */}
      <Dialog open={editDialogOpen} onClose={() => !actionLoading && setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Agent</DialogTitle>
        <DialogContent>
          {editFormError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {editFormError}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="normal"
            name="name"
            label="Agent Name"
            fullWidth
            value={editFormData.name}
            onChange={handleEditInputChange}
            required
          />
          
          <TextField
            margin="normal"
            name="version"
            label="Version"
            fullWidth
            value={editFormData.version || ''}
            onChange={handleEditInputChange}
          />
          
          <TextField
            margin="normal"
            name="tags"
            label="Tags (comma-separated)"
            fullWidth
            value={editFormData.tags ? editFormData.tags.join(', ') : ''}
            onChange={handleTagsChange}
            helperText="Enter tags separated by commas (e.g., production, windows, database)"
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Status</InputLabel>
            <Select
              name="status"
              value={editFormData.status}
              label="Status"
              onChange={handleEditInputChange}
            >
              <MenuItem value="online">Online</MenuItem>
              <MenuItem value="offline">Offline</MenuItem>
              <MenuItem value="busy">Busy</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleUpdateAgent} 
            color="primary" 
            variant="contained"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentDetail;