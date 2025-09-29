"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  Tabs,
  Tab,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Paper,
  Divider,
  Switch,
  FormControlLabel,
  Slider,
  Autocomplete,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Collapse,
  AlertTitle,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Edit,
  Delete,
  Add,
  Refresh,
  Info,
  ExpandMore,
  Timeline,
  AccountTree,
  Psychology,
  Code,
  Settings,
  Tune,
  Build,
  Visibility,
  VisibilityOff,
  Save,
  Cancel,
  CheckCircle,
  Error,
  Warning,
  Help,
  Download,
  Upload,
  ContentCopy,
  Preview,
  Schema,
  DataObject,
  Functions,
  Storage,
  Api,
  Webhook,
  Schedule,
  Event,
  Person,
  Group,
  Security,
  Speed,
  Memory,
  Storage as StorageIcon,
  NetworkCheck,
  CloudQueue,
  LocalOffer,
  TrendingUp,
  Assessment,
  Analytics,
  Dashboard,
  Monitor,
  BugReport,
  CodeOff,
  DataUsage,
  DeveloperMode,
  IntegrationInstructions,
  Link,
  Hub,
  Router,
  SwitchRight,
  CompareArrows,
  Transform,
  FilterList,
  Sort,
  Merge,
  Split,
  CallSplit,
  CallMerge,
  Timeline as TimelineIcon,
  Schedule as ScheduleIcon,
  Notifications,
  Email,
  Sms,
  Chat,
  Phone,
  VideoCall,
  LocationOn,
  AccessTime,
  Timer,
  TimerOff,
  Timer10,
  Timer3,
  HourglassEmpty,
  HourglassFull,
  HourglassBottom,
  HourglassTop,
  AccessAlarm,
  Alarm,
  AlarmAdd,
  AlarmOff,
  AlarmOn,
  Snooze,
  WatchLater,
  Update,
  Sync,
  SyncDisabled,
  SyncProblem,
  Cached,
  CloudSync,
  CloudDownload,
  CloudUpload,
  CloudOff,
  CloudDone,
  CloudQueue,
  Cloud,
  WbCloudy,
  Opacity,
  Brightness1,
  Brightness2,
  Brightness3,
  Brightness4,
  Brightness5,
  Brightness6,
  Brightness7,
  BrightnessAuto,
  BrightnessHigh,
  BrightnessLow,
  BrightnessMedium,
  Contrast,
  Adjust,
  AutoFixHigh,
  AutoFixNormal,
  AutoFixOff,
  AutoFixStandard,
  AutoStories,
  AutoAwesome,
  AutoAwesomeMotion,
  AutoDelete,
  AutoMode,
  AutoGraph,
  AutoFix,
  AutoRenew,
} from '@mui/icons-material';
import { workflowService } from '../../services/workflowService';

interface WorkflowConfigurationProps {
  workflowId?: string;
  workflowType?: 'langchain' | 'langgraph';
}

interface WorkflowNode {
  id: string;
  type: string;
  name: string;
  description?: string;
  config: Record<string, any>;
  position: { x: number; y: number };
  inputs: WorkflowPort[];
  outputs: WorkflowPort[];
}

interface WorkflowPort {
  id: string;
  name: string;
  dataType: string;
  required: boolean;
  description?: string;
  defaultValue?: any;
}

interface WorkflowParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'select' | 'array' | 'object';
  value: any;
  description?: string;
  required: boolean;
  options?: string[];
  min?: number;
  max?: number;
  step?: number;
  validation?: {
    pattern?: string;
    minLength?: number;
    maxLength?: number;
    custom?: string;
  };
}

