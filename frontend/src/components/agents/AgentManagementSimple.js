import React, { useState } from 'react';
import { 
  Box, Typography, Paper, Tabs, Tab, Button,
  Dialog, DialogTitle, DialogContent, DialogActions,
  TextField, FormControl, InputLabel, Select, MenuItem,
  Chip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import { getAgents } from '../../services/agentService';

function AgentManagementSimple() {
  const [tabIndex, setTabIndex] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  
  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };
  
  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab label="Agents" />
          <Tab label="Service Accounts" />
        </Tabs>
      </Paper>
      
      {tabIndex === 0 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6">
              Agent Management
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              onClick={() => setOpenDialog(true)}
            >
              Add Agent
            </Button>
          </Box>
          
          <Typography variant="body2" sx={{ mb: 2 }}>
            Configure remote agents that will execute automation jobs. Agents can be installed on Windows or Linux machines.
          </Typography>
          
          <Paper sx={{ p: 3 }}>
            <Typography>
              This is a simplified version of the agent management UI. To see the full functionality, 
              make sure to install the Lucide React icons package and styles correctly.
            </Typography>
          </Paper>
          
          {/* Add Agent Dialog */}
          <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
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
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  label="Status"
                  defaultValue="offline"
                >
                  <MenuItem value="online">Online</MenuItem>
                  <MenuItem value="offline">Offline</MenuItem>
                  <MenuItem value="busy">Busy</MenuItem>
                </Select>
              </FormControl>
              <TextField
                margin="dense"
                label="Tags (comma separated)"
                fullWidth
                variant="outlined"
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
              <Button variant="contained" onClick={() => setOpenDialog(false)}>Save</Button>
            </DialogActions>
          </Dialog>
        </Box>
      )}
      
      {tabIndex === 1 && (
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
            <Typography variant="h6">
              Service Accounts
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
            >
              Add Service Account
            </Button>
          </Box>
          
          <Typography variant="body2" sx={{ mb: 2 }}>
            Manage service accounts that can be used by agents for automated logins and authentication.
          </Typography>
          
          <Paper sx={{ p: 3 }}>
            <Typography>
              This tab will contain service account management functionality.
            </Typography>
          </Paper>
        </Box>
      )}
    </Box>
  );
}

export default AgentManagementSimple;