'use client';

/**
 * Canonical App Router login page for the Next.js frontend runtime.
 */
import React, { Suspense } from 'react';
import { CircularProgress, Box } from '@mui/material';
import Login from '@/components/pages/Login';

export const dynamic = 'force-dynamic';

function LoginWithSuspense() {
  return (
    <Suspense
      fallback={
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
          }}
        >
          <CircularProgress />
        </Box>
      }
    >
      <Login />
    </Suspense>
  );
}

export default function LoginPage() {
  return <LoginWithSuspense />;
}