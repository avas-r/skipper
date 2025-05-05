import React, { useState } from 'react';
import { useNavigate, Link as RouterLink, useLocation } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  Grid,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [credentials, setCredentials] = useState({
    username: location.state?.email || '',
    password: '',
  });
  const [error, setError] = useState('');
  const [message, setMessage] = useState(location.state?.message || '');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setCredentials((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Placeholder for login logic
      // This would typically call an API service 
      setTimeout(() => {
        // Mock successful login
        localStorage.setItem('token', 'mock-token');
        setLoading(false);
        navigate('/');
      }, 1000);
      
    } catch (error) {
      setError(error.message || 'Login failed');
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            padding: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography component="h1" variant="h4" sx={{ mb: 3 }}>
            Skipper
          </Typography>
          <Typography component="h2" variant="h5" sx={{ mb: 3 }}>
            Sign In
          </Typography>
          
          {message && (
            <Alert severity="success" sx={{ width: '100%', mb: 2 }} onClose={() => setMessage('')}>
              {message}
            </Alert>
          )}
          
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Username"
              name="username"
              autoComplete="username"
              autoFocus
              value={credentials.username}
              onChange={handleChange}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Password"
              type="password"
              id="password"
              autoComplete="current-password"
              value={credentials.password}
              onChange={handleChange}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Sign In'}
            </Button>
            
            <Grid container justifyContent="center">
              <Grid item>
                <Link 
                  component={RouterLink} 
                  to="/register"
                  variant="body2"
                >
                  Don't have an account? Register your organization
                </Link>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default LoginPage;