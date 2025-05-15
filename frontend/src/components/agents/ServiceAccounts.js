// frontend/src/components/agents/ServiceAccounts.js
import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Paper, Button, CircularProgress,
  Chip, IconButton, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, TextField,
  Dialog, DialogActions, DialogContent, DialogTitle,
  FormControl, InputLabel, Select, MenuItem, Alert
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { 
  getServiceAccounts, 
  createServiceAccount, 
  updateServiceAccount, 
  deleteServiceAccount 
} from '../../services/serviceAccountService';

function ServiceAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    display_name: '',
    description: '',
    password: '',
    account_type: 'robot'
  });
  const [actionLoading, setActionLoading] = useState(false);
  const [formError, setFormError] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [accountToDelete, setAccountToDelete] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    setLoading(true);
    setError(null);
    try {
      const accountsData = await getServiceAccounts();
      setAccounts(accountsData);
    } catch (err) {
      console.error('Failed to fetch service accounts:', err);
      setError('Failed to load service accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredAccounts = accounts?.filter(account =>
    !searchTerm || 
    account.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (account.description && account.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleOpenDialog = (account = null) => {
    if (account) {
      // Editing mode
      setIsEditing(true);
      setFormData({
        username: account.username,
        display_name: account.display_name,
        description: account.description || '',
        password: '',  // Password field is empty when editing
        account_type: account.account_type
      });
    } else {
      // Create mode
      setIsEditing(false);
      setFormData({
        username: '',
        display_name: '',
        description: '',
        password: '',
        account_type: 'robot'
      });
    }
    setFormError('');
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    // Validate form
    if (!formData.username) {
      setFormError('Username is required');
      return;
    }
    if (!formData.display_name) {
      setFormError('Display name is required');
      return;
    }
    if (!isEditing && !formData.password) {
      // Password is optional when editing, but required when creating
      setFormError('Password is required for new accounts');
      return;
    }

    setActionLoading(true);
    setFormError('');
    try {
      if (isEditing) {
        // Update existing account
        const accountToUpdate = accounts.find(a => a.username === formData.username);
        if (!accountToUpdate) {
          setFormError('Account not found');
          setActionLoading(false);
          return;
        }
        
        const updatedAccount = await updateServiceAccount(
          accountToUpdate.account_id, 
          // Only include password if provided
          formData.password ? formData : { ...formData, password: undefined }
        );
        
        // Update accounts list
        setAccounts(prev => 
          prev.map(acc => 
            acc.account_id === accountToUpdate.account_id ? updatedAccount : acc
          )
        );
      } else {
        // Create new account
        const newAccount = await createServiceAccount(formData);
        setAccounts(prev => [...prev, newAccount]);
      }
      
      setDialogOpen(false);
    } catch (err) {
      console.error('Failed to save service account:', err);
      setFormError(err.message || 'Failed to save account. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteClick = (account) => {
    setAccountToDelete(account);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!accountToDelete) return;
    
    setActionLoading(true);
    try {
      await deleteServiceAccount(accountToDelete.account_id);
      
      // Remove account from list
      setAccounts(prev => 
        prev.filter(acc => acc.account_id !== accountToDelete.account_id)
      );
      setDeleteDialogOpen(false);
    } catch (err) {
      console.error('Failed to delete service account:', err);
      setError(err.message || 'Failed to delete account. Please try again.');
    } finally {
      setActionLoading(false);
      setAccountToDelete(null);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5" component="h2">
          Service Accounts
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={fetchAccounts}
            sx={{ mr: 2 }}
            disabled={loading || actionLoading}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            disabled={actionLoading}
          >
            Add Account
          </Button>
        </Box>
      </Box>

      <TextField
        fullWidth
        label="Search accounts"
        variant="outlined"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : filteredAccounts.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography>
            No service accounts found. Add a new account to get started.
          </Typography>
        </Paper>
      ) : (
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
                      onClick={() => handleOpenDialog(account)}
                      disabled={actionLoading}
                      title="Edit Account"
                      size="small"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      onClick={() => handleDeleteClick(account)}
                      disabled={actionLoading}
                      title="Delete Account"
                      color="error"
                      size="small"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Account Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Edit Service Account' : 'Add Service Account'}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2, mt: 1 }}>
              {formError}
            </Alert>
          )}
          
          <TextField
            autoFocus
            margin="normal"
            name="username"
            label="Username"
            fullWidth
            value={formData.username}
            onChange={handleInputChange}
            required
            disabled={isEditing} // Can't change username when editing
          />
          
          <TextField
            margin="normal"
            name="display_name"
            label="Display Name"
            fullWidth
            value={formData.display_name}
            onChange={handleInputChange}
            required
          />
          
          <TextField
            margin="normal"
            name="password"
            label={isEditing ? "New Password (leave blank to keep current)" : "Password"}
            type="password"
            fullWidth
            value={formData.password}
            onChange={handleInputChange}
            required={!isEditing}
          />
          
          <TextField
            margin="normal"
            name="description"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={formData.description}
            onChange={handleInputChange}
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Account Type</InputLabel>
            <Select
              name="account_type"
              value={formData.account_type}
              label="Account Type"
              onChange={handleInputChange}
            >
              <MenuItem value="robot">Robot</MenuItem>
              <MenuItem value="service">Service</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : isEditing ? 'Save Changes' : 'Create Account'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => !actionLoading && setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Service Account</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the service account{' '}
            <strong>{accountToDelete?.display_name}</strong>?
            This action cannot be undone.
          </Typography>
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            Warning: Deleting a service account that is in use by agents will prevent those agents from functioning properly.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={actionLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmDelete} 
            variant="contained" 
            color="error"
            disabled={actionLoading}
          >
            {actionLoading ? <CircularProgress size={24} /> : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ServiceAccounts;