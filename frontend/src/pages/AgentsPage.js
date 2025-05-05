import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Grid,
  Card, CardContent, CardActions
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import AddIcon     from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getAgents } from '../services/agentService';

function AgentsPage() {
  const [open, setOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading, error, refetch } = useQuery('agents', getAgents);

  const handleOpenDialog = () => {
    setOpen(true);
  };

  const handleCloseDialog = () => {
    setOpen(false);
  };

  const handleCreateAgent = () => {
    // Handle agent creation logic
    setOpen(false);
  };

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

  const columns = [
    { field: 'name', headerName: 'Name', flex: 1 },
    { field: 'ip_address', headerName: 'IP Address', flex: 1 },
    { 
      field: 'status', 
      headerName: 'Status', 
      flex: 1,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={getStatusColor(params.value)} 
          size="small" 
        />
      ) 
    },
    { field: 'version', headerName: 'Version', flex: 1 },
    { 
      field: 'last_heartbeat', 
      headerName: 'Last Heartbeat', 
      flex: 1,
      valueFormatter: (params) => {
        if (!params.value) return 'Never';
        return new Date(params.value).toLocaleString();
      }
    },
  ];

  // Filter agents based on search term
  const filteredAgents = data?.filter(agent => 
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.ip_address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1">
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
            onClick={handleOpenDialog}
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
        <Paper sx={{ height: 400, width: '100%' }}>
          <DataGrid
            rows={filteredAgents.map(agent => ({
              id: agent.agent_id,
              ...agent
            }))}
            columns={columns}
            pageSize={5}
            rowsPerPageOptions={[5, 10, 25]}
            checkboxSelection
            disableSelectionOnClick
          />
        </Paper>
      ) : (
        <Paper sx={{ p: 3 }}>
          <Typography>No agents found. Add a new agent to get started.</Typography>
        </Paper>
      )}

      {/* Agent Stats Cards */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>Agent Status</Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Agents
                </Typography>
                <Typography variant="h4">
                  {data?.length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Online
                </Typography>
                <Typography variant="h4" color="success.main">
                  {data?.filter(agent => agent.status === 'online').length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Offline
                </Typography>
                <Typography variant="h4" color="error.main">
                  {data?.filter(agent => agent.status === 'offline').length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Busy
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {data?.filter(agent => agent.status === 'busy').length || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      {/* Add Agent Dialog */}
      <Dialog open={open} onClose={handleCloseDialog}>
        <DialogTitle>Add New Agent</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Agent Name"
            fullWidth
            variant="outlined"
            sx={{ mb: 2, mt: 1 }}
          />
          <TextField
            margin="dense"
            label="Machine ID"
            fullWidth
            variant="outlined"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Service Account ID"
            fullWidth
            variant="outlined"
            sx={{ mb: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCreateAgent} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default AgentsPage;