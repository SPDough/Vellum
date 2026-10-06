import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Add, Settings } from '@mui/icons-material';
import { workflowService } from '@/services/workflowService';

export default function WorkflowConfigurationTest() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const summary = await workflowService.getAllWorkflowsSummary();
      const allWorkflows = [
        ...summary.langchain_workflows.map((w: any) => ({ ...w, type: 'langchain' })),
        ...summary.langgraph_workflows.map((w: any) => ({ ...w, type: 'langgraph' })),
      ];
      setWorkflows(allWorkflows);
      setError(null);
    } catch (err) {
      setError('Failed to load workflows');
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const createTestWorkflow = async (type: 'langchain' | 'langgraph') => {
    try {
      setCreating(true);

      if (type === 'langchain') {
        await workflowService.createLangchainWorkflow('position_analysis');
      } else {
        await workflowService.createLanggraphWorkflow('fibo_mapping');
      }

      await loadWorkflows();
    } catch (err) {
      setError(`Failed to create ${type} workflow`);
      console.error('Error creating workflow:', err);
    } finally {
      setCreating(false);
    }
  };

  const openConfiguration = (workflow: any) => {
    navigate(`/workflow-configuration?id=${workflow.workflow_id}&type=${workflow.type}`);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" mb={3}>
        Workflow Configuration Test
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box display="flex" gap={2} mb={3}>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => createTestWorkflow('langchain')}
          disabled={creating}
        >
          Create LangChain Workflow
        </Button>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => createTestWorkflow('langgraph')}
          disabled={creating}
        >
          Create LangGraph Workflow
        </Button>
        <Button
          variant="outlined"
          onClick={loadWorkflows}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Grid container spacing={3}>
        {workflows.map((workflow) => (
          <Grid
            key={workflow.workflow_id}
            size={{
              xs: 12,
              md: 6,
              lg: 4
            }}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h3" mb={1}>
                  {workflow.name || workflow.workflow_id?.substring(0, 8) || 'Unnamed Workflow'}
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Type: {workflow.type === 'langchain' ? 'LangChain' : 'LangGraph'}
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  ID: {workflow.workflow_id}
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Settings />}
                  onClick={() => openConfiguration(workflow)}
                  fullWidth
                >
                  Configure
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {workflows.length === 0 && (
        <Alert severity="info">
          No workflows found. Create some workflows to test the configuration screen!
        </Alert>
      )}
    </Box>
  );
}
