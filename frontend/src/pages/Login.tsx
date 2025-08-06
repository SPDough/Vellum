import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
} from '@mui/material';
import { useAuthStore } from '@/store';

const Login: React.FC = () => {
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, isAuthenticated } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const from = searchParams?.get('from') || '/';

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push(from);
    }
  }, [isAuthenticated, router, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Mock login - in a real app, you'd call your auth API
      if (credentials.email && credentials.password) {
        const mockUser = {
          id: '1',
          name: credentials.email.split('@')[0],
          email: credentials.email,
          role: 'admin' as const,
          roles: ['admin'],
          groups: ['administrators'],
          avatar: '',
          preferences: {},
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        const mockToken = 'mock-jwt-token';
        
        // Store token in localStorage
        localStorage.setItem('auth_token', mockToken);
        
        login(mockUser, mockToken);
      } else {
        setError('Please enter both email and password');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 50%, #9333ea 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Container maxWidth="sm">
        <Card sx={{ borderRadius: 3, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)' }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Box
                sx={{
                  width: 64,
                  height: 64,
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                  borderRadius: 3,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                  fontWeight: 'bold',
                  fontSize: '2rem',
                  mx: 'auto',
                  mb: 2,
                }}
              >
                O
              </Box>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                Welcome to Otomeshon
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Sign in to your account to continue
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                margin="normal"
                required
                autoFocus
              />
              
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                margin="normal"
                required
              />

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{ 
                  mt: 3, 
                  mb: 2, 
                  py: 1.5,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #9333ea 100%)',
                  },
                }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 2 }}>
              Demo: Use any email and password to sign in
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default Login;
