// frontend/src/App.js
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
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
import UnauthorizedPage from './pages/UnauthorizedPage';
import NotFoundPage from './pages/NotFoundPage';

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
          {/* Public routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          
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
            
            {/* Agents - requires admin role or agent:read permission */}
            <Route 
              path="agents" 
              element={
                <ProtectedRoute requiredRoles={['admin', 'Admin']} requiredPermissions={['agent:read']}>
                  <AgentsPage />
                </ProtectedRoute>
              }
            />
            
            {/* Jobs - requires job:read permission */}
            <Route 
              path="jobs" 
              element={
                <ProtectedRoute requiredPermissions={['job:read']}>
                  <JobsPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Packages - requires package:read permission */}
            <Route 
              path="packages" 
              element={
                <ProtectedRoute requiredPermissions={['package:read']}>
                  <PackagesPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Schedules - requires schedule:read permission */}
            <Route 
              path="schedules" 
              element={
                <ProtectedRoute requiredPermissions={['schedule:read']}>
                  <SchedulesPage />
                </ProtectedRoute>
              } 
            />
            
            {/* Queues - requires queue:read permission */}
            <Route 
              path="queues" 
              element={
                <ProtectedRoute requiredPermissions={['queue:read']}>
                  <QueuesPage />
                </ProtectedRoute>
              } 
            />
          </Route>
          
          {/* Fallback routes */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;