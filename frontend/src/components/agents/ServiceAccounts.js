import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Grid,
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  Tooltip
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import { 
  getServiceAccounts, 
  createServiceAccount, 
  updateServiceAccount,
  deleteServiceAccount
} from '../../services/serviceAccountService';

function ServiceAccounts() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [currentAccount, setCurrentAccount] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [accountFormData, setAccountFormData] = useState({
    username: '',
    display_name: '',
    description: '',
    password: '',
    account_type: 'robot'
  });
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [accountToDelete, setAccountToDelete] = useState(null);

  const queryClient = useQueryClient();

  // Fetch service accounts
  const { data: accounts, isLoading, error, refetch } = useQuery(
    'serviceAccounts', 
    getServiceAccounts
  );

  // Create mutation
  const createMutation = useMutation(createServiceAccount, {
    onSuccess: () => {
      queryClient.invalidateQueries('serviceAccounts');
      handleCloseDialog();
    }
  });

  // Update mutation
  const updateMutation = useMutation(
    (data) => updateServiceAccount(data.id, data.accountData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('serviceAccounts');
        handleCloseDialog();
      }
    }
  );

  // Delete mutation
  const deleteMutation = useMutation(deleteServiceAccount, {
    onSuccess: () => {
      queryClient.invalidateQueries('serviceAccounts');
      setDeleteDialogOpen(false);
    }
  });

  const handleOpenDialog = (account = null) => {
    if (account) {
      setEditMode(true);
      setCurrentAccount(account);
      setAccountFormData({
        username: account.username,
        display_name: account.display_name,
        description: account.description || '',
        password: '',  // Password not pre-filled for security
        account_type: account.account_type || 'robot'
      });
    } else {
      setEditMode(false);
      setCurrentAccount(null);
      setAccountFormData({
        username: '',
        display_name: '',
        description: '',
        password: '',
        account_type: 'robot'
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditMode(false);
    setCurrentAccount(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setAccountFormData((prev) => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = () => {
    if (editMode) {
      // Only include password if it was changed
      const updateData = { ...accountFormData };
      if (!updateData.password) {
        delete updateData.password;
      }
      updateMutation.mutate({ 
        id: currentAccount.account_id, 
        accountData: updateData 
      });
    } else {
      createMutation.mutate(accountFormData);
    }
  };

  const handleDeleteClick = (account) => {
    setAccountToDelete(account);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (accountToDelete) {
      deleteMutation.mutate(accountToDelete.account_id);
    }
  };

  // Filter accounts based on search term
  const filteredAccounts = accounts?.filter(account => 
    account.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (account.description && account.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

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

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3 }}>
          <Typography color="error">Error loading service accounts: {error.message}</Typography>
        </Paper>
      ) : filteredAccounts?.length ? (
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
                <TableRow key={account.account_id}>
                  <TableCell>{account.username}</TableCell>
                  <TableCell>{account.display_name}</TableCell>
                  <TableCell>{account.account_type}</TableCell>
                  <TableCell>{account.description}</TableCell>
                  <TableCell>
                    <Chip 
                      label={account.status} 
                      color={account.status === 'active' ? 'success' : 'error'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit Account">
                      <IconButton onClick={() => handleOpenDialog(account)} size="small">
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Account">
                      <IconButton onClick={() => handleDeleteClick(account)} size="small" color="error">
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
          <Typography>No service accounts found. Add a new account to get started.</Typography>
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
          {editMode ? 'Edit Service Account' : 'Add Service Account'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Username"
                name="username"
                value={accountFormData.username}
                onChange={handleInputChange}
                disabled={editMode}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Display Name"
                name="display_name"
                value={accountFormData.display_name}
                onChange={handleInputChange}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Password"
                name="password"
                type="password"
                value={accountFormData.password}
                onChange={handleInputChange}
                helperText={editMode ? "Leave blank to keep current password" : ""}
                required={!editMode}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                name="description"
                value={accountFormData.description}
                onChange={handleInputChange}
                multiline
                rows={3}
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
              editMode ? 'Save Changes' : 'Create Account'
            )}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the service account 
            <strong>{accountToDelete?.display_name || accountToDelete?.username}</strong>?
            {accountToDelete?.account_type === 'robot' && (
              <>
                <br /><br />
                <span style={{ color: 'red' }}>
                  Warning: This will break any agent auto-login configurations using this account.
                </span>
              </>
            )}
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
    </Box>
  );
}

export default ServiceAccounts;