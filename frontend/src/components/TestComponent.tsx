import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const TestComponent: React.FC = () => {
  return (
    <Box p={3}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          🎉 Otomeshon is Working!
        </Typography>
        <Typography variant="body1">
          This is a test component to verify the application is loading correctly.
        </Typography>
      </Paper>
    </Box>
  );
};

export default TestComponent;