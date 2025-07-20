import React, { useState, useMemo } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  TextField,
  IconButton,
  Menu,
  MenuItem,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Paper,
  InputAdornment,
  Toolbar,
  Grid,
  FormControl,
  InputLabel,
  Select,
  Tooltip,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
  ViewColumn as ViewColumnIcon,
  MoreVert as MoreVertIcon,
  PlayArrow as PlayIcon,
  DataObject as DataIcon,
  Timeline as ChartIcon,
} from '@mui/icons-material';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
  VisibilityState,
} from '@tanstack/react-table';
import { useQuery } from 'react-query';

import WorkflowDataConnector from '@/components/DataSandbox/WorkflowDataConnector';
import MCPDataConnector from '@/components/DataSandbox/MCPDataConnector';
import ChartVisualization from '@/components/DataSandbox/ChartVisualization';
import { dataSandboxService } from '@/services/dataSandboxService';
import { useSystemWebSocket } from '@/hooks/useWebSocket';

// Sample data structure for demo
interface DataRecord {
  id: string;
  timestamp: string;
  symbol: string;
  price: number;
  volume: number;
  change: number;
  changePercent: number;
  market: string;
  sector: string;
  source: string;
}

interface DataSandboxProps {}

const DataSandbox: React.FC<DataSandboxProps> = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [globalFilter, setGlobalFilter] = useState('');
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 25,
  });
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedDataSource, setSelectedDataSource] = useState('workflow_output');
  
  // WebSocket connection for real-time updates
  const { 
    isConnected, 
    workflowUpdates, 
    mcpUpdates, 
    agentUpdates 
  } = useSystemWebSocket();

  // Sample data - in real app, this would come from workflows/APIs
  const sampleData: DataRecord[] = useMemo(() => [
    {
      id: '1',
      timestamp: '2024-01-15T09:30:00Z',
      symbol: 'AAPL',
      price: 185.42,
      volume: 1234567,
      change: 2.15,
      changePercent: 1.17,
      market: 'NASDAQ',
      sector: 'Technology',
      source: 'Trading Workflow'
    },
    {
      id: '2',
      timestamp: '2024-01-15T09:30:00Z',
      symbol: 'GOOGL',
      price: 142.87,
      volume: 987654,
      change: -1.23,
      changePercent: -0.85,
      market: 'NASDAQ',
      sector: 'Technology',
      source: 'Market Data API'
    },
    {
      id: '3',
      timestamp: '2024-01-15T09:30:00Z',
      symbol: 'TSLA',
      price: 238.45,
      volume: 2345678,
      change: 5.67,
      changePercent: 2.43,
      market: 'NASDAQ',
      sector: 'Automotive',
      source: 'Risk Monitor Agent'
    },
    // Add more sample data...
  ], []);

  const columnHelper = createColumnHelper<DataRecord>();

  const columns = useMemo<ColumnDef<DataRecord>[]>(() => [
    columnHelper.accessor('timestamp', {
      header: 'Timestamp',
      cell: info => new Date(info.getValue()).toLocaleString(),
      size: 150,
    }),
    columnHelper.accessor('symbol', {
      header: 'Symbol',
      cell: info => (
        <Chip 
          label={info.getValue()} 
          size="small" 
          color="primary" 
          variant="outlined"
        />
      ),
      size: 100,
    }),
    columnHelper.accessor('price', {
      header: 'Price',
      cell: info => `$${info.getValue().toFixed(2)}`,
      size: 100,
    }),
    columnHelper.accessor('volume', {
      header: 'Volume',
      cell: info => info.getValue().toLocaleString(),
      size: 120,
    }),
    columnHelper.accessor('change', {
      header: 'Change',
      cell: info => {
        const value = info.getValue();
        return (
          <Typography 
            variant="body2" 
            color={value >= 0 ? 'success.main' : 'error.main'}
            sx={{ fontWeight: 600 }}
          >
            {value >= 0 ? '+' : ''}{value.toFixed(2)}
          </Typography>
        );
      },
      size: 100,
    }),
    columnHelper.accessor('changePercent', {
      header: 'Change %',
      cell: info => {
        const value = info.getValue();
        return (
          <Typography 
            variant="body2" 
            color={value >= 0 ? 'success.main' : 'error.main'}
            sx={{ fontWeight: 600 }}
          >
            {value >= 0 ? '+' : ''}{value.toFixed(2)}%
          </Typography>
        );
      },
      size: 100,
    }),
    columnHelper.accessor('market', {
      header: 'Market',
      cell: info => (
        <Chip 
          label={info.getValue()} 
          size="small" 
          color="secondary"
        />
      ),
      size: 100,
    }),
    columnHelper.accessor('sector', {
      header: 'Sector',
      size: 120,
    }),
    columnHelper.accessor('source', {
      header: 'Source',
      cell: info => (
        <Chip 
          label={info.getValue()} 
          size="small" 
          color="info"
          variant="outlined"
        />
      ),
      size: 150,
    }),
  ], [columnHelper]);

  const table = useReactTable({
    data: sampleData,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      globalFilter,
      pagination,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onGlobalFilterChange: setGlobalFilter,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleExportData = (format: 'csv' | 'json' | 'xlsx') => {
    const data = table.getFilteredRowModel().rows.map(row => row.original);
    
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `data-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else if (format === 'csv') {
      const headers = columns.map(col => col.id).join(',');
      const rows = data.map(row => 
        columns.map(col => JSON.stringify(row[col.id as keyof DataRecord] || '')).join(',')
      ).join('\n');
      const csv = `${headers}\n${rows}`;
      
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `data-export-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
    
    handleMenuClose();
  };

  const dataSources = [
    { value: 'workflow_output', label: 'Workflow Outputs' },
    { value: 'mcp_data', label: 'MCP Data Streams' },
    { value: 'agent_results', label: 'Agent Results' },
    { value: 'market_data', label: 'Market Data' },
    { value: 'custom_query', label: 'Custom Query' },
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
            <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary' }}>
              Data Sandbox
            </Typography>
            <Chip 
              label={isConnected ? 'Live' : 'Offline'} 
              size="small" 
              color={isConnected ? 'success' : 'default'}
              variant={isConnected ? 'filled' : 'outlined'}
            />
          </Box>
          <Typography variant="body2" color="text.secondary">
            Explore and analyze data from workflows, APIs, and agents
            {isConnected && ' • Real-time updates enabled'}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<PlayIcon />}
            onClick={() => {/* Run query */}}
            sx={{ borderRadius: 2 }}
          >
            Run Query
          </Button>
          <Button
            variant="contained"
            startIcon={<RefreshIcon />}
            onClick={() => {/* Refresh data */}}
            sx={{ borderRadius: 2 }}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Data Source Selection */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Data Source</InputLabel>
            <Select
              value={selectedDataSource}
              onChange={(e) => setSelectedDataSource(e.target.value)}
              label="Data Source"
            >
              {dataSources.map((source) => (
                <MenuItem key={source.value} value={source.value}>
                  {source.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} md={8}>
          <TextField
            fullWidth
            placeholder="Search data..."
            value={globalFilter ?? ''}
            onChange={(e) => setGlobalFilter(String(e.target.value))}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
        </Grid>
      </Grid>

      {/* Main Content */}
      <Card sx={{ borderRadius: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Table View" icon={<DataIcon />} iconPosition="start" />
          <Tab label="Chart View" icon={<ChartIcon />} iconPosition="start" />
          <Tab label="Workflow Data" icon={<PlayIcon />} iconPosition="start" />
          <Tab label="MCP Data" icon={<RefreshIcon />} iconPosition="start" />
        </Tabs>

        <CardContent sx={{ p: 0 }}>
          {/* Table View */}
          {activeTab === 0 && (
            <Box>
              {/* Table Toolbar */}
              <Toolbar sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Typography variant="h6" sx={{ flex: 1 }}>
                  {table.getFilteredRowModel().rows.length} records
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Column Visibility">
                    <IconButton size="small">
                      <ViewColumnIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Filters">
                    <IconButton size="small">
                      <FilterIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <Tooltip title="Export Options">
                    <IconButton size="small" onClick={handleMenuOpen}>
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                  
                  <IconButton size="small">
                    <MoreVertIcon />
                  </IconButton>
                </Box>
              </Toolbar>

              {/* Data Table */}
              <TableContainer component={Paper} sx={{ maxHeight: 600 }}>
                <Table stickyHeader>
                  <TableHead>
                    {table.getHeaderGroups().map(headerGroup => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map(header => (
                          <TableCell
                            key={header.id}
                            sx={{ 
                              fontWeight: 600,
                              backgroundColor: 'background.paper',
                              cursor: header.column.getCanSort() ? 'pointer' : 'default',
                            }}
                            onClick={header.column.getToggleSortingHandler()}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                              {header.column.getIsSorted() === 'asc' && '↑'}
                              {header.column.getIsSorted() === 'desc' && '↓'}
                            </Box>
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableHead>
                  <TableBody>
                    {table.getRowModel().rows.map(row => (
                      <TableRow key={row.id} hover>
                        {row.getVisibleCells().map(cell => (
                          <TableCell key={cell.id}>
                            {flexRender(
                              cell.column.columnDef.cell,
                              cell.getContext()
                            )}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              <TablePagination
                rowsPerPageOptions={[10, 25, 50, 100]}
                component="div"
                count={table.getFilteredRowModel().rows.length}
                rowsPerPage={pagination.pageSize}
                page={pagination.pageIndex}
                onPageChange={(_, page) => setPagination(prev => ({ ...prev, pageIndex: page }))}
                onRowsPerPageChange={(e) => setPagination(prev => ({ 
                  ...prev, 
                  pageSize: parseInt(e.target.value), 
                  pageIndex: 0 
                }))}
              />
            </Box>
          )}

          {/* Chart View */}
          {activeTab === 1 && (
            <Box sx={{ p: 3 }}>
              <ChartVisualization 
                data={sampleData}
                height={500}
              />
            </Box>
          )}

          {/* Workflow Data */}
          {activeTab === 2 && (
            <Box sx={{ p: 3 }}>
              <WorkflowDataConnector 
                onDataSourceCreated={(dataSource) => {
                  console.log('Data source created:', dataSource);
                  // Switch to table view to show the new data
                  setActiveTab(0);
                }}
              />
            </Box>
          )}

          {/* MCP Data */}
          {activeTab === 3 && (
            <Box sx={{ p: 3 }}>
              <MCPDataConnector 
                onDataSourceCreated={(dataSource) => {
                  console.log('Data source created:', dataSource);
                  // Switch to table view to show the new data
                  setActiveTab(0);
                }}
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Export Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleExportData('csv')}>
          Export as CSV
        </MenuItem>
        <MenuItem onClick={() => handleExportData('json')}>
          Export as JSON
        </MenuItem>
        <MenuItem onClick={() => handleExportData('xlsx')} disabled>
          Export as Excel (Coming Soon)
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default DataSandbox;