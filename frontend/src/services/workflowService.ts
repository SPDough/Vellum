import { api } from './api';
import { Workflow } from '@/types/workflow';

export interface WorkflowCreateRequest {
  name: string;
  description?: string;
  nodes: any[];
  edges: any[];
  triggers?: any[];
  execution_settings?: Record<string, any>;
}

export interface WorkflowUpdateRequest {
  name?: string;
  description?: string;
  nodes?: any[];
  edges?: any[];
  triggers?: any[];
  execution_settings?: Record<string, any>;
  enabled?: boolean;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  trigger_type: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  started_at: string;
  completed_at?: string;
  error_message?: string;
  execution_steps: any[];
}

export interface WorkflowExecutionRequest {
  input_data?: Record<string, any>;
  trigger_type?: string;
}

export const workflowService = {
  // List all workflows
  async listWorkflows(params?: {
    status?: string;
    enabled_only?: boolean;
  }): Promise<Workflow[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.enabled_only) {
      queryParams.append('enabled_only', params.enabled_only.toString());
    }
    
    const url = `/workflows/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<Workflow[]>(url);
  },

  // Create a new workflow
  async createWorkflow(workflowData: WorkflowCreateRequest): Promise<Workflow> {
    return api.post<Workflow>('/workflows/', workflowData);
  },

  // Get a specific workflow
  async getWorkflow(workflowId: string): Promise<Workflow> {
    return api.get<Workflow>(`/workflows/${workflowId}`);
  },

  // Update a workflow
  async updateWorkflow(workflowId: string, updateData: WorkflowUpdateRequest): Promise<Workflow> {
    return api.put<Workflow>(`/workflows/${workflowId}`, updateData);
  },

  // Delete a workflow
  async deleteWorkflow(workflowId: string): Promise<{ message: string }> {
    return api.delete(`/workflows/${workflowId}`);
  },

  // Activate a workflow
  async activateWorkflow(workflowId: string): Promise<{ message: string }> {
    return api.post(`/workflows/${workflowId}/activate`);
  },

  // Deactivate a workflow
  async deactivateWorkflow(workflowId: string): Promise<{ message: string }> {
    return api.post(`/workflows/${workflowId}/deactivate`);
  },

  // Execute a workflow
  async executeWorkflow(workflowId: string, executionRequest: WorkflowExecutionRequest): Promise<WorkflowExecution> {
    return api.post<WorkflowExecution>(`/workflows/${workflowId}/execute`, executionRequest);
  },

  // List workflow executions
  async listWorkflowExecutions(workflowId: string, params?: {
    status?: string;
    limit?: number;
  }): Promise<WorkflowExecution[]> {
    const queryParams = new URLSearchParams();
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    
    const url = `/workflows/${workflowId}/executions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<WorkflowExecution[]>(url);
  },

  // Get workflow execution details
  async getWorkflowExecution(workflowId: string, executionId: string): Promise<WorkflowExecution> {
    return api.get<WorkflowExecution>(`/workflows/${workflowId}/executions/${executionId}`);
  },

  // Cancel workflow execution
  async cancelWorkflowExecution(workflowId: string, executionId: string): Promise<{ message: string }> {
    return api.post(`/workflows/${workflowId}/executions/${executionId}/cancel`);
  },

  // Validate workflow
  async validateWorkflow(workflowId: string): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
    workflow_id: string;
  }> {
    return api.get(`/workflows/${workflowId}/validate`);
  },
};