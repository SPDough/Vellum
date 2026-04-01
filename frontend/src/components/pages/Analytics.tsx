import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Alert,
} from '@mui/material';

const Analytics: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" sx={{ fontWeight: 600, mb: 3 }}>
        Analytics
      </Typography>
      
      <Card sx={{ borderRadius: 3 }}>
        <CardContent>
          <Alert severity="info">
            Analytics dashboard will be implemented in the next phase.
          </Alert>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Analytics;