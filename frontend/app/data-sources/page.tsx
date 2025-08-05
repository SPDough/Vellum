import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import DataSourceConfiguration from '@/pages/DataSourceConfiguration';

// Disable static generation for this page
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export default function DataSourcesPage() {
  return (
    <NextLayout>
      <DataSourceConfiguration />
    </NextLayout>
  );
}