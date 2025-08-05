import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import KnowledgeGraph from '@/pages/KnowledgeGraph';

// Disable static generation for this page
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export default function KnowledgeGraphPage() {
  return (
    <NextLayout>
      <KnowledgeGraph />
    </NextLayout>
  );
}