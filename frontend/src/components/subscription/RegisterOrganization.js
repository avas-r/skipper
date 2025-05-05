import React, { useState } from 'react';
import { 
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const tiers = [
  {
    name: 'free',
    displayName: 'Free',
    description: 'Limited resources for evaluation purposes',
    limits: '2 agents, 5 concurrent jobs',
    price: 'Free'
  },
  {
    name: 'standard',
    displayName: 'Standard',
    description: 'For small businesses with moderate resource needs',
    limits: '10 agents, 25 concurrent jobs',
    price: '$49.99/month'
  },
  {
    name: 'professional',
    displayName: 'Professional',
    description: 'For mid-sized companies with advanced automation needs',
    limits: '50 agents, 100 concurrent jobs',
    price: '$199.99/month'
  },
  {
    name: 'enterprise',
    displayName: 'Enterprise',
    description: 'For large organizations with high-volume automation requirements',
    limits: '250 agents, 500 concurrent jobs',
    price: '$999.99/month'
  }
];

const RegisterOrganization = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    organization_name: '',
    full_name: '',
    email: '',
    password: '',
    password_confirm: '',
    subscription_tier: 'free'
  });
  
  const [formErrors, setFormErrors] = useState({
    organization_name: '',
    full_name: '',
    email: '',
    password: '',
    password_confirm: ''
  });
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Clear error when field is edited
    if (formErrors[name]) {
      setFormErrors({
        ...formErrors,
        [name]: ''
      });
    }
  };
  
  const validateForm = () => {
    const errors = {};
    let isValid = true;
    
    if (!formData.organization_name.trim()) {
      errors.organization_name = 'Organization name is required';
      isValid = false;
    }
    
    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
      isValid = false;
    }
    
    if (!formData.email.trim()) {
      errors.email = 'Email is required';
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
      isValid = false;
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
      isValid = false;
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
      isValid = false;
    }
    
    if (formData.password !== formData.password_confirm) {
      errors.password_confirm = 'Passwords do not match';
      isValid = false;
    }
    
    setFormErrors(errors);
    return isValid;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Remove password_confirm from the data sent to the API
      const { password_confirm, ...registrationData } = formData;
      
      const response = await axios.post('/api/v1/subscriptions/register', registrationData);
      
      // Registration successful, redirect to login
      navigate('/login', { 
        state: { 
          message: 'Registration successful! Please log in with your new account.',
          email: formData.email
        } 
      });
    } catch (err) {
      setError(
        err.response?.data?.detail || 
        'Registration failed. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Get Started with Skipper
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Create your organization and start automating today
        </Typography>
      </Box>
      
      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardHeader title="Organization Details" />
              <Divider />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Organization Name"
                      name="organization_name"
                      value={formData.organization_name}
                      onChange={handleChange}
                      error={!!formErrors.organization_name}
                      helperText={formErrors.organization_name}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Your Full Name"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleChange}
                      error={!!formErrors.full_name}
                      helperText={formErrors.full_name}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Email Address"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleChange}
                      error={!!formErrors.email}
                      helperText={formErrors.email}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      error={!!formErrors.password}
                      helperText={formErrors.password || 'At least 8 characters'}
                      required
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Confirm Password"
                      name="password_confirm"
                      type="password"
                      value={formData.password_confirm}
                      onChange={handleChange}
                      error={!!formErrors.password_confirm}
                      helperText={formErrors.password_confirm}
                      required
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardHeader title="Subscription Plan" />
              <Divider />
              <CardContent>
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel id="subscription-tier-label">Subscription Tier</InputLabel>
                  <Select
                    labelId="subscription-tier-label"
                    name="subscription_tier"
                    value={formData.subscription_tier}
                    onChange={handleChange}
                    label="Subscription Tier"
                  >
                    {tiers.map((tier) => (
                      <MenuItem key={tier.name} value={tier.name}>
                        {tier.displayName} - {tier.price}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    Select a subscription tier based on your needs
                  </FormHelperText>
                </FormControl>
                
                {/* Show selected tier details */}
                {tiers.find(t => t.name === formData.subscription_tier) && (
                  <Box sx={{ p: 2, border: '1px solid #e0e0e0', borderRadius: 1, mb: 2 }}>
                    <Typography variant="h6">
                      {tiers.find(t => t.name === formData.subscription_tier).displayName}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {tiers.find(t => t.name === formData.subscription_tier).description}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Includes:</strong> {tiers.find(t => t.name === formData.subscription_tier).limits}
                    </Typography>
                    {formData.subscription_tier !== 'free' && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Includes 14-day free trial
                      </Typography>
                    )}
                  </Box>
                )}
                
                {error && (
                  <Typography color="error" sx={{ mt: 2 }}>
                    {error}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button 
                variant="contained" 
                color="primary" 
                size="large" 
                type="submit"
                disabled={loading}
                sx={{ minWidth: 200 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Create Organization'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Container>
  );
};

export default RegisterOrganization;