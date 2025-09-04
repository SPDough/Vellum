import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Chip,
  TextField,
  InputAdornment,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Badge,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Assessment as StatsIcon,
  Description as DocIcon,
  Drafts as DraftIcon,
  RateReview as ReviewIcon,
  CheckCircle as ApprovedIcon,
  Archive as DeprecatedIcon
} from '@mui/icons-material';
import { ProductDocumentEditor } from './ProductDocumentEditor';
import { useSnackbar } from 'notistack';

interface ProductDocument {
  id: string;
  title: string;
  product_name: string;
  version: string;
  status: string;
  owner: string;
  stakeholders: string[];
  target_users: string[];
  created_at: string;
  updated_at: string;
}

interface DocumentStats {
  total_documents: number;
  documents_by_status: Record<string, number>;
  documents_by_owner: Record<string, number>;
  recent_documents: ProductDocument[];
  documents_needing_review: number;
  average_review_rating: number;
}

const STATUS_COLORS = {
  Draft: 'default',
  Review: 'warning',
  Approved: 'success',
  Deprecated: 'error'
} as const;

const STATUS_ICONS = {
  Draft: DraftIcon,
  Review: ReviewIcon,
  Approved: ApprovedIcon,
  Deprecated: DeprecatedIcon
} as const;

interface DocumentationDashboardProps {
  onDocumentSelect?: (document: ProductDocument) => void;
}

