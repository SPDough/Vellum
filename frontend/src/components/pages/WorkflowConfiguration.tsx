"use client";

import React, { useEffect, useState } from 'react';
import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  FormControlLabel,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Tooltip,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Autocomplete,
} from '@mui/material';
import {
  AccountTree,
  Add,
  Api,
  Cancel,
  Code,
  CompareArrows,
  Delete,
  Download,
  Edit,
  ExpandMore,
  FilterList,
  Merge,
  Person,
  PlayArrow,
  Preview,
  Psychology,
  Refresh,
  Save,
  Security,
  Settings,
  Speed,
  Storage,
  SyncAlt,
  Transform,
  Tune,
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
    <div role="tabpanel" hidden={value !== index} {...other}>
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

  const [editMode, setEditMode] = useState(false);
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [nodeConfigDialogOpen, setNodeConfigDialogOpen] = useState(false);
  const [parameterDialogOpen, setParameterDialogOpen] = useState(false);
  const [editingParameter, setEditingParameter] = useState<WorkflowParameter | null>(null);

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
      const workflowData = workflowType === 'langchain'
        ? await workflowService.getLangchainWorkflowInfo(workflowId!)
        : await workflowService.getLanggraphWorkflowInfo(workflowId!);

      setWorkflow(workflowData);
      setNodes(workflowData.nodes || []);
      setParameters(workflowData.parameters || []);
      if (workflowData.execution_settings) {
        setExecutionSettings(workflowData.execution_settings);
      }
      setError(null);
    } catch (err) {
      setError('Failed to load workflow configuration');
      console.error(err);
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
      console.error(err);
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
    setEditingParameter({ name: '', type: 'string', value: '', required: false });
    setParameterDialogOpen(true);
  };

  const handleSaveParameter = () => {
    if (!editingParameter || editingParameter.name.trim() === '') {
      setError('Parameter name is required');
      return;
    }
    const existingIndex = parameters.findIndex((p) => p.name === editingParameter.name);
    if (existingIndex >= 0) {
      const updated = [...parameters];
      updated[existingIndex] = editingParameter;
      setParameters(updated);
    } else {
      setParameters([...parameters, editingParameter]);
    }
    setParameterDialogOpen(false);
    setEditingParameter(null);
  };

  const handleDeleteParameter = (parameterName: string) => {
    setParameters(parameters.filter((p) => p.name !== parameterName));
  };

  const handleDeleteNode = (nodeId: string) => {
    setNodes(nodes.filter((n) => n.id !== nodeId));
  };

  const getNodeTypeIcon = (type: string) => {
    switch (type) {
      case 'LLM_CALL': return <Psychology />;
      case 'API_CALL': return <Api />;
      case 'DATA_RETRIEVAL': return <Storage />;
      case 'RULES_ENGINE': return <Code />;
      case 'HUMAN_REVIEW': return <Person />;
      case 'DECISION': return <CompareArrows />;
      case 'TRANSFORM': return <Transform />;
      case 'FILTER': return <FilterList />;
      case 'AGGREGATE': return <Merge />;
      case 'START': return <PlayArrow />;
      default: return <SyncAlt />;
    }
  };

  const renderParameterValue = (parameter: WorkflowParameter) => {
    switch (parameter.type) {
      case 'boolean':
        return (
          <Switch
            checked={Boolean(parameter.value)}
            onChange={(e) => setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: e.target.checked } : p))}
            disabled={!editMode}
          />
        );
      case 'number':
        return (
          <TextField
            type="number"
            value={parameter.value || ''}
            onChange={(e) => setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: Number(e.target.value) } : p))}
            disabled={!editMode}
            size="small"
            fullWidth
          />
        );
      case 'select':
        return (
          <Select
            value={parameter.value || ''}
            onChange={(e) => setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: e.target.value } : p))}
            disabled={!editMode}
            size="small"
            fullWidth
          >
            {parameter.options?.map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
          </Select>
        );
      case 'array':
        return (
          <TextField
            value={Array.isArray(parameter.value) ? parameter.value.join(', ') : ''}
            onChange={(e) => setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: e.target.value.split(',').map((s) => s.trim()) } : p))}
            disabled={!editMode}
            size="small"
            fullWidth
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
                setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: parsed } : p));
              } catch {
                // ignore invalid JSON while typing
              }
            }}
            disabled={!editMode}
            size="small"
            fullWidth
          />
        );
      default:
        return (
          <TextField
            value={parameter.value || ''}
            onChange={(e) => setParameters(parameters.map((p) => p.name === parameter.name ? { ...p, value: e.target.value } : p))}
            disabled={!editMode}
            size="small"
            fullWidth
          />
        );
    }
  };

  if (loading) {
    return <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px"><CircularProgress /></Box>;
  }

  if (!workflowId) {
    return <Box sx={{ p: 3 }}><Alert severity="info">Please select a workflow to configure. No workflow ID provided.</Alert></Box>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4">Workflow Configuration</Typography>
          <Typography variant="body2" color="text.secondary">
            {workflowType === 'langchain' ? 'LangChain' : 'LangGraph'} Workflow: {workflow?.name || workflowId}
          </Typography>
        </Box>
        <Box>
          <Button variant="outlined" startIcon={<Refresh />} onClick={loadWorkflowConfiguration} sx={{ mr: 2 }}>Refresh</Button>
          {editMode ? (
            <>
              <Button variant="outlined" startIcon={<Cancel />} onClick={() => setEditMode(false)} sx={{ mr: 2 }}>Cancel</Button>
              <Button variant="contained" startIcon={<Save />} onClick={handleSaveConfiguration}>Save</Button>
            </>
          ) : (
            <Button variant="contained" startIcon={<Edit />} onClick={() => setEditMode(true)}>Edit Configuration</Button>
          )}
        </Box>
      </Box>

      {workflow && (
        <Paper sx={{ width: '100%', mb: 3 }}>
          <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} indicatorColor="primary" textColor="primary" variant="fullWidth">
            <Tab label={<Badge badgeContent={nodes.length} color="primary">Nodes</Badge>} icon={<AccountTree />} />
            <Tab label={<Badge badgeContent={parameters.length} color="secondary">Parameters</Badge>} icon={<Tune />} />
            <Tab label="Execution Settings" icon={<Settings />} />
            <Tab label="Performance" icon={<Speed />} />
            <Tab label="Security" icon={<Security />} />
            <Tab label="Preview" icon={<Preview />} />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Workflow Nodes</Typography>
              {editMode && <Button variant="contained" startIcon={<Add />} onClick={handleAddNode}>Add Node</Button>}
            </Box>
            <Grid container spacing={2}>
              {nodes.map((node) => (
                <Grid item xs={12} md={6} lg={4} key={node.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getNodeTypeIcon(node.type)}
                          <Typography variant="h6">{node.name}</Typography>
                          <Chip label={node.type} size="small" />
                        </Box>
                        {editMode && (
                          <Box>
                            <Tooltip title="Edit Node"><IconButton size="small" onClick={() => { setSelectedNode(node); setNodeConfigDialogOpen(true); }}><Edit /></IconButton></Tooltip>
                            <Tooltip title="Delete Node"><IconButton size="small" color="error" onClick={() => handleDeleteNode(node.id)}><Delete /></IconButton></Tooltip>
                          </Box>
                        )}
                      </Box>
                      {node.description && <Typography variant="body2" color="text.secondary" mb={1}>{node.description}</Typography>}
                      <Box display="flex" gap={1} flexWrap="wrap">
                        <Chip label={`${node.inputs.length} inputs`} variant="outlined" size="small" />
                        <Chip label={`${node.outputs.length} outputs`} variant="outlined" size="small" />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
            {nodes.length === 0 && <Alert severity="info">No nodes configured. {editMode && 'Add nodes to get started!'}</Alert>}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Workflow Parameters</Typography>
              {editMode && <Button variant="contained" startIcon={<Add />} onClick={handleAddParameter}>Add Parameter</Button>}
            </Box>
            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell><TableCell>Type</TableCell><TableCell>Value</TableCell><TableCell>Required</TableCell><TableCell>Description</TableCell>{editMode && <TableCell>Actions</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {parameters.map((parameter) => (
                    <TableRow key={parameter.name}>
                      <TableCell>{parameter.name}</TableCell>
                      <TableCell><Chip label={parameter.type} size="small" /></TableCell>
                      <TableCell>{renderParameterValue(parameter)}</TableCell>
                      <TableCell><Chip label={parameter.required ? 'Yes' : 'No'} size="small" /></TableCell>
                      <TableCell>{parameter.description || '-'}</TableCell>
                      {editMode && <TableCell><IconButton size="small" onClick={() => { setEditingParameter(parameter); setParameterDialogOpen(true); }}><Edit /></IconButton><IconButton size="small" color="error" onClick={() => handleDeleteParameter(parameter.name)}><Delete /></IconButton></TableCell>}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <Typography variant="h6" mb={2}>Execution Settings</Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}><TextField label="Max Concurrent Executions" type="number" value={executionSettings.maxConcurrentExecutions} onChange={(e) => setExecutionSettings({ ...executionSettings, maxConcurrentExecutions: Number(e.target.value) })} disabled={!editMode} fullWidth margin="normal" /></Grid>
              <Grid item xs={12} md={6}><TextField label="Execution Timeout (minutes)" type="number" value={executionSettings.executionTimeoutMinutes} onChange={(e) => setExecutionSettings({ ...executionSettings, executionTimeoutMinutes: Number(e.target.value) })} disabled={!editMode} fullWidth margin="normal" /></Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <Typography variant="h6" mb={2}>Performance Settings</Typography>
            <FormControlLabel control={<Switch checked={executionSettings.performanceSettings.enableCaching} onChange={(e) => setExecutionSettings({ ...executionSettings, performanceSettings: { ...executionSettings.performanceSettings, enableCaching: e.target.checked } })} disabled={!editMode} />} label="Enable Caching" />
          </TabPanel>

          <TabPanel value={tabValue} index={4}>
            <Typography variant="h6" mb={2}>Security Settings</Typography>
            <FormControlLabel control={<Switch checked={executionSettings.securitySettings.enableAuditLogging} onChange={(e) => setExecutionSettings({ ...executionSettings, securitySettings: { ...executionSettings.securitySettings, enableAuditLogging: e.target.checked } })} disabled={!editMode} />} label="Enable Audit Logging" />
            <Autocomplete
              multiple
              options={[] as string[]}
              freeSolo
              value={executionSettings.securitySettings.allowedUsers}
              onChange={(_, newValue) => setExecutionSettings({ ...executionSettings, securitySettings: { ...executionSettings.securitySettings, allowedUsers: newValue as string[] } })}
              disabled={!editMode}
              renderInput={(params) => <TextField {...params} label="Allowed Users" margin="normal" />}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={5}>
            <Typography variant="h6" mb={2}>Configuration Preview</Typography>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}><Typography variant="subtitle1">Configuration JSON</Typography></AccordionSummary>
              <AccordionDetails>
                <TextField multiline rows={20} value={JSON.stringify({ workflow: { id: workflowId, name: workflow?.name, type: workflowType, nodes, parameters, execution_settings: executionSettings } }, null, 2)} fullWidth InputProps={{ readOnly: true }} />
              </AccordionDetails>
            </Accordion>
            <Box mt={2}>
              <Button variant="outlined" startIcon={<Download />} onClick={() => {
                const configData = { workflow: { id: workflowId, name: workflow?.name, type: workflowType, nodes, parameters, execution_settings: executionSettings } };
                const blob = new Blob([JSON.stringify(configData, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = window.document.createElement('a');
                a.href = url;
                a.download = `${workflow?.name || 'workflow'}_configuration.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}>Export Configuration</Button>
            </Box>
          </TabPanel>
        </Paper>
      )}

      <Dialog open={parameterDialogOpen} onClose={() => setParameterDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingParameter?.name ? 'Edit Parameter' : 'Add Parameter'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}><TextField label="Parameter Name" value={editingParameter?.name || ''} onChange={(e) => setEditingParameter(editingParameter ? { ...editingParameter, name: e.target.value } : null)} fullWidth margin="normal" required /></Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select value={editingParameter?.type || 'string'} onChange={(e) => setEditingParameter(editingParameter ? { ...editingParameter, type: e.target.value as WorkflowParameter['type'] } : null)}>
                  <MenuItem value="string">String</MenuItem>
                  <MenuItem value="number">Number</MenuItem>
                  <MenuItem value="boolean">Boolean</MenuItem>
                  <MenuItem value="select">Select</MenuItem>
                  <MenuItem value="array">Array</MenuItem>
                  <MenuItem value="object">Object</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions><Button onClick={() => setParameterDialogOpen(false)}>Cancel</Button><Button onClick={handleSaveParameter} variant="contained">Save</Button></DialogActions>
      </Dialog>

      <Dialog open={nodeConfigDialogOpen} onClose={() => setNodeConfigDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{selectedNode?.name ? 'Edit Node' : 'Add Node'}</DialogTitle>
        <DialogContent><Typography variant="body2" color="text.secondary">Node configuration dialog - Implementation needed</Typography></DialogContent>
        <DialogActions><Button onClick={() => setNodeConfigDialogOpen(false)}>Cancel</Button><Button variant="contained">Save</Button></DialogActions>
      </Dialog>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}><Alert severity="error" onClose={() => setError(null)}>{error}</Alert></Snackbar>
      <Snackbar open={!!successMessage} autoHideDuration={6000} onClose={() => setSuccessMessage(null)}><Alert severity="success" onClose={() => setSuccessMessage(null)}>{successMessage}</Alert></Snackbar>
    </Box>
  );
};

export default WorkflowConfiguration;
