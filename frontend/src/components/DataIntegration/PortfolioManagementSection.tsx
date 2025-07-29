import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Avatar,
  Button,
  Chip,
  Alert,
} from '@mui/material';
import {
  Assessment as AssessmentIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';

interface PortfolioManagementSectionProps {
  onNewConnection: () => void;
}

const portfolioManagementSystems = [
  {
    id: 'blackrock-aladdin',
    name: 'BlackRock Aladdin',
    logo: '⚫',
    description: 'Comprehensive portfolio management and risk analytics platform',
    features: [
      'Portfolio Construction & Optimization',
      'Risk Analytics & Scenario Analysis',
      'Performance Attribution',
      'Order & Execution Management',
      'Compliance Monitoring',
      'Real-time Risk Monitoring'
    ],
    integrationStatus: 'available',
    dataTypes: ['Portfolios', 'Risk Metrics', 'Performance', 'Orders', 'Benchmarks']
  },
  {
    id: 'charles-river-crims',
    name: 'Charles River CRIMS',
    logo: '🌊',
    description: 'Investment management system for order and portfolio management',
    features: [
      'Order Management System (OMS)',
      'Portfolio Management System (PMS)',
      'Compliance & Risk Management',
      'Trade Allocation & Settlement',
      'Performance Measurement',
      'Client Reporting'
    ],
    integrationStatus: 'available',
    dataTypes: ['Orders', 'Allocations', 'Compliance', 'Performance', 'Portfolios']
  }
];

const PortfolioManagementSection: React.FC<PortfolioManagementSectionProps> = ({
  onNewConnection
}) => {
  return (
    <Box sx={{ mb: 4 }}>
      {/* Section Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: 'text.primary' }}>
          Portfolio Management Systems
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Connect to leading PMS platforms for comprehensive portfolio and risk management integration
        </Typography>
      </Box>

      {/* Overview Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
          Why Integrate Portfolio Management Systems?
        </Typography>
        <Typography variant="body2">
          Direct integration with PMS platforms enables real-time portfolio monitoring, automated risk analytics, 
          streamlined order management, and comprehensive performance attribution across your investment operations.
        </Typography>
      </Alert>

      {/* Portfolio Management System Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {portfolioManagementSystems.map((system) => (
          <Grid item xs={12} md={6} key={system.id}>
            <Card 
              sx={{ 
                height: '100%',
                borderRadius: 3,
                border: '1px solid',
                borderColor: 'divider',
                '&:hover': {
                  boxShadow: (theme) => theme.shadows[8],
                  transform: 'translateY(-4px)',
                  transition: 'all 0.3s ease-in-out'
                }
              }}
            >
              <CardContent sx={{ p: 3 }}>
                {/* Header */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <Typography variant="h3">{system.logo}</Typography>
                  <Box>
                    <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                      {system.name}
                    </Typography>
                    <Chip
                      label="Integration Available"
                      size="small"
                      color="success"
                      variant="outlined"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </Box>

                {/* Description */}
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3, lineHeight: 1.5 }}>
                  {system.description}
                </Typography>

                {/* Data Types */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                    Available Data Types:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {system.dataTypes.map((dataType) => (
                      <Chip
                        key={dataType}
                        label={dataType}
                        size="small"
                        variant="outlined"
                        sx={{ 
                          fontSize: '0.7rem',
                          borderColor: 'primary.main',
                          color: 'primary.main'
                        }}
                      />
                    ))}
                  </Box>
                </Box>

                {/* Key Features */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                    Key Integration Features:
                  </Typography>
                  <Box sx={{ pl: 1 }}>
                    {system.features.slice(0, 4).map((feature, index) => (
                      <Typography 
                        key={index}
                        variant="body2" 
                        color="text.secondary"
                        sx={{ 
                          fontSize: '0.8rem',
                          lineHeight: 1.4,
                          mb: 0.5,
                          '&::before': {
                            content: '"•"',
                            color: 'primary.main',
                            fontWeight: 'bold',
                            display: 'inline-block',
                            width: '1em',
                            marginLeft: '-1em'
                          }
                        }}
                      >
                        {feature}
                      </Typography>
                    ))}
                    {system.features.length > 4 && (
                      <Typography variant="caption" color="text.secondary">
                        +{system.features.length - 4} more features
                      </Typography>
                    )}
                  </Box>
                </Box>

                {/* Action Button */}
                <Button
                  variant="contained"
                  fullWidth
                  onClick={onNewConnection}
                  sx={{ 
                    borderRadius: 2,
                    textTransform: 'none',
                    fontWeight: 600
                  }}
                >
                  Configure Integration
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Integration Benefits */}
      <Card sx={{ borderRadius: 3, background: 'linear-gradient(135deg, #f6f9fc 0%, #e9f4ff 100%)' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, color: 'primary.main' }}>
            Portfolio Management Integration Benefits
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.light', color: 'primary.dark', width: 40, height: 40 }}>
                  <SpeedIcon />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Real-time Data
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Live portfolio positions and risk metrics
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.light', color: 'success.dark', width: 40, height: 40 }}>
                  <SecurityIcon />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Automated Compliance
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Real-time compliance monitoring and alerts
                  </Typography>
                </Box>
              </Box>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Avatar sx={{ bgcolor: 'info.light', color: 'info.dark', width: 40, height: 40 }}>
                  <AssessmentIcon />
                </Avatar>
                <Box>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    Advanced Analytics
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Comprehensive risk and performance analysis
                  </Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default PortfolioManagementSection;