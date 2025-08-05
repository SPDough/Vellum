'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import DataSourceConfiguration from '@/pages/DataSourceConfiguration';

export default function DataSourcesPage() {
  return (
    <NextLayout>
      <DataSourceConfiguration />
    </NextLayout>
  );
}