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
  Tooltip,
  Stepper,
  Step,
  StepLabel,
  StepContent
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Assignment as SOPIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Business as BusinessIcon,
  PersonAdd as PersonAddIcon,
  AccountBalance as TradeIcon,
  TrendingUp as TrendingUpIcon,
  Security as ComplianceIcon,
  Timeline as ProcessIcon
} from '@mui/icons-material';

interface SOPTemplate {
  title: string;
  document_number: string;
  version: string;
  category: string;
  business_area: string;
  process_type: string;
  content: string;
  summary: string;
  steps: SOPStep[];
}

interface SOPStep {
  step_number: number;
  step_title: string;
  step_description: string;
  is_automated?: boolean;
  is_manual?: boolean;
  is_decision_point?: boolean;
  estimated_duration_minutes: number;
  automation_tool?: string;
}

interface SOPExecution {
  id: string;
  sop_document_id: string;
  execution_name: string;
  status: string;
  initiated_by: string;
  assigned_to?: string;
  start_time?: string;
  end_time?: string;
  estimated_duration_minutes?: number;
  actual_duration_minutes?: number;
  current_step_id?: string;
  completion_percentage?: number;
  requires_approval: boolean;
  approval_status?: string;
  created_at: string;
}

interface SOPExecutionSummary {
  execution_id: string;
  sop_title: string;
  status: string;
  total_steps: number;
  completed_steps: number;
  failed_steps: number;
  progress_percentage: number;
  estimated_time_remaining_minutes?: number;
  compliance_status: string;
  risk_alerts: string[];
}

