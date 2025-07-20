import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Avatar,
  IconButton,
  Button,
  LinearProgress,
  Tabs,
  Tab,
  Alert,
  Tooltip,
  Fab,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Timeline as TimelineIcon,
  CloudSync as CloudSyncIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import { useQuery, useQueryClient } from 'react-query';

import { MCPServer, DataFlow, DataStream, ConnectionStatus, DataProviderType } from '@/types/data';
import { mcpServerService } from '@/services/mcpServerService';
import { dataStreamService } from '@/services/dataStreamService';
import MCPServerCard from '@/components/DataIntegration/MCPServerCard';
import DataFlowCard from '@/components/DataIntegration/DataFlowCard';
import DataStreamMonitor from '@/components/DataIntegration/DataStreamMonitor';
import NewConnectionDialog from '@/components/DataIntegration/NewConnectionDialog';

interface DataIntegrationProps {}

const DataIntegration: React.FC<DataIntegrationProps> = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [showNewConnectionDialog, setShowNewConnectionDialog] = useState(false);
  const queryClient = useQueryClient();

  // Fetch MCP servers from API
  const { data: mcpServers = [], isLoading: serversLoading, error: serversError } = useQuery<MCPServer[]>(
    'mcp-servers',
    () => mcpServerService.listServers(),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 10000, // Consider data stale after 10 seconds
    }
  );

  // Fetch data streams from API
  const { data: dataStreams = [], isLoading: streamsLoading, error: streamsError } = useQuery<DataStream[]>(
    'data-streams',
    () => dataStreamService.listStreams(),
    {
      refetchInterval: 5000, // Refresh every 5 seconds for real-time data
      staleTime: 2000,
    }
  );

  // Mock data flows - TODO: Replace with actual API when available
  const { data: dataFlows = [] } = useQuery<DataFlow[]>(
    'data-flows',
    async () => [
      {
        id: 'daily-positions-sync',
        name: 'Daily Position Reconciliation',
        description: 'Synchronizes position data from all custodians',
        source_servers: ['state-street-001', 'bny-mellon-cust'],
        target_systems: ['risk-system', 'reporting-db'],
        data_types: ['POSITIONS', 'CASH_FLOWS'],
        schedule: { type: 'CRON', cron_expression: '0 18 * * 1-5' },
        status: 'ACTIVE',
        last_run: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        next_run: new Date(Date.now() + 1000 * 60 * 60 * 14).toISOString(),
        transformations: [],
        quality_rules: [],
        metrics: {
          records_processed: 125000,
          records_success: 124850,
          records_failed: 150,
          processing_time_ms: 45000,
          data_quality_score: 99.2,
          errors: []
        }
      }
    ]
  );

  const handleRefresh = () => {
    queryClient.invalidateQueries('mcp-servers');
    queryClient.invalidateQueries('data-flows');
    queryClient.invalidateQueries('data-streams');
  };

  const handleNewConnectionSuccess = () => {
    setShowNewConnectionDialog(false);
    queryClient.invalidateQueries('mcp-servers');
  };

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED: return 'success';
      case ConnectionStatus.ERROR: return 'error';
      case ConnectionStatus.CONNECTING: return 'warning';
      case ConnectionStatus.MAINTENANCE: return 'info';
      default: return 'default';
    }
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

      {/* Tabs */}
      <Card sx={{ borderRadius: 3, mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              textTransform: 'none',
              fontWeight: 500,
              px: 3
            }
          }}
        >
          <Tab label="MCP Servers" />
          <Tab label="Data Flows" />
          <Tab label="Real-time Streams" />
          <Tab label="Data Quality" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {/* MCP Servers Tab */}
          {activeTab === 0 && (
            <Box sx={{ p: 3 }}>
              {serversLoading ? (
                <LinearProgress sx={{ borderRadius: 1 }} />
              ) : (
                <Grid container spacing={3}>
                  {mcpServers.map((server) => (
                    <Grid item xs={12} md={6} lg={4} key={server.id}>
                      <MCPServerCard server={server} />
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          )}

          {/* Data Flows Tab */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              <Grid container spacing={3}>
                {dataFlows.map((flow) => (
                  <Grid item xs={12} md={6} key={flow.id}>
                    <DataFlowCard flow={flow} />
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Real-time Streams Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              <DataStreamMonitor streams={dataStreams} />
            </Box>
          )}

          {/* Data Quality Tab */}
          {activeTab === 3 && (
            <Box sx={{ p: 3 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                Data quality monitoring dashboard coming soon
              </Alert>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* New Connection Dialog */}
      <NewConnectionDialog
        open={showNewConnectionDialog}
        onClose={() => setShowNewConnectionDialog(false)}
        onSuccess={handleNewConnectionSuccess}
      />

      {/* Error Display */}
      {(serversError || streamsError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {serversError && `Failed to load MCP servers: ${serversError.message}. `}
          {streamsError && `Failed to load data streams: ${streamsError.message}.`}
        </Alert>
      )}
    </Box>
  );
};

export default DataIntegration;