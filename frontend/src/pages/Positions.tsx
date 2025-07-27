import React from 'react';
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
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';

const Positions: React.FC = () => {
  const mockPositions = [
    {
      id: 'pos-001',
      account: 'Global Equity Fund',
      security: 'AAPL',
      securityName: 'Apple Inc.',
      quantity: 10000,
      marketValue: 1500000,
      unrealizedPnL: 50000,
      currency: 'USD',
      custodian: 'State Street',
    },
    {
      id: 'pos-002',
      account: 'Fixed Income Fund',
      security: 'MSFT',
      securityName: 'Microsoft Corporation',
      quantity: 5000,
      marketValue: 1750000,
      unrealizedPnL: 75000,
      currency: 'USD',
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

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <AccountBalanceIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4" component="h1">
          Positions
        </Typography>
      </Box>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Positions
              </Typography>
              <Typography variant="h5" component="div">
                {mockPositions.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Market Value
              </Typography>
              <Typography variant="h5" component="div">
                {formatCurrency(mockPositions.reduce((sum, pos) => sum + pos.marketValue, 0))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total P&amp;L
              </Typography>
              <Typography variant="h5" component="div" color="success.main">
                {formatCurrency(mockPositions.reduce((sum, pos) => sum + pos.unrealizedPnL, 0))}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Custodians
              </Typography>
              <Typography variant="h5" component="div">
                2
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Position Holdings</Typography>
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
              <TableCell>Account</TableCell>
              <TableCell>Security</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Market Value</TableCell>
              <TableCell align="right">Unrealized P&amp;L</TableCell>
              <TableCell>Custodian</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockPositions.map((position) => (
              <TableRow key={position.id} hover>
                <TableCell>{position.account}</TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2" fontWeight="bold">
                      {position.security}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {position.securityName}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">{formatNumber(position.quantity)}</TableCell>
                <TableCell align="right">{formatCurrency(position.marketValue)}</TableCell>
                <TableCell align="right">
                  <Typography
                    color={position.unrealizedPnL >= 0 ? 'success.main' : 'error.main'}
                  >
                    {formatCurrency(position.unrealizedPnL)}
                  </Typography>
                </TableCell>
                <TableCell>{position.custodian}</TableCell>
                <TableCell>
                  <Chip label="Active" color="success" size="small" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
        <Typography variant="body2" color="info.contrastText">
          <strong>Note:</strong> This is a placeholder page for custodian position management. 
          Future implementation will integrate with custodian APIs (State Street, BNY Mellon) 
          and FIBO ontology mapping for semantic data consistency.
        </Typography>
      </Box>
    </Box>
  );
};

export default Positions;
