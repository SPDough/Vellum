import React from 'react';
import { useSearchParams } from 'react-router-dom';
import WorkflowConfiguration from '@/components/pages/WorkflowConfiguration';

export default function WorkflowConfigurationPage() {
  const [searchParams] = useSearchParams();
  const workflowId = searchParams.get('id');
  const workflowType = (searchParams.get('type') as 'langchain' | 'langgraph') || 'langchain';

  return (
    <WorkflowConfiguration
      workflowId={workflowId || undefined}
      workflowType={workflowType}
    />
  );
}
