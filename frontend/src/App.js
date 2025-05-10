import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './context/AuthContext';
// Layout components
import Dashboard from './components/layout/Dashboard';
import ProtectedRoute from './components/auth/ProtectedRoute';

// Pages
import HomePage from './pages/HomePage';
import AgentsPage from './pages/AgentsPage';
import JobsPage from './pages/JobsPage';
import PackagesPage from './pages/PackagesPage';
import SchedulesPage from './pages/SchedulesPage';
import QueuesPage from './pages/QueuesPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import SubscriptionPage from './pages/SubscriptionPage';
import SubscriptionTiersPage from './pages/SubscriptionTiersPage';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline/>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Protected routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route path="packages" element={<PackagesPage />} />
            <Route path="schedules" element={<SchedulesPage />} />
            <Route path="queues" element={<QueuesPage />} />
            <Route path="subscription" element={<SubscriptionPage />} />
            <Route path="subscription/tiers" element={<SubscriptionTiersPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;