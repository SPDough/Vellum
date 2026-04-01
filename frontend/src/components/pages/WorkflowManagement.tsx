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
} from '@mui/icons-material';
import { workflowService } from '../../services/workflowService';

interface WorkflowSummary {
  summary: {
    total_workflows: number;
    langchain_count: number;
    langgraph_count: number;
    standard_count: number;
  };
  langchain_workflows: any[];
  langgraph_workflows: any[];
  standard_workflows: any[];
  templates: {
    langchain: any[];
    langgraph: any[];
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
      id={`workflow-tabpanel-${index}`}
      aria-labelledby={`workflow-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const WorkflowManagement: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [workflowSummary, setWorkflowSummary] = useState<WorkflowSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedWorkflowType, setSelectedWorkflowType] = useState<'langchain' | 'langgraph'>('langchain');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [executionDialogOpen, setExecutionDialogOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState<any>(null);
  const [executionInput, setExecutionInput] = useState('{}');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflowData();
  }, []);

  const loadWorkflowData = async () => {
    try {
      setLoading(true);
      const summary = await workflowService.getAllWorkflowsSummary();
      setWorkflowSummary(summary);
      setError(null);
    } catch (err) {
      setError('Failed to load workflow data');
      console.error('Error loading workflows:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = async () => {
    try {
      if (!selectedTemplate) {
        setError('Please select a template');
        return;
      }

      if (selectedWorkflowType === 'langchain') {
        await workflowService.createLangchainWorkflow(selectedTemplate);
        setSuccessMessage('Langchain workflow created successfully');
      } else {
        await workflowService.createLanggraphWorkflow(selectedTemplate);
        setSuccessMessage('Langgraph workflow created successfully');
      }

      setCreateDialogOpen(false);
      setSelectedTemplate('');
      await loadWorkflowData();
    } catch (err) {
      setError('Failed to create workflow');
      console.error('Error creating workflow:', err);
    }
  };

  const handleExecuteWorkflow = async () => {
    try {
      if (!selectedWorkflow) return;

      let inputData = {};
      try {
        inputData = JSON.parse(executionInput);
      } catch {
        setError('Invalid JSON in execution input');
        return;
      }

      if (selectedWorkflow.workflow_type === 'LANGCHAIN') {
        await workflowService.executeLangchainWorkflow(selectedWorkflow.workflow_id, inputData);
      } else if (selectedWorkflow.workflow_type === 'LANGGRAPH') {
        await workflowService.executeLanggraphWorkflow(selectedWorkflow.workflow_id, inputData);
      }

      setSuccessMessage('Workflow execution started');
      setExecutionDialogOpen(false);
      setExecutionInput('{}');
    } catch (err) {
      setError('Failed to execute workflow');
      console.error('Error executing workflow:', err);
    }
  };

  const getWorkflowTypeIcon = (type: string) => {
    switch (type) {
      case 'LANGCHAIN':
        return <Psychology color="primary" />;
      case 'LANGGRAPH':
        return <AccountTree color="secondary" />;
      default:
        return <Code color="action" />;
    }
  };

  const getWorkflowTypeColor = (type: string) => {
    switch (type) {
      case 'LANGCHAIN':
        return 'primary';
      case 'LANGGRAPH':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const WorkflowCard: React.FC<{ workflow: any; type: string }> = ({ workflow, type }) => (
    <Card sx={{ mb: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getWorkflowTypeIcon(type)}
            <Typography variant="h6" component="h3">
              {workflow.name || workflow.workflow_id?.substring(0, 8) || 'Unnamed Workflow'}
            </Typography>
            <Chip 
              label={type} 
              color={getWorkflowTypeColor(type) as any}
              size="small"
            />
          </Box>
          <Box>
            <Tooltip title="Configure Workflow">
              <IconButton
                color="primary"
                onClick={() => {
                  const workflowType = type === 'LANGCHAIN' ? 'langchain' : 'langgraph';
                  window.location.href = `/workflow-configuration?id=${workflow.workflow_id}&type=${workflowType}`;
                }}
              >
                <Settings />
              </IconButton>
            </Tooltip>
            <Tooltip title="Execute Workflow">
              <IconButton
                color="primary"
                onClick={() => {
                  setSelectedWorkflow({ ...workflow, workflow_type: type });
                  setExecutionDialogOpen(true);
                }}
              >
                <PlayArrow />
              </IconButton>
            </Tooltip>
            <Tooltip title="Workflow Info">
              <IconButton color="info">
                <Info />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {workflow.description && (
          <Typography variant="body2" color="text.secondary" mb={2}>
            {workflow.description}
          </Typography>
        )}

        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip 
            label={workflow.status || 'ACTIVE'} 
            color={workflow.status === 'ACTIVE' ? 'success' : 'default'}
            size="small"
          />
          {workflow.workflow_id && (
            <Chip 
              label={`ID: ${workflow.workflow_id.substring(0, 8)}...`}
              variant="outlined"
              size="small"
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const SummaryCards: React.FC = () => (
    <Grid container spacing={3} mb={3}>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2 }}>
          <Typography variant="h4" color="primary">
            {workflowSummary?.summary.total_workflows || 0}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Workflows
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
          <Typography variant="h4">
            {workflowSummary?.summary.langchain_count || 0}
          </Typography>
          <Typography variant="body2">
            Langchain
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'secondary.light', color: 'secondary.contrastText' }}>
          <Typography variant="h4">
            {workflowSummary?.summary.langgraph_count || 0}
          </Typography>
          <Typography variant="body2">
            Langgraph
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'grey.200' }}>
          <Typography variant="h4">
            {workflowSummary?.summary.standard_count || 0}
          </Typography>
          <Typography variant="body2">
            Standard
          </Typography>
        </Card>
      </Grid>
    </Grid>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Workflow Management
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadWorkflowData}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            Create Workflow
          </Button>
        </Box>
      </Box>

      {workflowSummary && <SummaryCards />}

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
              <Badge badgeContent={workflowSummary?.summary.langchain_count || 0} color="primary">
                Langchain Workflows
              </Badge>
            }
            icon={<Psychology />}
          />
          <Tab
            label={
              <Badge badgeContent={workflowSummary?.summary.langgraph_count || 0} color="secondary">
                Langgraph Workflows
              </Badge>
            }
            icon={<AccountTree />}
          />
          <Tab
            label={
              <Badge badgeContent={workflowSummary?.summary.standard_count || 0} color="default">
                Standard Workflows
              </Badge>
            }
            icon={<Timeline />}
          />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" mb={2}>Langchain Workflows</Typography>
          {workflowSummary?.langchain_workflows.length === 0 ? (
            <Alert severity="info">
              No Langchain workflows found. Create one to get started!
            </Alert>
          ) : (
            workflowSummary?.langchain_workflows.map((workflow, index) => (
              <WorkflowCard key={index} workflow={workflow} type="LANGCHAIN" />
            ))
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" mb={2}>Langgraph Workflows</Typography>
          {workflowSummary?.langgraph_workflows.length === 0 ? (
            <Alert severity="info">
              No Langgraph workflows found. Create one to get started!
            </Alert>
          ) : (
            workflowSummary?.langgraph_workflows.map((workflow, index) => (
              <WorkflowCard key={index} workflow={workflow} type="LANGGRAPH" />
            ))
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" mb={2}>Standard Workflows</Typography>
          {workflowSummary?.standard_workflows.length === 0 ? (
            <Alert severity="info">
              No standard workflows found.
            </Alert>
          ) : (
            workflowSummary?.standard_workflows.map((workflow, index) => (
              <WorkflowCard key={index} workflow={workflow} type="STANDARD" />
            ))
          )}
        </TabPanel>
      </Paper>

      {/* Templates Section */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">Available Templates</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" mb={2}>Langchain Templates</Typography>
              <List>
                {workflowSummary?.templates.langchain.map((template, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={template.name}
                      secondary={template.description}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" mb={2}>Langgraph Templates</Typography>
              <List>
                {workflowSummary?.templates.langgraph.map((template, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={template.class_name}
                      secondary={template.description}
                    />
                  </ListItem>
                ))}
              </List>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Create Workflow Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Workflow</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>Workflow Type</InputLabel>
            <Select
              value={selectedWorkflowType}
              onChange={(e) => setSelectedWorkflowType(e.target.value as 'langchain' | 'langgraph')}
            >
              <MenuItem value="langchain">Langchain</MenuItem>
              <MenuItem value="langgraph">Langgraph</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth margin="normal">
            <InputLabel>Template</InputLabel>
            <Select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
            >
              {selectedWorkflowType === 'langchain' 
                ? workflowSummary?.templates.langchain.map((template) => (
                    <MenuItem key={template.template_id} value={template.template_id}>
                      {template.name}
                    </MenuItem>
                  ))
                : workflowSummary?.templates.langgraph.map((template) => (
                    <MenuItem key={template.node_type} value={template.node_type.toLowerCase().replace('_', '_')}>
                      {template.class_name}
                    </MenuItem>
                  ))
              }
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateWorkflow} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>

      {/* Execution Dialog */}
      <Dialog open={executionDialogOpen} onClose={() => setExecutionDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Execute Workflow</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Workflow: {selectedWorkflow?.name || selectedWorkflow?.workflow_id}
          </Typography>
          <TextField
            label="Input Data (JSON)"
            multiline
            rows={6}
            fullWidth
            value={executionInput}
            onChange={(e) => setExecutionInput(e.target.value)}
            placeholder='{"positions": [...], "trades": [...]}'
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecutionDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleExecuteWorkflow} variant="contained">Execute</Button>
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

export default WorkflowManagement;