import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Alert,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Paper,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as ExecuteIcon,
  Code as CodeIcon,
  Assessment as AnalysisIcon,
  Security as SecurityIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import MonacoEditor from '@monaco-editor/react';

import { dataSourceService } from '@/services/dataSourceService';

interface DataSourceConfiguration {
  id: string;
  name: string;
  description?: string;
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
}

interface PythonREPLWorkflowProps {
  open: boolean;
  onClose: () => void;
  config?: DataSourceConfiguration | null;
}

interface WorkflowTemplate {
  name: string;
  description: string;
  prompt: string;
  category: string;
}

const PythonREPLWorkflow: React.FC<PythonREPLWorkflowProps> = ({ open, onClose, config }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [workflowPrompt, setWorkflowPrompt] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');
  const [useDockerREPL, setUseDockerREPL] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [replHealth, setReplHealth] = useState<any>(null);

  // Fetch workflow templates
  const { data: templates = {} } = useQuery({
    queryKey: ['workflowTemplates'],
    queryFn: () => fetch('/api/data-workflows/templates').then(res => res.json()),
  });

  // Fetch REPL health status
  const { data: healthData, refetch: refetchHealth } = useQuery({
    queryKey: ['replHealth'],
    queryFn: () => fetch('/api/data-workflows/repl/health').then(res => res.json()),
    enabled: open,
    refetchInterval: 30000, // Check every 30 seconds
  });

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: (data: any) => 
      fetch('/api/data-workflows/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }).then(res => res.json()),
    onSuccess: (result) => {
      setExecutionResult(result);
      setActiveTab(2); // Switch to results tab
    },
  });

  // Direct REPL execution mutation
  const directReplMutation = useMutation({
    mutationFn: (data: any) =>
      fetch('/api/data-workflows/repl/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }).then(res => res.json()),
  });

  useEffect(() => {
    setReplHealth(healthData);
  }, [healthData]);

  const handleTemplateSelect = (templateKey: string) => {
    const template = templates.templates?.[templateKey];
    if (template) {
      setWorkflowPrompt(template.prompt);
      setSelectedTemplate(templateKey);
    }
  };

  const handleExecuteWorkflow = () => {
    if (!config || !workflowPrompt.trim()) return;

    executeMutation.mutate({
      source_config_id: config.id,
      workflow_prompt: workflowPrompt,
      custom_instructions: customInstructions || undefined,
      use_docker_repl: useDockerREPL,
    });
  };

  const handleDirectREPLExecution = (code: string) => {
    directReplMutation.mutate({
      code,
      timeout_seconds: 30,
    });
  };

  const renderHealthStatus = () => {
    if (!replHealth) return null;

    const isHealthy = replHealth.status === 'healthy';
    const color = isHealthy ? 'success' : 'error';

    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <SecurityIcon />
              Docker Python REPL Status
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={replHealth.status}
                color={color}
                icon={isHealthy ? <SecurityIcon /> : undefined}
              />
              <IconButton onClick={() => refetchHealth()} size="small">
                <RefreshIcon />
              </IconButton>
            </Box>
          </Box>

          {isHealthy && replHealth.capabilities && (
            <Grid container spacing={2}>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <SpeedIcon color="primary" />
                  <Typography variant="caption" display="block">
                    Max Execution: {replHealth.capabilities.max_execution_time_seconds}s
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <MemoryIcon color="primary" />
                  <Typography variant="caption" display="block">
                    Max Memory: {replHealth.capabilities.max_memory_mb}MB
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <CodeIcon color="primary" />
                  <Typography variant="caption" display="block">
                    Active: {replHealth.active_executions?.active_count || 0}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <SecurityIcon color="primary" />
                  <Typography variant="caption" display="block">
                    Sandboxed
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          )}

          {!isHealthy && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              Docker REPL service is not available. Some features may be limited.
            </Alert>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderWorkflowBuilder = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Data Source Info */}
      {config && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Data Source: {config.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Chip label={config.data_source_type.replace('_', ' ')} size="small" />
              {config.description && (
                <Typography variant="body2" color="text.secondary">
                  {config.description}
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Workflow Templates */}
      {templates.templates && (
        <Accordion>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">Workflow Templates</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {Object.entries(templates.templates).map(([key, template]: [string, any]) => (
                <Grid item xs={12} md={6} key={key}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      border: selectedTemplate === key ? 2 : 1,
                      borderColor: selectedTemplate === key ? 'primary.main' : 'divider',
                    }}
                    onClick={() => handleTemplateSelect(key)}
                  >
                    <CardContent>
                      <Typography variant="subtitle1" gutterBottom>
                        {template.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {template.description}
                      </Typography>
                      <Chip label={template.category} size="small" />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </AccordionDetails>
        </Accordion>
      )}

      {/* Workflow Configuration */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Workflow Instructions
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={6}
            placeholder="Describe what you want to analyze or calculate..."
            value={workflowPrompt}
            onChange={(e) => setWorkflowPrompt(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Custom Instructions (Optional)"
            placeholder="Additional instructions for data processing..."
            value={customInstructions}
            onChange={(e) => setCustomInstructions(e.target.value)}
            sx={{ mb: 2 }}
          />

          <FormControlLabel
            control={
              <Switch
                checked={useDockerREPL}
                onChange={(e) => setUseDockerREPL(e.target.checked)}
              />
            }
            label="Use Secure Docker Python REPL (Recommended)"
          />
        </CardContent>
      </Card>

      {/* Execution Controls */}
      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          startIcon={<ExecuteIcon />}
          onClick={handleExecuteWorkflow}
          disabled={!config || !workflowPrompt.trim() || executeMutation.isPending}
        >
          {executeMutation.isPending ? 'Executing...' : 'Execute Workflow'}
        </Button>
      </Box>
    </Box>
  );

  const renderDirectREPL = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Alert severity="info">
        Direct REPL execution allows you to run Python code directly in the secure container.
        This is useful for testing and debugging.
      </Alert>

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Python Code Editor
          </Typography>
          <Paper sx={{ border: 1, borderColor: 'divider' }}>
            <MonacoEditor
              height="300px"
              language="python"
              theme="vs-light"
              value={`# Example: Calculate statistics
import pandas as pd
import numpy as np

# Sample data
data = {
    'values': [1, 2, 3, 4, 5, 10, 15, 20],
    'categories': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B']
}

df = pd.DataFrame(data)
print("Dataset:")
print(df)

# Calculate statistics
mean_val = df['values'].mean()
std_val = df['values'].std()

print(f"\\nMean: {mean_val:.2f}")
print(f"Standard Deviation: {std_val:.2f}")

# Group by category
grouped = df.groupby('categories')['values'].agg(['mean', 'count'])
print("\\nGrouped Statistics:")
print(grouped)`}
              onChange={(value) => {
                // Store the code for execution
                (window as any).currentREPLCode = value;
              }}
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
                fontSize: 14,
              }}
            />
          </Paper>
          
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<ExecuteIcon />}
              onClick={() => {
                const code = (window as any).currentREPLCode || '';
                if (code.trim()) {
                  handleDirectREPLExecution(code);
                }
              }}
              disabled={directReplMutation.isPending}
            >
              {directReplMutation.isPending ? 'Executing...' : 'Execute Code'}
            </Button>
          </Box>

          {directReplMutation.data && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Execution Result
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                  {directReplMutation.data.success 
                    ? directReplMutation.data.result 
                    : `Error: ${directReplMutation.data.error}`}
                </pre>
              </Paper>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );

  const renderResults = () => {
    if (!executionResult) {
      return (
        <Alert severity="info">
          No execution results yet. Run a workflow to see results here.
        </Alert>
      );
    }

    const { success, workflow_results, execution_time_seconds, execution_method } = executionResult;

    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* Execution Summary */}
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Chip
                label={success ? 'Success' : 'Failed'}
                color={success ? 'success' : 'error'}
              />
              <Chip label={execution_method || 'langchain'} variant="outlined" />
              <Typography variant="body2" color="text.secondary">
                Executed in {execution_time_seconds?.toFixed(2)}s
              </Typography>
            </Box>
          </CardContent>
        </Card>

        {/* Results */}
        {success && workflow_results && (
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Results
              </Typography>
              
              {workflow_results.agent_response && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>
                    Agent Response
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {workflow_results.agent_response}
                    </Typography>
                  </Paper>
                </Box>
              )}

              {workflow_results.intermediate_steps && workflow_results.intermediate_steps.length > 0 && (
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="subtitle1">
                      Execution Steps ({workflow_results.intermediate_steps.length})
                    </Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {workflow_results.intermediate_steps.map((step: any, index: number) => (
                        <Paper key={index} sx={{ p: 2 }}>
                          <Typography variant="caption" color="text.secondary">
                            Step {index + 1}
                          </Typography>
                          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: '0.875rem' }}>
                            {JSON.stringify(step, null, 2)}
                          </pre>
                        </Paper>
                      ))}
                    </Box>
                  </AccordionDetails>
                </Accordion>
              )}
            </CardContent>
          </Card>
        )}

        {/* Error Display */}
        {!success && (
          <Alert severity="error">
            <Typography variant="subtitle1" gutterBottom>
              Execution Failed
            </Typography>
            <Typography variant="body2">
              {executionResult.error_message}
            </Typography>
          </Alert>
        )}
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalysisIcon />
          Python REPL Workflow
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ width: '100%' }}>
          {renderHealthStatus()}
          
          <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
            <Tab label="Workflow Builder" />
            <Tab label="Direct REPL" />
            <Tab label="Results" />
          </Tabs>

          <Box sx={{ mt: 2 }}>
            {activeTab === 0 && renderWorkflowBuilder()}
            {activeTab === 1 && renderDirectREPL()}
            {activeTab === 2 && renderResults()}
          </Box>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default PythonREPLWorkflow;