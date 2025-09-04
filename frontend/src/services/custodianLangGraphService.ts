import { api } from './api';

export interface CustodianWorkflow {
  workflow_id: string;
  custodian_name: string;
  status: string;
  message: string;
}

export interface CustodianAnalysisRequest {
  endpoint: string;
  params?: Record<string, any>;
  user_question: string;
}

export interface CustodianAnalysisResult {
  data: {
    raw_data: any;
    record_count: number;
    columns: string[];
    extracted_at: string;
    dataframe_summary?: {
      shape: [number, number];
      columns: string[];
      dtypes: Record<string, string>;
      sample_data: Record<string, any>[];
      null_counts: Record<string, number>;
    };
  };
  analysis_results: {
    question: string;
    answer: string;
    analysis_timestamp: string;
  };
  context: {
    endpoint: string;
    params: Record<string, any>;
    user_question: string;
    workflow_id: string;
    execution_id: string;
    start_time: string;
    end_time: string;
    status: string;
  };
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
    node_id?: string;
  }>;
  errors: string[];
}

export interface CustodianConfig {
  name: string;
  base_url: string;
  auth_type: string;
  configured: boolean;
}

export interface CustodianConfigCreate {
  name: string;
  base_url: string;
  auth_type: string;
  api_key?: string;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  node_count: number;
  message: string;
}

export interface WorkflowList {
  workflows: Array<{
    workflow_id: string;
    node_count: number;
    status: string;
  }>;
  total_count: number;
}

class CustodianLangGraphService {
  private baseUrl = '/api/custodian-langgraph';

  // Workflow Management
  async createWorkflow(custodianName: string, apiKey?: string): Promise<CustodianWorkflow> {
    const response = await api.post<CustodianWorkflow>(`${this.baseUrl}/workflows/create`, {
      custodian_name: custodianName,
      api_key: apiKey
    });
    return response;
  }

  async executeAnalysis(
    workflowId: string, 
    request: CustodianAnalysisRequest
  ): Promise<CustodianAnalysisResult> {
    const response = await api.post<CustodianAnalysisResult>(
      `${this.baseUrl}/workflows/${workflowId}/execute`,
      request
    );
    return response;
  }

  async getWorkflowStatus(workflowId: string): Promise<WorkflowStatus> {
    const response = await api.get<WorkflowStatus>(`${this.baseUrl}/workflows/${workflowId}/status`);
    return response;
  }

  async deleteWorkflow(workflowId: string): Promise<{ workflow_id: string; status: string; message: string }> {
    const response = await api.delete<{ workflow_id: string; status: string; message: string }>(
      `${this.baseUrl}/workflows/${workflowId}`
    );
    return response;
  }

  async listWorkflows(): Promise<WorkflowList> {
    const response = await api.get<WorkflowList>(`${this.baseUrl}/workflows`);
    return response;
  }

  // Custodian Management
  async listCustodians(): Promise<CustodianConfig[]> {
    const response = await api.get<CustodianConfig[]>(`${this.baseUrl}/custodians`);
    return response;
  }

  async addCustodianConfig(config: CustodianConfigCreate): Promise<{
    name: string;
    base_url: string;
    auth_type: string;
    status: string;
    message: string;
  }> {
    const response = await api.post(`${this.baseUrl}/custodians`, config);
    return response;
  }
}

export const custodianLangGraphService = new CustodianLangGraphService();
