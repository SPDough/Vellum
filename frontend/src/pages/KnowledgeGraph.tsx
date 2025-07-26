import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  AccountTree as GraphIcon,
  Analytics as AnalyticsIcon,
  Search as SearchIcon,
  Add as AddIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from 'react-query';

import GraphVisualization from '@/components/KnowledgeGraph/GraphVisualization';
import { 
  knowledgeGraphService, 
  GraphStatistics, 
  GraphNode, 
  CentralityAnalysis,
  EntityCreateRequest
} from '@/services/knowledgeGraphService';

interface KnowledgeGraphProps {}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [createEntityOpen, setCreateEntityOpen] = useState(false);
  const [newEntityType, setNewEntityType] = useState('Account');
  const [entityProperties, setEntityProperties] = useState<Record<string, string>>({});
  
  const queryClient = useQueryClient();

  // Fetch graph statistics
  const { data: statistics } = useQuery<GraphStatistics>(
    'graph-statistics',
    () => knowledgeGraphService.getStatistics(),
    {
      refetchInterval: 30000,
    }
  );

  // Fetch centrality analysis
  const { data: centralityData } = useQuery<CentralityAnalysis>(
    'graph-centrality',
    () => knowledgeGraphService.getCentralityAnalysis({ limit: 10 }),
    {
      refetchInterval: 60000,
    }
  );

  // Create entity mutation
  const createEntityMutation = useMutation(
    (request: EntityCreateRequest) => knowledgeGraphService.createEntity(request),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('graph-statistics');
        queryClient.invalidateQueries('graph-visualization');
        setCreateEntityOpen(false);
        setEntityProperties({});
      },
    }
  );

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleNodeClick = (_node: GraphNode) => {
  };

  const handleCreateEntity = () => {
    const properties = {
      ...entityProperties,
      id: entityProperties.id || `${newEntityType.toLowerCase()}_${Date.now()}`,
    };

    createEntityMutation.mutate({
      entity_type: newEntityType,
      properties,
    });
  };

  const entityTypes = [
    'Account', 'Security', 'Trade', 'Position', 'MCPServer', 
    'Workflow', 'DataStream', 'Custodian', 'Portfolio'
  ];

  const getRequiredFields = (entityType: string): string[] => {
    const fieldMap: Record<string, string[]> = {
      Account: ['name', 'account_number', 'account_type', 'base_currency'],
      Security: ['name', 'symbol', 'security_type', 'currency'],
      MCPServer: ['name', 'server_url', 'provider_type', 'auth_type'],
      Workflow: ['name', 'workflow_type', 'status'],
      DataStream: ['name', 'data_type', 'source_system', 'status'],
    };
    return fieldMap[entityType] || ['name'];
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary' }}>
            Knowledge Graph
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Explore relationships and insights across your trading ecosystem
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateEntityOpen(true)}
          sx={{ borderRadius: 2 }}
        >
          Add Entity
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {statistics?.total_nodes || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Entities
                  </Typography>
                </Box>
                <GraphIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {statistics?.total_relationships || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Relationships
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {statistics?.node_types?.length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Entity Types
                  </Typography>
                </Box>
                <AnalyticsIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ 
            background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            color: 'white',
            borderRadius: 3
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
                    {statistics?.relationship_types?.length || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Relation Types
                  </Typography>
                </Box>
                <SearchIcon sx={{ fontSize: 40, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Card sx={{ borderRadius: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Graph Visualization" />
          <Tab label="Entity Analytics" />
          <Tab label="Schema Overview" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {/* Graph Visualization Tab */}
          {activeTab === 0 && (
            <GraphVisualization
              height={600}
              onNodeClick={handleNodeClick}
            />
          )}

          {/* Entity Analytics Tab */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                Most Connected Entities
              </Typography>
              
              {centralityData ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Entity</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell align="right">Connections</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {centralityData.centrality_analysis.map((entity) => (
                        <TableRow key={entity.entity_id}>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {entity.entity_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {entity.entity_id}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={entity.entity_type} 
                              size="small" 
                              color="primary" 
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="h6" color="primary">
                              {entity.degree_centrality}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <IconButton size="small">
                              <ViewIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">
                  Loading analytics data...
                </Alert>
              )}
            </Box>
          )}

          {/* Schema Overview Tab */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Entity Types
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Type</TableCell>
                          <TableCell align="right">Count</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {statistics?.node_types?.map((nodeType) => (
                          <TableRow key={nodeType.label}>
                            <TableCell>{nodeType.label}</TableCell>
                            <TableCell align="right">{nodeType.count}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                    Relationship Types
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Type</TableCell>
                          <TableCell align="right">Count</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {statistics?.relationship_types?.map((relType) => (
                          <TableRow key={relType.type}>
                            <TableCell>{relType.type}</TableCell>
                            <TableCell align="right">{relType.count}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Create Entity Dialog */}
      <Dialog open={createEntityOpen} onClose={() => setCreateEntityOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Entity</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Entity Type</InputLabel>
                <Select
                  value={newEntityType}
                  onChange={(e) => setNewEntityType(e.target.value)}
                  label="Entity Type"
                >
                  {entityTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            {getRequiredFields(newEntityType).map((field) => (
              <Grid item xs={12} sm={6} key={field}>
                <TextField
                  fullWidth
                  label={field.charAt(0).toUpperCase() + field.slice(1).replace('_', ' ')}
                  value={entityProperties[field] || ''}
                  onChange={(e) => setEntityProperties(prev => ({
                    ...prev,
                    [field]: e.target.value
                  }))}
                  required
                />
              </Grid>
            ))}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateEntityOpen(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={handleCreateEntity}
            disabled={createEntityMutation.isLoading}
          >
            {createEntityMutation.isLoading ? 'Creating...' : 'Create Entity'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KnowledgeGraph;