const SOPManager: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [templates, setTemplates] = useState<Record<string, SOPTemplate>>({});
  const [executions, setExecutions] = useState<SOPExecution[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [executionDialog, setExecutionDialog] = useState<SOPExecutionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executionName, setExecutionName] = useState('');
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    loadSOPTemplates();
    loadActiveExecutions();
    loadMetrics();
  }, []);

  const loadSOPTemplates = async () => {
    try {
      const response = await fetch('/api/sop-management/templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      setError('Failed to load SOP templates');
    }
  };

  const loadActiveExecutions = async () => {
    try {
      const response = await fetch('/api/sop-management/executions');
      const data = await response.json();
      setExecutions(data);
    } catch (err) {
      console.error('Failed to load executions:', err);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await fetch('/api/sop-management/metrics');
      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  const createSOPExecution = async (templateId: string) => {
    if (!executionName.trim()) {
      setError('Please enter an execution name');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/sop-management/executions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sop_document_id: templateId,
          execution_name: executionName,
          initiated_by: 'current_user',
          assigned_to: 'current_user'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create execution');
      }

      const execution = await response.json();
      
      // Start the execution
      await startExecution(execution.id);
      
      setExecutionName('');
      loadActiveExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create execution');
    } finally {
      setLoading(false);
    }
  };

  const startExecution = async (executionId: string) => {
    try {
      const response = await fetch(`/api/sop-management/executions/${executionId}/start?started_by=current_user`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Failed to start execution');
      }

      loadActiveExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start execution');
    }
  };

  const executeTradeSettlement = async () => {
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
        settlementDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      };

      const response = await fetch('/api/sop-management/executions/trade-settlement', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          trade_data: sampleTradeData,
          initiated_by: 'current_user'
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to execute trade settlement');
      }

      const result = await response.json();
      loadActiveExecutions();
      
      // Show execution summary
      const summaryResponse = await fetch(`/api/sop-management/executions/${result.id}/summary`);
      const summary = await summaryResponse.json();
      setExecutionDialog(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute trade settlement');
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
      case 'in_progress':
        return <CircularProgress size={20} />;
      case 'requires_approval':
        return <WarningIcon color="warning" />;
      default:
        return <ScheduleIcon color="action" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'trade settlement':
        return <TradeIcon color="primary" />;
      case 'corporate actions':
        return <TrendingUpIcon color="secondary" />;
      case 'client onboarding':
        return <PersonAddIcon color="info" />;
      case 'compliance':
        return <ComplianceIcon color="warning" />;
      default:
        return <ProcessIcon />;
    }
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A';
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const renderSOPTemplates = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          📋 Standard Operating Procedures
        </Typography>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadSOPTemplates}
          variant="outlined"
        >
          Refresh
        </Button>
      </Box>
      
      <Grid container spacing={3}>
        {Object.entries(templates).map(([templateId, template]) => (
          <Grid item xs={12} md={6} lg={4} key={templateId}>
            <Card 
              sx={{ 
                cursor: 'pointer',
                border: selectedTemplate === templateId ? 2 : 1,
                borderColor: selectedTemplate === templateId ? 'primary.main' : 'divider',
                height: '100%'
              }}
              onClick={() => setSelectedTemplate(templateId)}
            >
              <CardContent>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  {getCategoryIcon(template.category)}
                  <Typography variant="h6" component="div">
                    {template.title}
                  </Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {template.summary}
                </Typography>
                
                <Box display="flex" gap={1} mb={2} flexWrap="wrap">
                  <Chip size="small" label={template.category} />
                  <Chip size="small" label={template.process_type} variant="outlined" />
                  <Chip size="small" label={`${template.steps.length} steps`} variant="outlined" />
                </Box>
                
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="caption" color="text.secondary">
                    Est. Duration: {formatDuration(
                      template.steps.reduce((sum, step) => sum + step.estimated_duration_minutes, 0)
                    )}
                  </Typography>
                  <Typography variant="caption" color="primary">
                    {template.document_number}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {selectedTemplate && templates[selectedTemplate] && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Execute SOP: {templates[selectedTemplate].title}
            </Typography>
            
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Procedure Steps ({templates[selectedTemplate].steps.length})</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Stepper orientation="vertical">
                  {templates[selectedTemplate].steps.map((step, index) => (
                    <Step key={step.step_number} active={true}>
                      <StepLabel>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Typography fontWeight="medium">{step.step_title}</Typography>
                          <Box display="flex" gap={1}>
                            {step.is_automated && <Chip size="small" label="Automated" color="success" />}
                            {step.is_manual && <Chip size="small" label="Manual" color="default" />}
                            {step.is_decision_point && <Chip size="small" label="Decision" color="warning" />}
                          </Box>
                        </Box>
                      </StepLabel>
                      <StepContent>
                        <Typography variant="body2" color="text.secondary" paragraph>
                          {step.step_description}
                        </Typography>
                        <Typography variant="caption">
                          Estimated Duration: {formatDuration(step.estimated_duration_minutes)}
                          {step.automation_tool && ` • Tool: ${step.automation_tool}`}
                        </Typography>
                      </StepContent>
                    </Step>
                  ))}
                </Stepper>
              </AccordionDetails>
            </Accordion>

            <TextField
              label="Execution Name"
              fullWidth
              value={executionName}
              onChange={(e) => setExecutionName(e.target.value)}
              sx={{ mb: 2 }}
              placeholder="e.g., Trade Settlement - AAPL-001"
            />

            <Box display="flex" gap={2}>
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={() => createSOPExecution(selectedTemplate)}
                disabled={loading || !executionName.trim()}
              >
                Create & Start Execution
              </Button>
              
              {selectedTemplate === 'TRADE_SETTLEMENT' && (
                <Button
                  variant="outlined"
                  startIcon={<TradeIcon />}
                  onClick={executeTradeSettlement}
                  disabled={loading}
                >
                  Execute Sample Trade Settlement
                </Button>
              )}
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
          ⚡ Active SOP Executions
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
              <TableCell>SOP</TableCell>
              <TableCell>Execution Name</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Est. Duration</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {executions.map((execution) => (
              <TableRow key={execution.id}>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    {getStatusIcon(execution.status)}
                    <Typography variant="body2">
                      {execution.status.replace('_', ' ').toUpperCase()}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="medium">
                    {execution.sop_document_id.replace('_', ' ')}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {execution.execution_name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {execution.start_time ? 
                      new Date(execution.start_time).toLocaleTimeString() : 
                      'Not started'
                    }
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <LinearProgress
                      variant="determinate"
                      value={execution.completion_percentage || 0}
                      sx={{ width: 80 }}
                    />
                    <Typography variant="caption">
                      {(execution.completion_percentage || 0).toFixed(0)}%
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {formatDuration(execution.estimated_duration_minutes)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => viewExecutionDetails(execution.id)}
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
          No active SOP executions
        </Alert>
      )}
    </Box>
  );

  const renderMetrics = () => (
    <Box>
      <Typography variant="h5" gutterBottom>
        📊 SOP Performance Metrics
      </Typography>
      
      {metrics && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="primary">
                  {metrics.metrics.total_active_executions}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Executions
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="success.main">
                  {metrics.metrics.average_completion_time_minutes}m
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Completion Time
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="info.main">
                  {(metrics.metrics.automation_rate * 100).toFixed(0)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Automation Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography variant="h4" color="warning.main">
                  {(metrics.metrics.compliance_rate * 100).toFixed(0)}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Compliance Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );

  const viewExecutionDetails = async (executionId: string) => {
    try {
      const response = await fetch(`/api/sop-management/executions/${executionId}/summary`);
      const summary = await response.json();
      setExecutionDialog(summary);
    } catch (err) {
      setError('Failed to load execution details');
    }
  };

  const renderExecutionDialog = () => (
    <Dialog
      open={!!executionDialog}
      onClose={() => setExecutionDialog(null)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          {getStatusIcon(executionDialog?.status || '')}
          <Typography variant="h6">
            SOP Execution Details
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {executionDialog && (
          <Box>
            <Grid container spacing={2} mb={3}>
              <Grid item xs={6}>
                <Typography variant="subtitle2">SOP Title</Typography>
                <Typography variant="body2">
                  {executionDialog.sop_title}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Status</Typography>
                <Chip label={executionDialog.status} size="small" />
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Progress</Typography>
                <Box display="flex" alignItems="center" gap={1}>
                  <LinearProgress
                    variant="determinate"
                    value={executionDialog.progress_percentage}
                    sx={{ width: 100 }}
                  />
                  <Typography variant="body2">
                    {executionDialog.progress_percentage.toFixed(0)}%
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle2">Compliance Status</Typography>
                <Chip 
                  label={executionDialog.compliance_status} 
                  size="small"
                  color={executionDialog.compliance_status === 'COMPLIANT' ? 'success' : 'error'}
                />
              </Grid>
            </Grid>

            <Typography variant="h6" gutterBottom>
              Execution Summary
            </Typography>
            <Grid container spacing={2} mb={3}>
              <Grid item xs={3}>
                <Typography variant="subtitle2">Total Steps</Typography>
                <Typography variant="h6">{executionDialog.total_steps}</Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2">Completed</Typography>
                <Typography variant="h6" color="success.main">
                  {executionDialog.completed_steps}
                </Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2">Failed</Typography>
                <Typography variant="h6" color="error.main">
                  {executionDialog.failed_steps}
                </Typography>
              </Grid>
              <Grid item xs={3}>
                <Typography variant="subtitle2">Time Remaining</Typography>
                <Typography variant="h6" color="info.main">
                  {formatDuration(executionDialog.estimated_time_remaining_minutes)}
                </Typography>
              </Grid>
            </Grid>

            {executionDialog.risk_alerts.length > 0 && (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Risk Alerts
                </Typography>
                {executionDialog.risk_alerts.map((alert, index) => (
                  <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                    {alert}
                  </Alert>
                ))}
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
        🏦 SOP Management Portal
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Manage and execute standard operating procedures for custodian banking operations
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
          <Tab label="SOP Templates" />
          <Tab label="Active Executions" />
          <Tab label="Metrics" />
        </Tabs>
      </Box>

      {tabValue === 0 && renderSOPTemplates()}
      {tabValue === 1 && renderActiveExecutions()}
      {tabValue === 2 && renderMetrics()}

      {renderExecutionDialog()}
    </Box>
  );
};

export default SOPManager;