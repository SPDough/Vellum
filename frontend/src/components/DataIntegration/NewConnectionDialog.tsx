import React, { useState } from 'react';
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
  Box,
  Typography,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import { DataProviderType } from '@/types/data';
import { mcpServerService } from '@/services/mcpServerService';

interface NewConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

const predefinedProviders = [
  {
    id: 'state-street',
    name: 'State Street Global Services',
    type: DataProviderType.CUSTODIAN,
    description: 'Custody, fund accounting, and administration services',
    logo: '🏦',
    capabilities: ['Positions', 'Transactions', 'Cash Balances', 'Corporate Actions'],
  },
  {
    id: 'bny-mellon',
    name: 'BNY Mellon',
    type: DataProviderType.CUSTODIAN,
    description: 'Global custody and asset servicing',
    logo: '🏛️',
    capabilities: ['Positions', 'Settlements', 'FX Rates', 'Securities Lending'],
  },
  {
    id: 'bloomberg',
    name: 'Bloomberg Market Data',
    type: DataProviderType.MARKET_DATA,
    description: 'Real-time and historical market data',
    logo: '📊',
    capabilities: ['Real-time Prices', 'Historical Data', 'Reference Data', 'News'],
  },
  {
    id: 'refinitiv',
    name: 'Refinitiv Eikon',
    type: DataProviderType.MARKET_DATA,
    description: 'Market data and analytics platform',
    logo: '📈',
    capabilities: ['Market Data', 'Fundamentals', 'Estimates', 'News'],
  },
];

const NewConnectionDialog: React.FC<NewConnectionDialogProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [connectionName, setConnectionName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [authType, setAuthType] = useState('API_KEY');
  const [apiKey, setApiKey] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const steps = ['Select Provider', 'Configure Connection', 'Test Connection'];

  const handleNext = () => {
    if (activeStep === 0 && selectedProvider) {
      const provider = predefinedProviders.find(p => p.id === selectedProvider);
      if (provider) {
        setConnectionName(provider.name);
        setBaseUrl(`https://api.${provider.id.replace('-', '')}.com/mcp`);
      }
    }
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    
    try {
      // Create a temporary server config for testing
      const tempServerData = {
        name: connectionName,
        provider_type: predefinedProviders.find(p => p.id === selectedProvider)?.type || 'OTHER',
        base_url: baseUrl,
        auth_type: authType,
        auth_config: authType === 'API_KEY' ? { api_key: apiKey } : {},
        capabilities: predefinedProviders.find(p => p.id === selectedProvider)?.capabilities || [],
        description: predefinedProviders.find(p => p.id === selectedProvider)?.description
      };

      // Create server first
      const server = await mcpServerService.createServer(tempServerData);
      
      // Then test the connection
      await mcpServerService.testServer(server.id);
      
      // If we get here, connection was successful
      setTestResult('success');
      
      // Clean up the test server (in a real app, you might want to keep it)
      await mcpServerService.deleteServer(server.id);
      
    } catch (error) {
      console.error('Connection test failed:', error);
      setTestResult('error');
    } finally {
      setTesting(false);
    }
  };

  const handleCreate = async () => {
    try {
      const serverData = {
        name: connectionName,
        provider_type: predefinedProviders.find(p => p.id === selectedProvider)?.type || 'OTHER',
        base_url: baseUrl,
        auth_type: authType,
        auth_config: authType === 'API_KEY' ? { api_key: apiKey } : {},
        capabilities: predefinedProviders.find(p => p.id === selectedProvider)?.capabilities || [],
        description: predefinedProviders.find(p => p.id === selectedProvider)?.description
      };

      await mcpServerService.createServer(serverData);
      onSuccess();
    } catch (error) {
      console.error('Failed to create server:', error);
      // Could show error to user here
    }
  };

  const handleReset = () => {
    setActiveStep(0);
    setSelectedProvider('');
    setConnectionName('');
    setBaseUrl('');
    setAuthType('API_KEY');
    setApiKey('');
    setTestResult(null);
  };

  const selectedProviderData = predefinedProviders.find(p => p.id === selectedProvider);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Add New Data Connection
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Connect to a custodian or market data provider via MCP
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Step 0: Select Provider */}
        {activeStep === 0 && (
          <Box>
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
              Choose a data provider to connect to:
            </Typography>
            <Grid container spacing={2}>
              {predefinedProviders.map((provider) => (
                <Grid item xs={12} sm={6} key={provider.id}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedProvider === provider.id ? 2 : 1,
                      borderColor: selectedProvider === provider.id ? 'primary.main' : 'divider',
                      '&:hover': {
                        borderColor: 'primary.main',
                        boxShadow: 2,
                      },
                    }}
                    onClick={() => setSelectedProvider(provider.id)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Typography variant="h4">{provider.logo}</Typography>
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {provider.name}
                          </Typography>
                          <Chip
                            label={provider.type.replace('_', ' ')}
                            size="small"
                            color="primary"
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {provider.description}
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {provider.capabilities.map((capability) => (
                          <Chip
                            key={capability}
                            label={capability}
                            size="small"
                            variant="outlined"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Step 1: Configure Connection */}
        {activeStep === 1 && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {selectedProviderData && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Configuring connection to {selectedProviderData.name}
              </Alert>
            )}

            <TextField
              fullWidth
              label="Connection Name"
              value={connectionName}
              onChange={(e) => setConnectionName(e.target.value)}
              helperText="A friendly name for this connection"
            />

            <TextField
              fullWidth
              label="API Base URL"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              helperText="The base URL for the MCP server endpoint"
            />

            <FormControl fullWidth>
              <InputLabel>Authentication Type</InputLabel>
              <Select
                value={authType}
                onChange={(e) => setAuthType(e.target.value)}
                label="Authentication Type"
              >
                <MenuItem value="API_KEY">API Key</MenuItem>
                <MenuItem value="OAUTH">OAuth 2.0</MenuItem>
                <MenuItem value="CERTIFICATE">Certificate</MenuItem>
                <MenuItem value="BASIC">Basic Auth</MenuItem>
              </Select>
            </FormControl>

            {authType === 'API_KEY' && (
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                helperText="Your API key for authentication"
              />
            )}
          </Box>
        )}

        {/* Step 2: Test Connection */}
        {activeStep === 2 && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Test Your Connection
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              We'll verify that your configuration can successfully connect to the provider
            </Typography>

            {testResult === null && (
              <Button
                variant="contained"
                onClick={handleTestConnection}
                disabled={testing}
                size="large"
                sx={{ mb: 2 }}
              >
                {testing ? 'Testing Connection...' : 'Test Connection'}
              </Button>
            )}

            {testResult === 'success' && (
              <Alert severity="success" sx={{ mb: 2 }}>
                Connection test successful! Ready to create the connection.
              </Alert>
            )}

            {testResult === 'error' && (
              <Alert severity="error" sx={{ mb: 2 }}>
                Connection test failed. Please check your configuration.
              </Alert>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button onClick={onClose}>Cancel</Button>
        
        {activeStep > 0 && (
          <Button onClick={handleBack}>Back</Button>
        )}

        {activeStep < steps.length - 1 ? (
          <Button
            variant="contained"
            onClick={handleNext}
            disabled={activeStep === 0 && !selectedProvider}
          >
            Next
          </Button>
        ) : (
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={testResult !== 'success'}
          >
            Create Connection
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default NewConnectionDialog;