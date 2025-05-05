import React from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  Card, 
  CardContent, 
  CardActions,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import ComputerIcon        from '@mui/icons-material/Computer';
import WorkIcon            from '@mui/icons-material/Work';
import ScheduleIcon        from '@mui/icons-material/Schedule';
import ErrorIcon           from '@mui/icons-material/ErrorOutline';
import SuccessIcon         from '@mui/icons-material/CheckCircleOutline';
import PendingIcon         from '@mui/icons-material/HourglassEmpty';
import { Link } from 'react-router-dom';

function HomePage() {
  // Mock data for the dashboard
  const stats = {
    agents: {
      total: 12,
      online: 9,
      offline: 3
    },
    jobs: {
      total: 234,
      success: 189,
      failed: 15,
      running: 8,
      pending: 22
    },
    schedules: {
      total: 18,
      active: 12,
      paused: 6
    }
  };

  // Mock recent jobs
  const recentJobs = [
    { id: 1, name: 'Data Export', status: 'success', time: '2 minutes ago' },
    { id: 2, name: 'Customer Onboarding', status: 'running', time: '10 minutes ago' },
    { id: 3, name: 'Report Generation', status: 'failed', time: '1 hour ago' },
    { id: 4, name: 'System Backup', status: 'pending', time: 'Scheduled for 3:00 PM' },
    { id: 5, name: 'User Sync', status: 'success', time: '2 hours ago' },
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <HourglassEmpty color="info" />;
      case 'pending':
        return <PendingIcon color="warning" />;
      default:
        return null;
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ComputerIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Agents</Typography>
              </Box>
              <Typography variant="h3">{stats.agents.total}</Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.agents.online} online, {stats.agents.offline} offline
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={Link} to="/agents">View All</Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <WorkIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Jobs</Typography>
              </Box>
              <Typography variant="h3">{stats.jobs.total}</Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.jobs.success} successful, {stats.jobs.failed} failed, {stats.jobs.running} running
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={Link} to="/jobs">View All</Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ScheduleIcon sx={{ mr: 1 }} />
                <Typography variant="h6">Schedules</Typography>
              </Box>
              <Typography variant="h3">{stats.schedules.total}</Typography>
              <Typography variant="body2" color="text.secondary">
                {stats.schedules.active} active, {stats.schedules.paused} paused
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" component={Link} to="/schedules">View All</Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Jobs
            </Typography>
            <List>
              {recentJobs.map((job, index) => (
                <React.Fragment key={job.id}>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(job.status)}
                    </ListItemIcon>
                    <ListItemText 
                      primary={job.name}
                      secondary={job.time}
                    />
                  </ListItem>
                  {index < recentJobs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button component={Link} to="/jobs">
                View All Jobs
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="contained" 
                  component={Link} 
                  to="/jobs/create"
                  fullWidth
                >
                  Create Job
                </Button>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  component={Link} 
                  to="/schedules/create"
                  fullWidth
                >
                  Create Schedule
                </Button>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  component={Link} 
                  to="/packages/upload"
                  fullWidth
                >
                  Upload Package
                </Button>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Button 
                  variant="outlined" 
                  component={Link} 
                  to="/agents/register"
                  fullWidth
                >
                  Register Agent
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default HomePage;