export enum AgentType {
  TRADING_ANALYST = 'TRADING_ANALYST',
  RISK_MONITOR = 'RISK_MONITOR',
  COMPLIANCE_CHECKER = 'COMPLIANCE_CHECKER',
  DATA_ANALYST = 'DATA_ANALYST',
  PORTFOLIO_MANAGER = 'PORTFOLIO_MANAGER',
  SETTLEMENT_SPECIALIST = 'SETTLEMENT_SPECIALIST',
  MARKET_RESEARCHER = 'MARKET_RESEARCHER',
  CUSTOM = 'CUSTOM'
}

export enum AgentStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  TRAINING = 'TRAINING',
  ERROR = 'ERROR',
  PAUSED = 'PAUSED'
}

export enum AgentCapability {
  DATA_ANALYSIS = 'DATA_ANALYSIS',
  MARKET_RESEARCH = 'MARKET_RESEARCH',
  RISK_ASSESSMENT = 'RISK_ASSESSMENT',
  COMPLIANCE_CHECK = 'COMPLIANCE_CHECK',
  PORTFOLIO_OPTIMIZATION = 'PORTFOLIO_OPTIMIZATION',
  TRADE_EXECUTION = 'TRADE_EXECUTION',
  REPORT_GENERATION = 'REPORT_GENERATION',
  ANOMALY_DETECTION = 'ANOMALY_DETECTION',
  NATURAL_LANGUAGE_QUERY = 'NATURAL_LANGUAGE_QUERY',
  WORKFLOW_AUTOMATION = 'WORKFLOW_AUTOMATION'
}

export interface AgentModel {
  provider: 'OPENAI' | 'ANTHROPIC' | 'OLLAMA' | 'AZURE_OPENAI';
  model_name: string;
  temperature: number;
  max_tokens: number;
  api_key?: string;
  base_url?: string;
}

export interface AgentTool {
  id: string;
  name: string;
  description: string;
  tool_type: 'MCP_CALL' | 'API_CALL' | 'DATABASE_QUERY' | 'CALCULATION' | 'WORKFLOW_TRIGGER';
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface AgentMemory {
  type: 'CONVERSATION' | 'LONG_TERM' | 'WORKING';
  max_entries: number;
  retention_days: number;
  embeddings_enabled: boolean;
}

export interface AgentPrompt {
  system_prompt: string;
  instructions: string[];
  examples: Array<{
    input: string;
    output: string;
    explanation?: string;
  }>;
  constraints: string[];
}

export interface AgentSchedule {
  enabled: boolean;
  cron_expression?: string;
  frequency?: 'HOURLY' | 'DAILY' | 'WEEKLY' | 'MONTHLY';
  timezone: string;
  auto_tasks: string[];
}

export interface AgentMetrics {
  total_conversations: number;
  successful_tasks: number;
  failed_tasks: number;
  average_response_time_ms: number;
  last_24h_interactions: number;
  accuracy_score: number;
  user_satisfaction_score: number;
  uptime_percentage: number;
}

export interface AgentExecution {
  id: string;
  agent_id: string;
  task_type: string;
  input: any;
  output?: any;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  tokens_used: number;
  cost_usd: number;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  status: AgentStatus;
  capabilities: AgentCapability[];
  model: AgentModel;
  tools: AgentTool[];
  memory: AgentMemory;
  prompt: AgentPrompt;
  schedule: AgentSchedule;
  owner_id: string;
  team_ids: string[];
  tags: string[];
  version: number;
  created_at: string;
  updated_at: string;
  last_used: string;
  metrics: AgentMetrics;
}

export interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  capabilities: AgentCapability[];
  default_model: AgentModel;
  default_tools: AgentTool[];
  default_prompt: AgentPrompt;
  tags: string[];
  use_count: number;
}

export interface AgentConversation {
  id: string;
  agent_id: string;
  user_id: string;
  title: string;
  messages: AgentMessage[];
  status: 'ACTIVE' | 'ARCHIVED' | 'DELETED';
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface AgentMessage {
  id: string;
  role: 'USER' | 'AGENT' | 'SYSTEM';
  content: string;
  attachments?: Array<{
    type: 'FILE' | 'IMAGE' | 'DATA';
    name: string;
    url: string;
    size_bytes: number;
  }>;
  tool_calls?: Array<{
    tool_id: string;
    tool_name: string;
    parameters: Record<string, any>;
    result?: any;
  }>;
  timestamp: string;
  tokens_used: number;
  cost_usd: number;
}

export interface AgentCreateRequest {
  name: string;
  description: string;
  agent_type: AgentType;
  capabilities: AgentCapability[];
  model: AgentModel;
  tools: AgentTool[];
  memory: AgentMemory;
  prompt: AgentPrompt;
  schedule?: AgentSchedule;
  tags: string[];
}

export interface AgentUpdateRequest {
  name?: string;
  description?: string;
  status?: AgentStatus;
  capabilities?: AgentCapability[];
  model?: AgentModel;
  tools?: AgentTool[];
  memory?: AgentMemory;
  prompt?: AgentPrompt;
  schedule?: AgentSchedule;
  tags?: string[];
}

export interface AgentChatRequest {
  message: string;
  context?: Record<string, any>;
  tools_enabled?: boolean;
  stream?: boolean;
}

export interface AgentChatResponse {
  message: string;
  tool_calls?: Array<{
    tool_name: string;
    parameters: Record<string, any>;
    result: any;
  }>;
  tokens_used: number;
  cost_usd: number;
  response_time_ms: number;
}