'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  Stack,
  Typography,
} from '@mui/material';
import {
  AutoAwesome as AutoAwesomeIcon,
  FactCheck as FactCheckIcon,
  Hub as HubIcon,
  Rule as RuleIcon,
  SyncAlt as SyncAltIcon,
} from '@mui/icons-material';

const coreCapabilities = [
  {
    title: 'Integrate the operating stack',
    description:
      'Connect OMS, IBOR, ABOR, and CBOR data into canonical contracts that preserve lineage from investment intent to downstream outcome.',
    icon: <HubIcon color="primary" />,
  },
  {
    title: 'Apply deterministic controls',
    description:
      'Use proprietary rules to identify timing, lifecycle, quantity, cash, valuation, corporate-action, and governance breaks.',
    icon: <RuleIcon color="primary" />,
  },
  {
    title: 'Orchestrate workflows',
    description:
      'Route meaningful exceptions to the right owner, queue, and signoff path instead of forcing teams to sift through every mismatch.',
    icon: <SyncAltIcon color="primary" />,
  },
  {
    title: 'Accelerate resolution with AI',
    description:
      'Use RAG, LLMs, and agentic workflows to retrieve evidence, explain breaks, and support operator investigation and drafting.',
    icon: <AutoAwesomeIcon color="primary" />,
  },
];

const breakTypes = [
  'Timing mismatch',
  'Lifecycle mismatch',
  'Reference / enrichment mismatch',
  'Quantity mismatch',
  'Cash mismatch',
  'Valuation mismatch',
  'Corporate-action mismatch',
  'Missing-record mismatch',
  'Signoff / governance state mismatch',
];

export default function HomePage() {
  return (
    <NextLayout>
      <Box sx={{ py: { xs: 4, md: 6 } }}>
        <Container maxWidth="xl">
          <Stack spacing={6}>
            <Box
              sx={{
                p: { xs: 3, md: 5 },
                borderRadius: 4,
                background:
                  'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(168, 85, 247, 0.08) 100%)',
                border: '1px solid rgba(139, 92, 246, 0.12)',
              }}
            >
              <Stack spacing={3} maxWidth="900px">
                <Chip
                  label="The control layer for buy-side operations"
                  color="primary"
                  sx={{ alignSelf: 'flex-start', fontWeight: 600 }}
                />
                <Typography variant="h2" sx={{ fontWeight: 700, lineHeight: 1.1 }}>
                  Automate and verify middle- and back-office workflows across OMS,
                  IBOR, ABOR, and CBOR environments.
                </Typography>
                <Typography variant="h6" color="text.secondary" sx={{ maxWidth: 800 }}>
                  Vellum integrates buy-side operating data, applies proprietary rules,
                  orchestrates workflows, and uses AI to help teams detect meaningful
                  breaks, route exceptions, and resolve them faster with stronger evidence
                  and governance.
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                  <Button variant="contained" size="large">
                    Book a demo
                  </Button>
                  <Button variant="outlined" size="large">
                    See how it works
                  </Button>
                </Stack>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  Match everything. Escalate only exceptions.
                </Typography>
              </Stack>
            </Box>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3.5 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                      The problem
                    </Typography>
                    <Typography color="text.secondary" sx={{ mb: 2 }}>
                      Buy-side firms still depend on fragmented OMS, IBOR, ABOR, and CBOR
                      environments, manual reconciliations, and brittle exception workflows.
                    </Typography>
                    <Typography color="text.secondary">
                      That creates timing gaps, lifecycle mismatches, data-quality issues,
                      weak workflow visibility, and unnecessary operational and reimbursement
                      risk.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3.5 }}>
                    <Typography variant="h5" sx={{ fontWeight: 700, mb: 2 }}>
                      The solution
                    </Typography>
                    <Typography color="text.secondary" sx={{ mb: 2 }}>
                      Vellum is a rules-based, AI-enhanced workflow and control platform
                      for asset managers and asset owners.
                    </Typography>
                    <Typography color="text.secondary">
                      Instead of asking teams to inspect every mismatch, Vellum helps them
                      focus on the exceptions that actually matter — with deterministic
                      controls first and AI where it helps.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>

            <Box>
              <Typography variant="h4" sx={{ fontWeight: 700, mb: 1.5 }}>
                How Vellum works
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                From investment intent to operational truth.
              </Typography>
              <Grid container spacing={3}>
                {coreCapabilities.map((capability) => (
                  <Grid item xs={12} md={6} key={capability.title}>
                    <Card sx={{ height: '100%' }}>
                      <CardContent sx={{ p: 3.5 }}>
                        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                          {capability.icon}
                          <Typography variant="h6" sx={{ fontWeight: 700 }}>
                            {capability.title}
                          </Typography>
                        </Stack>
                        <Typography color="text.secondary">
                          {capability.description}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>

            <Card>
              <CardContent sx={{ p: 3.5 }}>
                <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
                  <FactCheckIcon color="primary" />
                  <Typography variant="h5" sx={{ fontWeight: 700 }}>
                    Core break types
                  </Typography>
                </Stack>
                <Typography color="text.secondary" sx={{ mb: 3 }}>
                  Vellum classifies meaningful operational exceptions instead of treating
                  every difference as equally important.
                </Typography>
                <Stack direction="row" flexWrap="wrap" gap={1.25}>
                  {breakTypes.map((item) => (
                    <Chip key={item} label={item} variant="outlined" />
                  ))}
                </Stack>
              </CardContent>
            </Card>

            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3.5 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                      Reduce manual reconciliation effort
                    </Typography>
                    <Typography color="text.secondary">
                      Catch breaks earlier and keep teams focused on true exceptions rather
                      than repetitive manual comparison work.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3.5 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                      Improve evidence, ownership, and signoff
                    </Typography>
                    <Typography color="text.secondary">
                      Preserve clearer lineage from OMS intent through downstream outcome
                      with governed workflows and audit-friendly operational controls.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={4}>
                <Card sx={{ height: '100%' }}>
                  <CardContent sx={{ p: 3.5 }}>
                    <Typography variant="h6" sx={{ fontWeight: 700, mb: 1.5 }}>
                      Move beyond brittle IBOR-heavy workflows
                    </Typography>
                    <Typography color="text.secondary">
                      Use canonical contracts, deterministic rules, and AI-enhanced
                      workflows to modernize buy-side operations without relying on another
                      passive dashboard layer.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Stack>
        </Container>
      </Box>
    </NextLayout>
  );
}
