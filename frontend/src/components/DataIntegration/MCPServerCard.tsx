import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Chip,
  Avatar,
  IconButton,
  LinearProgress,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  CloudDone as CloudDoneIcon,
  CloudOff as CloudOffIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Visibility as VisibilityIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

import { MCPServer, ConnectionStatus, DataProviderType } from '@/types/data';
import { mcpServerService } from '@/services/mcpServerService';

interface MCPServerCardProps {
  server: MCPServer;
  onSettings?: (server: MCPServer) => void;
  onView?: (server: MCPServer) => void;
  onRefresh?: (server: MCPServer) => void;
}

const MCPServerCard: React.FC<MCPServerCardProps> = ({
  server,
  onSettings,
  onView,
  onRefresh,
}) => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [isTestingConnection, setIsTestingConnection] = React.useState(false);
  const menuOpen = Boolean(anchorEl);

  const handleTestConnection = async () => {
    setIsTestingConnection(true);
    try {
      await mcpServerService.testServer(server.id);
      // Could show success message
      if (onRefresh) onRefresh(server);
    } catch (error) {
      console.error('Connection test failed:', error);
      // Could show error message
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleToggleEnabled = async () => {
    try {
      if (server.enabled) {
        await mcpServerService.disableServer(server.id);
      } else {
        await mcpServerService.enableServer(server.id);
      }
      if (onRefresh) onRefresh(server);
    } catch (error) {
      console.error('Failed to toggle server:', error);
    }
  };

  const getStatusIcon = () => {
    switch (server.status) {
      case ConnectionStatus.CONNECTED:
        return <CloudDoneIcon sx={{ color: 'success.main' }} />;
      case ConnectionStatus.ERROR:
        return <CloudOffIcon sx={{ color: 'error.main' }} />;
      case ConnectionStatus.CONNECTING:
        return <WarningIcon sx={{ color: 'warning.main' }} />;
      default:
        return <CloudOffIcon sx={{ color: 'grey.500' }} />;
    }
  };

  const getStatusColor = () => {
    switch (server.status) {
      case ConnectionStatus.CONNECTED: return 'success';
      case ConnectionStatus.ERROR: return 'error';
      case ConnectionStatus.CONNECTING: return 'warning';
      case ConnectionStatus.MAINTENANCE: return 'info';
      default: return 'default';
    }
  };

  const getProviderIcon = () => {
    switch (server.type) {
      case DataProviderType.CUSTODIAN:
        return '🏦';
      case DataProviderType.MARKET_DATA:
        return '📈';
      case DataProviderType.PRICING:
        return '💰';
      default:
        return '🔗';
    }
  };

  const formatLastConnected = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <Card 
      sx={{ 
        borderRadius: 3,
        border: server.status === ConnectionStatus.CONNECTED ? 2 : 1,
        borderColor: server.status === ConnectionStatus.CONNECTED ? 'success.main' : 'divider',
        '&:hover': {
          boxShadow: (theme) => theme.shadows[4],
          transform: 'translateY(-2px)',
          transition: 'all 0.2s ease-in-out'
        }
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <Avatar sx={{ width: 40, height: 40, fontSize: '1.2rem' }}>
              {getProviderIcon()}
            </Avatar>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
                {server.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                v{server.version}
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              icon={getStatusIcon()}
              label={server.status}
              color={getStatusColor() as any}
              size="small"
              sx={{ textTransform: 'capitalize' }}
            />
            <IconButton size="small" onClick={handleMenuClick}>
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Metrics */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Uptime
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {server.metrics.uptime_percentage.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={server.metrics.uptime_percentage}
            sx={{
              height: 6,
              borderRadius: 3,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 3,
                bgcolor: server.metrics.uptime_percentage > 95 ? 'success.main' : 
                         server.metrics.uptime_percentage > 90 ? 'warning.main' : 'error.main'
              }
            }}
          />
        </Box>

        {/* Stats Grid */}
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 2 }}>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Requests Today
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {server.metrics.requests_total.toLocaleString()}
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Success Rate
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600, color: 'success.main' }}>
              {((server.metrics.requests_success / server.metrics.requests_total) * 100).toFixed(1)}%
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Avg Response
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {server.metrics.avg_response_time}ms
            </Typography>
          </Box>
          <Box>
            <Typography variant="caption" color="text.secondary">
              Data Volume
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {(server.metrics.data_volume_mb / 1000).toFixed(1)}GB
            </Typography>
          </Box>
        </Box>

        {/* Capabilities */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            Capabilities
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {server.capabilities.slice(0, 3).map((capability) => (
              <Chip
                key={capability}
                label={capability.replace('-', ' ')}
                size="small"
                variant="outlined"
                sx={{ 
                  fontSize: '0.7rem',
                  height: 20,
                  textTransform: 'capitalize',
                  borderColor: 'primary.main',
                  color: 'primary.main'
                }}
              />
            ))}
            {server.capabilities.length > 3 && (
              <Chip
                label={`+${server.capabilities.length - 3}`}
                size="small"
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
            )}
          </Box>
        </Box>

        {/* Last Connected */}
        <Typography variant="caption" color="text.secondary">
          Last connected: {formatLastConnected(server.last_connected)}
        </Typography>
      </CardContent>

      {/* Menu */}
      <Menu
        anchorEl={anchorEl}
        open={menuOpen}
        onClose={handleMenuClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        transformOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <MenuItem onClick={() => { onView?.(server); handleMenuClose(); }}>
          <VisibilityIcon sx={{ mr: 1, fontSize: 20 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={() => { handleTestConnection(); handleMenuClose(); }}>
          <RefreshIcon sx={{ mr: 1, fontSize: 20 }} />
          {isTestingConnection ? 'Testing...' : 'Test Connection'}
        </MenuItem>
        <MenuItem onClick={() => { handleToggleEnabled(); handleMenuClose(); }}>
          <CloudDoneIcon sx={{ mr: 1, fontSize: 20 }} />
          {server.enabled ? 'Disable' : 'Enable'}
        </MenuItem>
        <MenuItem onClick={() => { onSettings?.(server); handleMenuClose(); }}>
          <SettingsIcon sx={{ mr: 1, fontSize: 20 }} />
          Settings
        </MenuItem>
      </Menu>
    </Card>
  );
};

export default MCPServerCard;
