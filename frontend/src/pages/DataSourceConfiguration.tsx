'use client';

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Tooltip,
  Menu,
  MenuItem,
  Switch,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
  Science as TestIcon,
  Schedule as ScheduleIcon,
  DataObject as DataIcon,
  Api as ApiIcon,
  Web as WebIcon,
  MoreVert as MoreVertIcon,
  Refresh as RefreshIcon,
  Psychology as PythonIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { dataSourceService } from '@/services/dataSourceService';
import DataSourceForm from '@/components/DataSources/DataSourceForm';
import DataSourceTestDialog from '@/components/DataSources/DataSourceTestDialog';
import ExecutionHistoryDialog from '@/components/DataSources/ExecutionHistoryDialog';
import PythonREPLWorkflow from '@/components/DataSources/PythonREPLWorkflow';

interface DataSourceConfiguration {
  id: string;
  name: string;
  description?: string;
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
  is_active: boolean;
  schedule_type: 'MANUAL' | 'INTERVAL' | 'CRON';
  last_run_at?: string;
  next_run_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  avg_execution_time_seconds?: number;
  created_at: string;
  created_by: string;
}

interface DataSourceConfigurationProps {}

const DataSourceConfiguration: React.FC<DataSourceConfigurationProps> = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [formDialogOpen, setFormDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [replWorkflowOpen, setReplWorkflowOpen] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<DataSourceConfiguration | null>(null);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [menuConfigId, setMenuConfigId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  // Fetch data sources
  const { data: dataSources = [], isLoading, error, refetch } = useQuery({
    queryKey: ['dataSources'],
    queryFn: () => dataSourceService.listDataSources(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (configId: string) => dataSourceService.deleteDataSource(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
      handleMenuClose();
    },
  });

  // Toggle active mutation
  const toggleMutation = useMutation({
    mutationFn: (configId: string) => dataSourceService.toggleDataSource(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
    },
  });

  // Execute data pull mutation
  const executeMutation = useMutation({
    mutationFn: (configId: string) => dataSourceService.executeDataPull(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dataSources'] });
      handleMenuClose();
    },
  });

  const handleCreateNew = () => {
    setSelectedConfig(null);
    setFormDialogOpen(true);
  };

  const handleEdit = (config: DataSourceConfiguration) => {
    setSelectedConfig(config);
    setFormDialogOpen(true);
    handleMenuClose();
  };

  const handleDelete = (configId: string) => {
    if (confirm('Are you sure you want to delete this data source configuration?')) {
      deleteMutation.mutate(configId);
    }
  };

  const handleToggleActive = (configId: string) => {
    toggleMutation.mutate(configId);
  };

  const handleExecute = (configId: string) => {
    executeMutation.mutate(configId);
  };

  const handleTest = (config: DataSourceConfiguration) => {
    setSelectedConfig(config);
    setTestDialogOpen(true);
    handleMenuClose();
  };

  const handleViewHistory = (config: DataSourceConfiguration) => {
    setSelectedConfig(config);
    setHistoryDialogOpen(true);
    handleMenuClose();
  };

  const handleOpenREPLWorkflow = (config: DataSourceConfiguration) => {
    setSelectedConfig(config);
    setReplWorkflowOpen(true);
    handleMenuClose();
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, configId: string) => {
    setAnchorEl(event.currentTarget);
    setMenuConfigId(configId);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuConfigId(null);
  };

  const getDataSourceTypeIcon = (type: string) => {
    switch (type) {
      case 'API':
        return <ApiIcon />;
      case 'MCP_SERVER':
        return <DataIcon />;
      case 'WEB_SCRAPING':
        return <WebIcon />;
      default:
        return <DataIcon />;
    }
  };

  const getStatusColor = (successfulRuns: number, totalRuns: number) => {
    if (totalRuns === 0) return 'default';
    const successRate = (successfulRuns / totalRuns) * 100;
    if (successRate >= 90) return 'success';
    if (successRate >= 70) return 'warning';
    return 'error';
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
            Data Source Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure scheduled data pulls from APIs, MCP servers, and web scraping
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateNew}
            sx={{ borderRadius: 2 }}
          >
            Add Data Source
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load data sources. Please try again.
        </Alert>
      )}

      {/* Main Content */}
      <Card sx={{ borderRadius: 3 }}>
        <Tabs
          value={selectedTab}
          onChange={(_, newValue) => setSelectedTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All Data Sources" />
          <Tab label="Active Sources" />
          <Tab label="Scheduled Sources" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Schedule</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Last Run</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Success Rate</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Avg Duration</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dataSources
                    .filter((config: any) => {
                      if (selectedTab === 1) return config.is_active;
                      if (selectedTab === 2) return config.schedule_type !== 'MANUAL';
                      return true;
                    })
                    .map((config: any) => (
                      <TableRow key={config.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getDataSourceTypeIcon(config.data_source_type)}
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {config.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {config.description}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={config.data_source_type.replace('_', ' ')}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <ScheduleIcon fontSize="small" />
                            <Typography variant="body2">
                              {config.schedule_type === 'MANUAL' ? 'Manual' : 'Scheduled'}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Switch
                              size="small"
                              checked={config.is_active}
                              onChange={() => handleToggleActive(config.id)}
                              disabled={toggleMutation.isPending}
                            />
                            <Chip
                              label={config.is_active ? 'Active' : 'Inactive'}
                              size="small"
                              color={config.is_active ? 'success' : 'default'}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDateTime(config.last_run_at)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={
                              config.total_runs > 0
                                ? `${Math.round((config.successful_runs / config.total_runs) * 100)}%`
                                : 'N/A'
                            }
                            size="small"
                            color={getStatusColor(config.successful_runs, config.total_runs)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {formatDuration(config.avg_execution_time_seconds)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <Tooltip title="Execute Now">
                              <IconButton
                                size="small"
                                onClick={() => handleExecute(config.id)}
                                disabled={!config.is_active || executeMutation.isPending}
                              >
                                <PlayIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="More Options">
                              <IconButton
                                size="small"
                                onClick={(e) => handleMenuOpen(e, config.id)}
                              >
                                <MoreVertIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem
          onClick={() => {
            const config = dataSources.find(c => c.id === menuConfigId);
            if (config) handleEdit(config);
          }}
        >
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit Configuration</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            const config = dataSources.find(c => c.id === menuConfigId);
            if (config) handleTest(config);
          }}
        >
          <ListItemIcon>
            <TestIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Test Connection</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            const config = dataSources.find(c => c.id === menuConfigId);
            if (config) handleViewHistory(config);
          }}
        >
          <ListItemIcon>
            <HistoryIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View History</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            const config = dataSources.find(c => c.id === menuConfigId);
            if (config) handleOpenREPLWorkflow(config);
          }}
        >
          <ListItemIcon>
            <PythonIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Python REPL Workflow</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (menuConfigId) handleDelete(menuConfigId);
          }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" color="error" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Data Source Form Dialog */}
      <DataSourceForm
        open={formDialogOpen}
        onClose={() => {
          setFormDialogOpen(false);
          setSelectedConfig(null);
        }}
        config={selectedConfig}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['dataSources'] });
          setFormDialogOpen(false);
          setSelectedConfig(null);
        }}
      />

      {/* Test Dialog */}
      {selectedConfig && (
        <DataSourceTestDialog
          open={testDialogOpen}
          onClose={() => {
            setTestDialogOpen(false);
            setSelectedConfig(null);
          }}
          config={selectedConfig}
        />
      )}

      {/* Execution History Dialog */}
      {selectedConfig && (
        <ExecutionHistoryDialog
          open={historyDialogOpen}
          onClose={() => {
            setHistoryDialogOpen(false);
            setSelectedConfig(null);
          }}
          config={selectedConfig}
        />
      )}

      {/* Python REPL Workflow Dialog */}
      {selectedConfig && (
        <PythonREPLWorkflow
          open={replWorkflowOpen}
          onClose={() => {
            setReplWorkflowOpen(false);
            setSelectedConfig(null);
          }}
          config={selectedConfig}
        />
      )}
    </Box>
  );
};

export default DataSourceConfiguration;
