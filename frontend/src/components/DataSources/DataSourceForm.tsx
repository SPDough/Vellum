import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { useMutation } from '@tanstack/react-query';

import { dataSourceService } from '@/services/dataSourceService';

interface DataSourceConfiguration {
  id: string;
  name: string;
  description?: string;
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
  source_config: any;
  processing_config?: any;
  schedule_type: 'MANUAL' | 'INTERVAL' | 'CRON';
  schedule_config?: any;
  output_to_sandbox: boolean;
  output_table_name?: string;
  is_active: boolean;
}

interface DataSourceFormProps {
  open: boolean;
  onClose: () => void;
  config?: DataSourceConfiguration | null;
  onSuccess: () => void;
}

const validationSchema = Yup.object({
  name: Yup.string().required('Name is required').min(3, 'Name must be at least 3 characters'),
  description: Yup.string(),
  data_source_type: Yup.string().required('Data source type is required'),
  schedule_type: Yup.string().required('Schedule type is required'),
  output_table_name: Yup.string().when('output_to_sandbox', {
    is: true,
    then: (schema) => schema.required('Output table name is required when outputting to sandbox'),
  }),
});

const DataSourceForm: React.FC<DataSourceFormProps> = ({ open, onClose, config, onSuccess }) => {
  const [sourceConfigFields, setSourceConfigFields] = useState<Array<{ key: string; value: string }>>([]);
  const [processingConfigFields, setProcessingConfigFields] = useState<Array<{ key: string; value: string }>>([]);
  const [scheduleConfigFields, setScheduleConfigFields] = useState<Array<{ key: string; value: string }>>([]);

  const createMutation = useMutation({
    mutationFn: (data: any) => 
      config 
        ? dataSourceService.updateDataSource(config.id, data)
        : dataSourceService.createDataSource({ ...data, created_by: 'current_user' }),
    onSuccess: () => {
      onSuccess();
    },
  });

  const formik = useFormik({
    initialValues: {
      name: '',
      description: '',
      data_source_type: 'API' as const,
      schedule_type: 'MANUAL' as const,
      output_to_sandbox: true,
      output_table_name: '',
    },
    validationSchema,
    onSubmit: async (values: any) => {
      // Build configuration objects from form fields
      const source_config = sourceConfigFields.reduce((acc, field) => {
        if (field.key && field.value) {
          acc[field.key] = field.value;
        }
        return acc;
      }, {} as any);

      const processing_config = processingConfigFields.reduce((acc, field) => {
        if (field.key && field.value) {
          try {
            acc[field.key] = JSON.parse(field.value);
          } catch {
            acc[field.key] = field.value;
          }
        }
        return acc;
      }, {} as any);

      const schedule_config = scheduleConfigFields.reduce((acc, field) => {
        if (field.key && field.value) {
          try {
            acc[field.key] = JSON.parse(field.value);
          } catch {
            acc[field.key] = field.value;
          }
        }
        return acc;
      }, {} as any);

      const payload = {
        ...values,
        source_config,
        processing_config: Object.keys(processing_config).length > 0 ? processing_config : undefined,
        schedule_config: Object.keys(schedule_config).length > 0 ? schedule_config : undefined,
      };

      await createMutation.mutateAsync(payload);
    },
  });

  // Initialize form when config changes
  useEffect(() => {
    if (config) {
      formik.setValues({
        name: config.name,
        description: config.description || '',
        data_source_type: config.data_source_type,
        schedule_type: config.schedule_type,
        output_to_sandbox: config.output_to_sandbox,
        output_table_name: config.output_table_name || '',
      });

      // Convert config objects to form fields
      setSourceConfigFields(
        Object.entries(config.source_config || {}).map(([key, value]) => ({
          key,
          value: typeof value === 'string' ? value : JSON.stringify(value),
        }))
      );

      setProcessingConfigFields(
        Object.entries(config.processing_config || {}).map(([key, value]) => ({
          key,
          value: typeof value === 'string' ? value : JSON.stringify(value),
        }))
      );

      setScheduleConfigFields(
        Object.entries(config.schedule_config || {}).map(([key, value]) => ({
          key,
          value: typeof value === 'string' ? value : JSON.stringify(value),
        }))
      );
    } else {
      formik.resetForm();
      setSourceConfigFields([]);
      setProcessingConfigFields([]);
      setScheduleConfigFields([]);
    }
  }, [config]);

  const addConfigField = (
    fields: Array<{ key: string; value: string }>,
    setFields: React.Dispatch<React.SetStateAction<Array<{ key: string; value: string }>>>
  ) => {
    setFields([...fields, { key: '', value: '' }]);
  };

  const updateConfigField = (
    index: number,
    field: 'key' | 'value',
    value: string,
    fields: Array<{ key: string; value: string }>,
    setFields: React.Dispatch<React.SetStateAction<Array<{ key: string; value: string }>>>
  ) => {
    const newFields = [...fields];
    newFields[index][field] = value;
    setFields(newFields);
  };

  const removeConfigField = (
    index: number,
    fields: Array<{ key: string; value: string }>,
    setFields: React.Dispatch<React.SetStateAction<Array<{ key: string; value: string }>>>
  ) => {
    const newFields = fields.filter((_, i) => i !== index);
    setFields(newFields);
  };

  const getSourceConfigTemplate = (type: string) => {
    const templates = {
      API: [
        { key: 'url', value: 'https://api.example.com/data' },
        { key: 'method', value: 'GET' },
        { key: 'timeout_seconds', value: '30' },
      ],
      MCP_SERVER: [
        { key: 'server_name', value: 'example-server' },
        { key: 'tool_name', value: 'get_data' },
        { key: 'timeout_seconds', value: '60' },
      ],
      WEB_SCRAPING: [
        { key: 'url', value: 'https://example.com' },
        { key: 'javascript_enabled', value: 'true' },
        { key: 'timeout_seconds', value: '60' },
      ],
    };
    return templates[type as keyof typeof templates] || [];
  };

  const loadTemplate = () => {
    const template = getSourceConfigTemplate(formik.values.data_source_type);
    setSourceConfigFields(template);
  };

  const renderConfigSection = (
    title: string,
    fields: Array<{ key: string; value: string }>,
    setFields: React.Dispatch<React.SetStateAction<Array<{ key: string; value: string }>>>,
    helpText?: string
  ) => (
    <Accordion>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="subtitle1">{title}</Typography>
          {helpText && (
            <Tooltip title={helpText}>
              <HelpIcon fontSize="small" color="action" />
            </Tooltip>
          )}
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {fields.map((field, index) => (
            <Grid container spacing={2} key={index} alignItems="center">
              <Grid item xs={4}>
                <TextField
                  fullWidth
                  label="Key"
                  value={field.key}
                  onChange={(e) => updateConfigField(index, 'key', e.target.value, fields, setFields)}
                  size="small"
                />
              </Grid>
              <Grid item xs={7}>
                <TextField
                  fullWidth
                  label="Value"
                  value={field.value}
                  onChange={(e) => updateConfigField(index, 'value', e.target.value, fields, setFields)}
                  size="small"
                  multiline
                  maxRows={3}
                />
              </Grid>
              <Grid item xs={1}>
                <IconButton
                  size="small"
                  onClick={() => removeConfigField(index, fields, setFields)}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Grid>
            </Grid>
          ))}
          <Button
            startIcon={<AddIcon />}
            onClick={() => addConfigField(fields, setFields)}
            variant="outlined"
            size="small"
            sx={{ alignSelf: 'flex-start' }}
          >
            Add Field
          </Button>
        </Box>
      </AccordionDetails>
    </Accordion>
  );

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {config ? 'Edit Data Source' : 'Create New Data Source'}
      </DialogTitle>
      <form onSubmit={formik.handleSubmit}>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {/* Basic Information */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Basic Information
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Name"
                      {...formik.getFieldProps('name')}
                      error={formik.touched.name && Boolean(formik.errors.name)}
                      helperText={formik.touched.name && formik.errors.name}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Data Source Type</InputLabel>
                      <Select
                        {...formik.getFieldProps('data_source_type')}
                        label="Data Source Type"
                      >
                        <MenuItem value="API">API Endpoint</MenuItem>
                        <MenuItem value="MCP_SERVER">MCP Server</MenuItem>
                        <MenuItem value="WEB_SCRAPING">Web Scraping</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Description"
                      multiline
                      rows={2}
                      {...formik.getFieldProps('description')}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>

            {/* Source Configuration */}
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">
                    Source Configuration
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={loadTemplate}
                  >
                    Load Template
                  </Button>
                </Box>
                {renderConfigSection(
                  'Connection Settings',
                  sourceConfigFields,
                  setSourceConfigFields,
                  'Configure how to connect to your data source'
                )}
              </CardContent>
            </Card>

            {/* Processing Configuration */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Processing (Optional)
                </Typography>
                {renderConfigSection(
                  'Processing Rules',
                  processingConfigFields,
                  setProcessingConfigFields,
                  'Configure how to process and transform the data using Pandas'
                )}
              </CardContent>
            </Card>

            {/* Schedule Configuration */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Schedule Configuration
                </Typography>
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={6}>
                    <FormControl fullWidth>
                      <InputLabel>Schedule Type</InputLabel>
                      <Select
                        {...formik.getFieldProps('schedule_type')}
                        label="Schedule Type"
                      >
                        <MenuItem value="MANUAL">Manual Execution</MenuItem>
                        <MenuItem value="INTERVAL">Interval-based</MenuItem>
                        <MenuItem value="CRON">Cron Expression</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
                {formik.values.schedule_type !== 'MANUAL' && (
                  <Box sx={{ mt: 2 }}>
                    {renderConfigSection(
                      'Schedule Settings',
                      scheduleConfigFields,
                      setScheduleConfigFields,
                      'Configure when and how often to run the data pull'
                    )}
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Output Configuration */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Output Configuration
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={formik.values.output_to_sandbox}
                          onChange={(e) => formik.setFieldValue('output_to_sandbox', e.target.checked)}
                        />
                      }
                      label="Output to Data Sandbox"
                    />
                  </Grid>
                  {formik.values.output_to_sandbox && (
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Output Table Name"
                        {...formik.getFieldProps('output_table_name')}
                        error={formik.touched.output_table_name && Boolean(formik.errors.output_table_name)}
                        helperText={formik.touched.output_table_name && formik.errors.output_table_name}
                      />
                    </Grid>
                  )}
                </Grid>
              </CardContent>
            </Card>

            {createMutation.error && (
              <Alert severity="error">
                Failed to save data source: {createMutation.error.message}
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            disabled={createMutation.isPending}
          >
            {createMutation.isPending ? 'Saving...' : config ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default DataSourceForm;