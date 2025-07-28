import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Pagination,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Schedule as PendingIcon,
  PlayArrow as RunningIcon,
  Cancel as CancelledIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

import { dataSourceService, DataSourceConfiguration, DataPullExecution } from '@/services/dataSourceService';

interface ExecutionHistoryDialogProps {
  open: boolean;
  onClose: () => void;
  config: DataSourceConfiguration;
}

const ExecutionHistoryDialog: React.FC<ExecutionHistoryDialogProps> = ({ open, onClose, config }) => {
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const offset = (page - 1) * pageSize;

  const { data: executions = [], isLoading, error, refetch } = useQuery({
    queryKey: ['executionHistory', config.id, page],
    queryFn: () => dataSourceService.getExecutionHistory(config.id, { limit: pageSize, offset }),
    enabled: open,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <SuccessIcon color="success" fontSize="small" />;
      case 'FAILED':
        return <ErrorIcon color="error" fontSize="small" />;
      case 'RUNNING':
        return <RunningIcon color="primary" fontSize="small" />;
      case 'PENDING':
      case 'SCHEDULED':
        return <PendingIcon color="warning" fontSize="small" />;
      case 'CANCELLED':
        return <CancelledIcon color="disabled" fontSize="small" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string): 'success' | 'error' | 'warning' | 'info' | 'default' => {
    switch (status) {
      case 'COMPLETED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'RUNNING':
        return 'info';
      case 'PENDING':
      case 'SCHEDULED':
        return 'warning';
      case 'CANCELLED':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatBytes = (bytes?: number) => {
    if (!bytes) return 'N/A';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const calculateSuccessRate = () => {
    if (executions.length === 0) return 0;
    const successful = executions.filter(e => e.status === 'COMPLETED').length;
    return Math.round((successful / executions.length) * 100);
  };

  const getAverageExecutionTime = () => {
    const completedExecutions = executions.filter(e => e.status === 'COMPLETED' && e.duration_seconds);
    if (completedExecutions.length === 0) return 0;
    const totalTime = completedExecutions.reduce((sum, e) => sum + (e.duration_seconds || 0), 0);
    return Math.round(totalTime / completedExecutions.length);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">
            Execution History: {config.name}
          </Typography>
          <IconButton onClick={() => refetch()} disabled={isLoading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Summary Statistics */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Chip
              label={`Total Runs: ${config.total_runs}`}
              variant="outlined"
            />
            <Chip
              label={`Success Rate: ${calculateSuccessRate()}%`}
              color={calculateSuccessRate() >= 90 ? 'success' : calculateSuccessRate() >= 70 ? 'warning' : 'error'}
              variant="outlined"
            />
            <Chip
              label={`Avg Duration: ${formatDuration(getAverageExecutionTime())}`}
              variant="outlined"
            />
            <Chip
              label={`Last Run: ${formatDateTime(config.last_run_at)}`}
              variant="outlined"
            />
          </Box>

          {/* Error State */}
          {error && (
            <Alert severity="error">
              Failed to load execution history. Please try again.
            </Alert>
          )}

          {/* Loading State */}
          {isLoading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {/* Execution History Table */}
          {!isLoading && !error && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Recent Executions
              </Typography>
              
              {executions.length === 0 ? (
                <Alert severity="info">
                  No execution history found for this data source.
                </Alert>
              ) : (
                <>
                  <TableContainer component={Paper} sx={{ maxHeight: 500 }}>
                    <Table stickyHeader size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Started</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Duration</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Records</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Data Size</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Trigger</TableCell>
                          <TableCell sx={{ fontWeight: 600 }}>Error</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {executions.map((execution) => (
                          <TableRow key={execution.id} hover>
                            <TableCell>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                {getStatusIcon(execution.status)}
                                <Chip
                                  label={execution.status}
                                  size="small"
                                  color={getStatusColor(execution.status)}
                                  variant="outlined"
                                />
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {formatDateTime(execution.started_at)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {formatDuration(execution.duration_seconds)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box>
                                <Typography variant="body2">
                                  {execution.records_processed !== undefined
                                    ? `${execution.records_successful || 0}/${execution.records_processed}`
                                    : 'N/A'}
                                </Typography>
                                {execution.records_failed && execution.records_failed > 0 && (
                                  <Typography variant="caption" color="error">
                                    {execution.records_failed} failed
                                  </Typography>
                                )}
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {formatBytes(execution.data_size_bytes)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box>
                                <Chip
                                  label={execution.trigger_type}
                                  size="small"
                                  variant="outlined"
                                />
                                <Typography variant="caption" color="text.secondary" display="block">
                                  by {execution.triggered_by}
                                </Typography>
                              </Box>
                            </TableCell>
                            <TableCell>
                              {execution.error_message ? (
                                <Tooltip title={execution.error_message} arrow>
                                  <Typography
                                    variant="caption"
                                    color="error"
                                    sx={{
                                      maxWidth: 150,
                                      overflow: 'hidden',
                                      textOverflow: 'ellipsis',
                                      whiteSpace: 'nowrap',
                                      cursor: 'help',
                                    }}
                                  >
                                    {execution.error_message}
                                  </Typography>
                                </Tooltip>
                              ) : (
                                <Typography variant="body2" color="text.secondary">
                                  -
                                </Typography>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>

                  {/* Pagination */}
                  {executions.length === pageSize && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                      <Pagination
                        count={Math.ceil(config.total_runs / pageSize)}
                        page={page}
                        onChange={(_, newPage) => setPage(newPage)}
                        color="primary"
                      />
                    </Box>
                  )}
                </>
              )}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExecutionHistoryDialog;