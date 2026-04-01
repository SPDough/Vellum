'use client';

import React, { useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
  Chip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Storage as DataIcon,
  AccountTree as WorkflowIcon,
  SmartToy as AgentIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  AccountCircle,
  Logout,
  Notifications,
  Psychology as KnowledgeGraphIcon,
  TableChart as DataSandboxIcon,
  AccountBalance as AccountBalanceIcon,
  SwapHoriz as SwapHorizIcon,
  CompareArrows as CompareArrowsIcon,
  Rule as RuleIcon,
  DataObject as DataSourceIcon,
  AutoAwesome as SearchIcon,
  Description as SopIcon,
  Hub as IntegrationIcon,
  ArrowOutward,
} from '@mui/icons-material';

import { useAuthStore } from '@/store';

const drawerWidth = 300;

interface LayoutProps {
  children: React.ReactNode;
}

interface NavigationItem {
  label: string;
  path: string;
  icon: React.ReactElement;
}

interface NavigationSection {
  title: string;
  items: NavigationItem[];
}

const navigationSections: NavigationSection[] = [
  {
    title: 'Overview',
    items: [
      { label: 'Home', path: '/', icon: <DashboardIcon /> },
      { label: 'Dashboard', path: '/dashboard', icon: <AnalyticsIcon /> },
      { label: 'Search', path: '/search', icon: <SearchIcon /> },
    ],
  },
  {
    title: 'Workflows & Operations',
    items: [
      { label: 'Workflows', path: '/workflows', icon: <WorkflowIcon /> },
      { label: 'Workflow Builder', path: '/workflow-builder', icon: <WorkflowIcon /> },
      { label: 'Workflow Executor', path: '/workflow-executor', icon: <WorkflowIcon /> },
      { label: 'SOP Manager', path: '/sop-manager', icon: <SopIcon /> },
      { label: 'Rules Catalog', path: '/rules', icon: <RuleIcon /> },
    ],
  },
  {
    title: 'Data',
    items: [
      { label: 'Data Integration', path: '/data', icon: <DataIcon /> },
      { label: 'Data Sources', path: '/data-sources', icon: <DataSourceIcon /> },
      { label: 'Data Sandbox', path: '/data-sandbox', icon: <DataSandboxIcon /> },
      { label: 'Positions', path: '/positions', icon: <AccountBalanceIcon /> },
      { label: 'Transactions', path: '/transactions', icon: <SwapHorizIcon /> },
      { label: 'Reconciliation', path: '/reconciliation', icon: <CompareArrowsIcon /> },
    ],
  },
  {
    title: 'Knowledge & AI',
    items: [
      { label: 'Knowledge Graph', path: '/knowledge-graph', icon: <KnowledgeGraphIcon /> },
      { label: 'Custodian LangGraph', path: '/custodian-langgraph', icon: <IntegrationIcon /> },
      { label: 'AI Agents', path: '/agents', icon: <AgentIcon /> },
      { label: 'Analytics', path: '/analytics', icon: <AnalyticsIcon /> },
    ],
  },
  {
    title: 'System',
    items: [{ label: 'Settings', path: '/settings', icon: <SettingsIcon /> }],
  },
];

const recentSearches = ['workflow exceptions', 'sandbox export status', 'knowledge graph sync', 'reconciliation results'];

