import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  AccountTree as WorkflowIcon,
  Rule as RuleIcon,
  SmartToy as AgentIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';

interface WorkflowTemplate {
  workflow_id: string;
  name: string;
  description: string;
  workflow_type: string;
  nodes: any[];
  entry_point: string;
  exit_conditions: any;
}

interface WorkflowExecution {
  execution_id: string;
  workflow_id: string;
  status: string;
  start_time: string;
  end_time?: string;
  total_execution_time_ms: number;
  node_results: any[];
  final_output: any;
  summary: any;
  error_message?: string;
}

interface NodeResult {
  node_id: string;
  node_type: string;
  status: string;
  start_time: string;
  end_time?: string;
  execution_time_ms: number;
  input_data: any;
  output_data: any;
  error_message?: string;
  alerts?: any[];
}

const WorkflowExecutor: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [inputData, setInputData] = useState<string>('{}');
  const [loading, setLoading] = useState(false);
  const [executionDialog, setExecutionDialog] = useState<WorkflowExecution | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflowTemplates();
    loadActiveExecutions();
  }, []);

  const loadWorkflowTemplates = async () => {
    try {
      const response = await fetch('/api/workflow-execution/templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      setError('Failed to load workflow templates');
    }
  };

  const loadActiveExecutions = async () => {
    try {
      const response = await fetch('/api/workflow-execution/executions');
      const data = await response.json();
      setExecutions(data);
    } catch (err) {
      console.error('Failed to load executions:', err);
    }
  };

  const executeWorkflow = async () => {
    if (!selectedTemplate) return;

    setLoading(true);
    setError(null);

    try {
      let parsedInputData;
      try {
        parsedInputData = JSON.parse(inputData);
      } catch {
        throw new Error('Invalid JSON in input data');
      }

      const response = await fetch('/api/workflow-execution/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          workflow_id: selectedTemplate.workflow_id,
          input_data: parsedInputData
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Execution failed');
      }

      const result = await response.json();
      setExecutionDialog(result);
      loadActiveExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed');
    } finally {
      setLoading(false);
    }
  };

  const executeTradeProcessing = async () => {
    setLoading(true);
    setError(null);

    try {
      const sampleTradeData = {
        tradeId: `TRADE_${Date.now()}`,
        tradeType: "EQUITY",
        counterpartyId: "CLIENT_001",
        securityId: "AAPL",
        quantity: 1000,
        price: 150.50,
        tradeValue: 150500.00,
        currency: "USD",
        tradeDate: new Date().toISOString().split('T')[0],
        settlementDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        status: "PENDING",
        portfolio: "PORTFOLIO_001",
        custodyAccount: "CUSTODY_001"
      };

      const portfolioData = {
        portfolioId: "PORTFOLIO_001",
        totalExposure: 5000000.00,
        exposureLimit: 10000000.00,
        concentrationLimit: 1000000.00,
        availableCash: 2000000.00
      };

      const clientData = {
        clientId: "CLIENT_001",
        kycStatus: "APPROVED",
        amlRiskRating: "LOW",
        creditRating: "A"
      };

      const response = await fetch('/api/workflow-execution/execute-trade-processing', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trade_data: sampleTradeData,
          portfolio_data: portfolioData,
          client_data: clientData
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Trade processing failed');
      }

      const result = await response.json();
      setExecutionDialog(result);
      loadActiveExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trade processing failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'running':
        return <CircularProgress size={20} />;
      default:
        return <ScheduleIcon color="warning" />;
    }
  };

  const getNodeTypeIcon = (nodeType: string) => {
    switch (nodeType) {
      case 'RULES_ENGINE':
        return <RuleIcon color="primary" />;
      case 'AGENT':
        return <AgentIcon color="secondary" />;
      case 'DECISION':
        return <TimelineIcon color="info" />;
      default:
        return <WorkflowIcon />;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const renderWorkflowTemplates = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        🔀 Workflow Templates
      </Typography>
      
      <Grid container spacing={3}>
        {templates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.workflow_id}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                border: selectedTemplate?.workflow_id === template.workflow_id ? 2 : 1,
                borderColor: selectedTemplate?.workflow_id === template.workflow_id ? 'primary.main' : 'divider'
              }}
              onClick={() => setSelectedTemplate(template)}
            >
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={1}>
                  <WorkflowIcon color="primary" />
                  <Typography variant="h6">{template.name}</Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {template.description}
                </Typography>
                
                <Box display="flex" gap={1} mb={2}>
                  <Chip size="small" label={template.workflow_type} />
                  <Chip size="small" label={`${template.nodes.length} nodes`} variant="outlined" />
                </Box>
                
                <Typography variant="caption" color="text.secondary">
                  Entry: {template.entry_point}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {selectedTemplate && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Configure Execution: {selectedTemplate.name}
            </Typography>
            
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Workflow Nodes ({selectedTemplate.nodes.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {selectedTemplate.nodes.map((node, index) => (
                    <ListItem key={node.node_id}>
                      <ListItemIcon>
                        {getNodeTypeIcon(node.node_type)}
                      </ListItemIcon>
                      <ListItemText
                        primary={node.name}
                        secondary={`${node.node_type} - ${node.description}`}
                      />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>

            <TextField
              label="Input Data (JSON)"
              multiline
              rows={6}
              fullWidth
              value={inputData}
              onChange={(e) => setInputData(e.target.value)}
              sx={{ mb: 2 }}
              placeholder='{"trade_data": {...}, "portfolio_data": {...}}'
            />

            <Box display="flex" gap={2}>
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={executeWorkflow}
                disabled={loading}
              >
                Execute Workflow
              </Button>
              
              <Button
                variant="outlined"
                startIcon={<PlayIcon />}
                onClick={executeTradeProcessing}
                disabled={loading}
              >
                Execute Sample Trade Processing
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderActiveExecutions = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          ⚡ Active Executions
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadActiveExecutions}
          variant="outlined"
        >
          Refresh
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Workflow</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {executions.map((execution) => (
              <TableRow key={execution.execution_id}>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getStatusIcon(execution.status)}
                    <Typography variant="body2">
                      {execution.status}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {execution.workflow_id}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {new Date(execution.start_time).toLocaleTimeString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDuration(execution.total_execution_time_ms || 0)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <LinearProgress
                      variant="determinate"
                      value={execution.node_results.length > 0 ? (execution.node_results.filter((n: any) => n.status === 'COMPLETED').length / execution.node_results.length) * 100 : 0}
                      sx={{ width: 60 }}
                    />
                    <Typography variant="caption">
                      {execution.node_results.filter((n: any) => n.status === 'COMPLETED').length}/{execution.node_results.length}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => viewExecutionDetails(execution.execution_id)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {executions.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No active workflow executions
        </Alert>
      )}
    </Box>
  );

  const viewExecutionDetails = async (executionId: string) => {
    try {
      const response = await fetch(`/api/workflow-execution/executions/${executionId}`);
      const execution = await response.json();
      setExecutionDialog(execution);
    } catch (err) {
      setError('Failed to load execution details');
    }
  };

  const renderExecutionDialog = () => (
    <Dialog
      open={!!executionDialog}
      onClose={() => setExecutionDialog(null)}
      maxWidth="lg"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          {getStatusIcon(executionDialog?.status || '')}
          <Typography variant="h6">
            Workflow Execution Details
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {executionDialog && (
          <Box>
            <Grid container spacing={2} mb={3}>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Execution ID</Typography>
                <Typography variant="body2" fontFamily="monospace">
                  {executionDialog.execution_id}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Workflow</Typography>
                <Typography variant="body2">
                  {executionDialog.workflow_id}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Status</Typography>
                <Chip label={executionDialog.status} size="small" />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Duration</Typography>
                <Typography variant="body2">
                  {formatDuration(executionDialog.total_execution_time_ms)}
                </Typography>
              </Grid>
            </Grid>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Node Execution Results
            </Typography>

            {executionDialog.node_results.map((node: NodeResult, index: number) => (
              <Accordion key={node.node_id} sx={{ mb: 1 }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    {getNodeTypeIcon(node.node_type)}
                    <Typography fontWeight="medium">{node.node_id}</Typography>
                    <Box ml="auto" display="flex" alignItems="center" gap={1}>
                      {getStatusIcon(node.status)}
                      <Typography variant="body2">
                        {formatDuration(node.execution_time_ms)}
                      </Typography>
                    </Box>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Type: {node.node_type}
                    </Typography>
                    
                    {node.alerts && node.alerts.length > 0 && (
                      <Box mb={2}>
                        <Typography variant="subtitle2" gutterBottom>
                          Alerts ({node.alerts.length})
                        </Typography>
                        {node.alerts.map((alert, i) => (
                          <Alert 
                            key={i} 
                            severity={
                              alert.severity === 'HIGH' ? 'error' :
                              alert.severity === 'MEDIUM' ? 'warning' : 'info'
                            }
                            sx={{ mb: 1 }}
                          >
                            <Typography variant="body2">
                              {alert.message || alert.type}
                            </Typography>
                          </Alert>
                        ))}
                      </Box>
                    )}

                    {node.error_message && (
                      <Alert severity="error" sx={{ mb: 2 }}>
                        {node.error_message}
                      </Alert>
                    )}

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="body2">Output Data</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                          {JSON.stringify(node.output_data, null, 2)}
                        </pre>
                      </AccordionDetails>
                    </Accordion>
                  </Box>
                </AccordionDetails>
              </Accordion>
            ))}

            {executionDialog.summary && (
              <Box mt={3}>
                <Typography variant="h6" gutterBottom>
                  Execution Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={3}>
                    <Typography variant="subtitle2">Success Rate</Typography>
                    <Typography variant="h6" color="primary">
                      {(executionDialog.summary.success_rate * 100).toFixed(1)}%
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="subtitle2">Total Alerts</Typography>
                    <Typography variant="h6" color="warning.main">
                      {executionDialog.summary.total_alerts}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="subtitle2">Completed Nodes</Typography>
                    <Typography variant="h6" color="success.main">
                      {executionDialog.summary.completed_nodes}
                    </Typography>
                  </Grid>
                  <Grid item xs={3}>
                    <Typography variant="subtitle2">Failed Nodes</Typography>
                    <Typography variant="h6" color="error.main">
                      {executionDialog.summary.failed_nodes}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={() => setExecutionDialog(null)}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🏦 Workflow Executor
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Configure and execute custodian banking workflows combining rules engine and AI agents
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && (
        <LinearProgress sx={{ mb: 3 }} />
      )}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Workflow Templates" />
          <Tab label="Active Executions" />
        </Tabs>
      </Box>

      {tabValue === 0 && renderWorkflowTemplates()}
      {tabValue === 1 && renderActiveExecutions()}

      {renderExecutionDialog()}
    </Box>
  );
};

export default WorkflowExecutor;
