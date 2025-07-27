import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Avatar,
  Button,
  Alert,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  CloudSync as CloudSyncIcon,
  CheckCircle as CheckCircleIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useQueryClient } from 'react-query';

import { MCPServer, DataStream } from '@/types/data';
import { mcpServerService } from '@/services/mcpServerService';
import { dataStreamService } from '@/services/dataStreamService';
import NewConnectionDialog from '@/components/DataIntegration/NewConnectionDialog';

interface DataIntegrationProps {}

const DataIntegration: React.FC<DataIntegrationProps> = () => {
  const [showNewConnectionDialog, setShowNewConnectionDialog] = useState(false);
  const queryClient = useQueryClient();

  // Fetch MCP servers from API
  const { data: mcpServers = [], error: serversError } = useQuery<MCPServer[], Error>(
    'mcp-servers',
    () => mcpServerService.listServers(),
    {
      refetchInterval: 30000,
      staleTime: 10000,
    }
  );

  // Fetch data streams from API
  const { data: dataStreams = [], error: streamsError } = useQuery<DataStream[], Error>(
    'data-streams',
    () => dataStreamService.listStreams(),
    {
      refetchInterval: 5000,
      staleTime: 2000,
    }
  );

  const handleRefresh = () => {
    queryClient.invalidateQueries('mcp-servers');
    queryClient.invalidateQueries('data-streams');
  };

  const handleNewConnectionSuccess = () => {
    setShowNewConnectionDialog(false);
    queryClient.invalidateQueries('mcp-servers');
  };

  const connectedServers = mcpServers.filter(s => s.status === 'CONNECTED').length;
  const totalDataVolume = mcpServers.reduce((acc, server) => acc + (server.metrics?.data_volume_mb || 0), 0);
  const avgUptime = mcpServers.length > 0 
    ? mcpServers.reduce((acc, server) => acc + (server.metrics?.uptime_percentage || 0), 0) / mcpServers.length 
    : 0;


  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary' }}>
            Data Integration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Monitor and manage connections to custodians and market data providers
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            sx={{ borderRadius: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setShowNewConnectionDialog(true)}
            sx={{ borderRadius: 2 }}
          >
            New Connection
          </Button>
        </Box>
      </Box>

      {/* Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {connectedServers}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Connected Servers
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 56, height: 56 }}>
                  <CloudSyncIcon sx={{ fontSize: 28 }} />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'primary.main' }}>
                    {totalDataVolume.toFixed(1)}GB
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Data Volume Today
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.light', color: 'primary.dark' }}>
                  <StorageIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'success.main' }}>
                    {avgUptime.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Average Uptime
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.light', color: 'success.dark' }}>
                  <CheckCircleIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1, color: 'primary.main' }}>
                    {dataStreams.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Streams
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.light', color: 'info.dark' }}>
                  <TimelineIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* New Connection Dialog */}
      <NewConnectionDialog
        open={showNewConnectionDialog}
        onClose={() => setShowNewConnectionDialog(false)}
        onSuccess={handleNewConnectionSuccess}
      />

      {/* Error Display */}
      {(serversError || streamsError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <span>
            {serversError && `Failed to load MCP servers: ${serversError.message || 'Unknown error'}. `}
            {streamsError && `Failed to load data streams: ${streamsError.message || 'Unknown error'}.`}
          </span>
        </Alert>
      )}
    </Box>
  );
};

export default DataIntegration;
