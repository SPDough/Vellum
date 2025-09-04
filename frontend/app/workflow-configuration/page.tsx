'use client';

import React from 'react';
import { useSearchParams } from 'next/navigation';
import NextLayout from '@/components/Layout/NextLayout';
import WorkflowConfiguration from '@/components/pages/WorkflowConfiguration';

export default function WorkflowConfigurationPage() {
  const searchParams = useSearchParams();
  const workflowId = searchParams.get('id');
  const workflowType = searchParams.get('type') as 'langchain' | 'langgraph' || 'langchain';

  return (
    <NextLayout>
      <WorkflowConfiguration 
        workflowId={workflowId || undefined}
        workflowType={workflowType}
      />
    </NextLayout>
  );
}
