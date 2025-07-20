import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  Grid,
  LinearProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
  Refresh as RefreshIcon,
  Link as LinkIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { mcpServerService } from '@/services/mcpServerService';
import { dataSandboxService } from '@/services/dataSandboxService';
import { MCPDataStream, DataSource } from '@/types/dataSandbox';

interface MCPDataConnectorProps {
  onDataSourceCreated?: (dataSource: DataSource) => void;
}

const MCPDataConnector: React.FC<MCPDataConnectorProps> = ({ onDataSourceCreated }) => {
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [selectedServerId, setSelectedServerId] = useState('');
  const [selectedStreamName, setSelectedStreamName] = useState('');
  const [dataSourceName, setDataSourceName] = useState('');
  
  const queryClient = useQueryClient();

  // Fetch MCP servers
  const { data: mcpServers } = useQuery(
    'mcp-servers',
    () => mcpServerService.listServers()
  );

  // Fetch recent MCP data streams
  const { data: mcpDataStreams, isLoading: streamsLoading } = useQuery(
    'mcp-data-streams',
    () => dataSandboxService.getMCPDataStreams({ limit: 20 }),
    {
      refetchInterval: 10000,
    }
  );

  // Create data source from MCP
  const createDataSourceMutation = useMutation(
    ({ serverId, streamName, name }: { serverId: string; streamName: string; name: string }) =>
      dataSandboxService.createDataSourceFromMCP(serverId, streamName).then(source => ({
        ...source,
        name: name || source.name,
      })),
    {
      onSuccess: (dataSource) => {
        queryClient.invalidateQueries(['data-sources']);
        onDataSourceCreated?.(dataSource);
        setConnectDialogOpen(false);
        resetForm();
      },
    }
  );

  const resetForm = () => {
    setSelectedServerId('');
    setSelectedStreamName('');
    setDataSourceName('');
  };

  const handleConnect = () => {
    if (selectedServerId && selectedStreamName) {
      createDataSourceMutation.mutate({
        serverId: selectedServerId,
        streamName: selectedStreamName,
        name: dataSourceName,
      });
    }
  };

  const handleViewStream = (stream: MCPDataStream) => {
    // Navigate to data sandbox with this specific stream
    console.log('View stream:', stream);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatDataSize = (size: number) => {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getDataPreview = (data: any) => {
    if (Array.isArray(data)) {
      return `Array (${data.length} items)`;
    } else if (typeof data === 'object' && data !== null) {
      const keys = Object.keys(data);
      return `Object (${keys.length} keys: ${keys.slice(0, 3).join(', ')}${keys.length > 3 ? '...' : ''})`;
    } else {
      return String(data).slice(0, 50) + (String(data).length > 50 ? '...' : '');
    }
  };

  const getServerStatus = (serverId: string) => {
    const server = mcpServers?.find(s => s.id === serverId);
    return server?.status || 'unknown';
  };

  const getServerStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'success';
      case 'disconnected':
        return 'error';
      case 'connecting':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          MCP Data Sources
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => queryClient.invalidateQueries('mcp-data-streams')}
            sx={{ borderRadius: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setConnectDialogOpen(true)}
            sx={{ borderRadius: 2 }}
          >
            Connect MCP Stream
          </Button>
        </Box>
      </Box>

      {/* MCP Data Streams */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Recent MCP Data Streams
              </Typography>
              
              {streamsLoading && <LinearProgress sx={{ mb: 2 }} />}
              
              {mcpDataStreams && mcpDataStreams.length > 0 ? (
                <List>
                  {mcpDataStreams.map((stream) => (
                    <ListItem key={stream.id} divider>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {stream.streamName}
                            </Typography>
                            <Chip 
                              label={stream.serverName} 
                              size="small" 
                              color="primary" 
                              variant="outlined"
                              icon={<LinkIcon />}
                            />
                            <Chip 
                              label={getServerStatus(stream.serverId)} 
                              size="small" 
                              color={getServerStatusColor(getServerStatus(stream.serverId)) as any}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {formatTimestamp(stream.timestamp)} • 
                              Type: {stream.metadata.contentType} • 
                              Size: {formatDataSize(stream.metadata.size)}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }}>
                              Data: {getDataPreview(stream.data)}
                            </Typography>
                            {stream.metadata.encoding && (
                              <Typography variant="caption" color="text.secondary">
                                Encoding: {stream.metadata.encoding}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <IconButton 
                            size="small" 
                            onClick={() => handleViewStream(stream)}
                          >
                            <ViewIcon />
                          </IconButton>
                          <IconButton size="small">
                            <ExportIcon />
                          </IconButton>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  No MCP data streams found. Configure MCP servers to start receiving data.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Connected MCP Servers Overview */}
        <Grid item xs={12}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Connected MCP Servers
              </Typography>
              
              {mcpServers && mcpServers.length > 0 ? (
                <Grid container spacing={2}>
                  {mcpServers.map((server) => (
                    <Grid item xs={12} sm={6} md={4} key={server.id}>
                      <Card variant="outlined" sx={{ borderRadius: 2 }}>
                        <CardContent>
                          <Typography variant="body1" sx={{ fontWeight: 600, mb: 1 }}>
                            {server.name}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                            <Chip 
                              label={server.status} 
                              size="small" 
                              color={getServerStatusColor(server.status) as any}
                            />
                            <Chip 
                              label={server.provider_type} 
                              size="small" 
                              variant="outlined"
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary">
                            {server.description}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Alert severity="warning">
                  No MCP servers configured. Set up MCP servers to start receiving data streams.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Connect MCP Stream Dialog */}
      <Dialog open={connectDialogOpen} onClose={() => setConnectDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Connect MCP Data Stream</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>MCP Server</InputLabel>
                <Select
                  value={selectedServerId}
                  onChange={(e) => setSelectedServerId(e.target.value)}
                  label="MCP Server"
                >
                  {mcpServers?.filter(server => server.status === 'connected').map((server) => (
                    <MenuItem key={server.id} value={server.id}>
                      {server.name} ({server.provider_type})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Stream Name"
                value={selectedStreamName}
                onChange={(e) => setSelectedStreamName(e.target.value)}
                placeholder="e.g., market_data, trades, prices"
                helperText="The name of the data stream from the MCP server"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Data Source Name"
                value={dataSourceName}
                onChange={(e) => setDataSourceName(e.target.value)}
                placeholder="Enter a descriptive name for this data source"
                helperText="This will be the display name in the data sandbox"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConnectDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleConnect}
            disabled={!selectedServerId || !selectedStreamName || createDataSourceMutation.isLoading}
          >
            {createDataSourceMutation.isLoading ? 'Connecting...' : 'Connect'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default MCPDataConnector;