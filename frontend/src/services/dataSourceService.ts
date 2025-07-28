import { api } from './api';

export interface DataSourceConfiguration {
  id: string;
  name: string;
  description?: string;
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
  source_config: Record<string, any>;
  processing_config?: Record<string, any>;
  schedule_type: 'MANUAL' | 'INTERVAL' | 'CRON';
  schedule_config?: Record<string, any>;
  output_to_sandbox: boolean;
  output_table_name?: string;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  avg_execution_time_seconds?: number;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface DataSourceConfigurationCreate {
  name: string;
  description?: string;
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
  source_config: Record<string, any>;
  processing_config?: Record<string, any>;
  schedule_type: 'MANUAL' | 'INTERVAL' | 'CRON';
  schedule_config?: Record<string, any>;
  output_to_sandbox: boolean;
  output_table_name?: string;
  created_by: string;
}

export interface DataSourceConfigurationUpdate {
  name?: string;
  description?: string;
  source_config?: Record<string, any>;
  processing_config?: Record<string, any>;
  schedule_type?: 'MANUAL' | 'INTERVAL' | 'CRON';
  schedule_config?: Record<string, any>;
  output_to_sandbox?: boolean;
  output_table_name?: string;
  is_active?: boolean;
}

export interface DataPullExecution {
  id: string;
  configuration_id: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'SCHEDULED';
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  records_processed?: number;
  records_successful?: number;
  records_failed?: number;
  data_size_bytes?: number;
  output_location?: string;
  error_message?: string;
  trigger_type: string;
  triggered_by: string;
}

export interface DataSourceTestRequest {
  data_source_type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING';
  source_config: Record<string, any>;
  processing_config?: Record<string, any>;
  sample_size?: number;
}

export interface DataSourceTestResponse {
  success: boolean;
  sample_data?: Array<Record<string, any>>;
  record_count?: number;
  error_message?: string;
  execution_time_seconds?: number;
  data_schema?: Record<string, string>;
}

export interface DataSourceStatus {
  config_id: string;
  name: string;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_execution_time_seconds?: number;
  recent_executions: DataPullExecution[];
}

class DataSourceService {
  private baseUrl = '/api/data-sources';

