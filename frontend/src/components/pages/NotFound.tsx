import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Typography } from '@mui/material';

export default function NotFound() {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        textAlign: 'center',
        p: 3,
      }}
    >
      <Typography variant="h2" sx={{ fontWeight: 700 }}>
        404
      </Typography>
      <Typography variant="h6" color="text.secondary">
        This page doesn't exist.
      </Typography>
      <Button component={Link} to="/" variant="contained">
        Back to home
      </Button>
    </Box>
  );
}
