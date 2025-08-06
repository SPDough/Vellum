import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Chip,
  TextField,
  Grid,
} from '@mui/material';
import { useMutation } from '@tanstack/react-query';

import { dataSourceService } from '@/services/dataSourceService';
import type { DataSourceConfiguration, DataSourceTestResponse } from '@/services/dataSourceService';

interface DataSourceTestDialogProps {
  open: boolean;
  onClose: () => void;
  config: DataSourceConfiguration;
}

const DataSourceTestDialog: React.FC<DataSourceTestDialogProps> = ({ open, onClose, config }) => {
  const [sampleSize, setSampleSize] = useState(10);
  const [testResult, setTestResult] = useState<DataSourceTestResponse | null>(null);

  const testMutation = useMutation({
    mutationFn: () =>
      dataSourceService.testDataSource({
        data_source_type: config.data_source_type,
        source_config: config.source_config,
        processing_config: config.processing_config,
        sample_size: sampleSize,
      }),
    onSuccess: (result: any) => {
      setTestResult(result);
    },
  });

  const handleTest = () => {
    setTestResult(null);
    testMutation.mutate();
  };

  const handleClose = () => {
    setTestResult(null);
    testMutation.reset();
    onClose();
  };

  const renderSampleData = (data: Array<Record<string, any>>) => {
    if (!data || data.length === 0) {
      return <Typography>No sample data available</Typography>;
    }

    const columns = Object.keys(data[0]);

    return (
      <TableContainer component={Paper} sx={{ maxHeight: 400, mt: 2 }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell key={column} sx={{ fontWeight: 600 }}>
                  {column}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, index) => (
              <TableRow key={index}>
                {columns.map((column) => (
                  <TableCell key={column}>
                    {typeof row[column] === 'object'
                      ? JSON.stringify(row[column])
                      : String(row[column] || '')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderDataSchema = (schema: Record<string, string>) => {
    if (!schema || Object.keys(schema).length === 0) {
      return null;
    }

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Data Schema
        </Typography>
        <Grid container spacing={1}>
          {Object.entries(schema).map(([column, type]) => (
            <Grid item key={column}>
              <Chip
                label={`${column}: ${type}`}
                variant="outlined"
                size="small"
              />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        Test Data Source: {config.name}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* Test Configuration */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Test Configuration
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Sample Size"
                  type="number"
                  value={sampleSize}
                  onChange={(e) => setSampleSize(Math.max(1, parseInt(e.target.value) || 10))}
                  inputProps={{ min: 1, max: 100 }}
                  size="small"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <Chip
                  label={config.data_source_type.replace('_', ' ')}
                  color="primary"
                  variant="outlined"
                />
              </Grid>
            </Grid>
          </Box>

          {/* Source Configuration Preview */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Source Configuration
            </Typography>
            <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
              <pre style={{ margin: 0, fontSize: '0.875rem', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(config.source_config, null, 2)}
              </pre>
            </Paper>
          </Box>

          {/* Test Results */}
          {testMutation.isPending && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={24} />
              <Typography>Testing connection and retrieving sample data...</Typography>
            </Box>
          )}

          {testMutation.error && (
            <Alert severity="error">
              Test failed: {testMutation.error.message}
            </Alert>
          )}

          {testResult && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Test Results
              </Typography>
              
              {testResult.success ? (
                <Alert severity="success" sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', flex: 1, flexDirection: 'column', gap: 1 }}>
                    <Typography variant="body2">
                      ✅ Connection successful!
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                      <Typography variant="caption">
                        Records: {testResult.record_count || 0}
                      </Typography>
                      <Typography variant="caption">
                        Duration: {testResult.execution_time_seconds?.toFixed(2)}s
                      </Typography>
                    </Box>
                  </Box>
                </Alert>
              ) : (
                <Alert severity="error" sx={{ mb: 2 }}>
                  <Typography variant="body2">
                    ❌ Test failed: {testResult.error_message}
                  </Typography>
                </Alert>
              )}

              {testResult.success && testResult.sample_data && (
                <Box>
                  <Typography variant="subtitle1" gutterBottom>
                    Sample Data ({testResult.sample_data.length} of {testResult.record_count} records)
                  </Typography>
                  {renderSampleData(testResult.sample_data)}
                </Box>
              )}

              {testResult.success && testResult.data_schema && (
                renderDataSchema(testResult.data_schema)
              )}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Close</Button>
        <Button
          variant="contained"
          onClick={handleTest}
          disabled={testMutation.isPending}
        >
          {testMutation.isPending ? 'Testing...' : 'Run Test'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DataSourceTestDialog;