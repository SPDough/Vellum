import React from 'react';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  AccountBalance as AccountBalanceIcon,
  Download as DownloadIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const Positions: React.FC = () => {
  const mockPositions = [
    {
      id: 'pos-001',
      surface: 'OMS vs ABOR',
      account: 'Global Equity Fund',
      security: 'AAPL',
      securityName: 'Apple Inc.',
      expectedQuantity: 10000,
      observedQuantity: 9950,
      marketValue: 1500000,
      breakType: 'QUANTITY_MISMATCH',
      currency: 'USD',
      downstreamBook: 'State Street',
      status: 'Exception Open',
    },
    {
      id: 'pos-002',
      surface: 'IBOR vs CBOR',
      account: 'Fixed Income Fund',
      security: 'MSFT',
      securityName: 'Microsoft Corporation',
      expectedQuantity: 5000,
      observedQuantity: 5000,
      marketValue: 1750000,
      breakType: 'MATCHED',
      currency: 'USD',
      downstreamBook: 'BNY Mellon',
      status: 'Matched',
    },
  ];

  const formatCurrency = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
  const formatNumber = (num: number) => new Intl.NumberFormat('en-US').format(num);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
        <AccountBalanceIcon sx={{ mr: 2, fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h4">Positions</Typography>
      </Box>
      <Typography color="text.secondary" sx={{ mb: 3, maxWidth: 920 }}>
        Position views in Vellum should help operators compare expected and observed state across OMS, IBOR, ABOR, and CBOR surfaces — not just display holdings in isolation.
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Compared position records</Typography><Typography variant="h5">{mockPositions.length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Downstream market value</Typography><Typography variant="h5">{formatCurrency(mockPositions.reduce((sum, pos) => sum + pos.marketValue, 0))}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Open position breaks</Typography><Typography variant="h5" color="warning.main">{mockPositions.filter((pos) => pos.breakType !== 'MATCHED').length}</Typography></CardContent></Card></Grid>
        <Grid item xs={12} sm={6} md={3}><Card><CardContent><Typography color="text.secondary">Comparison surfaces</Typography><Typography variant="h5">2</Typography></CardContent></Card></Grid>
      </Grid>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Cross-stack position comparison</Typography>
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
              <TableCell>Surface</TableCell>
              <TableCell>Account</TableCell>
              <TableCell>Security</TableCell>
              <TableCell align="right">Expected Qty</TableCell>
              <TableCell align="right">Observed Qty</TableCell>
              <TableCell align="right">Difference</TableCell>
              <TableCell align="right">Market Value</TableCell>
              <TableCell>Downstream Book</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockPositions.map((position) => {
              const difference = position.expectedQuantity - position.observedQuantity;
              return (
                <TableRow key={position.id} hover>
                  <TableCell>{position.surface}</TableCell>
                  <TableCell>{position.account}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2" fontWeight="bold">{position.security}</Typography>
                      <Typography variant="caption" color="text.secondary">{position.securityName}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell align="right">{formatNumber(position.expectedQuantity)}</TableCell>
                  <TableCell align="right">{formatNumber(position.observedQuantity)}</TableCell>
                  <TableCell align="right">
                    <Typography color={difference === 0 ? 'success.main' : 'error.main'}>{formatNumber(difference)}</Typography>
                  </TableCell>
                  <TableCell align="right">{formatCurrency(position.marketValue)}</TableCell>
                  <TableCell>{position.downstreamBook}</TableCell>
                  <TableCell>
                    <Chip label={position.status} color={position.breakType === 'MATCHED' ? 'success' : 'warning'} size="small" />
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>

      <Alert severity="info" sx={{ mt: 3 }}>
        Long term, this view should support OMS → IBOR → ABOR / CBOR lineage, break classification, evidence links, and direct workflow-case creation for unresolved position differences.
      </Alert>
    </Box>
  );
};

export default Positions;
