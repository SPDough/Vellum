import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Grid,
  Tabs,
  Tab,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Paper,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Collapse,
} from '@mui/material';
import {
  Search,
  PlayArrow,
  Code,
  Settings,
  ExpandMore,
  Info,
  Speed,
  Security,
  Assessment,
  Schedule,
  TrendingUp,
  Refresh,
  FilterList,
  Visibility,
  Edit,
  Upload,
  Add,
} from '@mui/icons-material';
import { rulesService, Rule, RulesCatalog, RuleCategory } from '../services/rulesService';

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
      id={`rules-tabpanel-${index}`}
      aria-labelledby={`rules-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RulesCatalogPage: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [catalog, setCatalog] = useState<RulesCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Rule[]>([]);
  const [ruleDetailOpen, setRuleDetailOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testSymbol, setTestSymbol] = useState('AAPL');
  const [testPrice, setTestPrice] = useState(150);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});

  const categoryConfig = {
    trade_validation: { icon: <Assessment />, color: 'primary' },
    risk_management: { icon: <Security />, color: 'error' },
    compliance: { icon: <Security />, color: 'warning' },
    settlement: { icon: <Schedule />, color: 'info' },
    market_timing: { icon: <Speed />, color: 'secondary' },
    pricing: { icon: <TrendingUp />, color: 'success' },
  };

  useEffect(() => {
    loadRulesCatalog();
  }, []);

  useEffect(() => {
    if (searchQuery.trim()) {
      performSearch();
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, selectedCategory]);

  const loadRulesCatalog = async () => {
    try {
      setLoading(true);
      const catalogData = await rulesService.getRulesCatalog();
      setCatalog(catalogData);
      setError(null);
    } catch (err) {
      setError('Failed to load rules catalog');
      console.error('Error loading rules catalog:', err);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    try {
      const results = await rulesService.searchRules({
        query: searchQuery,
        category: selectedCategory || undefined,
      });
      setSearchResults(results.results);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    }
  };

  const handleCategoryExpand = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const handleTestEquityPricing = async () => {
    try {
      const result = await rulesService.testEquityPricing(testSymbol, testPrice);
      setSuccessMessage(`Equity pricing test completed: ${result.rules_fired.length} rules fired`);
      setTestDialogOpen(false);
      console.log('Pricing test result:', result);
    } catch (err) {
      setError('Failed to test equity pricing');
      console.error('Pricing test failed:', err);
    }
  };

  const RuleCard: React.FC<{ rule: Rule; categoryKey?: string }> = ({ rule, categoryKey }) => (
    <Card sx={{ mb: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {categoryKey && categoryConfig[categoryKey as keyof typeof categoryConfig] && 
              categoryConfig[categoryKey as keyof typeof categoryConfig].icon
            }
            <Typography variant="h6" component="h3">
              {rule.name}
            </Typography>
            <Chip 
              label={`Salience: ${rule.salience}`} 
              size="small"
              color="default"
              variant="outlined"
            />
          </Box>
          <Box>
            <Tooltip title="View Details">
              <IconButton
                color="info"
                onClick={() => {
                  setSelectedRule(rule);
                  setRuleDetailOpen(true);
                }}
              >
                <Visibility />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={2}>
          {rule.description}
        </Typography>

        <Box mb={2}>
          <Typography variant="caption" color="text.secondary" display="block">
            Trigger Condition:
          </Typography>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
            {rule.trigger_condition}
          </Typography>
        </Box>

        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          {rule.actions.map((action, index) => (
            <Chip 
              key={index}
              label={action}
              size="small"
              variant="outlined"
              color="secondary"
            />
          ))}
        </Box>

        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip 
            label={rule.file}
            variant="outlined"
            size="small"
            icon={<Code />}
          />
          <Chip 
            label={`Lines: ${rule.line_range}`}
            variant="outlined"
            size="small"
          />
          {rule.category_name && (
            <Chip 
              label={rule.category_name}
              size="small"
              color={categoryConfig[rule.category as keyof typeof categoryConfig]?.color as any || 'default'}
            />
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const SummaryCards: React.FC = () => (
    <Grid container spacing={3} mb={3}>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2 }}>
          <Typography variant="h4" color="primary">
            {catalog?.summary.total_rules || 0}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Rules
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
          <Typography variant="h4">
            {catalog?.summary.total_categories || 0}
          </Typography>
          <Typography variant="body2">
            Categories
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}>
          <Typography variant="h4">
            {catalog?.catalog.pricing?.rules.length || 0}
          </Typography>
          <Typography variant="body2">
            Pricing Rules
          </Typography>
        </Card>
      </Grid>
      <Grid item xs={12} sm={6} md={3}>
        <Card sx={{ textAlign: 'center', p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
          <Typography variant="h4">
            {catalog?.catalog.risk_management?.rules.length || 0}
          </Typography>
          <Typography variant="body2">
            Risk Rules
          </Typography>
        </Card>
      </Grid>
    </Grid>
  );

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Drools Rules Catalog
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadRulesCatalog}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<TrendingUp />}
            onClick={() => setTestDialogOpen(true)}
          >
            Test Pricing
          </Button>
        </Box>
      </Box>

      {catalog && <SummaryCards />}

      {/* Search Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" mb={2}>Search Rules</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search rules..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category Filter</InputLabel>
              <Select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                label="Category Filter"
              >
                <MenuItem value="">All Categories</MenuItem>
                {catalog?.summary.categories.map(category => (
                  <MenuItem key={category} value={category}>
                    {catalog.catalog[category].category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<FilterList />}
              onClick={performSearch}
            >
              Search
            </Button>
          </Grid>
        </Grid>

        {searchResults.length > 0 && (
          <Box mt={3}>
            <Typography variant="subtitle1" mb={2}>
              Search Results ({searchResults.length})
            </Typography>
            {searchResults.map((rule, index) => (
              <RuleCard key={index} rule={rule} categoryKey={rule.category} />
            ))}
          </Box>
        )}
      </Paper>

      {/* Rules by Category */}
      <Paper sx={{ width: '100%', mb: 3 }}>
        <Typography variant="h6" sx={{ p: 3, pb: 0 }}>Rules by Category</Typography>
        
        {catalog && Object.entries(catalog.catalog).map(([categoryKey, categoryData]) => (
          <Accordion 
            key={categoryKey}
            expanded={expandedCategories[categoryKey]}
            onChange={() => handleCategoryExpand(categoryKey)}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box display="flex" alignItems="center" gap={2}>
                {categoryConfig[categoryKey as keyof typeof categoryConfig]?.icon}
                <Typography variant="h6">{categoryData.category}</Typography>
                <Badge 
                  badgeContent={categoryData.rules.length} 
                  color={categoryConfig[categoryKey as keyof typeof categoryConfig]?.color as any || 'default'}
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" mb={3}>
                {categoryData.description}
              </Typography>
              
              {categoryData.rules.map((rule, index) => (
                <RuleCard key={index} rule={rule} categoryKey={categoryKey} />
              ))}
            </AccordionDetails>
          </Accordion>
        ))}
      </Paper>

      {/* Rule Detail Dialog */}
      <Dialog open={ruleDetailOpen} onClose={() => setRuleDetailOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Info />
            Rule Details: {selectedRule?.name}
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedRule && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Description</Typography>
                <Typography variant="body2" paragraph>{selectedRule.description}</Typography>
                
                <Typography variant="subtitle2" gutterBottom>Trigger Condition</Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace' }}>
                  {selectedRule.trigger_condition}
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Properties</Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Salience" secondary={selectedRule.salience} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="File" secondary={selectedRule.file} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Line Range" secondary={selectedRule.line_range} />
                  </ListItem>
                </List>
                
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>Actions</Typography>
                <List dense>
                  {selectedRule.actions.map((action, index) => (
                    <ListItem key={index}>
                      <ListItemText primary={action} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRuleDetailOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Test Equity Pricing Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Test Equity Pricing Rules</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Test the equity pricing calculation rules with sample data.
          </Typography>
          
          <TextField
            label="Stock Symbol"
            value={testSymbol}
            onChange={(e) => setTestSymbol(e.target.value)}
            fullWidth
            margin="normal"
          />
          
          <TextField
            label="Market Price ($)"
            type="number"
            value={testPrice}
            onChange={(e) => setTestPrice(Number(e.target.value))}
            fullWidth
            margin="normal"
          />
          
          <Alert severity="info" sx={{ mt: 2 }}>
            This will execute the equity pricing rules with the provided symbol and market price,
            applying liquidity and volatility adjustments as configured.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleTestEquityPricing} variant="contained">Test Pricing</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbars */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage(null)}
      >
        <Alert severity="success" onClose={() => setSuccessMessage(null)}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RulesCatalog;
