import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import {
  SwapHoriz as SwapHorizIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
} from '@mui/icons-material';

const Transactions: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const mockTransactions = [
    {
      id: 'txn-001',
      tradeId: 'TRD20241201001',
      account: 'Global Equity Fund',
      security: 'AAPL',
      securityName: 'Apple Inc.',
      side: 'BUY',
      quantity: 1000,
      price: 150.25,
      grossAmount: 150250,
      netAmount: 150000,
      commission: 25,
      fees: 225,
      currency: 'USD',
      executionVenue: 'NASDAQ',
      status: 'SETTLED',
      tradeDate: '2024-01-15',
      settlementDate: '2024-01-17',
      custodian: 'State Street',
    },
    {
      id: 'txn-002',
      tradeId: 'TRD20241201002',
      account: 'Fixed Income Fund',
      security: 'MSFT',
      securityName: 'Microsoft Corporation',
      side: 'SELL',
      quantity: 500,
      price: 140.50,
      grossAmount: 70250,
      netAmount: 70000,
      commission: 15,
      fees: 235,
      currency: 'USD',
      executionVenue: 'NASDAQ',
      status: 'PENDING',
      tradeDate: '2024-01-16',
      settlementDate: '2024-01-18',
      custodian: 'BNY Mellon',
    },
  ];

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SETTLED':
        return 'success';
      case 'PENDING':
        return 'warning';
      case 'FAILED':
        return 'error';
      default:
        return 'default';
    }
  };

  const getSideColor = (side: string) => {
    return side === 'BUY' ? 'success' : 'error';
  };

  const filteredTransactions = mockTransactions.filter(txn => {
    const matchesStatus = filterStatus === 'all' || txn.status.toLowerCase() === filterStatus;
    const matchesSearch = searchTerm === '' || 
      txn.security.toLowerCase().includes(searchTerm.toLowerCase()) ||
      txn.securityName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      txn.tradeId.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SwapHorizIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Transactions
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Transactions
              </Typography>
              <Typography variant="h5" component="div">
                {mockTransactions.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Settled Today
              </Typography>
              <Typography variant="h5" component="div">
                {mockTransactions.filter(t => t.status === 'SETTLED').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Pending Settlement
              </Typography>
              <Typography variant="h5" component="div">
                {mockTransactions.filter(t => t.status === 'PENDING').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Volume
              </Typography>
              <Typography variant="h5" component="div">
                {formatCurrency(mockTransactions.reduce((sum, txn) => sum + txn.netAmount, 0))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search transactions..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
          />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={filterStatus}
              label="Status"
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="settled">Settled</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Box>
          <IconButton>
            <FilterIcon />
          </IconButton>
          <IconButton>
            <RefreshIcon />
          </IconButton>
          <IconButton>
            <DownloadIcon />
          </IconButton>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Trade ID</TableCell>
              <TableCell>Account</TableCell>
              <TableCell>Security</TableCell>
              <TableCell>Side</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">Net Amount</TableCell>
              <TableCell>Trade Date</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Custodian</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTransactions.map((transaction) => (
              <TableRow key={transaction.id} hover>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">
                    {transaction.tradeId}
                  </Typography>
                </TableCell>
                <TableCell>{transaction.account}</TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {transaction.security}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {transaction.securityName}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={transaction.side} 
                    color={getSideColor(transaction.side)} 
                    size="small" 
                  />
                </TableCell>
                <TableCell align="right">{formatNumber(transaction.quantity)}</TableCell>
                <TableCell align="right">{formatCurrency(transaction.price)}</TableCell>
                <TableCell align="right">{formatCurrency(transaction.netAmount)}</TableCell>
                <TableCell>{transaction.tradeDate}</TableCell>
                <TableCell>
                  <Chip 
                    label={transaction.status} 
                    color={getStatusColor(transaction.status)} 
                    size="small" 
                  />
                </TableCell>
                <TableCell>{transaction.custodian}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="body2" color="info.contrastText">
          <strong>Note:</strong> This is a placeholder page for custodian transaction management. 
          Future implementation will integrate with custodian APIs for real-time transaction data, 
          automated reconciliation, and FIBO ontology compliance for regulatory reporting.
        </Typography>
      </Box>
    </Box>
  );
};

export default Transactions;
