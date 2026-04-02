import React, { useState } from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material';
import {
  Download as DownloadIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  SwapHoriz as SwapHorizIcon,
} from '@mui/icons-material';

const Transactions: React.FC = () => {
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const mockTransactions = [
    {
      id: 'txn-001',
      tradeId: 'TRD20241201001',
      surface: 'OMS → ABOR',
      account: 'Global Equity Fund',
      security: 'AAPL',
      securityName: 'Apple Inc.',
      side: 'BUY',
      quantity: 1000,
      price: 150.25,
      netAmount: 150000,
      breakType: 'LIFECYCLE_MISMATCH',
      status: 'EXCEPTION_OPEN',
      tradeDate: '2024-01-15',
      settlementDate: '2024-01-17',
      downstreamBook: 'State Street',
    },
    {
      id: 'txn-002',
      tradeId: 'TRD20241201002',
      surface: 'IBOR → CBOR',
      account: 'Fixed Income Fund',
      security: 'MSFT',
      securityName: 'Microsoft Corporation',
      side: 'SELL',
      quantity: 500,
      price: 140.5,
      netAmount: 70000,
      breakType: 'MATCHED',
      status: 'MATCHED',
      tradeDate: '2024-01-16',
      settlementDate: '2024-01-18',
      downstreamBook: 'BNY Mellon',
    },
  ];

  const formatCurrency = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  const formatNumber = (num: number) => new Intl.NumberFormat('en-US').format(num);

  const filteredTransactions = mockTransactions.filter((txn) => {
    const matchesStatus = filterStatus === 'all' || txn.status.toLowerCase() === filterStatus;
    const matchesSearch = searchTerm === '' || txn.security.toLowerCase().includes(searchTerm.toLowerCase()) || txn.securityName.toLowerCase().includes(searchTerm.toLowerCase()) || txn.tradeId.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <SwapHorizIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4">Transactions</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 920 }}>
        Transaction views in Vellum should show how trade intent propagates through the operating stack, where lifecycle state diverges, and which records need workflow intervention.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Compared transactions</Typography><Typography variant="h5">{mockTransactions.length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Matched trades</Typography><Typography variant="h5">{mockTransactions.filter((t) => t.breakType === 'MATCHED').length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Open transaction breaks</Typography><Typography variant="h5" color="warning.main">{mockTransactions.filter((t) => t.breakType !== 'MATCHED').length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Net notional tracked</Typography><Typography variant="h5">{formatCurrency(mockTransactions.reduce((sum, txn) => sum + txn.netAmount, 0))}</Typography></CardContent></Card></Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField size="small" placeholder="Search transactions..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} /> }} />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select value={filterStatus} label="Status" onChange={(e) => setFilterStatus(e.target.value)}>
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="matched">Matched</MenuItem>
              <MenuItem value="exception_open">Exception Open</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Box>
          <IconButton><FilterIcon /></IconButton>
          <IconButton><RefreshIcon /></IconButton>
          <IconButton><DownloadIcon /></IconButton>
        </Box>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Trade ID</TableCell>
              <TableCell>Surface</TableCell>
              <TableCell>Account</TableCell>
              <TableCell>Security</TableCell>
              <TableCell>Side</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">Net Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Downstream Book</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredTransactions.map((transaction) => (
              <TableRow key={transaction.id} hover>
                <TableCell><Typography variant="body2" fontWeight="bold">{transaction.tradeId}</Typography></TableCell>
                <TableCell>{transaction.surface}</TableCell>
                <TableCell>{transaction.account}</TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">{transaction.security}</Typography>
                    <Typography variant="caption" color="text.secondary">{transaction.securityName}</Typography>
                  </Box>
                </TableCell>
                <TableCell><Chip label={transaction.side} color={transaction.side === 'BUY' ? 'success' : 'error'} size="small" /></TableCell>
                <TableCell align="right">{formatNumber(transaction.quantity)}</TableCell>
                <TableCell align="right">{formatCurrency(transaction.price)}</TableCell>
                <TableCell align="right">{formatCurrency(transaction.netAmount)}</TableCell>
                <TableCell><Chip label={transaction.status.replace('_', ' ')} color={transaction.breakType === 'MATCHED' ? 'success' : 'warning'} size="small" /></TableCell>
                <TableCell>{transaction.downstreamBook}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Alert severity="info" sx={{ mt: 3 }}>
        Long term, this view should support lifecycle mismatch detection, missing-record checks, settlement-state drift, and direct routing into transaction investigation workflows.
      </Alert>
    </Box>
  );
};

export default Transactions;
