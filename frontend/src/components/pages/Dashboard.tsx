import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material';
import {
  AccountTree,
  AutoAwesome,
  CompareArrows,
  Hub,
  Rule,
  WarningAmber,
} from '@mui/icons-material';

const operatingBreaks = [
  'Timing mismatch',
  'Lifecycle mismatch',
  'Quantity mismatch',
  'Cash mismatch',
  'Valuation mismatch',
  'Signoff / governance mismatch',
];

const Dashboard: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            Buy-side operations control center
          </Typography>
          <Typography color="text.secondary" sx={{ maxWidth: 900 }}>
            Vellum helps asset managers and asset owners automate and verify the path from
            investment intent to operational outcome across OMS, IBOR, ABOR, and CBOR
            environments.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)', color: 'white', borderRadius: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>18</Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>Active cross-stack controls</Typography>
                  </Box>
                  <Rule sx={{ fontSize: 40, opacity: 0.85 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white', borderRadius: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>42</Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>Workflow cases orchestrated</Typography>
                  </Box>
                  <AccountTree sx={{ fontSize: 40, opacity: 0.85 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)', color: 'white', borderRadius: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>9</Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>Connected operating surfaces</Typography>
                  </Box>
                  <Hub sx={{ fontSize: 40, opacity: 0.85 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)', color: 'white', borderRadius: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>7</Typography>
                    <Typography variant="body2" sx={{ opacity: 0.9 }}>Meaningful exceptions open</Typography>
                  </Box>
                  <WarningAmber sx={{ fontSize: 40, opacity: 0.85 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Operating model status
                </Typography>
                <Box sx={{ mb: 2.5 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    OMS → IBOR / control layer coverage
                  </Typography>
                  <LinearProgress variant="determinate" value={84} sx={{ height: 8, borderRadius: 4 }} />
                </Box>
                <Box sx={{ mb: 2.5 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    IBOR / control layer → ABOR / CBOR workflow readiness
                  </Typography>
                  <LinearProgress variant="determinate" value={72} sx={{ height: 8, borderRadius: 4 }} color="success" />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Evidence, signoff, and AI-assist coverage
                  </Typography>
                  <LinearProgress variant="determinate" value={67} sx={{ height: 8, borderRadius: 4 }} color="secondary" />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={5}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
                  Core break taxonomy
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Vellum classifies operational differences so only meaningful exceptions are routed into governed workflows.
                </Typography>
                <Stack direction="row" flexWrap="wrap" gap={1}>
                  {operatingBreaks.map((item) => (
                    <Chip key={item} label={item} variant="outlined" />
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                  <CompareArrows color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Match everything
                  </Typography>
                </Box>
                <Typography color="text.secondary">
                  Normalize OMS, IBOR, ABOR, and CBOR data into canonical contracts and preserve lineage from investment intent to downstream outcome.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                  <Rule color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Escalate only exceptions
                  </Typography>
                </Box>
                <Typography color="text.secondary">
                  Apply deterministic rules and route only true breaks into workflow cases with clear ownership, severity, and signoff state.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ borderRadius: 3, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 1.5 }}>
                  <AutoAwesome color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    Use AI where it helps
                  </Typography>
                </Box>
                <Typography color="text.secondary">
                  Use RAG, LLMs, and agentic workflows for evidence retrieval, operator guidance, draft communications, and faster investigation.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Stack>
    </Box>
  );
};

export default Dashboard;
