export interface DataRecord {
  id: string;
  timestamp: string;
  [key: string]: any; // Allow dynamic fields
}

export interface DataSource {
  id: string;
  name: string;
  type: 'workflow' | 'mcp' | 'agent' | 'api' | 'manual';
  description: string;
  schema?: DataSchema;
  lastUpdated: string;
  recordCount: number;
  status: 'active' | 'inactive' | 'error';
}

export interface DataSchema {
  fields: DataField[];
}

export interface DataField {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'object' | 'array';
  required: boolean;
  description?: string;
  format?: string; // For dates, numbers, etc.
}

export interface DataQuery {
  source: string;
  filters?: DataFilter[];
  sorts?: DataSort[];
  limit?: number;
  offset?: number;
  fields?: string[];
}

export interface DataFilter {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'nin' | 'like' | 'regex';
  value: any;
}

export interface DataSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface DataQueryResult {
  data: DataRecord[];
  totalCount: number;
  schema: DataSchema;
  executionTime: number;
  source: DataSource;
}

export interface DataExportRequest {
  query: DataQuery;
  format: 'csv' | 'json' | 'xlsx' | 'parquet';
  filename?: string;
}

export interface WorkflowOutput {
  id: string;
  workflowId: string;
  workflowName: string;
  executionId: string;
  stepName: string;
  data: any;
  schema?: DataSchema;
  timestamp: string;
  metadata: {
    stepType: string;
    duration: number;
    status: 'success' | 'error' | 'warning';
    [key: string]: any;
  };
}

export interface MCPDataStream {
  id: string;
  serverId: string;
  serverName: string;
  streamName: string;
  data: any;
  schema?: DataSchema;
  timestamp: string;
  metadata: {
    contentType: string;
    size: number;
    encoding?: string;
    [key: string]: any;
  };
}

export interface AgentResult {
  id: string;
  agentId: string;
  agentName: string;
  executionId: string;
  taskType: string;
  result: any;
  schema?: DataSchema;
  timestamp: string;
  metadata: {
    tokensUsed: number;
    cost: number;
    duration: number;
    toolsUsed: string[];
    [key: string]: any;
  };
}

export interface DataVisualizationConfig {
  type: 'table' | 'chart' | 'graph' | 'map';
  title: string;
  description?: string;
  config: {
    // Chart specific config
    chartType?: 'line' | 'bar' | 'pie' | 'scatter' | 'area' | 'heatmap';
    xAxis?: string;
    yAxis?: string[];
    groupBy?: string;
    aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max';
    
    // Table specific config
    columns?: string[];
    sortBy?: DataSort[];
    groupColumns?: string[];
    
    // Common config
    filters?: DataFilter[];
    limit?: number;
    refreshInterval?: number;
  };
}