  async listDataSources(params?: {
    created_by?: string;
    data_source_type?: string;
    is_active?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<DataSourceConfiguration[]> {
    const searchParams = new URLSearchParams();
    if (params?.created_by) searchParams.append('created_by', params.created_by);
    if (params?.data_source_type) searchParams.append('data_source_type', params.data_source_type);
    if (params?.is_active !== undefined) searchParams.append('is_active', params.is_active.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const url = searchParams.toString() ? `${this.baseUrl}?${searchParams}` : this.baseUrl;
    const response = await api.get<DataSourceConfiguration[]>(url);
    return response.data;
  }

  async getDataSource(configId: string): Promise<DataSourceConfiguration> {
    const response = await api.get<DataSourceConfiguration>(`${this.baseUrl}/${configId}`);
    return response.data;
  }

  async createDataSource(data: DataSourceConfigurationCreate): Promise<DataSourceConfiguration> {
    const response = await api.post<DataSourceConfiguration>(this.baseUrl, data);
    return response.data;
  }

  async updateDataSource(
    configId: string,
    data: DataSourceConfigurationUpdate
  ): Promise<DataSourceConfiguration> {
    const response = await api.put<DataSourceConfiguration>(`${this.baseUrl}/${configId}`, data);
    return response.data;
  }

  async deleteDataSource(configId: string): Promise<void> {
    await api.delete(`${this.baseUrl}/${configId}`);
  }

  async testDataSource(testRequest: DataSourceTestRequest): Promise<DataSourceTestResponse> {
    const response = await api.post<DataSourceTestResponse>(`${this.baseUrl}/test`, testRequest);
    return response.data;
  }

  async executeDataPull(
    configId: string,
    triggerType: string = 'MANUAL',
    triggeredBy: string = 'user'
  ): Promise<DataPullExecution> {
    const response = await api.post<DataPullExecution>(
      `${this.baseUrl}/${configId}/execute`,
      null,
      {
        params: {
          trigger_type: triggerType,
          triggered_by: triggeredBy,
        },
      }
    );
    return response.data;
  }

  async getExecutionHistory(
    configId: string,
    params?: { limit?: number; offset?: number }
  ): Promise<DataPullExecution[]> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const url = searchParams.toString()
      ? `${this.baseUrl}/${configId}/executions?${searchParams}`
      : `${this.baseUrl}/${configId}/executions`;

    const response = await api.get<DataPullExecution[]>(url);
    return response.data;
  }

  async getDataSourceStatus(configId: string): Promise<DataSourceStatus> {
    const response = await api.get<DataSourceStatus>(`${this.baseUrl}/${configId}/status`);
    return response.data;
  }

  async toggleDataSource(configId: string): Promise<{ message: string; is_active: boolean }> {
    const response = await api.post<{ message: string; is_active: boolean }>(
      `${this.baseUrl}/${configId}/toggle`
    );
    return response.data;
  }

  // Utility methods for common operations
  async getActiveDataSources(): Promise<DataSourceConfiguration[]> {
    return this.listDataSources({ is_active: true });
  }

  async getScheduledDataSources(): Promise<DataSourceConfiguration[]> {
    const allSources = await this.listDataSources();
    return allSources.filter(source => source.schedule_type !== 'MANUAL');
  }

  async getDataSourcesByType(type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING'): Promise<DataSourceConfiguration[]> {
    return this.listDataSources({ data_source_type: type });
  }

  async getRecentExecutions(configId: string, limit: number = 10): Promise<DataPullExecution[]> {
    return this.getExecutionHistory(configId, { limit });
  }

  // Batch operations
  async bulkToggleDataSources(configIds: string[], activate: boolean): Promise<void> {
    const promises = configIds.map(async (id) => {
      const current = await this.getDataSource(id);
      if (current.is_active !== activate) {
        return this.toggleDataSource(id);
      }
    });

    await Promise.all(promises);
  }

  async bulkExecuteDataPulls(configIds: string[]): Promise<DataPullExecution[]> {
    const promises = configIds.map(id => this.executeDataPull(id));
    return Promise.all(promises);
  }

  // Statistics and analytics
  async getDataSourceMetrics(): Promise<{
    total_sources: number;
    active_sources: number;
    scheduled_sources: number;
    total_executions_today: number;
    success_rate: number;
    by_type: Record<string, number>;
  }> {
    const sources = await this.listDataSources();
    const activeSources = sources.filter(s => s.is_active);
    const scheduledSources = sources.filter(s => s.schedule_type !== 'MANUAL');

    // Calculate executions today (would need to be implemented on backend)
    const today = new Date().toISOString().split('T')[0];
    
    const totalExecutions = sources.reduce((sum, s) => sum + s.total_runs, 0);
    const totalSuccessful = sources.reduce((sum, s) => sum + s.successful_runs, 0);
    const successRate = totalExecutions > 0 ? (totalSuccessful / totalExecutions) * 100 : 0;

    const byType = sources.reduce((acc, source) => {
      acc[source.data_source_type] = (acc[source.data_source_type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    return {
      total_sources: sources.length,
      active_sources: activeSources.length,
      scheduled_sources: scheduledSources.length,
      total_executions_today: 0, // Would need backend implementation
      success_rate: Math.round(successRate),
      by_type: byType,
    };
  }

  // Validation helpers
  validateApiConfig(config: Record<string, any>): string[] {
    const errors: string[] = [];
    if (!config.url) errors.push('URL is required for API sources');
    if (config.method && !['GET', 'POST', 'PUT', 'DELETE'].includes(config.method)) {
      errors.push('Invalid HTTP method');
    }
    return errors;
  }

  validateMcpConfig(config: Record<string, any>): string[] {
    const errors: string[] = [];
    if (!config.server_name) errors.push('Server name is required for MCP sources');
    if (!config.tool_name) errors.push('Tool name is required for MCP sources');
    return errors;
  }

  validateWebScrapingConfig(config: Record<string, any>): string[] {
    const errors: string[] = [];
    if (!config.url) errors.push('URL is required for web scraping sources');
    if (!config.selector_config) errors.push('Selector configuration is required for web scraping');
    return errors;
  }

  validateSourceConfig(type: 'API' | 'MCP_SERVER' | 'WEB_SCRAPING', config: Record<string, any>): string[] {
    switch (type) {
      case 'API':
        return this.validateApiConfig(config);
      case 'MCP_SERVER':
        return this.validateMcpConfig(config);
      case 'WEB_SCRAPING':
        return this.validateWebScrapingConfig(config);
      default:
        return ['Invalid data source type'];
    }
  }
}

export const dataSourceService = new DataSourceService();