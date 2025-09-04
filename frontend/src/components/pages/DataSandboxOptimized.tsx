import React, { useState, useMemo, useCallback, useRef } from 'react';
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
  SortingState,
  ColumnFiltersState,
  VisibilityState,
} from '@tanstack/react-table';

import WorkflowDataConnector from '@/components/DataSandbox/WorkflowDataConnector';
import MCPDataConnector from '@/components/DataSandbox/MCPDataConnector';
import ChartVisualization from '@/components/DataSandbox/ChartVisualization';
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

// OPTIMIZED: Move sample data generation outside component to prevent recreation
const generateSampleData = (): DataRecord[] => [
  {
    id: '1',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'AAPL',
    price: 185.42,
    volume: 1250000,
    change: 2.15,
    changePercent: 1.17,
    market: 'NASDAQ',
    sector: 'Technology',
    source: 'workflow_output',
  },
  {
    id: '2',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'MSFT',
    price: 378.85,
    volume: 890000,
    change: -1.23,
    changePercent: -0.32,
    market: 'NASDAQ',
    sector: 'Technology',
    source: 'workflow_output',
  },
  {
    id: '3',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'GOOGL',
    price: 142.56,
    volume: 2100000,
    change: 0.89,
    changePercent: 0.63,
    market: 'NASDAQ',
    sector: 'Technology',
    source: 'mcp_stream',
  },
  {
    id: '4',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'TSLA',
    price: 248.50,
    volume: 3400000,
    change: -5.20,
    changePercent: -2.05,
    market: 'NASDAQ',
    sector: 'Automotive',
    source: 'agent_result',
  },
  {
    id: '5',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'AMZN',
    price: 155.20,
    volume: 1800000,
    change: 1.45,
    changePercent: 0.94,
    market: 'NASDAQ',
    sector: 'Consumer Discretionary',
    source: 'workflow_output',
  },
  {
    id: '6',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'META',
    price: 378.99,
    volume: 950000,
    change: 3.21,
    changePercent: 0.85,
    market: 'NASDAQ',
    sector: 'Technology',
    source: 'mcp_stream',
  },
  {
    id: '7',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'NVDA',
    price: 485.09,
    volume: 2800000,
    change: 12.45,
    changePercent: 2.63,
    market: 'NASDAQ',
    sector: 'Technology',
    source: 'agent_result',
  },
  {
    id: '8',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'NFLX',
    price: 492.42,
    volume: 420000,
    change: -2.18,
    changePercent: -0.44,
    market: 'NASDAQ',
    sector: 'Communication Services',
    source: 'workflow_output',
  },
  {
    id: '9',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'JPM',
    price: 172.56,
    volume: 680000,
    change: 0.78,
    changePercent: 0.45,
    market: 'NYSE',
    sector: 'Financial Services',
    source: 'mcp_stream',
  },
  {
    id: '10',
    timestamp: '2024-01-15T09:30:00Z',
    symbol: 'JNJ',
    price: 162.34,
    volume: 320000,
    change: -0.45,
    changePercent: -0.28,
    market: 'NYSE',
    sector: 'Healthcare',
    source: 'agent_result',
  },
];

// OPTIMIZED: Pre-generate sample data
const SAMPLE_DATA = generateSampleData();

