'use client';

import React, { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import NextLayout from '@/components/Layout/NextLayout';
import WorkflowConfiguration from '@/components/pages/WorkflowConfiguration';

function WorkflowConfigurationContent() {
  const searchParams = useSearchParams();
  const workflowId = searchParams.get('id');
  const workflowType = searchParams.get('type') as 'langchain' | 'langgraph' || 'langchain';

  return (
    <WorkflowConfiguration 
      workflowId={workflowId || undefined}
      workflowType={workflowType}
    />
  );
}

export default function WorkflowConfigurationPage() {
  return (
    <NextLayout>
      <Suspense fallback={<div>Loading...</div>}>
        <WorkflowConfigurationContent />
      </Suspense>
    </NextLayout>
  );
}
