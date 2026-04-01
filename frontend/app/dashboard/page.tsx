'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import Dashboard from '@/components/pages/Dashboard';

/**
 * Canonical App Router dashboard page.
 */
export default function DashboardPage() {
  return (
    <NextLayout>
      <Dashboard />
    </NextLayout>
  );
}
