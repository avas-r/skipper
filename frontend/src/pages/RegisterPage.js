import React from 'react';
import { Box } from '@mui/material';
import RegisterOrganization from '../components/subscription/RegisterOrganization';

function RegisterPage() {
  return (
    <Box sx={{ p: 3 }}>
      <RegisterOrganization />
    </Box>
  );
}

export default RegisterPage;