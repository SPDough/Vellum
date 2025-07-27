import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  LinearProgress,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import {
  CompareArrows as CompareArrowsIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  PlayArrow as PlayArrowIcon,
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
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`reconciliation-tabpanel-${index}`}
      aria-labelledby={`reconciliation-tab-${index}`}
      {...other}
    >
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
      type: 'Daily Position Reconciliation',
      status: 'COMPLETED',
      totalRecords: 1250,
      matchedRecords: 1200,
      unmatchedRecords: 50,
      exceptions: 5,
      custodian: 'State Street',
      duration: '00:02:45',
    },
    {
      id: 'rec-002',
      runDate: '2024-01-15',
      type: 'Transaction Reconciliation',
      status: 'IN_PROGRESS',
      totalRecords: 850,
      matchedRecords: 800,
      unmatchedRecords: 30,
      exceptions: 2,
      custodian: 'BNY Mellon',
      duration: '00:01:30',
    },
  ];

  const mockExceptions = [
    {
      id: 'exc-001',
      type: 'QUANTITY_MISMATCH',
      security: 'AAPL',
      account: 'Global Equity Fund',
      internalQuantity: 10000,
      custodianQuantity: 9950,
      difference: 50,
      severity: 'HIGH',
      status: 'OPEN',
      assignedTo: 'Operations Team',
    },
    {
      id: 'exc-002',
      type: 'PRICE_VARIANCE',
      security: 'MSFT',
      account: 'Tech Fund',
      internalPrice: 140.50,
      custodianPrice: 140.25,
      difference: 0.25,
      severity: 'MEDIUM',
      status: 'INVESTIGATING',
      assignedTo: 'Risk Team',
    },
  ];

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'success';
      case 'IN_PROGRESS':
        return 'info';
      case 'FAILED':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'info';
      default:
        return 'default';
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const calculateMatchRate = (matched: number, total: number) => {
    return ((matched / total) * 100).toFixed(1);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <CompareArrowsIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Reconciliation
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Today's Runs
              </Typography>
              <Typography variant="h5" component="div">
                {mockReconciliationRuns.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Match Rate
              </Typography>
              <Typography variant="h5" component="div" color="success.main">
                {calculateMatchRate(
                  mockReconciliationRuns.reduce((sum, run) => sum + run.matchedRecords, 0),
                  mockReconciliationRuns.reduce((sum, run) => sum + run.totalRecords, 0)
                )}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Open Exceptions
              </Typography>
              <Typography variant="h5" component="div" color="warning.main">
                {mockExceptions.filter(exc => exc.status === 'OPEN').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                High Priority
              </Typography>
              <Typography variant="h5" component="div" color="error.main">
                {mockExceptions.filter(exc => exc.severity === 'HIGH').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          color="primary"
        >
          Run Reconciliation
        </Button>
        <Box>
          <IconButton>
            <RefreshIcon />
          </IconButton>
          <IconButton>
            <DownloadIcon />
          </IconButton>
        </Box>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Reconciliation Runs" />
          <Tab label="Exceptions" />
          <Tab label="FIBO Mapping" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Run Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Custodian</TableCell>
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
                  <TableCell>{run.custodian}</TableCell>
                  <TableCell align="right">{formatNumber(run.totalRecords)}</TableCell>
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {formatNumber(run.matchedRecords)}
                      <LinearProgress
                        variant="determinate"
                        value={(run.matchedRecords / run.totalRecords) * 100}
                        sx={{ width: 50, height: 4 }}
                        color="success"
                      />
                    </Box>
                  </TableCell>
                  <TableCell align="right">{formatNumber(run.unmatchedRecords)}</TableCell>
                  <TableCell align="right">
                    {run.exceptions > 0 ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <WarningIcon color="warning" fontSize="small" />
                        {run.exceptions}
                      </Box>
                    ) : (
                      <CheckCircleIcon color="success" fontSize="small" />
                    )}
                  </TableCell>
                  <TableCell>{run.duration}</TableCell>
                  <TableCell>
                    <Chip 
                      label={run.status} 
                      color={getStatusColor(run.status)} 
                      size="small" 
                    />
                  </TableCell>
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
                <TableCell>Exception Type</TableCell>
                <TableCell>Security</TableCell>
                <TableCell>Account</TableCell>
                <TableCell>Internal Value</TableCell>
                <TableCell>Custodian Value</TableCell>
                <TableCell>Difference</TableCell>
                <TableCell>Severity</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Assigned To</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {mockExceptions.map((exception) => (
                <TableRow key={exception.id} hover>
                  <TableCell>{exception.type.replace('_', ' ')}</TableCell>
                  <TableCell>{exception.security}</TableCell>
                  <TableCell>{exception.account}</TableCell>
                  <TableCell>
                    {exception.type === 'QUANTITY_MISMATCH' 
                      ? formatNumber(exception.internalQuantity!)
                      : `$${exception.internalPrice!.toFixed(2)}`
                    }
                  </TableCell>
                  <TableCell>
                    {exception.type === 'QUANTITY_MISMATCH' 
                      ? formatNumber(exception.custodianQuantity!)
                      : `$${exception.custodianPrice!.toFixed(2)}`
                    }
                  </TableCell>
                  <TableCell>
                    <Typography color={exception.difference > 0 ? 'error.main' : 'success.main'}>
                      {exception.type === 'QUANTITY_MISMATCH' 
                        ? formatNumber(exception.difference)
                        : `$${exception.difference.toFixed(2)}`
                      }
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={exception.severity} 
                      color={getSeverityColor(exception.severity)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={exception.status} size="small" />
                  </TableCell>
                  <TableCell>{exception.assignedTo}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Alert severity="info" sx={{ mb: 2 }}>
          FIBO ontology mapping ensures semantic consistency across custodian data sources.
        </Alert>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="h6" color="textSecondary">
            FIBO Mapping Dashboard
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            This section will display FIBO ontology mappings and semantic reconciliation results.
          </Typography>
          <Button variant="outlined" sx={{ mt: 2 }}>
            Configure FIBO Mappings
          </Button>
        </Box>
      </TabPanel>

      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="body2" color="info.contrastText">
          <strong>Note:</strong> This is a placeholder page for custodian reconciliation management. 
          Future implementation will include automated reconciliation workflows, LangGraph-powered 
          exception resolution, and FIBO ontology compliance validation.
        </Typography>
      </Box>
    </Box>
  );
};

export default Reconciliation;
