import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Paper,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Add as AddIcon,
  PlayArrow as PlayIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  DataObject as DataIcon,
} from '@mui/icons-material';

import {
  custodianLangGraphService,
  CustodianWorkflow,
  CustodianAnalysisRequest,
  CustodianAnalysisResult,
  CustodianConfig,
  CustodianConfigCreate,
  WorkflowStatus,
  WorkflowList,
} from '@/services/custodianLangGraphService';

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
      id={`custodian-tabpanel-${index}`}
      aria-labelledby={`custodian-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const CustodianLangGraph: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [workflows, setWorkflows] = useState<WorkflowList>({ workflows: [], total_count: 0 });
  const [custodians, setCustodians] = useState<CustodianConfig[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>('');
  const [analysisResult, setAnalysisResult] = useState<CustodianAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [createWorkflowDialog, setCreateWorkflowDialog] = useState(false);
  const [addCustodianDialog, setAddCustodianDialog] = useState(false);
  const [analysisDialog, setAnalysisDialog] = useState(false);

  // Form states
  const [newWorkflow, setNewWorkflow] = useState({
    custodianName: '',
    apiKey: '',
  });
  const [newCustodian, setNewCustodian] = useState<CustodianConfigCreate>({
    name: '',
    base_url: '',
    auth_type: 'bearer',
    api_key: '',
  });
  const [analysisRequest, setAnalysisRequest] = useState<CustodianAnalysisRequest>({
    endpoint: '/positions',
    params: {},
    user_question: 'Analyze this custodian data',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [workflowsData, custodiansData] = await Promise.all([
        custodianLangGraphService.listWorkflows(),
        custodianLangGraphService.listCustodians(),
      ]);
      setWorkflows(workflowsData);
      setCustodians(custodiansData);
    } catch (err) {
      setError('Failed to load data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWorkflow = async () => {
    try {
      setLoading(true);
      await custodianLangGraphService.createWorkflow(
        newWorkflow.custodianName,
        newWorkflow.apiKey || undefined
      );
      setCreateWorkflowDialog(false);
      setNewWorkflow({ custodianName: '', apiKey: '' });
      await loadData();
    } catch (err) {
      setError('Failed to create workflow');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCustodian = async () => {
    try {
      setLoading(true);
      await custodianLangGraphService.addCustodianConfig(newCustodian);
      setAddCustodianDialog(false);
      setNewCustodian({ name: '', base_url: '', auth_type: 'bearer', api_key: '' });
      await loadData();
    } catch (err) {
      setError('Failed to add custodian');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteAnalysis = async () => {
    if (!selectedWorkflow) return;

    try {
      setLoading(true);
      const result = await custodianLangGraphService.executeAnalysis(
        selectedWorkflow,
        analysisRequest
      );
      setAnalysisResult(result);
      setAnalysisDialog(false);
    } catch (err) {
      setError('Failed to execute analysis');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorkflow = async (workflowId: string) => {
    try {
      await custodianLangGraphService.deleteWorkflow(workflowId);
      await loadData();
    } catch (err) {
      setError('Failed to delete workflow');
      console.error(err);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Custodian LangGraph Workflows
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Create and manage LangGraph workflows for custodian data analysis
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="custodian tabs">
          <Tab label="Workflows" icon={<AnalyticsIcon />} />
          <Tab label="Custodians" icon={<SettingsIcon />} />
          <Tab label="Analysis Results" icon={<DataIcon />} />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Workflows</Typography>
            <Box>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCreateWorkflowDialog(true)}
                sx={{ mr: 1 }}
              >
                Create Workflow
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadData}
                disabled={loading}
              >
                Refresh
              </Button>
            </Box>
          </Box>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <List>
              {workflows.workflows.map((workflow) => (
                <ListItem key={workflow.workflow_id} divider>
                  <ListItemText
                    primary={`Workflow ${workflow.workflow_id.slice(0, 8)}...`}
                    secondary={`Nodes: ${workflow.node_count} | Status: ${workflow.status}`}
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => {
                        setSelectedWorkflow(workflow.workflow_id);
                        setAnalysisDialog(true);
                      }}
                      sx={{ mr: 1 }}
                    >
                      <PlayIcon />
                    </IconButton>
                    <IconButton
                      edge="end"
                      onClick={() => handleDeleteWorkflow(workflow.workflow_id)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
              {workflows.workflows.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                  No workflows found. Create your first workflow to get started.
                </Typography>
              )}
            </List>
          )}
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Custodian Configurations</Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddCustodianDialog(true)}
            >
              Add Custodian
            </Button>
          </Box>

          <Grid container spacing={2}>
            {custodians.map((custodian) => (
              <Grid item xs={12} md={6} key={custodian.name}>
                <Card>
                  <CardContent>
                    <Typography variant="h6">{custodian.name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {custodian.base_url}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Chip
                        label={custodian.auth_type}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Chip
                        label={custodian.configured ? 'Configured' : 'Not Configured'}
                        color={custodian.configured ? 'success' : 'warning'}
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom>
            Analysis Results
          </Typography>
          {analysisResult ? (
            <Box>
              <Accordion defaultExpanded>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Analysis Summary</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body1" gutterBottom>
                    <strong>Question:</strong> {analysisResult.analysis_results.question}
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    <strong>Answer:</strong>
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                    <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                      {analysisResult.analysis_results.answer}
                    </Typography>
                  </Paper>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Data Summary</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" gutterBottom>
                    <strong>Records:</strong> {analysisResult.data.record_count}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Columns:</strong> {analysisResult.data.columns.join(', ')}
                  </Typography>
                  {analysisResult.data.dataframe_summary && (
                    <Box>
                      <Typography variant="body2" gutterBottom>
                        <strong>Shape:</strong> {analysisResult.data.dataframe_summary.shape.join(' x ')}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Sample Data:</strong>
                      </Typography>
                      <TableContainer component={Paper} sx={{ maxHeight: 200 }}>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              {analysisResult.data.dataframe_summary.columns.map((col) => (
                                <TableCell key={col}>{col}</TableCell>
                              ))}
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {analysisResult.data.dataframe_summary.sample_data.map((row, idx) => (
                              <TableRow key={idx}>
                                {analysisResult.data.dataframe_summary!.columns.map((col) => (
                                  <TableCell key={col}>
                                    {row[col]?.toString() || ''}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">Execution Details</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="body2" gutterBottom>
                    <strong>Status:</strong> {analysisResult.context.status}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Start Time:</strong> {new Date(analysisResult.context.start_time).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>End Time:</strong> {new Date(analysisResult.context.end_time).toLocaleString()}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Endpoint:</strong> {analysisResult.context.endpoint}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">
              No analysis results available. Execute a workflow to see results here.
            </Typography>
          )}
        </TabPanel>
      </Paper>

      {/* Create Workflow Dialog */}
      <Dialog open={createWorkflowDialog} onClose={() => setCreateWorkflowDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Workflow</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Custodian</InputLabel>
            <Select
              value={newWorkflow.custodianName}
              onChange={(e) => setNewWorkflow({ ...newWorkflow, custodianName: e.target.value })}
            >
              {custodians.map((custodian) => (
                <MenuItem key={custodian.name} value={custodian.name}>
                  {custodian.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="API Key (Optional)"
            value={newWorkflow.apiKey}
            onChange={(e) => setNewWorkflow({ ...newWorkflow, apiKey: e.target.value })}
            sx={{ mt: 2 }}
            type="password"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateWorkflowDialog(false)}>Cancel</Button>
          <Button onClick={handleCreateWorkflow} variant="contained" disabled={loading}>
            Create
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Custodian Dialog */}
      <Dialog open={addCustodianDialog} onClose={() => setAddCustodianDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Custodian Configuration</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={newCustodian.name}
            onChange={(e) => setNewCustodian({ ...newCustodian, name: e.target.value })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Base URL"
            value={newCustodian.base_url}
            onChange={(e) => setNewCustodian({ ...newCustodian, base_url: e.target.value })}
            sx={{ mt: 2 }}
          />
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Auth Type</InputLabel>
            <Select
              value={newCustodian.auth_type}
              onChange={(e) => setNewCustodian({ ...newCustodian, auth_type: e.target.value })}
            >
              <MenuItem value="bearer">Bearer Token</MenuItem>
              <MenuItem value="api_key">API Key</MenuItem>
              <MenuItem value="oauth">OAuth</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="API Key"
            value={newCustodian.api_key}
            onChange={(e) => setNewCustodian({ ...newCustodian, api_key: e.target.value })}
            sx={{ mt: 2 }}
            type="password"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddCustodianDialog(false)}>Cancel</Button>
          <Button onClick={handleAddCustodian} variant="contained" disabled={loading}>
            Add
          </Button>
        </DialogActions>
      </Dialog>

      {/* Analysis Dialog */}
      <Dialog open={analysisDialog} onClose={() => setAnalysisDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Execute Analysis</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Endpoint"
            value={analysisRequest.endpoint}
            onChange={(e) => setAnalysisRequest({ ...analysisRequest, endpoint: e.target.value })}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="User Question"
            value={analysisRequest.user_question}
            onChange={(e) => setAnalysisRequest({ ...analysisRequest, user_question: e.target.value })}
            multiline
            rows={3}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="Parameters (JSON)"
            value={JSON.stringify(analysisRequest.params, null, 2)}
            onChange={(e) => {
              try {
                const params = JSON.parse(e.target.value);
                setAnalysisRequest({ ...analysisRequest, params });
              } catch (err) {
                // Invalid JSON, ignore
              }
            }}
            multiline
            rows={3}
            sx={{ mt: 2 }}
            helperText="Enter parameters as JSON object"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialog(false)}>Cancel</Button>
          <Button onClick={handleExecuteAnalysis} variant="contained" disabled={loading}>
            Execute
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CustodianLangGraph;
