import { api } from './api';
import {
  DataSource,
  DataQuery,
  DataQueryResult,
  DataExportRequest,
  WorkflowOutput,
  MCPDataStream,
  AgentResult,
  DataVisualizationConfig,
  DataRecord,
} from '@/types/dataSandbox';

export const dataSandboxService = {
  // Data Sources Management
  async listDataSources(): Promise<DataSource[]> {
    return api.get<DataSource[]>('/data-sandbox/sources');
  },

  async getDataSource(sourceId: string): Promise<DataSource> {
    return api.get<DataSource>(`/data-sandbox/sources/${sourceId}`);
  },

  async createDataSource(source: Omit<DataSource, 'id' | 'lastUpdated' | 'recordCount'>): Promise<DataSource> {
    return api.post<DataSource>('/data-sandbox/sources', source);
  },

  async updateDataSource(sourceId: string, updates: Partial<DataSource>): Promise<DataSource> {
    return api.put<DataSource>(`/data-sandbox/sources/${sourceId}`, updates);
  },

  async deleteDataSource(sourceId: string): Promise<{ message: string }> {
    return api.delete(`/data-sandbox/sources/${sourceId}`);
  },

  // Data Querying
  async queryData(query: DataQuery): Promise<DataQueryResult> {
    return api.post<DataQueryResult>('/data-sandbox/query', query);
  },

  async executeSQL(sql: string, params?: Record<string, any>): Promise<DataQueryResult> {
    return api.post<DataQueryResult>('/data-sandbox/sql', { sql, params });
  },

  async getDataPreview(sourceId: string, limit: number = 100): Promise<DataQueryResult> {
    return api.get<DataQueryResult>(`/data-sandbox/sources/${sourceId}/preview?limit=${limit}`);
  },

  // Workflow Integration
  async getWorkflowOutputs(params?: {
    workflowId?: string;
    executionId?: string;
    stepName?: string;
    limit?: number;
    since?: string;
  }): Promise<WorkflowOutput[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.workflowId) queryParams.append('workflow_id', params.workflowId);
    if (params?.executionId) queryParams.append('execution_id', params.executionId);
    if (params?.stepName) queryParams.append('step_name', params.stepName);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.since) queryParams.append('since', params.since);

    const url = `/data-sandbox/workflow-outputs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<WorkflowOutput[]>(url);
  },

  async getWorkflowOutput(outputId: string): Promise<WorkflowOutput> {
    return api.get<WorkflowOutput>(`/data-sandbox/workflow-outputs/${outputId}`);
  },

  async createDataSourceFromWorkflow(workflowId: string, outputName: string): Promise<DataSource> {
    return api.post<DataSource>('/data-sandbox/sources/from-workflow', {
      workflow_id: workflowId,
      output_name: outputName,
    });
  },

  // MCP Integration
  async getMCPDataStreams(params?: {
    serverId?: string;
    streamName?: string;
    limit?: number;
    since?: string;
  }): Promise<MCPDataStream[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.serverId) queryParams.append('server_id', params.serverId);
    if (params?.streamName) queryParams.append('stream_name', params.streamName);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.since) queryParams.append('since', params.since);

    const url = `/data-sandbox/mcp-streams${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<MCPDataStream[]>(url);
  },

  async getMCPDataStream(streamId: string): Promise<MCPDataStream> {
    return api.get<MCPDataStream>(`/data-sandbox/mcp-streams/${streamId}`);
  },

  async createDataSourceFromMCP(serverId: string, streamName: string): Promise<DataSource> {
    return api.post<DataSource>('/data-sandbox/sources/from-mcp', {
      server_id: serverId,
      stream_name: streamName,
    });
  },

  // Agent Integration
  async getAgentResults(params?: {
    agentId?: string;
    executionId?: string;
    taskType?: string;
    limit?: number;
    since?: string;
  }): Promise<AgentResult[]> {
    const queryParams = new URLSearchParams();
    
    if (params?.agentId) queryParams.append('agent_id', params.agentId);
    if (params?.executionId) queryParams.append('execution_id', params.executionId);
    if (params?.taskType) queryParams.append('task_type', params.taskType);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.since) queryParams.append('since', params.since);

    const url = `/data-sandbox/agent-results${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<AgentResult[]>(url);
  },

  async getAgentResult(resultId: string): Promise<AgentResult> {
    return api.get<AgentResult>(`/data-sandbox/agent-results/${resultId}`);
  },

  async createDataSourceFromAgent(agentId: string, taskType?: string): Promise<DataSource> {
    return api.post<DataSource>('/data-sandbox/sources/from-agent', {
      agent_id: agentId,
      task_type: taskType,
    });
  },

  // Data Export
  async exportData(request: DataExportRequest): Promise<Blob> {
    const response = await fetch(`${api.defaults?.baseURL}/data-sandbox/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': localStorage.getItem('auth_token') ? `Bearer ${localStorage.getItem('auth_token')}` : '',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error('Failed to export data');
    }
    
    return response.blob();
  },

  async scheduleExport(request: DataExportRequest & {
    schedule: string; // cron expression
    destination: 'email' | 's3' | 'ftp';
    destination_config: Record<string, any>;
  }): Promise<{ message: string; schedule_id: string }> {
    return api.post('/data-sandbox/scheduled-exports', request);
  },

  // Data Transformation
  async transformData(sourceId: string, transformations: Array<{
    type: 'filter' | 'sort' | 'group' | 'aggregate' | 'join' | 'pivot';
    config: Record<string, any>;
  }>): Promise<DataQueryResult> {
    return api.post<DataQueryResult>(`/data-sandbox/sources/${sourceId}/transform`, {
      transformations,
    });
  },

  async saveTransformation(name: string, sourceId: string, transformations: any[]): Promise<DataSource> {
    return api.post<DataSource>('/data-sandbox/transformations', {
      name,
      source_id: sourceId,
      transformations,
    });
  },

  // Visualizations
  async saveVisualization(config: DataVisualizationConfig): Promise<{ id: string } & DataVisualizationConfig> {
    return api.post('/data-sandbox/visualizations', config);
  },

  async getVisualizations(): Promise<Array<{ id: string } & DataVisualizationConfig>> {
    return api.get('/data-sandbox/visualizations');
  },

  async getVisualization(vizId: string): Promise<{ id: string } & DataVisualizationConfig> {
    return api.get(`/data-sandbox/visualizations/${vizId}`);
  },

  async deleteVisualization(vizId: string): Promise<{ message: string }> {
    return api.delete(`/data-sandbox/visualizations/${vizId}`);
  },

  // Real-time Data
  async subscribeToDataUpdates(sourceId: string, callback: (data: DataRecord[]) => void): Promise<() => void> {
    // WebSocket or Server-Sent Events implementation
    const eventSource = new EventSource(`${api.defaults?.baseURL}/data-sandbox/sources/${sourceId}/stream`);
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data);
    };
    
    return () => {
      eventSource.close();
    };
  },

  // Data Quality
  async analyzeDataQuality(sourceId: string): Promise<{
    completeness: number;
    accuracy: number;
    consistency: number;
    timeliness: number;
    issues: Array<{
      type: 'missing_values' | 'duplicates' | 'outliers' | 'format_errors';
      count: number;
      description: string;
      affected_fields: string[];
    }>;
  }> {
    return api.get(`/data-sandbox/sources/${sourceId}/quality`);
  },

  // Data Lineage
  async getDataLineage(sourceId: string): Promise<{
    upstream: Array<{
      id: string;
      name: string;
      type: string;
      relationship: string;
    }>;
    downstream: Array<{
      id: string;
      name: string;
      type: string;
      relationship: string;
    }>;
  }> {
    return api.get(`/data-sandbox/sources/${sourceId}/lineage`);
  },

  // Collaboration
  async shareDataView(config: {
    query: DataQuery;
    visualization?: DataVisualizationConfig;
    permissions: Array<{
      user_id: string;
      access_level: 'view' | 'edit' | 'admin';
    }>;
    expires_at?: string;
  }): Promise<{ share_id: string; share_url: string }> {
    return api.post('/data-sandbox/shared-views', config);
  },

  async getSharedView(shareId: string): Promise<{
    query: DataQuery;
    visualization?: DataVisualizationConfig;
    data: DataQueryResult;
  }> {
    return api.get(`/data-sandbox/shared-views/${shareId}`);
  },
};