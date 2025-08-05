import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Security as SecurityIcon,
} from '@mui/icons-material';

interface AuthProvider {
  name: string;
  description: string;
  demo_accounts?: Array<{
    email: string;
    password: string;
    role: string;
  }>;
}

interface AuthConfig {
  simple: AuthProvider;
}

interface AuthProviderSelectorProps {
  onProviderChange: (provider: string) => void;
  currentProvider: string;
}

export const AuthProviderSelector: React.FC<AuthProviderSelectorProps> = ({ 
  onProviderChange: _, 
  currentProvider: __
}) => {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAuthConfig();
  }, []);

  const fetchAuthConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/auth/providers');
      
      if (!response.ok) {
        throw new Error('Failed to fetch auth config');
      }
      
      const config = await response.json();
      setAuthConfig(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load auth providers');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={2}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!authConfig) {
    return null;
  }

  return (
    <Box sx={{ mb: 3 }}>
      <Box display="flex" alignItems="center" gap={1} mb={2}>
        <SecurityIcon />
        <Typography variant="h6">
          Simple Authentication
        </Typography>
        <Chip label="Active" size="small" color="primary" />
      </Box>
      
      <Card sx={{ maxWidth: 400 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {authConfig.simple.name}
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {authConfig.simple.description}
          </Typography>
          
          {authConfig.simple.demo_accounts && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Demo Accounts:
              </Typography>
              {authConfig.simple.demo_accounts.map((account, index) => (
                <Box key={index} sx={{ mb: 1 }}>
                  <Typography variant="body2">
                    <strong>{account.role}:</strong> {account.email} / {account.password}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};