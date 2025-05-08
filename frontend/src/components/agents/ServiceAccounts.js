import React, { useState, useEffect } from 'react';
import { 
  Box, Typography, Paper, Button, 
  CircularProgress, Chip, IconButton, 
  Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow,
  TextField
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { getServiceAccounts } from '../../services/serviceAccountService';

function ServiceAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  useEffect(() => {
    fetchAccounts();
  }, []);
  
  const fetchAccounts = async () => {
    setLoading(true);
    setError('');
    try {
      const accountsData = await getServiceAccounts();
      setAccounts(accountsData);
    } catch (err) {
      console.error('Failed to fetch service accounts:', err);
      setError('Error loading service accounts: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };
  
  const filteredAccounts = accounts?.filter(account => 
    account.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.display_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
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
            onClick={fetchAccounts}
            sx={{ mr: 1 }}
          >
            Refresh
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
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
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3 }}>
          <Typography color="error">{error}</Typography>
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
                    <IconButton size="small">
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" color="error">
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
          <Typography>No service accounts found. Add a new account to get started.</Typography>
        </Paper>
      )}
    </Box>
  );
}

export default ServiceAccounts;