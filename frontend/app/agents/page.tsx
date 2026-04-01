import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import Agents from '@/components/pages/Agents';

// Disable static generation for this page
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function AgentsPage() {
  return (
    <NextLayout>
      <Agents />
    </NextLayout>
  );
}