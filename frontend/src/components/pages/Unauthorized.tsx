import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Button, Typography } from '@mui/material';

export default function Unauthorized() {
  return (
    <Box
      sx={{
        minHeight: '60vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 2,
        textAlign: 'center',
        p: 3,
      }}
    >
      <Typography variant="h4" sx={{ fontWeight: 700 }}>
        Not authorized
      </Typography>
      <Typography color="text.secondary">
        You don't have permission to view this page.
      </Typography>
      <Button component={Link} to="/" variant="contained">
        Back to home
      </Button>
    </Box>
  );
}
