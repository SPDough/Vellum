'use client';

import React from 'react';
import NextLayout from '@/components/Layout/NextLayout';
import WorkflowBuilder from '@/components/pages/WorkflowBuilder';

export default function WorkflowBuilderPage() {
  return (
    <NextLayout>
      <WorkflowBuilder />
    </NextLayout>
  );
}