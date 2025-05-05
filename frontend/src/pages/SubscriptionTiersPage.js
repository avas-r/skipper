import React from 'react';
import { Box } from '@mui/material';
import SubscriptionTiers from '../components/subscription/SubscriptionTiers';

function SubscriptionTiersPage() {
  return (
    <Box sx={{ p: 3 }}>
      <SubscriptionTiers />
    </Box>
  );
}

export default SubscriptionTiersPage;