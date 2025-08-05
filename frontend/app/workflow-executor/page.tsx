'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import WorkflowExecutor from '@/pages/WorkflowExecutor';

export default function WorkflowExecutorPage() {
  return (
    <NextLayout>
      <WorkflowExecutor />
    </NextLayout>
  );
}