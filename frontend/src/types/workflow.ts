// Workflow Management Types

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  type: WorkflowType;
  status: WorkflowStatus;
  version: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  
  // Workflow definition
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  triggers: WorkflowTrigger[];
  
  // Execution settings
  execution_settings: WorkflowExecutionSettings;
  
  // Metrics
  metrics: WorkflowMetrics;
  
  // Dependencies
  dependencies: string[]; // Other workflow IDs
}

export enum WorkflowType {
  DATA_INGESTION = 'DATA_INGESTION',
  DATA_TRANSFORMATION = 'DATA_TRANSFORMATION',
  DATA_VALIDATION = 'DATA_VALIDATION',
  RECONCILIATION = 'RECONCILIATION',
  REPORTING = 'REPORTING',
  MONITORING = 'MONITORING',
  ALERT_PROCESSING = 'ALERT_PROCESSING',
  EXCEPTION_HANDLING = 'EXCEPTION_HANDLING',
}

export enum WorkflowStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  ARCHIVED = 'ARCHIVED',
  ERROR = 'ERROR',
}

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  name: string;
  description?: string;
  position: { x: number; y: number };
  config: WorkflowNodeConfig;
  inputs: WorkflowPort[];
  outputs: WorkflowPort[];
}

export enum WorkflowNodeType {
  // Data nodes
  MCP_CALL = 'MCP_CALL',
  DATA_SOURCE = 'DATA_SOURCE',
  DATA_SINK = 'DATA_SINK',
  
  // Processing nodes
  TRANSFORM = 'TRANSFORM',
  FILTER = 'FILTER',
  AGGREGATE = 'AGGREGATE',
  JOIN = 'JOIN',
  SORT = 'SORT',
  
  // Logic nodes
  CONDITION = 'CONDITION',
  LOOP = 'LOOP',
  PARALLEL = 'PARALLEL',
  
  // Integration nodes
  API_CALL = 'API_CALL',
  DATABASE = 'DATABASE',
  FILE_OPERATION = 'FILE_OPERATION',
  
  // Notification nodes
  EMAIL = 'EMAIL',
  WEBHOOK = 'WEBHOOK',
  ALERT = 'ALERT',
  
  // Control nodes
  START = 'START',
  END = 'END',
  ERROR_HANDLER = 'ERROR_HANDLER',
}

export interface WorkflowNodeConfig {
  // MCP-specific config
  mcp_server_id?: string;
  endpoint_id?: string;
  parameters?: Record<string, any>;
  
  // Processing config
  transformation_code?: string;
  sql_query?: string;
  filter_expression?: string;
  
  // Retry and error handling
  retry_attempts?: number;
  timeout_seconds?: number;
  on_error?: 'FAIL' | 'CONTINUE' | 'RETRY' | 'SKIP';
  
  // Generic config
  settings?: Record<string, any>;
}

export interface WorkflowPort {
  id: string;
  name: string;
  data_type: string;
  required: boolean;
  description?: string;
}

export interface WorkflowEdge {
  id: string;
  source_node_id: string;
  source_port_id: string;
  target_node_id: string;
  target_port_id: string;
  condition?: string; // For conditional edges
}

export interface WorkflowTrigger {
  id: string;
  type: WorkflowTriggerType;
  config: WorkflowTriggerConfig;
  enabled: boolean;
}

export enum WorkflowTriggerType {
  SCHEDULE = 'SCHEDULE',
  DATA_CHANGE = 'DATA_CHANGE',
  MCP_EVENT = 'MCP_EVENT',
  MANUAL = 'MANUAL',
  WEBHOOK = 'WEBHOOK',
  FILE_WATCH = 'FILE_WATCH',
}

export interface WorkflowTriggerConfig {
  // Schedule trigger
  cron_expression?: string;
  timezone?: string;
  
  // Data change trigger
  data_source?: string;
  change_type?: 'INSERT' | 'UPDATE' | 'DELETE' | 'ANY';
  
