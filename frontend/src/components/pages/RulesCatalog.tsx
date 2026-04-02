import React, { useEffect, useState } from 'react';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Assessment,
  ExpandMore,
  FilterList,
  Info,
  Refresh,
  Rule as RuleIcon,
  Search,
  Security,
  Speed,
  TrendingUp,
  Visibility,
} from '@mui/icons-material';
import { rulesService, Rule, RulesCatalog } from '../../services/rulesService';

const categoryConfig = {
  trade_validation: { icon: <Assessment />, color: 'primary' },
  risk_management: { icon: <Security />, color: 'error' },
  compliance: { icon: <Security />, color: 'warning' },
  settlement: { icon: <Speed />, color: 'info' },
  market_timing: { icon: <TrendingUp />, color: 'secondary' },
  pricing: { icon: <TrendingUp />, color: 'success' },
};

const RulesCatalogPage: React.FC = () => {
  const [catalog, setCatalog] = useState<RulesCatalog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Rule[]>([]);
  const [ruleDetailOpen, setRuleDetailOpen] = useState(false);
  const [selectedRule, setSelectedRule] = useState<Rule | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});

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
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async () => {
    try {
      const results = await rulesService.searchRules({ query: searchQuery, category: selectedCategory || undefined });
      setSearchResults(results.results);
    } catch (err) {
      setSearchResults([]);
    }
  };

  const handleCategoryExpand = (category: string) => {
    setExpandedCategories((prev) => ({ ...prev, [category]: !prev[category] }));
  };

  const RuleCard: React.FC<{ rule: Rule; categoryKey?: string }> = ({ rule, categoryKey }) => (
    <Card sx={{ mb: 2, border: '1px solid', borderColor: 'divider' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {categoryKey && categoryConfig[categoryKey as keyof typeof categoryConfig]?.icon}
            <Typography variant="h6">{rule.name}</Typography>
            <Chip label={`Priority ${rule.salience}`} size="small" variant="outlined" />
          </Box>
          <Tooltip title="View details"><IconButton color="info" onClick={() => { setSelectedRule(rule); setRuleDetailOpen(true); }}><Visibility /></IconButton></Tooltip>
        </Box>

        <Typography variant="body2" color="text.secondary" mb={2}>{rule.description}</Typography>
        <Typography variant="caption" color="text.secondary" display="block">Trigger condition</Typography>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1, mb: 2 }}>{rule.trigger_condition}</Typography>
        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          {rule.actions.map((action, index) => <Chip key={index} label={action} size="small" variant="outlined" color="secondary" />)}
        </Box>
        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip label={rule.file} variant="outlined" size="small" icon={<RuleIcon />} />
          <Chip label={`Lines: ${rule.line_range}`} variant="outlined" size="small" />
          {rule.category_name && <Chip label={rule.category_name} size="small" color={categoryConfig[rule.category as keyof typeof categoryConfig]?.color as any || 'default'} />}
        </Box>
      </CardContent>
    </Card>
  );

  if (loading) return <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px"><CircularProgress /></Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1.5}>
        <Typography variant="h4">Rules catalog</Typography>
        <Button variant="outlined" startIcon={<Refresh />} onClick={loadRulesCatalog}>Refresh</Button>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 940 }}>
        Deterministic rules are the core decision layer in Vellum. They classify cross-stack mismatches,
        decide whether a condition is met, and feed governed workflows without letting probabilistic models override control logic.
      </Typography>

      {catalog && (
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}><Card sx={{ textAlign: 'center', p: 2 }}><Typography variant="h4" color="primary">{catalog.summary.total_rules}</Typography><Typography variant="body2" color="text.secondary">Total rules</Typography></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card sx={{ textAlign: 'center', p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}><Typography variant="h4">{catalog.summary.total_categories}</Typography><Typography variant="body2">Rule domains</Typography></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card sx={{ textAlign: 'center', p: 2, bgcolor: 'warning.light', color: 'warning.contrastText' }}><Typography variant="h4">9</Typography><Typography variant="body2">Break classes covered</Typography></Card></Grid>
          <Grid item xs={12} sm={6} md={3}><Card sx={{ textAlign: 'center', p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}><Typography variant="h4">Rules First</Typography><Typography variant="body2">Authority principle</Typography></Card></Grid>
        </Grid>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" mb={2}>Search deterministic controls</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField fullWidth label="Search rules..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} InputProps={{ startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} /> }} />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category Filter</InputLabel>
              <Select value={selectedCategory} label="Category Filter" onChange={(e) => setSelectedCategory(e.target.value)}>
                <MenuItem value="">All Categories</MenuItem>
                {catalog?.summary.categories.map((category) => <MenuItem key={category} value={category}>{catalog.catalog[category].category}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}><Button fullWidth variant="outlined" startIcon={<FilterList />} onClick={performSearch}>Search</Button></Grid>
        </Grid>

        {searchResults.length > 0 && (
          <Box mt={3}>
            <Typography variant="subtitle1" mb={2}>Search Results ({searchResults.length})</Typography>
            {searchResults.map((rule, index) => <RuleCard key={index} rule={rule} categoryKey={rule.category} />)}
          </Box>
        )}
      </Paper>

      <Paper sx={{ width: '100%', mb: 3 }}>
        <Typography variant="h6" sx={{ p: 3, pb: 0 }}>Rules by domain</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ px: 3, pb: 2 }}>
          These controls should evolve toward OMS / IBOR / ABOR / CBOR break detection, workflow-case creation, and evidence-backed operational action.
        </Typography>
        {catalog && Object.entries(catalog.catalog).map(([categoryKey, categoryData]) => (
          <Accordion key={categoryKey} expanded={expandedCategories[categoryKey]} onChange={() => handleCategoryExpand(categoryKey)}>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box display="flex" alignItems="center" gap={2}>
                {categoryConfig[categoryKey as keyof typeof categoryConfig]?.icon}
                <Typography variant="h6">{categoryData.category}</Typography>
                <Badge badgeContent={categoryData.rules.length} color={categoryConfig[categoryKey as keyof typeof categoryConfig]?.color as any || 'default'} />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" color="text.secondary" mb={3}>{categoryData.description}</Typography>
              {categoryData.rules.map((rule, index) => <RuleCard key={index} rule={rule} categoryKey={categoryKey} />)}
            </AccordionDetails>
          </Accordion>
        ))}
      </Paper>

      <Dialog open={ruleDetailOpen} onClose={() => setRuleDetailOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Rule Details: {selectedRule?.name}</DialogTitle>
        <DialogContent>
          {selectedRule && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Description</Typography>
                <Typography variant="body2" paragraph>{selectedRule.description}</Typography>
                <Typography variant="subtitle2" gutterBottom>Trigger Condition</Typography>
                <Paper sx={{ p: 2, bgcolor: 'grey.100', fontFamily: 'monospace' }}>{selectedRule.trigger_condition}</Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>Actions</Typography>
                <List dense>{selectedRule.actions.map((action, index) => <ListItem key={index}><ListItemText primary={action} /></ListItem>)}</List>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions><Button onClick={() => setRuleDetailOpen(false)}>Close</Button></DialogActions>
      </Dialog>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}><Alert severity="error" onClose={() => setError(null)}>{error}</Alert></Snackbar>
      <Snackbar open={!!successMessage} autoHideDuration={6000} onClose={() => setSuccessMessage(null)}><Alert severity="success" onClose={() => setSuccessMessage(null)}>{successMessage}</Alert></Snackbar>
    </Box>
  );
};

export default RulesCatalogPage;
