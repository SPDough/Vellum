import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import DataIntegration from '@/components/pages/DataIntegration';

// Disable static generation for this page
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export default function DataPage() {
  return (
    <NextLayout>
      <DataIntegration />
    </NextLayout>
  );
}