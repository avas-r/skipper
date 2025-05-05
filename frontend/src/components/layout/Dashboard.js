import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { 
  AppBar, Box, Toolbar, Typography, Drawer, List, ListItem, 
  ListItemIcon, ListItemText, Divider, IconButton
} from '@mui/material';
import MenuIcon      from '@mui/icons-material/Menu';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ComputerIcon  from '@mui/icons-material/Computer';
import WorkIcon      from '@mui/icons-material/Work';
import PackageIcon   from '@mui/icons-material/Inventory';
import ScheduleIcon  from '@mui/icons-material/Schedule';
import QueueIcon     from '@mui/icons-material/Queue';
import PaymentIcon   from '@mui/icons-material/Payment';
import LogoutIcon    from '@mui/icons-material/Logout';

const drawerWidth = 240;

export default function Dashboard() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleNavigation = (path) => {
    navigate(path);
    setMobileOpen(false);
  };

  const handleLogout = () => {
    // Handle logout logic here
    navigate('/login');
  };

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Skipper
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        <ListItem button onClick={() => handleNavigation('/')}>
          <ListItemIcon><DashboardIcon /></ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/agents')}>
          <ListItemIcon><ComputerIcon /></ListItemIcon>
          <ListItemText primary="Agents" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/jobs')}>
          <ListItemIcon><WorkIcon /></ListItemIcon>
          <ListItemText primary="Jobs" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/packages')}>
          <ListItemIcon><PackageIcon /></ListItemIcon>
          <ListItemText primary="Packages" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/schedules')}>
          <ListItemIcon><ScheduleIcon /></ListItemIcon>
          <ListItemText primary="Schedules" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/queues')}>
          <ListItemIcon><QueueIcon /></ListItemIcon>
          <ListItemText primary="Queues" />
        </ListItem>
        <ListItem button onClick={() => handleNavigation('/subscription')}>
          <ListItemIcon><PaymentIcon /></ListItemIcon>
          <ListItemText primary="Subscription" />
        </ListItem>
      </List>
      <Divider />
      <List>
        <ListItem button onClick={handleLogout}>
          <ListItemIcon><LogoutIcon /></ListItemIcon>
          <ListItemText primary="Logout" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            Skipper Automation Platform
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}