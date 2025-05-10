// src/components/agents/AgentDetail.js
import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Tabs, Tab, Card, CardContent, 
  CardHeader, Grid, Button, Divider, Chip, Alert, CircularProgress,
  List, ListItem, ListItemText, IconButton
} from '@mui/material';
import Icon from '../common/Icon';
import { getAgentById, getAgentLogs, sendAgentCommand } from '../../services/agentService';

function AgentDetail({ agentId, onBack }) {
  const [agent, setAgent] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logsLoading, setLogsLoading] = useState(false);
  const [error, setError] = useState('');
  const [tabIndex, setTabIndex] = useState(0);
  const [commandLoading, setCommandLoading] = useState(false);

  useEffect(() => {
    if (agentId) {
      fetchAgentDetails();
    }
  }, [agentId]);

  const fetchAgentDetails = async () => {
    setLoading(true);
    setError('');
    try {
      const agentData = await getAgentById(agentId);
      setAgent(agentData);
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
    } finally {
      setLogsLoading(false);
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
    
    setCommandLoading(true);
    try {
      const commandData = {
        command_type: commandType,
        parameters: {}
      };
      
      await sendAgentCommand(agentId, commandData);
      // Refetch agent after command
      fetchAgentDetails();
    } catch (err) {
      console.error(`Failed to send ${commandType} command:`, err);
      setError(`Failed to send command: ${err.message || 'Unknown error'}`);
    } finally {
      setCommandLoading(false);
    }
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
      <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
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
          <Icon icon="ArrowLeft" />
        </IconButton>
        <Typography variant="h5">{agent.name}</Typography>
        <Chip 
          label={agent.status} 
          color={agent.status === 'online' ? 'success' : agent.status === 'busy' ? 'warning' : 'error'} 
          size="small" 
          sx={{ ml: 2 }}
        />
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
          startIcon={<Icon icon="RefreshCw" />}
          onClick={fetchAgentDetails}
        >
          Refresh
        </Button>
        {agent.status === 'online' || agent.status === 'busy' ? (
          <Button 
            variant="outlined" 
            color="warning"
            startIcon={<Icon icon="Pause" />}
            onClick={() => handleSendCommand('stop')}
            disabled={commandLoading}
          >
            {commandLoading ? <CircularProgress size={24} /> : 'Stop Agent'}
          </Button>
        ) : (
          <Button 
            variant="outlined" 
            color="success"
            startIcon={<Icon icon="Play" />}
            onClick={() => handleSendCommand('start')}
            disabled={commandLoading}
          >
            {commandLoading ? <CircularProgress size={24} /> : 'Start Agent'}
          </Button>
        )}
        {agent.auto_login_enabled ? (
          <Button 
            variant="outlined" 
            color="error"
            startIcon={<Icon icon="LogOut" />}
          >
            Disable Auto-Login
          </Button>
        ) : (
          <Button 
            variant="outlined" 
            color="primary"
            startIcon={<Icon icon="LogIn" />}
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
                        <ListItemText primary={key} secondary={JSON.stringify(value)} />
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
        </Grid>
      )}

      {tabIndex === 1 && (
        <Box>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              variant="outlined"
              startIcon={<Icon icon="RefreshCw" />}
              onClick={fetchAgentLogs}
              disabled={logsLoading}
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
                      secondary={new Date(log.created_at).toLocaleString()}
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
    </Box>
  );
}

export default AgentDetail;