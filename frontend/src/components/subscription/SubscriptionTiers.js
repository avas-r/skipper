import React, { useState, useEffect } from 'react';
import {
  Box, 
  Button, 
  Card, 
  CardActions, 
  CardContent, 
  CardHeader,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent, 
  DialogContentText,
  DialogTitle,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography
} from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import CloseIcon from '@mui/icons-material/Close';
import StarIcon from '@mui/icons-material/Star';
import UpgradeIcon from '@mui/icons-material/Upgrade';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SubscriptionTiers = () => {
  const [tiers, setTiers] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);
  const [selectedTier, setSelectedTier] = useState(null);
  const [upgradeLoading, setUpgradeLoading] = useState(false);
  
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [tiersResponse, subscriptionResponse] = await Promise.all([
          axios.get('/api/v1/subscriptions/tiers/public'),
          axios.get('/api/v1/subscriptions/current')
        ]);
        
        setTiers(tiersResponse.data);
        setCurrentSubscription(subscriptionResponse.data);
      } catch (err) {
        setError('Failed to load subscription information');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleUpgradeClick = (tier) => {
    setSelectedTier(tier);
    setUpgradeDialogOpen(true);
  };
  
  const handleUpgradeConfirm = async () => {
    setUpgradeLoading(true);
    
    try {
      await axios.post('/api/v1/subscriptions/change-tier', null, {
        params: { tier_id: selectedTier.tier_id }
      });
      
      // Refresh subscription data
      const subscriptionResponse = await axios.get('/api/v1/subscriptions/current');
      setCurrentSubscription(subscriptionResponse.data);
      
      // Close dialog
      setUpgradeDialogOpen(false);
      
      // Show success notification or redirect to subscription details
      navigate('/subscription', { 
        state: { 
          message: `Successfully upgraded to ${selectedTier.display_name} tier!` 
        }
      });
      
    } catch (err) {
      const errorDetail = err.response?.data?.detail;
      // Handle case where detail might be an object (validation error)
      if (errorDetail && typeof errorDetail === 'object') {
        console.error('Validation error:', errorDetail);
        setError('Failed to upgrade subscription: validation error');
      } else {
        setError(
          errorDetail || 
          'Failed to upgrade subscription. Please try again.'
        );
      }
    } finally {
      setUpgradeLoading(false);
    }
  };
  
  const isTierActive = (tierName) => {
    return currentSubscription && currentSubscription.tier_name === tierName;
  };
  
  const isTierUpgrade = (tierName) => {
    if (!currentSubscription) return false;
    
    const tierLevels = {
      'free': 0,
      'standard': 1,
      'professional': 2,
      'enterprise': 3
    };
    
    return tierLevels[tierName] > tierLevels[currentSubscription.tier_name];
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
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Subscription Plans
        </Typography>
        <Typography variant="body1" paragraph>
          Choose the right plan for your automation needs. All paid plans come with a 14-day free trial.
        </Typography>
        
        {currentSubscription && (
          <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="subtitle1">
              Your current plan: <strong>{currentSubscription.tier_display_name}</strong>
            </Typography>
            {currentSubscription.is_trial && (
              <Typography variant="body2" color="primary">
                Trial ends on {new Date(currentSubscription.trial_end_date).toLocaleDateString()}
              </Typography>
            )}
          </Box>
        )}
      </Paper>
      
      <Grid container spacing={3}>
        {tiers.map((tier) => (
          <Grid item key={tier.tier_id} xs={12} md={6} lg={3}>
            <Card 
              sx={{ 
                height: '100%', 
                display: 'flex', 
                flexDirection: 'column',
                position: 'relative',
                ...(isTierActive(tier.name) && {
                  border: '2px solid',
                  borderColor: 'primary.main',
                })
              }}
            >
              {isTierActive(tier.name) && (
                <Box 
                  sx={{ 
                    position: 'absolute', 
                    top: 0, 
                    right: 0, 
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    px: 2,
                    py: 0.5,
                    borderBottomLeftRadius: 8
                  }}
                >
                  Current Plan
                </Box>
              )}
              
              <CardHeader
                title={tier.display_name}
                titleTypographyProps={{ align: 'center', variant: 'h5' }}
                sx={{ bgcolor: 'background.default' }}
                action={tier.name === 'enterprise' ? <StarIcon color="primary" /> : null}
              />
              
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'baseline', mb: 2 }}>
                  <Typography component="h2" variant="h3" color="text.primary">
                    ${tier.price_monthly}
                  </Typography>
                  <Typography variant="h6" color="text.secondary">
                    /mo
                  </Typography>
                </Box>
                <Divider sx={{ my: 2 }} />
                
                <List dense>
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={`${tier.max_agents} agents`} />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={`${tier.max_concurrent_jobs} concurrent jobs`} />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={`${tier.max_schedules} schedules`} />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={`${tier.max_queues} queues`} />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckIcon color="success" />
                    </ListItemIcon>
                    <ListItemText primary={`${tier.storage_gb} GB storage`} />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {tier.enable_analytics ? <CheckIcon color="success" /> : <CloseIcon color="disabled" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Analytics" 
                      primaryTypographyProps={{
                        color: tier.enable_analytics ? 'textPrimary' : 'textSecondary'
                      }}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {tier.enable_custom_branding ? <CheckIcon color="success" /> : <CloseIcon color="disabled" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="Custom Branding" 
                      primaryTypographyProps={{
                        color: tier.enable_custom_branding ? 'textPrimary' : 'textSecondary'
                      }}
                    />
                  </ListItem>
                  
                  <ListItem>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {tier.enable_sla_support ? <CheckIcon color="success" /> : <CloseIcon color="disabled" />}
                    </ListItemIcon>
                    <ListItemText 
                      primary="SLA Support" 
                      primaryTypographyProps={{
                        color: tier.enable_sla_support ? 'textPrimary' : 'textSecondary'
                      }}
                    />
                  </ListItem>
                </List>
              </CardContent>
              
              <CardActions>
                {isTierActive(tier.name) ? (
                  <Button 
                    fullWidth 
                    variant="outlined" 
                    disabled
                  >
                    Current Plan
                  </Button>
                ) : isTierUpgrade(tier.name) ? (
                  <Button 
                    fullWidth 
                    variant="contained" 
                    color="primary"
                    startIcon={<UpgradeIcon />}
                    onClick={() => handleUpgradeClick(tier)}
                  >
                    Upgrade
                  </Button>
                ) : (
                  <Button 
                    fullWidth 
                    variant="outlined"
                    disabled={!isTierUpgrade(tier.name) && currentSubscription}
                  >
                    {currentSubscription ? 'Contact Support' : 'Select'}
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {/* Upgrade Confirmation Dialog */}
      <Dialog
        open={upgradeDialogOpen}
        onClose={() => setUpgradeDialogOpen(false)}
      >
        <DialogTitle>Confirm Subscription Upgrade</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {selectedTier && `Are you sure you want to upgrade to the ${selectedTier.display_name} plan?`}
          </DialogContentText>
          {selectedTier && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1">
                Price: ${selectedTier.price_monthly}/month
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Your subscription will be upgraded immediately. You will be charged the prorated amount for the remainder of your billing cycle.
              </Typography>
            </Box>
          )}
          {error && (
            <Typography color="error" sx={{ mt: 2 }}>
              {error}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleUpgradeConfirm} 
            color="primary" 
            variant="contained"
            disabled={upgradeLoading}
          >
            {upgradeLoading ? <CircularProgress size={24} /> : 'Confirm Upgrade'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default SubscriptionTiers;