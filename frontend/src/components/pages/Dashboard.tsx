import React from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Chip,
  LinearProgress,
  Paper,
  Typography,
} from '@mui/material';
import {
  AccountTree,
  Storage,
  Psychology,
  Search,
  Gavel,
  ArrowOutward,
} from '@mui/icons-material';

const dashboardStats = [
  { title: 'Active Workflows', value: '8', change: '3 running now', icon: <AccountTree />, color: 'info.main' },
  { title: 'Data Sources', value: '24', change: '2 refreshed today', icon: <Storage />, color: 'primary.main' },
  { title: 'Knowledge Graph Health', value: '95%', change: 'Sync stable', icon: <Psychology />, color: 'success.main' },
  { title: 'Rules Coverage', value: '41', change: '6 recently updated', icon: <Gavel />, color: 'warning.main' },
];

const quickActions = [
  { title: 'Explore Data Sandbox', description: 'Filter records, inspect sources, and export data', icon: <Storage />, cta: 'Open Sandbox' },
  { title: 'Run Workflows', description: 'Execute automation and orchestration flows', icon: <AccountTree />, cta: 'Open Workflows' },
  { title: 'Search Platform', description: 'Find data, rules, workflows, and graph entities', icon: <Search />, cta: 'Open Search' },
  { title: 'Open Knowledge Graph', description: 'Navigate ontology and linked operational context', icon: <Psychology />, cta: 'Open Graph' },
];

const recentActivity = [
  { type: 'Workflow', name: 'Trade settlement automation completed', time: '2 min ago', status: 'success' },
  { type: 'Data', name: 'Sandbox source refresh finished', time: '14 min ago', status: 'info' },
  { type: 'Rules', name: 'Exception handling policy updated', time: '1 hour ago', status: 'warning' },
  { type: 'Graph', name: 'Knowledge graph sync completed', time: '3 hours ago', status: 'success' },
];

const performanceItems = [
  { label: 'Workflow Engine', value: 92, color: 'success' as const },
  { label: 'Data Processing', value: 87, color: 'primary' as const },
  { label: 'Knowledge Graph Sync', value: 95, color: 'success' as const },
];

const Dashboard: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Financial Intelligence Dashboard
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Monitor workflows, data systems, and operational intelligence across the platform.
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr', md: 'repeat(4, 1fr)' }, gap: 3, mb: 4 }}>
        {dashboardStats.map((stat) => (
          <Card key={stat.title} sx={{ borderRadius: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                <Typography variant="h6" sx={{ ml: 1, fontWeight: 700 }}>
                  {stat.title}
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: stat.color, fontWeight: 700 }}>
                {stat.value}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {stat.change}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '2fr 1fr' }, gap: 4, mb: 4 }}>
        <Card sx={{ borderRadius: 3 }}>
          <CardHeader title="Quick Actions" titleTypographyProps={{ fontWeight: 700 }} />
          <CardContent>
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
              {quickActions.map((action) => (
                <Paper key={action.title} sx={{ p: 2.5, borderRadius: 3, '&:hover': { bgcolor: 'action.hover' }, transition: 'background-color 0.2s' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, gap: 1 }}>
                    {action.icon}
                    <Typography variant="h6" sx={{ fontWeight: 700 }}>{action.title}</Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {action.description}
                  </Typography>
                  <Button size="small" endIcon={<ArrowOutward />}>{action.cta}</Button>
                </Paper>
              ))}
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ borderRadius: 3 }}>
          <CardHeader title="Recent Activity" titleTypographyProps={{ fontWeight: 700 }} />
          <CardContent>
            <Box sx={{ maxHeight: 320, overflow: 'auto' }}>
              {recentActivity.map((activity, index) => (
                <Box key={`${activity.type}-${index}`} sx={{ mb: 2, pb: 2, borderBottom: index < recentActivity.length - 1 ? 1 : 0, borderColor: 'divider' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="subtitle2">{activity.name}</Typography>
                    <Chip label={activity.type} size="small" variant="outlined" color={activity.status as any} />
                  </Box>
                  <Typography variant="body2" color="text.secondary">{activity.time}</Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      </Box>

      <Card sx={{ borderRadius: 3 }}>
        <CardHeader title="System Performance" titleTypographyProps={{ fontWeight: 700 }} />
        <CardContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}>
            {performanceItems.map((item) => (
              <Box key={item.label}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">{item.label}</Typography>
                  <Typography variant="body2">{item.value}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={item.value} color={item.color} />
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard;
