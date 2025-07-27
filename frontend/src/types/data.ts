// Data Integration Types for MCP Servers

export interface MCPServer {
  id: string;
  name: string;
  type: DataProviderType;
  status: ConnectionStatus;
  url: string;
  version: string;
  capabilities: string[];
  last_connected: string;
  config: MCPServerConfig;
  metrics: MCPServerMetrics;
  enabled: boolean;
  description?: string;
  provider_type?: string;
}

export enum DataProviderType {
  CUSTODIAN = 'CUSTODIAN',
  MARKET_DATA = 'MARKET_DATA',
  PRICING = 'PRICING',
  REFERENCE_DATA = 'REFERENCE_DATA',
  SETTLEMENT = 'SETTLEMENT',
  REGULATORY = 'REGULATORY',
  INTERNAL = 'INTERNAL',
}

export enum ConnectionStatus {
  CONNECTED = 'CONNECTED',
  DISCONNECTED = 'DISCONNECTED',
  ERROR = 'ERROR',
  CONNECTING = 'CONNECTING',
  MAINTENANCE = 'MAINTENANCE',
}

export interface MCPServerConfig {
  auth_type: 'API_KEY' | 'OAUTH' | 'CERTIFICATE' | 'BASIC';
  rate_limit: number;
  timeout_seconds: number;
  retry_attempts: number;
  batch_size?: number;
  polling_interval?: number;
  endpoints: MCPEndpoint[];
}

export interface MCPEndpoint {
  id: string;
  name: string;
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  data_type: DataType;
  required_params: string[];
  optional_params: string[];
  response_format: 'JSON' | 'XML' | 'CSV' | 'FIX';
}

export interface MCPServerMetrics {
  requests_total: number;
  requests_success: number;
  requests_failed: number;
  avg_response_time: number;
  last_error?: string;
  uptime_percentage: number;
  data_volume_mb: number;
}

export enum DataType {
  POSITIONS = 'POSITIONS',
  TRANSACTIONS = 'TRANSACTIONS',
  MARKET_PRICES = 'MARKET_PRICES',
  REFERENCE_DATA = 'REFERENCE_DATA',
  CORPORATE_ACTIONS = 'CORPORATE_ACTIONS',
  CASH_FLOWS = 'CASH_FLOWS',
  SETTLEMENTS = 'SETTLEMENTS',
  RECONCILIATION = 'RECONCILIATION',
  RISK_METRICS = 'RISK_METRICS',
  COMPLIANCE = 'COMPLIANCE',
}

// Data Flow Management
export interface DataFlow {
  id: string;
  name: string;
  description?: string;
  source_servers: string[]; // MCP server IDs
  target_systems: string[];
  data_types: DataType[];
  schedule: DataFlowSchedule;
  status: DataFlowStatus;
  last_run: string;
  next_run: string;
  transformations: DataTransformation[];
  quality_rules: DataQualityRule[];
  metrics: DataFlowMetrics;
}

export enum DataFlowStatus {
  ACTIVE = 'ACTIVE',
  PAUSED = 'PAUSED',
  ERROR = 'ERROR',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
}

export interface DataFlowSchedule {
  type: 'REAL_TIME' | 'INTERVAL' | 'CRON' | 'EVENT_DRIVEN';
  interval_minutes?: number;
  cron_expression?: string;
  event_trigger?: string;
}

export interface DataTransformation {
  id: string;
  name: string;
  type: 'MAPPING' | 'ENRICHMENT' | 'VALIDATION' | 'AGGREGATION' | 'FILTERING';
  config: Record<string, any>;
  order: number;
}

export interface DataQualityRule {
  id: string;
  name: string;
  field: string;
  rule_type: 'NOT_NULL' | 'RANGE' | 'FORMAT' | 'UNIQUENESS' | 'REFERENCE';
  parameters: Record<string, any>;
  severity: 'ERROR' | 'WARNING' | 'INFO';
}

export interface DataFlowMetrics {
  records_processed: number;
  records_success: number;
  records_failed: number;
  processing_time_ms: number;
  data_quality_score: number;
  errors: DataFlowError[];
}

export interface DataFlowError {
  timestamp: string;
  error_type: string;
  message: string;
  affected_records: number;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
}

// Real-time Data Streaming
export interface DataStream {
  id: string;
  name: string;
  mcp_server_id: string;
  data_type: DataType;
  status: 'ACTIVE' | 'PAUSED' | 'ERROR';
  records_per_second: number;
  latency_ms: number;
  last_update: string;
  buffer_size: number;
  subscribers: string[];
}

// Data Catalog & Discovery
export interface DataCatalogEntry {
  id: string;
  name: string;
  description?: string;
  data_type: DataType;
  source_system: string;
  schema: DataSchema;
  tags: string[];
  business_owner: string;
  technical_owner: string;
  sensitivity: 'PUBLIC' | 'INTERNAL' | 'CONFIDENTIAL' | 'RESTRICTED';
  last_updated: string;
  usage_stats: DataUsageStats;
}

export interface DataSchema {
  fields: DataField[];
  primary_keys: string[];
  foreign_keys: DataForeignKey[];
  indexes: string[];
}

export interface DataField {
  name: string;
  type: 'STRING' | 'INTEGER' | 'DECIMAL' | 'DATE' | 'DATETIME' | 'BOOLEAN';
  nullable: boolean;
  description?: string;
  constraints?: string[];
  sample_values?: string[];
}

export interface DataForeignKey {
  field: string;
  references_table: string;
  references_field: string;
}

export interface DataUsageStats {
  daily_access_count: number;
  unique_users: number;
  avg_query_time: number;
  most_accessed_fields: string[];
}

// Data Quality Monitoring
export interface DataQualityReport {
  id: string;
  data_flow_id: string;
  timestamp: string;
  overall_score: number;
  rule_results: DataQualityRuleResult[];
  recommendations: string[];
  trend: 'IMPROVING' | 'STABLE' | 'DEGRADING';
}

export interface DataQualityRuleResult {
  rule_id: string;
  rule_name: string;
  passed: boolean;
  score: number;
  affected_records: number;
  details: string;
}

// Custodian-specific Data Types
export interface CustodianPosition {
  account_id: string;
  instrument_id: string;
  quantity: number;
  market_value: number;
  currency: string;
  price: number;
  price_date: string;
  custodian: string;
  settlement_date: string;
}

export interface MarketDataPoint {
  symbol: string;
  price: number;
  currency: string;
  timestamp: string;
  volume?: number;
  bid?: number;
  ask?: number;
  provider: string;
  data_quality: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface CustodianTransaction {
  transaction_id: string;
  account_id: string;
  instrument_id: string;
  transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'COUPON' | 'TRANSFER';
  quantity: number;
  price: number;
  gross_amount: number;
  net_amount: number;
  fees: number;
  currency: string;
  trade_date: string;
  settlement_date: string;
  custodian: string;
  status: 'PENDING' | 'SETTLED' | 'FAILED';
}