interface WorkflowExecutionSettings {
  maxConcurrentExecutions: number;
  executionTimeoutMinutes: number;
  retryPolicy: {
    maxAttempts: number;
    backoffStrategy: 'linear' | 'exponential' | 'fixed';
    delaySeconds: number;
    maxDelaySeconds?: number;
  };
  notificationSettings: {
    onSuccess: boolean;
    onFailure: boolean;
    onLongRunning: boolean;
    recipients: string[];
    channels: ('email' | 'slack' | 'webhook')[];
  };
  performanceSettings: {
    enableCaching: boolean;
    cacheTimeoutSeconds: number;
    enableParallelProcessing: boolean;
    maxParallelNodes: number;
    enableOptimization: boolean;
  };
  securitySettings: {
    enableEncryption: boolean;
    encryptionKey?: string;
    enableAuditLogging: boolean;
    restrictAccess: boolean;
    allowedUsers: string[];
  };
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`workflow-config-tabpanel-${index}`}
      aria-labelledby={`workflow-config-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const WorkflowConfiguration: React.FC<WorkflowConfigurationProps> = ({
  workflowId,
  workflowType = 'langchain',
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Workflow data
  const [workflow, setWorkflow] = useState<any>(null);
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [parameters, setParameters] = useState<WorkflowParameter[]>([]);
  const [executionSettings, setExecutionSettings] = useState<WorkflowExecutionSettings>({
    maxConcurrentExecutions: 5,
    executionTimeoutMinutes: 30,
    retryPolicy: {
      maxAttempts: 3,
      backoffStrategy: 'exponential',
      delaySeconds: 5,
      maxDelaySeconds: 300,
    },
    notificationSettings: {
      onSuccess: true,
      onFailure: true,
      onLongRunning: false,
      recipients: [],
      channels: ['email'],
    },
    performanceSettings: {
      enableCaching: true,
      cacheTimeoutSeconds: 3600,
      enableParallelProcessing: false,
      maxParallelNodes: 3,
      enableOptimization: true,
    },
    securitySettings: {
      enableEncryption: false,
      enableAuditLogging: true,
      restrictAccess: false,
      allowedUsers: [],
    },
  });

  // UI state
  const [editMode, setEditMode] = useState(false);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [nodeConfigDialogOpen, setNodeConfigDialogOpen] = useState(false);
  const [parameterDialogOpen, setParameterDialogOpen] = useState(false);
  const [editingParameter, setEditingParameter] = useState<WorkflowParameter | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

  useEffect(() => {
    if (workflowId) {
      loadWorkflowConfiguration();
    } else {
      setLoading(false);
    }
  }, [workflowId, workflowType]);

  const loadWorkflowConfiguration = async () => {
    try {
      setLoading(true);
      let workflowData;
      
      if (workflowType === 'langchain') {
        workflowData = await workflowService.getLangchainWorkflowInfo(workflowId!);
      } else {
        workflowData = await workflowService.getLanggraphWorkflowInfo(workflowId!);
      }
      
      setWorkflow(workflowData);
      
      // Parse nodes from workflow data
      if (workflowData.nodes) {
        setNodes(workflowData.nodes);
      }
      
      // Parse parameters from workflow data
      if (workflowData.parameters) {
        setParameters(workflowData.parameters);
      }
      
      // Parse execution settings
      if (workflowData.execution_settings) {
        setExecutionSettings(workflowData.execution_settings);
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to load workflow configuration');
      console.error('Error loading workflow configuration:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfiguration = async () => {
    try {
      const updatedWorkflow = {
        ...workflow,
        nodes,
        parameters,
        execution_settings: executionSettings,
      };

      if (workflowType === 'langchain') {
        await workflowService.updateLangchainWorkflowConfiguration(workflowId!, updatedWorkflow);
      } else {
        await workflowService.updateLanggraphWorkflowConfiguration(workflowId!, updatedWorkflow);
      }

      setSuccessMessage('Workflow configuration saved successfully');
      setEditMode(false);
      await loadWorkflowConfiguration();
    } catch (err) {
      setError('Failed to save workflow configuration');
      console.error('Error saving workflow configuration:', err);
    }
  };

  const handleAddNode = () => {
    const newNode: WorkflowNode = {
      id: `node_${Date.now()}`,
      type: 'ACTION',
      name: 'New Node',
      description: '',
      config: {},
      position: { x: 0, y: 0 },
      inputs: [],
      outputs: [],
    };
    setNodes([...nodes, newNode]);
    setSelectedNode(newNode);
    setNodeConfigDialogOpen(true);
  };

  const handleAddParameter = () => {
    const newParameter: WorkflowParameter = {
      name: '',
      type: 'string',
      value: '',
      description: '',
      required: false,
    };
    setEditingParameter(newParameter);
    setParameterDialogOpen(true);
  };

  const handleSaveParameter = () => {
    if (!editingParameter) return;

    if (editingParameter.name.trim() === '') {
      setError('Parameter name is required');
      return;
    }

    const existingIndex = parameters.findIndex(p => p.name === editingParameter.name);
    if (existingIndex >= 0 && !editingParameter.name.startsWith('temp_')) {
      // Update existing parameter
      const updatedParameters = [...parameters];
      updatedParameters[existingIndex] = editingParameter;
      setParameters(updatedParameters);
    } else {
      // Add new parameter
      setParameters([...parameters, editingParameter]);
    }

    setParameterDialogOpen(false);
    setEditingParameter(null);
  };

  const handleDeleteParameter = (parameterName: string) => {
    setParameters(parameters.filter(p => p.name !== parameterName));
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes(nodes.filter(n => n.id !== nodeId));
  };

  const getNodeTypeIcon = (type: string) => {
    switch (type) {
      case 'LLM_CALL':
        return <Psychology />;
      case 'API_CALL':
        return <Api />;
      case 'DATA_RETRIEVAL':
        return <Storage />;
      case 'RULES_ENGINE':
        return <Code />;
      case 'HUMAN_REVIEW':
        return <Person />;
      case 'DECISION':
        return <CompareArrows />;
      case 'TRANSFORM':
        return <Transform />;
      case 'FILTER':
        return <FilterList />;
      case 'AGGREGATE':
        return <Merge />;
      case 'START':
        return <PlayArrow />;
      case 'END':
        return <Stop />;
      default:
        return <Code />;
    }
  };

  const getNodeTypeColor = (type: string) => {
    switch (type) {
      case 'LLM_CALL':
        return 'primary';
      case 'API_CALL':
        return 'secondary';
      case 'DATA_RETRIEVAL':
        return 'success';
      case 'RULES_ENGINE':
        return 'warning';
      case 'HUMAN_REVIEW':
        return 'info';
      case 'DECISION':
        return 'error';
      default:
        return 'default';
    }
  };

  const renderParameterValue = (parameter: WorkflowParameter) => {
    switch (parameter.type) {
      case 'boolean':
        return (
          <Switch
            checked={Boolean(parameter.value)}
            onChange={(e) => {
              const updatedParameters = parameters.map(p =>
                p.name === parameter.name ? { ...p, value: e.target.checked } : p
              );
              setParameters(updatedParameters);
            }}
            disabled={!editMode}
          />
        );
      case 'number':
        return (
          <TextField
            type="number"
            value={parameter.value || ''}
            onChange={(e) => {
              const updatedParameters = parameters.map(p =>
                p.name === parameter.name ? { ...p, value: Number(e.target.value) } : p
              );
              setParameters(updatedParameters);
            }}
            disabled={!editMode}
            size="small"
            fullWidth
          />
        );
      case 'select':
        return (
          <Select
            value={parameter.value || ''}
            onChange={(e) => {
              const updatedParameters = parameters.map(p =>
                p.name === parameter.name ? { ...p, value: e.target.value } : p
              );
              setParameters(updatedParameters);
            }}
            disabled={!editMode}
            size="small"
            fullWidth
          >
            {parameter.options?.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
        );
      case 'array':
        return (
          <TextField
            value={Array.isArray(parameter.value) ? parameter.value.join(', ') : ''}
            onChange={(e) => {
              const updatedParameters = parameters.map(p =>
                p.name === parameter.name ? { ...p, value: e.target.value.split(',').map(s => s.trim()) } : p
              );
              setParameters(updatedParameters);
            }}
            disabled={!editMode}
            size="small"
            fullWidth
            placeholder="Comma-separated values"
          />
        );
      case 'object':
        return (
          <TextField
            multiline
            rows={3}
            value={typeof parameter.value === 'object' ? JSON.stringify(parameter.value, null, 2) : ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                const updatedParameters = parameters.map(p =>
                  p.name === parameter.name ? { ...p, value: parsed } : p
                );
                setParameters(updatedParameters);
              } catch {
                // Invalid JSON, ignore
              }
            }}
            disabled={!editMode}
            size="small"
            fullWidth
            placeholder="JSON object"
          />
        );
      default:
        return (
          <TextField
            value={parameter.value || ''}
            onChange={(e) => {
              const updatedParameters = parameters.map(p =>
                p.name === parameter.name ? { ...p, value: e.target.value } : p
              );
              setParameters(updatedParameters);
            }}
            disabled={!editMode}
            size="small"
            fullWidth
          />
        );
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!workflowId) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          Please select a workflow to configure. No workflow ID provided.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1">
            Workflow Configuration
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {workflowType === 'langchain' ? 'LangChain' : 'LangGraph'} Workflow: {workflow?.name || workflowId}
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadWorkflowConfiguration}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          {editMode ? (
            <>
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={() => setEditMode(false)}
                sx={{ mr: 2 }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleSaveConfiguration}
              >
                Save
              </Button>
            </>
          ) : (
            <Button
              variant="contained"
              startIcon={<Edit />}
              onClick={() => setEditMode(true)}
            >
              Edit Configuration
            </Button>
          )}
        </Box>
      </Box>

      {workflow && (
        <Paper sx={{ width: '100%', mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={(_, newValue) => setTabValue(newValue)}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab
              label={
                <Badge badgeContent={nodes.length} color="primary">
                  Nodes
                </Badge>
              }
              icon={<AccountTree />}
            />
            <Tab
              label={
                <Badge badgeContent={parameters.length} color="secondary">
                  Parameters
                </Badge>
              }
              icon={<Tune />}
            />
            <Tab
              label="Execution Settings"
              icon={<Settings />}
            />
            <Tab
              label="Performance"
              icon={<Speed />}
            />
            <Tab
              label="Security"
              icon={<Security />}
            />
            <Tab
              label="Preview"
              icon={<Preview />}
            />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Workflow Nodes</Typography>
              {editMode && (
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={handleAddNode}
                >
                  Add Node
                </Button>
              )}
            </Box>
            
            <Grid container spacing={2}>
              {nodes.map((node) => (
                <Grid item xs={12} md={6} lg={4} key={node.id}>
                  <Card sx={{ border: '1px solid', borderColor: 'divider' }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getNodeTypeIcon(node.type)}
                          <Typography variant="h6" component="h3">
                            {node.name}
                          </Typography>
                          <Chip 
                            label={node.type} 
                            color={getNodeTypeColor(node.type) as any}
                            size="small"
                          />
                        </Box>
                        {editMode && (
                          <Box>
                            <Tooltip title="Edit Node">
                              <IconButton
                                size="small"
                                onClick={() => {
                                  setSelectedNode(node);
                                  setNodeConfigDialogOpen(true);
                                }}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Node">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteNode(node.id)}
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        )}
                      </Box>

                      {node.description && (
                        <Typography variant="body2" color="text.secondary" mb={1}>
                          {node.description}
                        </Typography>
                      )}

                      <Box display="flex" gap={1} flexWrap="wrap">
                        <Chip 
                          label={`${node.inputs.length} inputs`}
                          variant="outlined"
                          size="small"
                        />
                        <Chip 
                          label={`${node.outputs.length} outputs`}
                          variant="outlined"
                          size="small"
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {nodes.length === 0 && (
              <Alert severity="info">
                No nodes configured. {editMode && 'Add nodes to get started!'}
              </Alert>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Workflow Parameters</Typography>
              {editMode && (
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={handleAddParameter}
                >
                  Add Parameter
                </Button>
              )}
            </Box>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Value</TableCell>
                    <TableCell>Required</TableCell>
                    <TableCell>Description</TableCell>
                    {editMode && <TableCell>Actions</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parameters.map((parameter) => (
                    <TableRow key={parameter.name}>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {parameter.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={parameter.type} 
                          size="small"
                          color={parameter.required ? 'error' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        {renderParameterValue(parameter)}
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={parameter.required ? 'Yes' : 'No'}
                          color={parameter.required ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {parameter.description || '-'}
                        </Typography>
                      </TableCell>
                      {editMode && (
                        <TableCell>
                          <IconButton
                            size="small"
                            onClick={() => {
                              setEditingParameter(parameter);
                              setParameterDialogOpen(true);
                            }}
                          >
                            <Edit />
                          </IconButton>
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteParameter(parameter.name)}
                          >
                            <Delete />
                          </IconButton>
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {parameters.length === 0 && (
              <Alert severity="info">
                No parameters configured. {editMode && 'Add parameters to customize workflow behavior!'}
              </Alert>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" mb={2}>Execution Settings</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  label="Max Concurrent Executions"
                  type="number"
                  value={executionSettings.maxConcurrentExecutions}
                  onChange={(e) => setExecutionSettings({
                    ...executionSettings,
                    maxConcurrentExecutions: Number(e.target.value)
                  })}
                  disabled={!editMode}
                  fullWidth
                  margin="normal"
                  inputProps={{ min: 1, max: 100 }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  label="Execution Timeout (minutes)"
                  type="number"
                  value={executionSettings.executionTimeoutMinutes}
                  onChange={(e) => setExecutionSettings({
                    ...executionSettings,
                    executionTimeoutMinutes: Number(e.target.value)
                  })}
                  disabled={!editMode}
                  fullWidth
                  margin="normal"
                  inputProps={{ min: 1, max: 1440 }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle1" mb={1}>Retry Policy</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Max Attempts"
                      type="number"
                      value={executionSettings.retryPolicy.maxAttempts}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        retryPolicy: {
                          ...executionSettings.retryPolicy,
                          maxAttempts: Number(e.target.value)
                        }
                      })}
                      disabled={!editMode}
                      fullWidth
                      inputProps={{ min: 0, max: 10 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Backoff Strategy</InputLabel>
                      <Select
                        value={executionSettings.retryPolicy.backoffStrategy}
                        onChange={(e) => setExecutionSettings({
                          ...executionSettings,
                          retryPolicy: {
                            ...executionSettings.retryPolicy,
                            backoffStrategy: e.target.value as 'linear' | 'exponential' | 'fixed'
                          }
                        })}
                        disabled={!editMode}
                      >
                        <MenuItem value="linear">Linear</MenuItem>
                        <MenuItem value="exponential">Exponential</MenuItem>
                        <MenuItem value="fixed">Fixed</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Delay (seconds)"
                      type="number"
                      value={executionSettings.retryPolicy.delaySeconds}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        retryPolicy: {
                          ...executionSettings.retryPolicy,
                          delaySeconds: Number(e.target.value)
                        }
                      })}
                      disabled={!editMode}
                      fullWidth
                      inputProps={{ min: 1, max: 3600 }}
                    />
                  </Grid>
                </Grid>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle1" mb={1}>Notification Settings</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={executionSettings.notificationSettings.onSuccess}
                          onChange={(e) => setExecutionSettings({
                            ...executionSettings,
                            notificationSettings: {
                              ...executionSettings.notificationSettings,
                              onSuccess: e.target.checked
                            }
                          })}
                          disabled={!editMode}
                        />
                      }
                      label="Notify on Success"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={executionSettings.notificationSettings.onFailure}
                          onChange={(e) => setExecutionSettings({
                            ...executionSettings,
                            notificationSettings: {
                              ...executionSettings.notificationSettings,
                              onFailure: e.target.checked
                            }
                          })}
                          disabled={!editMode}
                        />
                      }
                      label="Notify on Failure"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" mb={2}>Performance Settings</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.performanceSettings.enableCaching}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        performanceSettings: {
                          ...executionSettings.performanceSettings,
                          enableCaching: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Enable Caching"
                />
                {executionSettings.performanceSettings.enableCaching && (
                  <TextField
                    label="Cache Timeout (seconds)"
                    type="number"
                    value={executionSettings.performanceSettings.cacheTimeoutSeconds}
                    onChange={(e) => setExecutionSettings({
                      ...executionSettings,
                      performanceSettings: {
                        ...executionSettings.performanceSettings,
                        cacheTimeoutSeconds: Number(e.target.value)
                      }
                    })}
                    disabled={!editMode}
                    fullWidth
                    margin="normal"
                    inputProps={{ min: 60, max: 86400 }}
                  />
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.performanceSettings.enableParallelProcessing}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        performanceSettings: {
                          ...executionSettings.performanceSettings,
                          enableParallelProcessing: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Enable Parallel Processing"
                />
                {executionSettings.performanceSettings.enableParallelProcessing && (
                  <TextField
                    label="Max Parallel Nodes"
                    type="number"
                    value={executionSettings.performanceSettings.maxParallelNodes}
                    onChange={(e) => setExecutionSettings({
                      ...executionSettings,
                      performanceSettings: {
                        ...executionSettings.performanceSettings,
                        maxParallelNodes: Number(e.target.value)
                      }
                    })}
                    disabled={!editMode}
                    fullWidth
                    margin="normal"
                    inputProps={{ min: 2, max: 20 }}
                  />
                )}
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.performanceSettings.enableOptimization}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        performanceSettings: {
                          ...executionSettings.performanceSettings,
                          enableOptimization: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Enable Performance Optimization"
                />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Typography variant="h6" mb={2}>Security Settings</Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.securitySettings.enableEncryption}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        securitySettings: {
                          ...executionSettings.securitySettings,
                          enableEncryption: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Enable Data Encryption"
                />
                {executionSettings.securitySettings.enableEncryption && (
                  <TextField
                    label="Encryption Key"
                    type="password"
                    value={executionSettings.securitySettings.encryptionKey || ''}
                    onChange={(e) => setExecutionSettings({
                      ...executionSettings,
                      securitySettings: {
                        ...executionSettings.securitySettings,
                        encryptionKey: e.target.value
                      }
                    })}
                    disabled={!editMode}
                    fullWidth
                    margin="normal"
                    helperText="Leave empty to use system default"
                  />
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.securitySettings.enableAuditLogging}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        securitySettings: {
                          ...executionSettings.securitySettings,
                          enableAuditLogging: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Enable Audit Logging"
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={executionSettings.securitySettings.restrictAccess}
                      onChange={(e) => setExecutionSettings({
                        ...executionSettings,
                        securitySettings: {
                          ...executionSettings.securitySettings,
                          restrictAccess: e.target.checked
                        }
                      })}
                      disabled={!editMode}
                    />
                  }
                  label="Restrict Access"
                />
                {executionSettings.securitySettings.restrictAccess && (
                  <Autocomplete
                    multiple
                    options={[]}
                    freeSolo
                    value={executionSettings.securitySettings.allowedUsers}
                    onChange={(_, newValue) => setExecutionSettings({
                      ...executionSettings,
                      securitySettings: {
                        ...executionSettings.securitySettings,
                        allowedUsers: newValue
                      }
                    })}
                    disabled={!editMode}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Allowed Users"
                        placeholder="Add user email or ID"
                        margin="normal"
                      />
                    )}
                  />
                )}
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={5}>
            <Typography variant="h6" mb={2}>Configuration Preview</Typography>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Workflow Overview</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Name</Typography>
                    <Typography variant="body1">{workflow.name || 'Unnamed Workflow'}</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Type</Typography>
                    <Chip 
                      label={workflowType === 'langchain' ? 'LangChain' : 'LangGraph'} 
                      color="primary"
                      size="small"
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Nodes</Typography>
                    <Typography variant="body1">{nodes.length} nodes configured</Typography>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="body2" color="text.secondary">Parameters</Typography>
                    <Typography variant="body1">{parameters.length} parameters configured</Typography>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography variant="subtitle1">Configuration JSON</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TextField
                  multiline
                  rows={20}
                  value={JSON.stringify({
                    workflow: {
                      id: workflowId,
                      name: workflow.name,
                      type: workflowType,
                      nodes,
                      parameters,
                      execution_settings: executionSettings,
                    }
                  }, null, 2)}
                  fullWidth
                  variant="outlined"
                  InputProps={{
                    readOnly: true,
                  }}
                />
              </AccordionDetails>
            </Accordion>

            <Box mt={2}>
              <Button
                variant="outlined"
                startIcon={<Download />}
                onClick={() => {
                  const configData = {
                    workflow: {
                      id: workflowId,
                      name: workflow.name,
                      type: workflowType,
                      nodes,
                      parameters,
                      execution_settings: executionSettings,
                    }
                  };
                  const blob = new Blob([JSON.stringify(configData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${workflow.name || 'workflow'}_configuration.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                Export Configuration
              </Button>
            </Box>
          </TabPanel>
        </Paper>
      )}

      {/* Parameter Dialog */}
      <Dialog open={parameterDialogOpen} onClose={() => setParameterDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingParameter?.name ? 'Edit Parameter' : 'Add Parameter'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Parameter Name"
                value={editingParameter?.name || ''}
                onChange={(e) => setEditingParameter(editingParameter ? {
                  ...editingParameter,
                  name: e.target.value
                } : null)}
                fullWidth
                margin="normal"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select
                  value={editingParameter?.type || 'string'}
                  onChange={(e) => setEditingParameter(editingParameter ? {
                    ...editingParameter,
                    type: e.target.value as WorkflowParameter['type']
                  } : null)}
                >
                  <MenuItem value="string">String</MenuItem>
                  <MenuItem value="number">Number</MenuItem>
                  <MenuItem value="boolean">Boolean</MenuItem>
                  <MenuItem value="select">Select</MenuItem>
                  <MenuItem value="array">Array</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Description"
                value={editingParameter?.description || ''}
                onChange={(e) => setEditingParameter(editingParameter ? {
                  ...editingParameter,
                  description: e.target.value
                } : null)}
                fullWidth
                margin="normal"
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={editingParameter?.required || false}
                    onChange={(e) => setEditingParameter(editingParameter ? {
                      ...editingParameter,
                      required: e.target.checked
                    } : null)}
                  />
                }
                label="Required"
              />
            </Grid>
            {editingParameter?.type === 'select' && (
              <Grid item xs={12}>
                <TextField
                  label="Options (comma-separated)"
                  value={editingParameter?.options?.join(', ') || ''}
                  onChange={(e) => setEditingParameter(editingParameter ? {
                    ...editingParameter,
                    options: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                  } : null)}
                  fullWidth
                  margin="normal"
                  helperText="Enter options separated by commas"
                />
              </Grid>
            )}
            <Grid item xs={12}>
              {renderParameterValue(editingParameter || { name: '', type: 'string', value: '', required: false })}
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setParameterDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveParameter} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Node Configuration Dialog */}
      <Dialog open={nodeConfigDialogOpen} onClose={() => setNodeConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedNode?.name ? 'Edit Node' : 'Add Node'}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Node configuration dialog - Implementation needed
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNodeConfigDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbars */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage(null)}
      >
        <Alert severity="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WorkflowConfiguration;
