import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { 
  CssBaseline, 
  Box, 
  AppBar, 
  Toolbar, 
  Typography, 
  Container,
  Button,
  Avatar,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import { 
  AccountCircle as AccountIcon,
  AccountCircle,
  Settings as SettingsIcon,
  Settings,
  Logout as LogoutIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

// Import pages - using safe imports
import DataSandbox from './pages/DataSandbox';
import WorkflowExecutor from './pages/WorkflowExecutor';
import SOPManager from './pages/SOPManager';

// Custodian Bank theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1565c0', // Professional blue for custodian banking
    },
    secondary: {
      main: '#37474f', // Dark gray
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
});

// Simple user type
interface User {
  id: number;
  email: string;
  full_name: string;
  role: string;
  department?: string;
}

// Mock user for development
const mockUser: User = {
  id: 1,
  email: 'admin@otomeshon.com',
  full_name: 'Custodian Administrator',
  role: 'Admin',
  department: 'Custody Operations'
};

// User Menu Component
const UserMenu: React.FC<{ user: User; onLogout: () => void }> = ({ user, onLogout }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    onLogout();
    handleMenuClose();
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <>
      <IconButton onClick={handleMenuOpen} sx={{ p: 0 }}>
        <Avatar sx={{ bgcolor: '#1565c0', width: 40, height: 40 }}>
          {getInitials(user.full_name)}
        </Avatar>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        onClick={handleMenuClose}
        sx={{ mt: 1.5 }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="subtitle1" fontWeight="medium">
            {user.full_name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {user.email}
          </Typography>
          <Typography variant="caption" color="primary.main" fontWeight="medium">
            {user.role} - {user.department}
          </Typography>
        </Box>
        <Divider />
        <MenuItem onClick={handleMenuClose}>
          <AccountIcon sx={{ mr: 1 }} fontSize="small" />
          Profile
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <SettingsIcon sx={{ mr: 1 }} fontSize="small" />
          Settings
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>
          <LogoutIcon sx={{ mr: 1 }} fontSize="small" />
          Sign Out
        </MenuItem>
      </Menu>
    </>
  );
};

// Simple Login Component
const LoginPage: React.FC<{ onLogin: (user: User) => void }> = ({ onLogin }) => {
  const [email, setEmail] = useState('admin@otomeshon.com');
  const [password, setPassword] = useState('admin123');

  const handleLogin = () => {
    // Simple validation for demo
    if (email && password) {
      onLogin(mockUser);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1565c0 0%, #37474f 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Box
          sx={{
            bgcolor: 'background.paper',
            p: 4,
            borderRadius: 2,
            boxShadow: 3,
            textAlign: 'center',
          }}
        >
          <SecurityIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Otomeshon Custodian Portal
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            Banking Operations Automation Platform
          </Typography>
          
          <Box sx={{ mt: 3, mb: 3 }}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                marginBottom: '16px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px',
              }}
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '12px',
                marginBottom: '16px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '16px',
              }}
            />
          </Box>

          <Button
            variant="contained"
            fullWidth
            size="large"
            onClick={handleLogin}
            sx={{ mb: 2 }}
          >
            Sign In
          </Button>

          <Typography variant="caption" color="text.secondary">
            Demo: admin@otomeshon.com / admin123
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

// Dashboard Component
const Dashboard: React.FC<{ user: User }> = ({ user }) => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Custodian Banking Dashboard
      </Typography>
      <Typography variant="body1" paragraph>
        Welcome to the Otomeshon Custodian Portal, {user.full_name}!
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Role: {user.role} | Department: {user.department}
      </Typography>
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Platform Modules
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ cursor: 'pointer' }} onClick={() => window.location.href = '/workflows'}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <AccountCircle sx={{ fontSize: 40, color: 'primary.main' }} />
                  <Typography variant="h6">Workflow Executor</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Configure and execute custodian banking workflows with rules engine and AI agents
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ cursor: 'pointer' }} onClick={() => window.location.href = '/sop-manager'}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <SecurityIcon sx={{ fontSize: 40, color: 'warning.main' }} />
                  <Typography variant="h6">SOP Manager</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Manage and execute standard operating procedures for custodian banking operations
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card sx={{ cursor: 'pointer' }} onClick={() => window.location.href = '/data-sandbox'}>
              <CardContent>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Settings sx={{ fontSize: 40, color: 'secondary.main' }} />
                  <Typography variant="h6">Data Sandbox</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  Advanced data analysis and visualization for operational insights
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
      
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6" gutterBottom>
          Core Custodian Services
        </Typography>
        <ul>
          <li>Securities Safekeeping & Custody</li>
          <li>Trade Settlement & Clearing</li>
          <li>Corporate Actions Processing</li>
          <li>Fund Administration</li>
          <li>Regulatory Reporting</li>
          <li>Risk Management</li>
        </ul>
      </Box>
    </Box>
  );
};

// Main App Layout
const AppLayout: React.FC<{ 
  children: React.ReactNode; 
  user: User | null; 
  onLogout: () => void;
}> = ({ children, user, onLogout }) => {
  if (!user) {
    return <>{children}</>;
  }

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🏦 Otomeshon Custodian Portal
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography variant="body2" color="inherit">
              Welcome, {user.full_name}
            </Typography>
            <UserMenu user={user} onLogout={onLogout} />
          </Box>
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
        {children}
      </Container>
    </Box>
  );
};

// Main App Component
const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const savedUser = localStorage.getItem('otomeshon_user');
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (error) {
        console.error('Failed to parse saved user:', error);
        localStorage.removeItem('otomeshon_user');
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (newUser: User) => {
    setUser(newUser);
    localStorage.setItem('otomeshon_user', JSON.stringify(newUser));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('otomeshon_user');
  };

  if (loading) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
          }}
        >
          <Typography>Loading...</Typography>
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppLayout user={user} onLogout={handleLogout}>
          <Routes>
            <Route 
              path="/login" 
              element={
                user ? <Navigate to="/" replace /> : <LoginPage onLogin={handleLogin} />
              } 
            />
            
            <Route 
              path="/" 
              element={
                user ? <Dashboard user={user} /> : <Navigate to="/login" replace />
              } 
            />
            
            <Route 
              path="/data-sandbox" 
              element={
                user ? <DataSandbox /> : <Navigate to="/login" replace />
              } 
            />
            
            <Route 
              path="/workflows" 
              element={
                user ? <WorkflowExecutor /> : <Navigate to="/login" replace />
              } 
            />
            
            <Route 
              path="/sop-manager" 
              element={
                user ? <SOPManager /> : <Navigate to="/login" replace />
              } 
            />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </Router>
    </ThemeProvider>
  );
};

export default App;