export const DocumentationDashboard: React.FC<DocumentationDashboardProps> = ({
  onDocumentSelect
}) => {
  const { enqueueSnackbar } = useSnackbar();
  
  const [documents, setDocuments] = useState<ProductDocument[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<ProductDocument[]>([]);
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [ownerFilter, setOwnerFilter] = useState<string>('all');
  const [currentTab, setCurrentTab] = useState(0);
  
  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<ProductDocument | null>(null);
  const [actionMenuAnchor, setActionMenuAnchor] = useState<null | HTMLElement>(null);
  const [actionMenuDocument, setActionMenuDocument] = useState<ProductDocument | null>(null);
  
  // Mock data for demonstration
  useEffect(() => {
    const mockDocuments: ProductDocument[] = [
      {
        id: '1',
        title: 'User Authentication System',
        product_name: 'Auth Service',
        version: '1.0.0',
        status: 'Approved',
        owner: 'John Doe',
        stakeholders: ['Security Team', 'Product Team'],
        target_users: ['End Users', 'Developers'],
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-20T14:30:00Z'
      },
      {
        id: '2',
        title: 'Payment Processing Workflow',
        product_name: 'Payment Engine',
        version: '0.9.0',
        status: 'Review',
        owner: 'Jane Smith',
        stakeholders: ['Finance Team', 'Compliance Team'],
        target_users: ['Merchants', 'Customers'],
        created_at: '2024-01-10T09:00:00Z',
        updated_at: '2024-01-18T16:45:00Z'
      },
      {
        id: '3',
        title: 'Data Analytics Dashboard',
        product_name: 'Analytics Platform',
        version: '0.5.0',
        status: 'Draft',
        owner: 'Mike Johnson',
        stakeholders: ['Data Team', 'Business Team'],
        target_users: ['Analysts', 'Managers'],
        created_at: '2024-01-05T11:00:00Z',
        updated_at: '2024-01-15T13:20:00Z'
      }
    ];
    
    setDocuments(mockDocuments);
    setFilteredDocuments(mockDocuments);
    
    // Mock stats
    setStats({
      total_documents: mockDocuments.length,
      documents_by_status: {
        Draft: 1,
        Review: 1,
        Approved: 1,
        Deprecated: 0
      },
      documents_by_owner: {
        'John Doe': 1,
        'Jane Smith': 1,
        'Mike Johnson': 1
      },
      recent_documents: mockDocuments.slice(0, 3),
      documents_needing_review: 2,
      average_review_rating: 4.2
    });
    
    setLoading(false);
  }, []);

  // Filter documents based on search and filters
  useEffect(() => {
    let filtered = documents;
    
    if (searchQuery) {
      filtered = filtered.filter(doc =>
        doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.owner.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    if (statusFilter !== 'all') {
      filtered = filtered.filter(doc => doc.status === statusFilter);
    }
    
    if (ownerFilter !== 'all') {
      filtered = filtered.filter(doc => doc.owner === ownerFilter);
    }
    
    setFilteredDocuments(filtered);
  }, [documents, searchQuery, statusFilter, ownerFilter]);

  const handleCreateDocument = () => {
    setCreateDialogOpen(true);
  };

  const handleDocumentSave = async (documentData: any) => {
    try {
      // TODO: Implement API call to save document
      const newDocument: ProductDocument = {
        id: Date.now().toString(),
        ...documentData,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      
      setDocuments(prev => [newDocument, ...prev]);
      setCreateDialogOpen(false);
      enqueueSnackbar('Document created successfully', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Failed to create document', { variant: 'error' });
    }
  };

  const handleDocumentAction = (action: string, document: ProductDocument) => {
    setActionMenuAnchor(null);
    setActionMenuDocument(null);
    
    switch (action) {
      case 'view':
        if (onDocumentSelect) {
          onDocumentSelect(document);
        }
        break;
      case 'edit':
        setSelectedDocument(document);
        break;
      case 'delete':
        // TODO: Implement delete confirmation
        enqueueSnackbar('Delete functionality not implemented yet', { variant: 'info' });
        break;
      case 'download':
        // TODO: Implement download
        enqueueSnackbar('Download functionality not implemented yet', { variant: 'info' });
        break;
    }
  };

  const getStatusIcon = (status: string) => {
    const IconComponent = STATUS_ICONS[status as keyof typeof STATUS_ICONS] || DraftIcon;
    return <IconComponent fontSize="small" />;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Product Documentation</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateDocument}
        >
          Create Document
        </Button>
      </Box>

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Documents
                </Typography>
                <Typography variant="h4">{stats.total_documents}</Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  In Review
                </Typography>
                <Typography variant="h4" color="warning.main">
                  {stats.documents_by_status.Review || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Approved
                </Typography>
                <Typography variant="h4" color="success.main">
                  {stats.documents_by_status.Approved || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Drafts
                </Typography>
                <Typography variant="h4" color="textSecondary">
                  {stats.documents_by_status.Draft || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search documents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <TextField
              select
              fullWidth
              label="Status"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Statuses</MenuItem>
              <MenuItem value="Draft">Draft</MenuItem>
              <MenuItem value="Review">Review</MenuItem>
              <MenuItem value="Approved">Approved</MenuItem>
              <MenuItem value="Deprecated">Deprecated</MenuItem>
            </TextField>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <TextField
              select
              fullWidth
              label="Owner"
              value={ownerFilter}
              onChange={(e) => setOwnerFilter(e.target.value)}
            >
              <MenuItem value="all">All Owners</MenuItem>
              {stats?.documents_by_owner && Object.keys(stats.documents_by_owner).map(owner => (
                <MenuItem key={owner} value={owner}>{owner}</MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Documents List */}
      <Paper>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
          <Tab label="All Documents" />
          <Tab 
            label={
              <Badge badgeContent={stats?.documents_needing_review || 0} color="warning">
                Needs Review
              </Badge>
            } 
          />
          <Tab label="Recent" />
        </Tabs>
        
        <Box p={2}>
          {filteredDocuments.length === 0 ? (
            <Box textAlign="center" py={4}>
              <DocIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary">
                No documents found
              </Typography>
              <Typography color="textSecondary">
                {searchQuery || statusFilter !== 'all' || ownerFilter !== 'all' 
                  ? 'Try adjusting your search or filters'
                  : 'Create your first product document to get started'
                }
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {filteredDocuments.map((document) => (
                <Grid item xs={12} key={document.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                        <Box flex={1}>
                          <Typography variant="h6" gutterBottom>
                            {document.title}
                          </Typography>
                          <Typography color="textSecondary" gutterBottom>
                            {document.product_name} • v{document.version}
                          </Typography>
                          
                          <Box display="flex" alignItems="center" gap={1} mb={1}>
                            <Chip
                              icon={getStatusIcon(document.status)}
                              label={document.status}
                              color={STATUS_COLORS[document.status as keyof typeof STATUS_COLORS] as any}
                              size="small"
                            />
                            <Typography variant="body2" color="textSecondary">
                              Owner: {document.owner}
                            </Typography>
                          </Box>
                          
                          <Box display="flex" flexWrap="wrap" gap={0.5} mb={1}>
                            {document.stakeholders.slice(0, 3).map((stakeholder, index) => (
                              <Chip
                                key={index}
                                label={stakeholder}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                            {document.stakeholders.length > 3 && (
                              <Chip
                                label={`+${document.stakeholders.length - 3} more`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          </Box>
                          
                          <Typography variant="body2" color="textSecondary">
                            Created: {formatDate(document.created_at)} • 
                            Updated: {formatDate(document.updated_at)}
                          </Typography>
                        </Box>
                        
                        <IconButton
                          onClick={(e) => {
                            setActionMenuAnchor(e.currentTarget);
                            setActionMenuDocument(document);
                          }}
                        >
                          <MoreIcon />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenuAnchor}
        open={Boolean(actionMenuAnchor)}
        onClose={() => setActionMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleDocumentAction('view', actionMenuDocument!)}>
          <ListItemIcon>
            <ViewIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>View</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => handleDocumentAction('edit', actionMenuDocument!)}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => handleDocumentAction('download', actionMenuDocument!)}>
          <ListItemIcon>
            <DownloadIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Download</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => handleDocumentAction('delete', actionMenuDocument!)}>
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Create Document Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Create New Product Document</DialogTitle>
        <DialogContent>
          <ProductDocumentEditor
            mode="create"
            onSave={handleDocumentSave}
            onCancel={() => setCreateDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>

      {/* Edit Document Dialog */}
      <Dialog
        open={Boolean(selectedDocument)}
        onClose={() => setSelectedDocument(null)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Edit Product Document</DialogTitle>
        <DialogContent>
          {selectedDocument && (
            <ProductDocumentEditor
              mode="edit"
              document={selectedDocument}
              onSave={handleDocumentSave}
              onCancel={() => setSelectedDocument(null)}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

