import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Alert,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayIcon,
  Visibility as ViewIcon,
  Download as ExportIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import { workflowService } from '@/services/workflowService';
import { dataSandboxService } from '@/services/dataSandboxService';
import { WorkflowOutput, DataSource } from '@/types/dataSandbox';

interface WorkflowDataConnectorProps {
  onDataSourceCreated?: (dataSource: DataSource) => void;
}

const WorkflowDataConnector: React.FC<WorkflowDataConnectorProps> = ({ onDataSourceCreated }) => {
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('');
  const [selectedOutputName, setSelectedOutputName] = useState('');
  const [dataSourceName, setDataSourceName] = useState('');
  
  const queryClient = useQueryClient();

  // Fetch workflows
  const { data: workflows } = useQuery(
    'workflows',
    () => workflowService.listWorkflows()
  );

  // Fetch recent workflow outputs
  const { data: workflowOutputs } = useQuery(
    'workflow-outputs',
    () => dataSandboxService.getWorkflowOutputs({ limit: 20 }),
    {
      refetchInterval: 10000,
    }
  );

  // Create data source from workflow
  const createDataSourceMutation = useMutation(
    ({ workflowId, outputName, name }: { workflowId: string; outputName: string; name: string }) =>
      dataSandboxService.createDataSourceFromWorkflow(workflowId, outputName).then(source => ({
        ...source,
        name: name || source.name,
      })),
    {
      onSuccess: (dataSource) => {
        queryClient.invalidateQueries(['data-sources']);
        onDataSourceCreated?.(dataSource);
        setConnectDialogOpen(false);
        resetForm();
      },
    }
  );

  const resetForm = () => {
    setSelectedWorkflowId('');
    setSelectedOutputName('');
    setDataSourceName('');
  };

  const handleConnect = () => {
    if (selectedWorkflowId && selectedOutputName) {
      createDataSourceMutation.mutate({
        workflowId: selectedWorkflowId,
        outputName: selectedOutputName,
        name: dataSourceName,
      });
    }
  };

  const handleViewOutput = (output: WorkflowOutput) => {
    // Navigate to data sandbox with this specific output
    console.log('View output:', output);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getOutputPreview = (data: any) => {
    if (Array.isArray(data)) {
      return `Array (${data.length} items)`;
    } else if (typeof data === 'object' && data !== null) {
      const keys = Object.keys(data);
      return `Object (${keys.length} keys: ${keys.slice(0, 3).join(', ')}${keys.length > 3 ? '...' : ''})`;
    } else {
      return String(data).slice(0, 50) + (String(data).length > 50 ? '...' : '');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Workflow Data Sources
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setConnectDialogOpen(true)}
          sx={{ borderRadius: 2 }}
        >
          Connect Workflow
        </Button>
      </Box>

      {/* Recent Workflow Outputs */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Recent Workflow Outputs
              </Typography>
              
              {workflowOutputs && workflowOutputs.length > 0 ? (
                <List>
                  {workflowOutputs.map((output) => (
                    <ListItem key={output.id} divider>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                            <Typography variant="body1" sx={{ fontWeight: 600 }}>
                              {output.workflowName}
                            </Typography>
                            <Chip 
                              label={output.stepName} 
                              size="small" 
                              color="primary" 
                              variant="outlined"
                            />
                            <Chip 
                              label={output.metadata.status} 
                              size="small" 
                              color={getStatusColor(output.metadata.status) as any}
                            />
                          </Box>
                        }
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {formatTimestamp(output.timestamp)} • Duration: {output.metadata.duration}ms
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }}>
                              Data: {getOutputPreview(output.data)}
                            </Typography>
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <IconButton 
                            size="small" 
                            onClick={() => handleViewOutput(output)}
                          >
                            <ViewIcon />
                          </IconButton>
                          <IconButton size="small">
                            <ExportIcon />
                          </IconButton>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Alert severity="info">
                  No workflow outputs found. Run some workflows to see data here.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Workflow Output Details */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Workflow Integration Guide</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" paragraph>
                To connect workflow outputs to the data sandbox:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="1. Run a workflow that produces data output"
                    secondary="Workflows should return structured data (JSON, CSV, etc.)"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="2. Click 'Connect Workflow' to create a data source"
                    secondary="This will make the workflow output available for querying"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="3. Use the data sandbox to explore and analyze the data"
                    secondary="Apply filters, create visualizations, and export results"
                  />
                </ListItem>
              </List>
            </AccordionDetails>
          </Accordion>
        </Grid>
      </Grid>

      {/* Connect Workflow Dialog */}
      <Dialog open={connectDialogOpen} onClose={() => setConnectDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Connect Workflow Output</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Workflow</InputLabel>
                <Select
                  value={selectedWorkflowId}
                  onChange={(e) => setSelectedWorkflowId(e.target.value)}
                  label="Workflow"
                >
                  {workflows?.map((workflow) => (
                    <MenuItem key={workflow.id} value={workflow.id}>
                      {workflow.name} ({workflow.status})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Output Step Name"
                value={selectedOutputName}
                onChange={(e) => setSelectedOutputName(e.target.value)}
                placeholder="e.g., data_processing, api_fetch, analysis_result"
                helperText="The name of the workflow step that produces the data output"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Data Source Name"
                value={dataSourceName}
                onChange={(e) => setDataSourceName(e.target.value)}
                placeholder="Enter a descriptive name for this data source"
                helperText="This will be the display name in the data sandbox"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConnectDialogOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleConnect}
            disabled={!selectedWorkflowId || !selectedOutputName || createDataSourceMutation.isLoading}
          >
            {createDataSourceMutation.isLoading ? 'Connecting...' : 'Connect'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorkflowDataConnector;