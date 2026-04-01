'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import WorkflowManagement from '@/components/pages/WorkflowManagement';

export default function WorkflowsPage() {
  return (
    <NextLayout>
      <WorkflowManagement />
    </NextLayout>
  );
}