const DataSandboxOptimized: React.FC<DataSandboxProps> = () => {
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
  
  // OPTIMIZED: Use ref to prevent unnecessary re-renders
  const exportTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // WebSocket connection for real-time updates
  const { isConnected } = useSystemWebSocket();

  // OPTIMIZED: Use memoized data with proper dependencies
  const filteredData = useMemo(() => {
    if (!globalFilter) return SAMPLE_DATA;
    
    return SAMPLE_DATA.filter(record => 
      Object.values(record).some(value => 
        String(value).toLowerCase().includes(globalFilter.toLowerCase())
      )
    );
  }, [globalFilter]);

  // OPTIMIZED: Memoize column helper to prevent recreation
  const columnHelper = useMemo(() => createColumnHelper<DataRecord>(), []);

  // OPTIMIZED: Memoize columns with proper dependencies
  const columns = useMemo(() => [
    columnHelper.accessor('symbol', {
      header: 'Symbol',
      cell: info => (
        <Box sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          {info.getValue()}
        </Box>
      ),
    }),
    columnHelper.accessor('price', {
      header: 'Price',
      cell: info => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          ${info.getValue().toFixed(2)}
        </Typography>
      ),
    }),
    columnHelper.accessor('volume', {
      header: 'Volume',
      cell: info => (
        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
          {info.getValue().toLocaleString()}
        </Typography>
      ),
    }),
    columnHelper.accessor('change', {
      header: 'Change',
      cell: info => {
        const value = info.getValue();
        const isPositive = value >= 0;
        return (
          <Typography
            variant="body2"
            sx={{
              color: isPositive ? 'success.main' : 'error.main',
              fontWeight: 'bold',
            }}
          >
            {isPositive ? '+' : ''}{value.toFixed(2)}
          </Typography>
        );
      },
    }),
    columnHelper.accessor('changePercent', {
      header: 'Change %',
      cell: info => {
        const value = info.getValue();
        const isPositive = value >= 0;
        return (
          <Typography
            variant="body2"
            sx={{
              color: isPositive ? 'success.main' : 'error.main',
              fontWeight: 'bold',
            }}
          >
            {isPositive ? '+' : ''}{value.toFixed(2)}%
          </Typography>
        );
      },
    }),
    columnHelper.accessor('market', {
      header: 'Market',
      cell: info => (
        <Chip
          label={info.getValue()}
          size="small"
          variant="outlined"
          color="primary"
        />
      ),
    }),
    columnHelper.accessor('sector', {
      header: 'Sector',
      cell: info => (
        <Typography variant="body2" color="text.secondary">
          {info.getValue()}
        </Typography>
      ),
    }),
    columnHelper.accessor('source', {
      header: 'Source',
      cell: info => {
        const source = info.getValue();
        const getSourceColor = (source: string) => {
          switch (source) {
            case 'workflow_output': return 'success';
            case 'mcp_stream': return 'info';
            case 'agent_result': return 'warning';
            default: return 'default';
          }
        };
        return (
          <Chip
            label={source.replace('_', ' ')}
            size="small"
            color={getSourceColor(source) as any}
          />
        );
      },
    }),
  ], [columnHelper]);

  // OPTIMIZED: Memoize table instance
  const table = useReactTable({
    data: filteredData,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      pagination,
      globalFilter,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onPaginationChange: setPagination,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  // OPTIMIZED: Memoize event handlers
  const handleTabChange = useCallback((_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  }, []);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  }, []);

  const handleMenuClose = useCallback(() => {
    setAnchorEl(null);
  }, []);

  // OPTIMIZED: Efficient CSV export with single transformation
  const handleExportData = useCallback((format: 'csv' | 'json' | 'xlsx') => {
    if (exportTimeoutRef.current) {
      clearTimeout(exportTimeoutRef.current);
    }

    exportTimeoutRef.current = setTimeout(() => {
      try {
        let dataToExport = filteredData;
        
        // Single transformation for CSV export
        if (format === 'csv') {
          const csvData = dataToExport.map(record => ({
            Symbol: record.symbol,
            Price: `$${record.price.toFixed(2)}`,
            Volume: record.volume.toLocaleString(),
            Change: `${record.change >= 0 ? '+' : ''}${record.change.toFixed(2)}`,
            'Change %': `${record.changePercent >= 0 ? '+' : ''}${record.changePercent.toFixed(2)}%`,
            Market: record.market,
            Sector: record.sector,
            Source: record.source.replace('_', ' '),
            Timestamp: new Date(record.timestamp).toLocaleString(),
          }));

          const csvContent = [
            Object.keys(csvData[0]).join(','),
            ...csvData.map(row => Object.values(row).join(','))
          ].join('\n');

          const blob = new Blob([csvContent], { type: 'text/csv' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `data_sandbox_export_${new Date().toISOString().split('T')[0]}.csv`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else if (format === 'json') {
          const jsonContent = JSON.stringify(dataToExport, null, 2);
          const blob = new Blob([jsonContent], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `data_sandbox_export_${new Date().toISOString().split('T')[0]}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }
      } catch (error) {
        console.error('Export failed:', error);
      }
    }, 100);
  }, [filteredData]);

  // Cleanup timeout on unmount
  React.useEffect(() => {
    return () => {
      if (exportTimeoutRef.current) {
        clearTimeout(exportTimeoutRef.current);
      }
    };
  }, []);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Data Sandbox
      </Typography>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Real-time Data Analysis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Analyze and visualize data from multiple sources including workflows, MCP servers, and AI agents.
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Chip
                  label={`${filteredData.length} Records`}
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={isConnected ? 'Connected' : 'Disconnected'}
                  color={isConnected ? 'success' : 'error'}
                  size="small"
                />
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Data Table" />
        <Tab label="Charts" />
        <Tab label="Data Sources" />
        <Tab label="Connectors" />
      </Tabs>

      {activeTab === 0 && (
        <Card>
          <CardContent>
            <Toolbar sx={{ pl: { sm: 2 }, pr: { xs: 1, sm: 1 } }}>
              <TextField
                placeholder="Search all columns..."
                value={globalFilter ?? ''}
                onChange={e => setGlobalFilter(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ mr: 2, minWidth: 300 }}
              />
              
              <Box sx={{ flexGrow: 1 }} />
              
              <Tooltip title="Filter list">
                <IconButton>
                  <FilterIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="View columns">
                <IconButton>
                  <ViewColumnIcon />
                </IconButton>
              </Tooltip>
              
              <Tooltip title="Export data">
                <IconButton onClick={handleMenuOpen}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
              
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
              >
                <MenuItem onClick={() => { handleExportData('csv'); handleMenuClose(); }}>
                  Export as CSV
                </MenuItem>
                <MenuItem onClick={() => { handleExportData('json'); handleMenuClose(); }}>
                  Export as JSON
                </MenuItem>
              </Menu>
            </Toolbar>

            <TableContainer component={Paper}>
              <Table>
                <TableHead>
                  {table.getHeaderGroups().map(headerGroup => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map(header => (
                        <TableCell key={header.id}>
                          {header.isPlaceholder
                            ? null
                            : flexRender(
                                header.column.columnDef.header,
                                header.getContext()
                              )}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableHead>
                <TableBody>
                  {table.getRowModel().rows.map(row => (
                    <TableRow key={row.id}>
                      {row.getVisibleCells().map(cell => (
                        <TableCell key={cell.id}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={table.getFilteredRowModel().rows.length}
              rowsPerPage={table.getState().pagination.pageSize}
              page={table.getState().pagination.pageIndex}
              onPageChange={(_, page) => table.setPageIndex(page)}
              onRowsPerPageChange={e => {
                const size = e.target.value ? Number(e.target.value) : 10;
                table.setPageSize(size);
              }}
            />
          </CardContent>
        </Card>
      )}

      {activeTab === 1 && (
        <Card>
          <CardContent>
            <ChartVisualization data={filteredData} />
          </CardContent>
        </Card>
      )}

      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Sources
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Chip
                    label="Workflow Output (3 sources)"
                    color="success"
                    variant="outlined"
                  />
                  <Chip
                    label="MCP Streams (2 sources)"
                    color="info"
                    variant="outlined"
                  />
                  <Chip
                    label="Agent Results (2 sources)"
                    color="warning"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Data Quality
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Typography variant="body2">
                    Completeness: 98.5%
                  </Typography>
                  <Typography variant="body2">
                    Accuracy: 99.2%
                  </Typography>
                  <Typography variant="body2">
                    Consistency: 97.8%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {activeTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <WorkflowDataConnector />
          </Grid>
          <Grid item xs={12} md={6}>
            <MCPDataConnector />
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default DataSandboxOptimized;
