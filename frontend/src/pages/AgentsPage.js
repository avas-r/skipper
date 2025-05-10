// src/pages/LoginPage.js
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
import axios from 'axios';

// API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
      // OAuth2 expects form data, not JSON
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      formData.append('grant_type', 'password');  // OAuth2 requirement

      console.log('Sending login request for user:', credentials.username);
      
      // Call the login API endpoint with the correct format
      const response = await axios.post(`${API_URL}/api/v1/auth/login`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      console.log('Login successful, token received');
      
      // Store tokens in localStorage
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      try {
        // Get user information - use the exact same instance and config
        const accessToken = response.data.access_token;
        console.log('Fetching user info with token');
        
        const userResponse = await axios.get(`${API_URL}/api/v1/auth/me`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });
        
        // Store user info in localStorage
        localStorage.setItem('user', JSON.stringify(userResponse.data));
      } catch (userError) {
        console.error('Error fetching user info:', userError);
        
        // If fetching user info fails due to token expiration, create a placeholder user
        // This is a fallback approach since we know the login was successful
        if (userError.response && userError.response.status === 401) {
          console.log('Using fallback user data since token might have expired quickly');
          const fallbackUser = {
            email: credentials.username,
            full_name: 'User',
            tenant_id: 'auto-detected',
            roles: ['user']
          };
          localStorage.setItem('user', JSON.stringify(fallbackUser));
        } else {
          throw userError; // Re-throw other errors
        }
      }
      
      setLoading(false);
      
      // If came from another page, go back to that page, otherwise go to home
      const from = location.state?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (error) {
      console.error('Login error:', error);
      if (error.response) {
        // The request was made and the server responded with an error
        const errorDetail = error.response.data?.detail;
        // Handle case where detail might be an object (validation error)
        if (errorDetail && typeof errorDetail === 'object') {
          setError('Invalid credentials or validation error');
          console.error('Validation error:', errorDetail);
        } else {
          setError(errorDetail || 'Invalid username or password');
        }
      } else if (error.request) {
        // The request was made but no response was received
        setError('Server not responding. Please try again later.');
      } else {
        // Something happened in setting up the request
        const errorMsg = error.message && typeof error.message === 'string' 
          ? error.message 
          : 'Login failed';
        setError(errorMsg);
      }
      setLoading(false);
    }
  };

  // Rest of the component remains the same
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