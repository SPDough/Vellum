import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem,
  Alert,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  MoreVert as MoreVertIcon,
  TrendingUp,
  Speed,
  CheckCircle,
  Error,
  Warning,
  Info,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

import { agentService } from '@/services/agentService';
import { Agent, AgentStatus } from '@/types/agent';

interface AgentMonitoringDashboardProps {
  agentId?: string;
}

const AgentMonitoringDashboard: React.FC<AgentMonitoringDashboardProps> = ({ agentId }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);

  // Fetch agents or specific agent
  const { data: agents, isLoading } = useQuery<Agent[]>({
    queryKey: agentId ? ['agent', agentId] : ['agents'],
    queryFn: () => agentId ? agentService.getAgent(agentId).then(agent => [agent]) : agentService.listAgents(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Fetch agent metrics for selected agent
  const { data: metrics } = useQuery({
    queryKey: ['agent-metrics', selectedAgent?.id],
    queryFn: () => selectedAgent ? agentService.getAgentMetrics(selectedAgent.id) : null,
    enabled: !!selectedAgent,
    refetchInterval: 5000,
  });

  // Fetch agent logs for selected agent
  const { data: logs } = useQuery({
    queryKey: ['agent-logs', selectedAgent?.id],
    queryFn: () => selectedAgent ? agentService.getAgentLogs(selectedAgent.id, { limit: 100 }) : null,
    enabled: !!selectedAgent,
    refetchInterval: 5000,
  });

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, agent: Agent) => {
    setAnchorEl(event.currentTarget);
    setSelectedAgent(agent);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const getStatusColor = (status: AgentStatus) => {
    switch (status) {
      case AgentStatus.ACTIVE:
        return 'success';
      case AgentStatus.INACTIVE:
        return 'default';
      case AgentStatus.ERROR:
        return 'error';
      case AgentStatus.TRAINING:
        return 'warning';
      case AgentStatus.PAUSED:
        return 'info';
      default:
        return 'default';
    }
  };

  const getLogLevelIcon = (level: string) => {
    switch (level) {
      case 'ERROR':
        return <Error color="error" />;
      case 'WARN':
        return <Warning color="warning" />;
      case 'INFO':
        return <Info color="info" />;
      default:
        return <CheckCircle color="success" />;
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading agent monitoring data...</Typography>
      </Box>
    );
  }

  if (!agents || agents.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">No agents found for monitoring.</Alert>
      </Box>
    );
  }

  const activeAgents = agents.filter(agent => agent.status === AgentStatus.ACTIVE);
  const totalTasks = agents.reduce((sum, agent) => sum + agent.metrics.successful_tasks + agent.metrics.failed_tasks, 0);
  const successfulTasks = agents.reduce((sum, agent) => sum + agent.metrics.successful_tasks, 0);
  const avgResponseTime = agents.reduce((sum, agent) => sum + agent.metrics.average_response_time_ms, 0) / agents.length;

  return (
    <Box>
      {/* Overview Metrics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'success.main' }}>
                    {activeAgents.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Agents
                  </Typography>
                </Box>
                <TrendingUp sx={{ color: 'success.main', fontSize: 32 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
                    {((successfulTasks / totalTasks) * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Success Rate
                  </Typography>
                </Box>
                <CheckCircle sx={{ color: 'primary.main', fontSize: 32 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'info.main' }}>
                    {avgResponseTime.toFixed(0)}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Response Time
                  </Typography>
                </Box>
                <Speed sx={{ color: 'info.main', fontSize: 32 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: 'warning.main' }}>
                    {totalTasks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Tasks
                  </Typography>
                </Box>
                <TrendingUp sx={{ color: 'warning.main', fontSize: 32 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Monitoring */}
      <Card sx={{ borderRadius: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Agent Status" />
          <Tab label="Performance Metrics" />
          <Tab label="Activity Logs" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {/* Agent Status Tab */}
          {activeTab === 0 && (
            <Box sx={{ p: 3 }}>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Agent</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell>Uptime</TableCell>
                      <TableCell>Tasks Today</TableCell>
                      <TableCell>Success Rate</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {agents.map((agent) => (
                      <TableRow key={agent.id}>
                        <TableCell>
                          <Box>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {agent.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {agent.id}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={agent.status} 
                            size="small" 
                            color={getStatusColor(agent.status) as any}
                          />
                        </TableCell>
                        <TableCell>{agent.agent_type}</TableCell>
                        <TableCell>{agent.metrics.uptime_percentage}%</TableCell>
                        <TableCell>{agent.metrics.last_24h_interactions}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <LinearProgress 
                              variant="determinate" 
                              value={agent.metrics.accuracy_score} 
                              sx={{ width: 60, height: 6 }}
                            />
                            <Typography variant="caption">
                              {agent.metrics.accuracy_score}%
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton 
                            size="small"
                            onClick={(e) => handleMenuOpen(e, agent)}
                          >
                            <MoreVertIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}

          {/* Performance Metrics Tab */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              {selectedAgent && metrics ? (
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                      Execution Metrics
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Successful Tasks: {metrics.metrics.successful_executions || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Failed Tasks: {metrics.metrics.failed_executions || 0}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Response Time: {metrics.metrics.avg_response_time_ms || 0}ms
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                      Token Usage
                    </Typography>
                    {metrics.token_usage_over_time.map((usage, index) => (
                      <Box key={index} sx={{ mb: 1 }}>
                        <Typography variant="body2">
                          {usage.date}: {usage.tokens} tokens (${usage.cost_usd.toFixed(4)})
                        </Typography>
                      </Box>
                    ))}
                  </Grid>
                </Grid>
              ) : (
                <Alert severity="info">
                  Select an agent from the Status tab to view detailed metrics.
                </Alert>
              )}
            </Box>
          )}

          {/* Activity Logs Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              {selectedAgent && logs ? (
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Recent Activity - {selectedAgent.name}
                  </Typography>
                  <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                    {logs.map((log, index) => (
                      <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          {getLogLevelIcon(log.level)}
                          <Typography variant="caption" color="text.secondary">
                            {new Date(log.timestamp).toLocaleString()}
                          </Typography>
                          <Chip label={log.level} size="small" />
                        </Box>
                        <Typography variant="body2">
                          {log.message}
                        </Typography>
                        {log.metadata && (
                          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                            Metadata: {JSON.stringify(log.metadata, null, 2)}
                          </Typography>
                        )}
                      </Box>
                    ))}
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">
                  Select an agent from the Status tab to view activity logs.
                </Alert>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Context Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          setSelectedAgent(selectedAgent);
          setActiveTab(1);
          handleMenuClose();
        }}>
          View Metrics
        </MenuItem>
        <MenuItem onClick={() => {
          setSelectedAgent(selectedAgent);
          setActiveTab(2);
          handleMenuClose();
        }}>
          View Logs
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleMenuClose}>
          Restart Agent
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default AgentMonitoringDashboard;
