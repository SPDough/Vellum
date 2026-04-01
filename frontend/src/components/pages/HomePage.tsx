'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Container,
  InputAdornment,
  TextField,
  Typography,
  Chip,
} from '@mui/material';
import {
  Search,
  Dashboard as DashboardIcon,
  AccountTree,
  Storage,
  Psychology,
  ArrowOutward,
} from '@mui/icons-material';

const quickActions = [
  {
    title: 'Dashboard',
    description: 'Real-time platform overview and operational metrics',
    icon: <DashboardIcon />,
    path: '/dashboard',
    emphasis: 'Monitor platform health',
  },
  {
    title: 'Workflows',
    description: 'Manage automation, orchestration, and execution flows',
    icon: <AccountTree />,
    path: '/workflows',
    emphasis: 'Run operations faster',
  },
  {
    title: 'Data Sandbox',
    description: 'Explore records, filters, exports, and source activity',
    icon: <Storage />,
    path: '/data-sandbox',
    emphasis: 'Inspect operational data',
  },
  {
    title: 'Knowledge Graph',
    description: 'Inspect ontology, relationships, and AI-connected context',
    icon: <Psychology />,
    path: '/knowledge-graph',
    emphasis: 'Navigate linked context',
  },
];

const HomePage: React.FC = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = () => {
    const query = searchQuery.trim();
    if (!query) return;

    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }}>
      <Box sx={{ textAlign: 'center', mb: { xs: 6, md: 9 }, mt: { xs: 2, md: 6 } }}>
        <Chip label="Search-first platform experience" color="secondary" variant="outlined" sx={{ mb: 3 }} />
        <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Otomeshon Intelligence Platform
        </Typography>
        <Typography variant="h5" color="text.secondary" sx={{ mb: 5, maxWidth: 900, mx: 'auto' }}>
          Search across workflows, data, rules, and knowledge systems to drive custodian operations faster.
        </Typography>

        <Box sx={{ maxWidth: 720, mx: 'auto', mb: 3 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search workflows, data sources, sandbox records, rules, and more..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 4,
                fontSize: '1.05rem',
                py: 0.5,
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search sx={{ color: 'primary.main' }} />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <Button variant="contained" onClick={handleSearch} sx={{ borderRadius: 3 }}>
                    Search
                  </Button>
                </InputAdornment>
              ),
            }}
          />
        </Box>

        <Typography variant="body1" color="text.secondary">
          Try: “failed workflows”, “settlement exceptions”, “sandbox export”, or “knowledge graph sync”
        </Typography>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' },
          gap: 3,
        }}
      >
        {quickActions.map((action) => (
          <Card
            key={action.title}
            sx={{
              cursor: 'pointer',
              borderRadius: 3,
              '&:hover': {
                boxShadow: 8,
                transform: 'translateY(-2px)',
                transition: 'all 0.2s ease-in-out',
              },
            }}
            onClick={() => router.push(action.path)}
          >
            <CardHeader
              avatar={<Box sx={{ color: 'primary.main', display: 'flex', alignItems: 'center' }}>{action.icon}</Box>}
              title={action.title}
              titleTypographyProps={{ variant: 'h6', fontWeight: 700 }}
              subheader={action.emphasis}
            />
            <CardContent sx={{ pt: 0 }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {action.description}
              </Typography>
              <Button size="small" endIcon={<ArrowOutward />}>
                Open
              </Button>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Container>
  );
};

export default HomePage;