const NextLayout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleDrawerToggle = () => {
    setMobileOpen((prev) => !prev);
  };

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleProfileMenuClose();
    router.push('/login');
  };

  const isActivePath = (path: string) => {
    if (path === '/') return pathname === '/';
    return pathname?.startsWith(path) || false;
  };

  const drawer = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 42,
              height: 42,
              background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
              borderRadius: 2.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '1.2rem',
              boxShadow: '0 10px 20px rgba(139, 92, 246, 0.24)',
            }}
          >
            O
          </Box>
          <Box>
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
              Otomeshon
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Operational Intelligence
            </Typography>
          </Box>
        </Box>
      </Toolbar>

      <Divider />

      <Box sx={{ overflow: 'auto', flexGrow: 1, px: 2, py: 1.5 }}>
        {navigationSections.map((section) => (
          <Box key={section.title} sx={{ mb: 2.5 }}>
            <Typography
              variant="subtitle2"
              sx={{
                px: 1.5,
                py: 1,
                color: 'text.secondary',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                fontSize: '0.72rem',
              }}
            >
              {section.title}
            </Typography>
            <List dense sx={{ py: 0 }}>
              {section.items.map((item) => (
                <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    onClick={() => router.push(item.path)}
                    selected={isActivePath(item.path)}
                    sx={{
                      borderRadius: 2.5,
                      py: 1,
                      '&.Mui-selected': {
                        background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                        color: 'white',
                        boxShadow: '0 10px 20px rgba(139, 92, 246, 0.18)',
                        '&:hover': {
                          background: 'linear-gradient(135deg, #7c3aed 0%, #9333ea 100%)',
                        },
                        '& .MuiListItemIcon-root': { color: 'white' },
                      },
                      '&:hover': { backgroundColor: 'rgba(139, 92, 246, 0.08)' },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40, color: isActivePath(item.path) ? 'white' : 'text.secondary' }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{ fontWeight: isActivePath(item.path) ? 600 : 500, fontSize: '0.9rem' }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        ))}
      </Box>

      <Divider />

      <Box sx={{ px: 2, py: 2 }}>
        <Typography variant="subtitle2" sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary', fontWeight: 700, mb: 1 }}>
          <SearchIcon fontSize="small" /> Recent Searches
        </Typography>
        <List dense sx={{ py: 0 }}>
          {recentSearches.map((item) => (
            <ListItem key={item} disablePadding>
              <ListItemButton sx={{ borderRadius: 2 }} onClick={() => router.push(`/search?q=${encodeURIComponent(item)}`)}>
                <ListItemText
                  primary={item}
                  primaryTypographyProps={{ fontSize: '0.84rem', color: 'text.secondary', noWrap: true }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          backgroundColor: 'background.paper',
          borderBottom: 1,
          borderColor: 'divider',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.06)',
        }}
      >
        <Toolbar>
          <IconButton color="inherit" aria-label="open drawer" edge="start" onClick={handleDrawerToggle} sx={{ mr: 2, display: { md: 'none' }, color: 'text.primary' }}>
            <MenuIcon />
          </IconButton>

          <Box>
            <Typography variant="subtitle1" sx={{ color: 'text.primary', fontWeight: 700 }}>
              Platform Navigation
            </Typography>
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              Explore workflows, data systems, knowledge modules, and search
            </Typography>
          </Box>

          <Box sx={{ flexGrow: 1 }} />

          <Chip label="Search-first UX" size="small" variant="outlined" sx={{ mr: 1, display: { xs: 'none', md: 'inline-flex' } }} />

          <IconButton sx={{ color: 'text.primary', mr: 1 }}>
            <Notifications />
          </IconButton>

          <IconButton onClick={handleProfileMenuOpen} sx={{ color: 'text.primary' }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              {user?.name?.charAt(0) || 'U'}
            </Avatar>
          </IconButton>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleProfileMenuClose}>
              <ListItemIcon><AccountCircle fontSize="small" /></ListItemIcon>
              Profile
            </MenuItem>
            <MenuItem onClick={() => { handleProfileMenuClose(); router.push('/search'); }}>
              <ListItemIcon><ArrowOutward fontSize="small" /></ListItemIcon>
              Open Search
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon><Logout fontSize="small" /></ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: 'background.paper',
            borderRight: 1,
            borderColor: 'divider',
          },
        }}
      >
        {drawer}
      </Drawer>

      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundColor: 'background.paper',
            borderRight: 1,
            borderColor: 'divider',
          },
        }}
        open
      >
        {drawer}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, width: { md: `calc(100% - ${drawerWidth}px)` }, backgroundColor: 'background.default', minHeight: '100vh' }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

export default NextLayout;
