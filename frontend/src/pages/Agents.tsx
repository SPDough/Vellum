import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  SmartToy as AgentIcon,
  Add as AddIcon,
  Edit as EditIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Chat as ChatIcon,
  ExpandMore as ExpandMoreIcon,
  Psychology as PsychologyIcon,
  TrendingUp as MetricsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import { agentService } from '@/services/agentService';
import { Agent, AgentCreateRequest, AgentType, AgentStatus } from '@/types/agent';
import AgentMonitoringDashboard from '@/components/Agents/AgentMonitoringDashboard';
import AgentChatInterface from '@/components/Agents/AgentChatInterface';

interface AgentsProps {}

const Agents: React.FC<AgentsProps> = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [createAgentOpen, setCreateAgentOpen] = useState(false);
  const [chatAgent, setChatAgent] = useState<Agent | null>(null);
  const [agentFormData, setAgentFormData] = useState<Partial<AgentCreateRequest>>({
    name: '',
    description: '',
    agent_type: AgentType.CUSTOM,
    capabilities: [],
    model: {
      provider: 'OPENAI',
      model_name: 'gpt-4',
      temperature: 0.7,
      max_tokens: 4000,
    },
    tools: [],
    memory: {
      type: 'CONVERSATION',
      max_entries: 100,
      retention_days: 30,
      embeddings_enabled: false,
    },
    prompt: {
      system_prompt: '',
      instructions: [],
      examples: [],
      constraints: [],
    },
    tags: [],
  });

  const queryClient = useQueryClient();

  // Fetch agents
  const { data: agents, isLoading: agentsLoading } = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => agentService.listAgents(),
    refetchInterval: 30000,
  });

  // Fetch agent templates
  const { data: templates } = useQuery({
    queryKey: ['agent-templates'],
    queryFn: () => agentService.listTemplates(),
  });

  // Create agent mutation
  const createAgentMutation = useMutation({
    mutationFn: (request: AgentCreateRequest) => agentService.createAgent(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      setCreateAgentOpen(false);
      resetForm();
    },
  });

  // Activate/Deactivate agent mutations
  const activateAgentMutation = useMutation({
    mutationFn: (agentId: string) => agentService.activateAgent(agentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agents'] }),
  });

  const deactivateAgentMutation = useMutation({
    mutationFn: (agentId: string) => agentService.deactivateAgent(agentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agents'] }),
  });

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const resetForm = () => {
    setAgentFormData({
      name: '',
      description: '',
      agent_type: AgentType.CUSTOM,
      capabilities: [],
      model: {
        provider: 'OPENAI',
        model_name: 'gpt-4',
        temperature: 0.7,
        max_tokens: 4000,
      },
      tools: [],
      memory: {
        type: 'CONVERSATION',
        max_entries: 100,
        retention_days: 30,
        embeddings_enabled: false,
      },
      prompt: {
        system_prompt: '',
        instructions: [],
        examples: [],
        constraints: [],
      },
      tags: [],
    });
  };

  const handleCreateAgent = () => {
    if (agentFormData.name && agentFormData.description) {
      createAgentMutation.mutate(agentFormData as AgentCreateRequest);
    }
  };

  const handleToggleAgent = (agent: Agent) => {
    if (agent.status === AgentStatus.ACTIVE) {
      deactivateAgentMutation.mutate(agent.id);
    } else {
      activateAgentMutation.mutate(agent.id);
    }
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

  const getAgentTypeColor = (type: AgentType) => {
    const colors = {
      [AgentType.TRADING_ANALYST]: 'primary',
      [AgentType.RISK_MONITOR]: 'error',
      [AgentType.COMPLIANCE_CHECKER]: 'warning',
      [AgentType.DATA_ANALYST]: 'info',
      [AgentType.PORTFOLIO_MANAGER]: 'success',
      [AgentType.SETTLEMENT_SPECIALIST]: 'secondary',
      [AgentType.MARKET_RESEARCHER]: 'primary',
      [AgentType.CUSTOM]: 'default',
    };
    return colors[type] || 'default';
  };

  const activeAgents = agents?.filter(agent => agent.status === AgentStatus.ACTIVE) || [];
  const totalAgents = agents?.length || 0;
  const avgAccuracy = totalAgents > 0 ? (agents?.reduce((acc, agent) => acc + agent.metrics.accuracy_score, 0) || 0) / totalAgents : 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary' }}>
            AI Agents
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage and monitor your trading agents
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateAgentOpen(true)}
          sx={{ borderRadius: 2 }}
        >
          Create Agent
        </Button>
      </Box>

      {/* Statistics Cards */}
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
                    {totalAgents}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Agents
                  </Typography>
                </Box>
                <AgentIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {activeAgents.length}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Agents
                  </Typography>
                </Box>
                <PsychologyIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {avgAccuracy.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Avg Accuracy
                  </Typography>
                </Box>
                <MetricsIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {templates?.length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Templates
                  </Typography>
                </Box>
                <SettingsIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Card sx={{ borderRadius: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All Agents" />
          <Tab label="Monitoring" />
          <Tab label="Chat" />
          <Tab label="Templates" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {/* Agents List Tab */}
          {activeTab === 0 && (
            <Box sx={{ p: 3 }}>
              {agentsLoading ? (
                <LinearProgress />
              ) : agents && agents.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Agent</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Capabilities</TableCell>
                        <TableCell>Performance</TableCell>
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
                                {agent.description}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={agent.agent_type} 
                              size="small" 
                              color={getAgentTypeColor(agent.agent_type) as any}
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={agent.status} 
                              size="small" 
                              color={getStatusColor(agent.status) as any}
                            />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                              {agent.capabilities.slice(0, 2).map((cap) => (
                                <Chip 
                                  key={cap} 
                                  label={cap.replace('_', ' ')} 
                                  size="small" 
                                  variant="outlined"
                                />
                              ))}
                              {agent.capabilities.length > 2 && (
                                <Chip 
                                  label={`+${agent.capabilities.length - 2}`} 
                                  size="small" 
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </TableCell>
                          <TableCell>
                            <Box>
                              <Typography variant="body2">
                                Accuracy: {agent.metrics.accuracy_score}%
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {agent.metrics.successful_tasks} successful tasks
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <IconButton 
                                size="small"
                                onClick={() => handleToggleAgent(agent)}
                                color={agent.status === AgentStatus.ACTIVE ? 'error' : 'success'}
                              >
                                {agent.status === AgentStatus.ACTIVE ? <StopIcon /> : <StartIcon />}
                              </IconButton>
                              <IconButton 
                                size="small"
                                onClick={() => {
                                  setChatAgent(agent);
                                  setActiveTab(2);
                                }}
                              >
                                <ChatIcon />
                              </IconButton>
                              <IconButton size="small">
                                <EditIcon />
                              </IconButton>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  No agents found. Create your first agent to get started.
                </Alert>
              )}
            </Box>
          )}

          {/* Monitoring Tab */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              <AgentMonitoringDashboard />
            </Box>
          )}

          {/* Chat Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              {chatAgent ? (
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                    Chat with {chatAgent.name}
                  </Typography>
                  <AgentChatInterface agent={chatAgent} />
                </Box>
              ) : (
                <Alert severity="info">
                  Select an agent from the "All Agents" tab to start a conversation.
                </Alert>
              )}
            </Box>
          )}

          {/* Templates Tab */}
          {activeTab === 3 && (
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Agent Templates
              </Typography>
              
              <Grid container spacing={3}>
                {templates?.map((template) => (
                  <Grid item xs={12} md={6} lg={4} key={template.id}>
                    <Card sx={{ borderRadius: 2, height: '100%' }}>
                      <CardContent>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                          {template.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {template.description}
                        </Typography>
                        <Chip 
                          label={template.agent_type} 
                          size="small" 
                          color="primary" 
                          sx={{ mb: 2 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 2 }}>
                          Used {template.use_count} times
                        </Typography>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          fullWidth
                          sx={{ borderRadius: 2 }}
                        >
                          Use Template
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}

          {/* Performance Tab (moved to index 4, but removed for now) */}
          {activeTab === 4 && (
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Agent Performance Analytics
              </Typography>
              <Alert severity="info">
                Performance analytics will be implemented in the next phase.
              </Alert>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Create Agent Dialog */}
      <Dialog open={createAgentOpen} onClose={() => setCreateAgentOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Agent</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Agent Name"
                value={agentFormData.name}
                onChange={(e) => setAgentFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Agent Type</InputLabel>
                <Select
                  value={agentFormData.agent_type}
                  onChange={(e) => setAgentFormData(prev => ({ ...prev, agent_type: e.target.value as AgentType }))}
                  label="Agent Type"
                >
                  {Object.values(AgentType).map((type) => (
                    <MenuItem key={type} value={type}>
                      {type.replace('_', ' ')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="Description"
                value={agentFormData.description}
                onChange={(e) => setAgentFormData(prev => ({ ...prev, description: e.target.value }))}
                required
              />
            </Grid>

            <Grid item xs={12}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Model Configuration</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Provider</InputLabel>
                        <Select
                          value={agentFormData.model?.provider}
                          onChange={(e) => setAgentFormData(prev => ({
                            ...prev,
                            model: { ...prev.model!, provider: e.target.value as any }
                          }))}
                          label="Provider"
                        >
                          <MenuItem value="OPENAI">OpenAI</MenuItem>
                          <MenuItem value="ANTHROPIC">Anthropic</MenuItem>
                          <MenuItem value="OLLAMA">Ollama</MenuItem>
                          <MenuItem value="AZURE_OPENAI">Azure OpenAI</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Model Name"
                        value={agentFormData.model?.model_name}
                        onChange={(e) => setAgentFormData(prev => ({
                          ...prev,
                          model: { ...prev.model!, model_name: e.target.value }
                        }))}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateAgentOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreateAgent}
            disabled={createAgentMutation.isPending || !agentFormData.name || !agentFormData.description}
          >
            {createAgentMutation.isPending ? 'Creating...' : 'Create Agent'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Agents;