  // MCP event trigger
  mcp_server_id?: string;
  event_type?: string;
  
  // Generic config
  parameters?: Record<string, any>;
}

export interface WorkflowExecutionSettings {
  max_concurrent_executions: number;
  execution_timeout_minutes: number;
  retry_policy: WorkflowRetryPolicy;
  notification_settings: WorkflowNotificationSettings;
}

export interface WorkflowRetryPolicy {
  max_attempts: number;
  backoff_strategy: 'LINEAR' | 'EXPONENTIAL' | 'FIXED';
  delay_seconds: number;
  max_delay_seconds?: number;
}

export interface WorkflowNotificationSettings {
  on_success: boolean;
  on_failure: boolean;
  on_long_running: boolean;
  recipients: string[];
  channels: ('EMAIL' | 'SLACK' | 'WEBHOOK')[];
}

export interface WorkflowMetrics {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  average_duration_seconds: number;
  last_execution_date?: string;
  last_execution_status?: WorkflowExecutionStatus;
  next_scheduled_execution?: string;
}

// Workflow Execution
export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_version: string;
  status: WorkflowExecutionStatus;
  trigger_type: WorkflowTriggerType;
  trigger_data?: Record<string, any>;
  
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  
  // Node executions
  node_executions: WorkflowNodeExecution[];
  
  // Results and errors
  output_data?: Record<string, any>;
  error_message?: string;
  
  // Metrics
  records_processed?: number;
  data_volume_mb?: number;
}

export enum WorkflowExecutionStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  TIMEOUT = 'TIMEOUT',
}

export interface WorkflowNodeExecution {
  id: string;
  node_id: string;
  status: WorkflowExecutionStatus;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count: number;
}

// Workflow Templates
export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: WorkflowTemplateCategory;
  template_data: Workflow;
  parameters: WorkflowTemplateParameter[];
  tags: string[];
  use_cases: string[];
  complexity: 'SIMPLE' | 'MEDIUM' | 'COMPLEX';
}

export enum WorkflowTemplateCategory {
  DATA_INTEGRATION = 'DATA_INTEGRATION',
  RECONCILIATION = 'RECONCILIATION',
  MONITORING = 'MONITORING',
  REPORTING = 'REPORTING',
  VALIDATION = 'VALIDATION',
}

export interface WorkflowTemplateParameter {
  name: string;
  type: 'STRING' | 'NUMBER' | 'BOOLEAN' | 'SELECT' | 'MCP_SERVER';
  required: boolean;
  default_value?: any;
  options?: string[]; // For SELECT type
  description: string;
}

// Workflow Builder UI Types
export interface WorkflowBuilderState {
  workflow: Workflow;
  selected_nodes: string[];
  selected_edges: string[];
  zoom_level: number;
  pan_position: { x: number; y: number };
  is_dirty: boolean; // Has unsaved changes
}

export interface WorkflowNodeLibrary {
  categories: WorkflowNodeCategory[];
}

export interface WorkflowNodeCategory {
  id: string;
  name: string;
  icon: string;
  nodes: WorkflowNodeTemplate[];
}

export interface WorkflowNodeTemplate {
  type: WorkflowNodeType;
  name: string;
  description: string;
  icon: string;
  default_config: WorkflowNodeConfig;
  default_inputs: WorkflowPort[];
  default_outputs: WorkflowPort[];
}

// Workflow Monitoring
export interface WorkflowMonitor {
  workflow_id: string;
  alerts: WorkflowAlert[];
  health_score: number;
  last_check: string;
  metrics_history: WorkflowMetricsHistory[];
}

export interface WorkflowAlert {
  id: string;
  type: 'ERROR' | 'WARNING' | 'INFO';
  message: string;
  timestamp: string;
  acknowledged: boolean;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export interface WorkflowMetricsHistory {
  timestamp: string;
  executions_count: number;
  success_rate: number;
  average_duration: number;
  error_count: number;
}