'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import KnowledgeGraph from '@/pages/KnowledgeGraph';

export const dynamic = 'force-dynamic';

export default function KnowledgeGraphPage() {
  return (
    <NextLayout>
      <KnowledgeGraph />
    </NextLayout>
  );
}