import React, { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from '@mui/material';
import {
  CompareArrows as CompareArrowsIcon,
  Download as DownloadIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';

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

const Reconciliation: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);

  const mockReconciliationRuns = [
    {
      id: 'rec-001',
      runDate: '2024-01-15',
      type: 'OMS → ABOR Position Control',
      status: 'COMPLETED',
      totalRecords: 1250,
      matchedRecords: 1200,
      unmatchedRecords: 50,
      exceptions: 5,
      surface: 'OMS vs ABOR',
      duration: '00:02:45',
    },
    {
      id: 'rec-002',
      runDate: '2024-01-15',
      type: 'IBOR → CBOR Cash Control',
      status: 'IN_PROGRESS',
      totalRecords: 850,
      matchedRecords: 800,
      unmatchedRecords: 30,
      exceptions: 2,
      surface: 'IBOR vs CBOR',
      duration: '00:01:30',
    },
  ];

  const mockExceptions = [
    {
      id: 'exc-001',
      breakType: 'QUANTITY_MISMATCH',
      surface: 'OMS → ABOR',
      security: 'AAPL',
      account: 'Global Equity Fund',
      expectedValue: 10000,
      observedValue: 9950,
      difference: 50,
      severity: 'HIGH',
      status: 'OPEN',
      assignedTo: 'Operations Team',
    },
    {
      id: 'exc-002',
      breakType: 'VALUATION_MISMATCH',
      surface: 'IBOR → ABOR',
      security: 'MSFT',
      account: 'Tech Fund',
      expectedValue: 140.5,
      observedValue: 140.25,
      difference: 0.25,
      severity: 'MEDIUM',
      status: 'INVESTIGATING',
      assignedTo: 'Risk Team',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'success';
      case 'IN_PROGRESS': return 'info';
      case 'FAILED': return 'error';
      default: return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH': return 'error';
      case 'MEDIUM': return 'warning';
      case 'LOW': return 'info';
      default: return 'default';
    }
  };

  const formatNumber = (num: number) => new Intl.NumberFormat('en-US').format(num);
  const calculateMatchRate = (matched: number, total: number) => ((matched / total) * 100).toFixed(1);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <CompareArrowsIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">Cross-stack reconciliation</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 900 }}>
        Vellum compares OMS, IBOR, ABOR, and CBOR views, classifies only the meaningful breaks,
        and routes exceptions into governed workflows with evidence, ownership, and signoff.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Today's control runs</Typography><Typography variant="h5">{mockReconciliationRuns.length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Aggregate match rate</Typography><Typography variant="h5" color="success.main">{calculateMatchRate(mockReconciliationRuns.reduce((s, r) => s + r.matchedRecords, 0), mockReconciliationRuns.reduce((s, r) => s + r.totalRecords, 0))}%</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Open workflow exceptions</Typography><Typography variant="h5" color="warning.main">{mockExceptions.filter((exc) => exc.status === 'OPEN').length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">High-priority breaks</Typography><Typography variant="h5" color="error.main">{mockExceptions.filter((exc) => exc.severity === 'HIGH').length}</Typography></CardContent></Card></Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Button variant="contained" startIcon={<PlayArrowIcon />}>Run control set</Button>
        <Box>
          <IconButton><RefreshIcon /></IconButton>
          <IconButton><DownloadIcon /></IconButton>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Control Runs" />
          <Tab label="Exceptions" />
          <Tab label="Break Taxonomy" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Run Date</TableCell>
                <TableCell>Control Set</TableCell>
                <TableCell>Comparison Surface</TableCell>
                <TableCell align="right">Total Records</TableCell>
                <TableCell align="right">Matched</TableCell>
                <TableCell align="right">Unmatched</TableCell>
                <TableCell align="right">Exceptions</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockReconciliationRuns.map((run) => (
                <TableRow key={run.id} hover>
                  <TableCell>{run.runDate}</TableCell>
                  <TableCell>{run.type}</TableCell>
                  <TableCell>{run.surface}</TableCell>
                  <TableCell align="right">{formatNumber(run.totalRecords)}</TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {formatNumber(run.matchedRecords)}
                      <LinearProgress variant="determinate" value={(run.matchedRecords / run.totalRecords) * 100} sx={{ width: 50, height: 4 }} color="success" />
                    </Box>
                  </TableCell>
                  <TableCell align="right">{formatNumber(run.unmatchedRecords)}</TableCell>
                  <TableCell align="right">
                    {run.exceptions > 0 ? <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><WarningIcon color="warning" fontSize="small" />{run.exceptions}</Box> : <CheckCircleIcon color="success" fontSize="small" />}
                  </TableCell>
                  <TableCell>{run.duration}</TableCell>
                  <TableCell><Chip label={run.status} color={getStatusColor(run.status)} size="small" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Break Type</TableCell>
                <TableCell>Surface</TableCell>
                <TableCell>Security</TableCell>
                <TableCell>Account</TableCell>
                <TableCell>Expected</TableCell>
                <TableCell>Observed</TableCell>
                <TableCell>Difference</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Assigned To</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockExceptions.map((exception) => (
                <TableRow key={exception.id} hover>
                  <TableCell>{exception.breakType.replace('_', ' ')}</TableCell>
                  <TableCell>{exception.surface}</TableCell>
                  <TableCell>{exception.security}</TableCell>
                  <TableCell>{exception.account}</TableCell>
                  <TableCell>{formatNumber(exception.expectedValue)}</TableCell>
                  <TableCell>{formatNumber(exception.observedValue)}</TableCell>
                  <TableCell><Typography color={exception.difference > 0 ? 'error.main' : 'success.main'}>{formatNumber(exception.difference)}</Typography></TableCell>
                  <TableCell><Chip label={exception.severity} color={getSeverityColor(exception.severity)} size="small" /></TableCell>
                  <TableCell><Chip label={exception.status} size="small" /></TableCell>
                  <TableCell>{exception.assignedTo}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Alert severity="info" sx={{ mb: 2 }}>
          Vellum’s operating grammar is built around timing, lifecycle, reference/enrichment, quantity, cash, valuation, corporate-action, missing-record, and signoff/governance mismatches.
        </Alert>
        <Box sx={{ p: 3, bgcolor: 'background.paper', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="h6" sx={{ mb: 1.5 }}>Why this matters</Typography>
          <Typography color="text.secondary">
            The platform should not just say two systems differ. It should identify where the divergence first appears,
            classify what kind of break it is, and route the right workflow response.
          </Typography>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default Reconciliation;
