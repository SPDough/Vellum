import { api } from './api';
import { 
  Agent, 
  AgentCreateRequest, 
  AgentUpdateRequest, 
  AgentExecution, 
  AgentConversation,
  AgentTemplate,
  AgentChatRequest,
  AgentChatResponse,
  AgentType,
  AgentStatus
} from '@/types/agent';

export const agentService = {
  // Agent Management
  async listAgents(params?: {
    agent_type?: AgentType;
    status?: AgentStatus;
    capabilities?: string[];
    tags?: string[];
    limit?: number;
  }): Promise<Agent[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.agent_type) {
      queryParams.append('agent_type', params.agent_type);
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.capabilities) {
      params.capabilities.forEach(cap => queryParams.append('capabilities', cap));
    }
    if (params?.tags) {
      params.tags.forEach(tag => queryParams.append('tags', tag));
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }

    const url = `/agents/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<Agent[]>(url);
  },

  async createAgent(agentData: AgentCreateRequest): Promise<Agent> {
    return api.post<Agent>('/agents/', agentData);
  },

  async getAgent(agentId: string): Promise<Agent> {
    return api.get<Agent>(`/agents/${agentId}`);
  },

  async updateAgent(agentId: string, updateData: AgentUpdateRequest): Promise<Agent> {
    return api.put<Agent>(`/agents/${agentId}`, updateData);
  },

  async deleteAgent(agentId: string): Promise<{ message: string }> {
    return api.delete(`/agents/${agentId}`);
  },

  async activateAgent(agentId: string): Promise<{ message: string }> {
    return api.post(`/agents/${agentId}/activate`);
  },

  async deactivateAgent(agentId: string): Promise<{ message: string }> {
    return api.post(`/agents/${agentId}/deactivate`);
  },

  async cloneAgent(agentId: string, newName: string): Promise<Agent> {
    return api.post(`/agents/${agentId}/clone`, { name: newName });
  },

  // Agent Templates
  async listTemplates(): Promise<AgentTemplate[]> {
    return api.get<AgentTemplate[]>('/agents/templates/');
  },

  async getTemplate(templateId: string): Promise<AgentTemplate> {
    return api.get<AgentTemplate>(`/agents/templates/${templateId}`);
  },

  async createAgentFromTemplate(templateId: string, agentData: {
    name: string;
    description?: string;
    customizations?: Record<string, any>;
  }): Promise<Agent> {
    return api.post(`/agents/templates/${templateId}/create`, agentData);
  },

  // Agent Conversations
  async listConversations(agentId: string, params?: {
    limit?: number;
    status?: string;
  }): Promise<AgentConversation[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }

    const url = `/agents/${agentId}/conversations${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<AgentConversation[]>(url);
  },

  async getConversation(agentId: string, conversationId: string): Promise<AgentConversation> {
    return api.get<AgentConversation>(`/agents/${agentId}/conversations/${conversationId}`);
  },

  async createConversation(agentId: string, title?: string): Promise<AgentConversation> {
    return api.post(`/agents/${agentId}/conversations/`, { title });
  },

  async deleteConversation(agentId: string, conversationId: string): Promise<{ message: string }> {
    return api.delete(`/agents/${agentId}/conversations/${conversationId}`);
  },

  // Agent Chat
  async chatWithAgent(agentId: string, conversationId: string, request: AgentChatRequest): Promise<AgentChatResponse> {
    return api.post<AgentChatResponse>(`/agents/${agentId}/conversations/${conversationId}/chat`, request);
  },

  async streamChatWithAgent(
    agentId: string, 
    conversationId: string, 
    request: AgentChatRequest,
    _onChunk: (chunk: string) => void,
    onComplete: (response: AgentChatResponse) => void,
    onError: (error: any) => void
  ): Promise<void> {
    // Note: This would need Server-Sent Events or WebSocket implementation
    // For now, falling back to regular chat
    try {
      const response = await this.chatWithAgent(agentId, conversationId, request);
      onComplete(response);
    } catch (error) {
      onError(error);
    }
  },

  // Agent Executions
  async listExecutions(agentId: string, params?: {
    limit?: number;
    status?: string;
    task_type?: string;
  }): Promise<AgentExecution[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.task_type) {
      queryParams.append('task_type', params.task_type);
    }

    const url = `/agents/${agentId}/executions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<AgentExecution[]>(url);
  },

  async getExecution(agentId: string, executionId: string): Promise<AgentExecution> {
    return api.get<AgentExecution>(`/agents/${agentId}/executions/${executionId}`);
  },

  async cancelExecution(agentId: string, executionId: string): Promise<{ message: string }> {
    return api.post(`/agents/${agentId}/executions/${executionId}/cancel`);
  },

  // Agent Tasks
  async executeTask(agentId: string, task: {
    task_type: string;
    input: any;
    tools_enabled?: boolean;
    async_execution?: boolean;
  }): Promise<AgentExecution> {
    return api.post<AgentExecution>(`/agents/${agentId}/execute`, task);
  },

  async scheduleTask(agentId: string, task: {
    task_type: string;
    input: any;
    schedule: string; // cron expression
    enabled: boolean;
  }): Promise<{ message: string; schedule_id: string }> {
    return api.post(`/agents/${agentId}/schedule`, task);
  },

  // Agent Analytics
  async getAgentMetrics(agentId: string, timeframe?: {
    start_date: string;
    end_date: string;
  }): Promise<{
    metrics: Record<string, any>;
    executions_over_time: Array<{ date: string; count: number; success_rate: number }>;
    token_usage_over_time: Array<{ date: string; tokens: number; cost_usd: number }>;
    popular_tools: Array<{ tool_name: string; usage_count: number }>;
  }> {
    const queryParams = new URLSearchParams();
    
    if (timeframe?.start_date) {
      queryParams.append('start_date', timeframe.start_date);
    }
    if (timeframe?.end_date) {
      queryParams.append('end_date', timeframe.end_date);
    }

    const url = `/agents/${agentId}/metrics${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get(url);
  },

  async getAgentLogs(agentId: string, params?: {
    limit?: number;
    level?: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
    start_date?: string;
    end_date?: string;
  }): Promise<Array<{
    timestamp: string;
    level: string;
    message: string;
    metadata?: Record<string, any>;
  }>> {
    const queryParams = new URLSearchParams();
    
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.level) {
      queryParams.append('level', params.level);
    }
    if (params?.start_date) {
      queryParams.append('start_date', params.start_date);
    }
    if (params?.end_date) {
      queryParams.append('end_date', params.end_date);
    }

    const url = `/agents/${agentId}/logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get(url);
  },

  // Tool Management
  async getAvailableTools(): Promise<Array<{
    id: string;
    name: string;
    description: string;
    category: string;
    parameters: Record<string, any>;
  }>> {
    return api.get('/agents/tools/available');
  },

  async testTool(toolConfig: {
    tool_type: string;
    configuration: Record<string, any>;
    test_parameters: Record<string, any>;
  }): Promise<{
    success: boolean;
    result?: any;
    error?: string;
    response_time_ms: number;
  }> {
    return api.post('/agents/tools/test', toolConfig);
  },

  // Agent Training and Feedback
  async provideFeedback(agentId: string, executionId: string, feedback: {
    rating: number; // 1-5
    comments?: string;
    correct_output?: any;
    tags?: string[];
  }): Promise<{ message: string }> {
    return api.post(`/agents/${agentId}/executions/${executionId}/feedback`, feedback);
  },

  async trainAgent(agentId: string, trainingData: {
    examples: Array<{
      input: any;
      expected_output: any;
      explanation?: string;
    }>;
    validation_split?: number;
    epochs?: number;
  }): Promise<{ message: string; training_id: string }> {
    return api.post(`/agents/${agentId}/train`, trainingData);
  },

  // Utility Methods
  async validateAgentConfig(config: AgentCreateRequest): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
  }> {
    return api.post('/agents/validate', config);
  },

  async exportAgent(agentId: string): Promise<Blob> {
    const baseURL = 'http://localhost:8000/api/v1';
    const response = await fetch(`${baseURL}/agents/${agentId}/export`, {
      headers: {
        'Authorization': localStorage.getItem('auth_token') ? `Bearer ${localStorage.getItem('auth_token')}` : '',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to export agent');
    }
    
    return response.blob();
  },

  async importAgent(file: File): Promise<Agent> {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post<Agent>('/agents/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
};

export type {
  Agent,
  AgentCreateRequest,
  AgentUpdateRequest,
  AgentExecution,
  AgentConversation,
  AgentMessage,
  AgentChatRequest,
  AgentChatResponse,
  AgentTemplate
} from '@/types/agent';

export {
  AgentType,
  AgentStatus,
  AgentCapability
} from '@/types/agent';
