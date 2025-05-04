import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Layout components
import Dashboard from './components/layout/Dashboard';

// Pages
import HomePage from './pages/HomePage';
import AgentsPage from './pages/AgentsPage';
import JobsPage from './pages/JobsPage';
import PackagesPage from './pages/PackagesPage';
import SchedulesPage from './pages/SchedulesPage';
import QueuesPage from './pages/QueuesPage';
import LoginPage from './pages/LoginPage';

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
      <CssBaseline />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route path="/" element={<Dashboard />}>
          <Route index element={<HomePage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="packages" element={<PackagesPage />} />
          <Route path="schedules" element={<SchedulesPage />} />
          <Route path="queues" element={<QueuesPage />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;