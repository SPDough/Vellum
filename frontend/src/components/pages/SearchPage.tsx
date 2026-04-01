'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  InputAdornment,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import {
  Search as SearchIcon,
  TableChart,
  AccountTree,
  Analytics,
  FilterList,
  OpenInNew,
} from '@mui/icons-material';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const dataResults = [
  { name: 'Sandbox Export Status', type: 'Dataset', description: 'Recent data sandbox exports and processing state', path: '/data-sandbox' },
  { name: 'Source Activity Overview', type: 'Table', description: 'Latest source ingestion and refresh details', path: '/data-sources' },
  { name: 'Reconciliation Exception Feed', type: 'Stream', description: 'Operational exception records and review queue', path: '/reconciliation' },
];

const workflowResults = [
  { name: 'Trade Settlement Workflow', type: 'Workflow', description: 'Automated settlement execution and validation path', path: '/workflow-executor' },
  { name: 'Exception Handling Rules', type: 'Rules', description: 'Rules and branching logic for exception triage', path: '/rules' },
  { name: 'Custodian LangGraph Flow', type: 'AI Flow', description: 'AI-assisted orchestration and operational reasoning graph', path: '/custodian-langgraph' },
];

const ontologyResults = [
  { name: 'Financial Instrument', type: 'FIBO Class', description: 'Core classification for securities and derivatives', path: '/knowledge-graph' },
  { name: 'Market Participant', type: 'Graph Entity', description: 'Operational entities and role relationships', path: '/knowledge-graph' },
  { name: 'Risk Measure', type: 'Ontology Property', description: 'Risk quantification concepts linked to operational data', path: '/knowledge-graph' },
];

const recentSearchSuggestions = ['workflow exceptions', 'sandbox export status', 'graph sync', 'rules coverage'];
const filterChips = ['Data', 'Workflows', 'Knowledge', 'Exceptions'];

const SearchPage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const currentQuery = searchParams.get('q') || '';

  const [searchQuery, setSearchQuery] = useState(currentQuery);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    setSearchQuery(currentQuery);
  }, [currentQuery]);

  const normalizedQuery = currentQuery.trim().toLowerCase();

  const filteredDataResults = useMemo(() => {
    if (!normalizedQuery) return dataResults;
    return dataResults.filter((result) =>
      `${result.name} ${result.type} ${result.description}`.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  const filteredWorkflowResults = useMemo(() => {
    if (!normalizedQuery) return workflowResults;
    return workflowResults.filter((result) =>
      `${result.name} ${result.type} ${result.description}`.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  const filteredOntologyResults = useMemo(() => {
    if (!normalizedQuery) return ontologyResults;
    return ontologyResults.filter((result) =>
      `${result.name} ${result.type} ${result.description}`.toLowerCase().includes(normalizedQuery)
    );
  }, [normalizedQuery]);

  const totalResults = filteredDataResults.length + filteredWorkflowResults.length + filteredOntologyResults.length;

  const handleSearch = (value?: string) => {
    const query = (value ?? searchQuery).trim();
    const nextUrl = query ? `/search?q=${encodeURIComponent(query)}` : '/search';
    router.push(nextUrl);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
        Global Search
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Search across data, workflows, rules, and knowledge systems from one place.
      </Typography>

      <Card sx={{ mb: 4, borderRadius: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, mb: 2, flexDirection: { xs: 'column', sm: 'row' } }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Search workflows, sandbox records, graph entities, and more..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
            <Button variant="contained" onClick={() => handleSearch()} sx={{ minWidth: 120 }}>
              Search
            </Button>
          </Box>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
            <Chip label="Advanced Filters" icon={<FilterList />} variant="outlined" />
            {filterChips.map((chip) => (
              <Chip key={chip} label={chip} size="small" variant="outlined" />
            ))}
          </Box>

          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {recentSearchSuggestions.map((item) => (
              <Chip key={item} label={`Recent: ${item}`} size="small" onClick={() => handleSearch(item)} />
            ))}
          </Box>
        </CardContent>
      </Card>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {currentQuery ? `Results for “${currentQuery}”` : 'Browse search domains'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {totalResults} results across platform domains
        </Typography>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label={`Data (${filteredDataResults.length})`} icon={<TableChart />} iconPosition="start" />
          <Tab label={`Workflows (${filteredWorkflowResults.length})`} icon={<AccountTree />} iconPosition="start" />
          <Tab label={`Knowledge (${filteredOntologyResults.length})`} icon={<Analytics />} iconPosition="start" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Data Results
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 2 }}>
          {filteredDataResults.map((result) => (
            <Card key={result.name} sx={{ borderRadius: 3 }}>
              <CardContent>
                <Typography variant="h6">{result.name}</Typography>
                <Chip label={result.type} size="small" sx={{ mb: 1 }} />
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {result.description}
                </Typography>
                <Button size="small" endIcon={<OpenInNew />} onClick={() => router.push(result.path)}>
                  Open
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Typography variant="h6" gutterBottom>
          Workflow Results
        </Typography>
        <List>
          {filteredWorkflowResults.map((result) => (
            <ListItem key={result.name} divider secondaryAction={<Button size="small" onClick={() => router.push(result.path)}>Open</Button>}>
              <ListItemIcon>
                <AccountTree />
              </ListItemIcon>
              <ListItemText
                primary={result.name}
                secondary={
                  <Box>
                    <Chip label={result.type} size="small" sx={{ mr: 1 }} />
                    {result.description}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Typography variant="h6" gutterBottom>
          Knowledge Results
        </Typography>
        <List>
          {filteredOntologyResults.map((result) => (
            <ListItem key={result.name} divider secondaryAction={<Button size="small" onClick={() => router.push(result.path)}>Open</Button>}>
              <ListItemIcon>
                <Analytics />
              </ListItemIcon>
              <ListItemText
                primary={result.name}
                secondary={
                  <Box>
                    <Chip label={result.type} size="small" sx={{ mr: 1 }} />
                    {result.description}
                  </Box>
                }
              />
            </ListItem>
          ))}
        </List>
      </TabPanel>
    </Container>
  );
};

export default SearchPage;
