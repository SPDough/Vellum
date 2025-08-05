'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import DataSourceConfiguration from '@/pages/DataSourceConfiguration';

export const dynamic = 'force-dynamic';

export default function DataSourcesPage() {
  return (
    <NextLayout>
      <DataSourceConfiguration />
    </NextLayout>
  );
}