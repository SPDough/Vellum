'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import DataIntegration from '@/pages/DataIntegration';

export const dynamic = 'force-dynamic';

export default function DataPage() {
  return (
    <NextLayout>
      <DataIntegration />
    </NextLayout>
  );
}