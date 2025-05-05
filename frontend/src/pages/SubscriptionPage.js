import React, { useState, useEffect } from 'react';
import { 
  Alert, 
  Box, 
  Button, 
  Card, 
  CardContent, 
  CircularProgress, 
  Container, 
  Divider,
  Grid, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Paper, 
  Typography 
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import PeopleIcon from '@mui/icons-material/People';
import ComputerIcon from '@mui/icons-material/Computer';
import WorkIcon from '@mui/icons-material/Work';
import ScheduleIcon from '@mui/icons-material/Schedule';
import QueueIcon from '@mui/icons-material/Queue';
import StorageIcon from '@mui/icons-material/Storage';
import PaymentIcon from '@mui/icons-material/Payment';
import ReceiptIcon from '@mui/icons-material/Receipt';
import UpgradeIcon from '@mui/icons-material/Upgrade';
import axios from 'axios';

function SubscriptionPage() {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const location = useLocation();
  const navigate = useNavigate();
  
  // Check for success message passed through navigation
  const [message, setMessage] = useState(location.state?.message || '');
  
  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const response = await axios.get('/api/v1/subscriptions/current');
        setSubscription(response.data);
      } catch (err) {
        setError('Failed to load subscription information');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSubscription();
  }, []);
  
  const handleUpgradeClick = () => {
    navigate('/subscription/tiers');
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {message && (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}
      
      <Typography variant="h4" gutterBottom>
        Subscription
      </Typography>
      
      {error ? (
        <Paper sx={{ p: 3 }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {/* Subscription Summary */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h5">
                    {subscription.tier_display_name} Plan
                  </Typography>
                </Box>
                
                <Typography variant="body1" color="text.secondary" paragraph>
                  Status: <strong>{subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}</strong>
                </Typography>
                
                {subscription.is_trial && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Trial ends on {new Date(subscription.trial_end_date).toLocaleDateString()}
                  </Alert>
                )}
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body1">Billing Cycle:</Typography>
                  <Typography variant="body1">
                    <strong>
                      {subscription.billing_cycle.charAt(0).toUpperCase() + subscription.billing_cycle.slice(1)}
                    </strong>
                  </Typography>
                </Box>
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body1">Price:</Typography>
                  <Typography variant="body1">
                    <strong>${subscription.price}</strong>/{subscription.billing_cycle === 'monthly' ? 'month' : 'year'}
                  </Typography>
                </Box>
                
                {subscription.next_billing_date && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                    <Typography variant="body1">Next Billing Date:</Typography>
                    <Typography variant="body1">
                      <strong>{new Date(subscription.next_billing_date).toLocaleDateString()}</strong>
                    </Typography>
                  </Box>
                )}
                
                <Divider sx={{ my: 2 }} />
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    onClick={handleUpgradeClick}
                    startIcon={<UpgradeIcon />}
                  >
                    View Plans & Upgrade
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Resource Limits */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Resources & Limits
                </Typography>
                
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <ComputerIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Agents" 
                      secondary={`${subscription.max_agents} agents allowed`} 
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <WorkIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Concurrent Jobs" 
                      secondary={`${subscription.max_concurrent_jobs} concurrent jobs allowed`} 
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <ScheduleIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Schedules" 
                      secondary={`${subscription.max_schedules} schedules allowed`} 
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      <QueueIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary="Queues" 
                      secondary={`${subscription.max_queues} queues allowed`} 
                    />
                  </ListItem>
                </List>
                
                <Divider sx={{ my: 2 }} />
                
                <Typography variant="h6" gutterBottom>
                  Features
                </Typography>
                
                <List>
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.api_access ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="API Access" />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.schedules ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="Schedules" />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.queues ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="Queues" />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.analytics ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="Analytics" />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.custom_branding ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="Custom Branding" />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon>
                      {subscription.features.sla_support ? 
                        <CheckCircleIcon color="success" /> : 
                        <CheckCircleIcon color="disabled" />
                      }
                    </ListItemIcon>
                    <ListItemText primary="SLA Support" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Billing History */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Billing History
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ py: 2 }}>
                  Billing history not available in the current version.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Container>
  );
}

export default SubscriptionPage;