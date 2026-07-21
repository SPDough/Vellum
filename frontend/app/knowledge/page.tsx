import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import KnowledgeChat from '@/components/pages/KnowledgeChat';

// Disable static generation for this page
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function KnowledgePage() {
  return (
    <NextLayout>
      <KnowledgeChat />
    </NextLayout>
  );
}
