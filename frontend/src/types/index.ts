// Domain Types for Data Integration & Workflow Management PoC

export interface User {
  id: string;
  email: string;
  name: string;
  preferred_username?: string;
  given_name?: string;
  family_name?: string;
  roles: string[];
  groups: string[];
  identity_provider?: string;
  provider_id?: string;
  employee_id?: string;
  department?: string;
  business_unit?: string;
  clearance_level?: string;
}

export interface Trade {
  id: string;
  trade_reference: string;
  counterparty_id: string;
  instrument_id: string;
  trade_type: TradeType;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  trade_value: number;
  currency: string;
  trade_date: string;
  settlement_date: string;
  value_date?: string;
  status: TradeStatus;
  priority: Priority;
  requires_manual_review: boolean;
  created_at: string;
  updated_at: string;
  processed_by?: string;
  notes?: string;
}

export enum TradeStatus {
  PENDING = 'PENDING',
  VALIDATED = 'VALIDATED',
  MATCHED = 'MATCHED',
  CONFIRMED = 'CONFIRMED',
  SETTLED = 'SETTLED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  REQUIRES_MANUAL_REVIEW = 'REQUIRES_MANUAL_REVIEW',
}

export enum TradeType {
  EQUITY = 'EQUITY',
  BOND = 'BOND',
  FX = 'FX',
  DERIVATIVE = 'DERIVATIVE',
  REPO = 'REPO',
  SECURITIES_LENDING = 'SECURITIES_LENDING',
}

export enum Priority {
  LOW = 'LOW',
  NORMAL = 'NORMAL',
  HIGH = 'HIGH',
  URGENT = 'URGENT',
}

export interface TradeException {
  id: string;
  trade_id: string;
  exception_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  resolution_status: 'OPEN' | 'IN_PROGRESS' | 'RESOLVED';
  assigned_to?: string;
  created_at: string;
  resolved_at?: string;
}

export interface SOPDocument {
  id: string;
  title: string;
  document_number: string;
  version: string;
  content: string;
  summary?: string;
  category: string;
  subcategory?: string;
  process_type: string;
  business_area: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  last_reviewed?: string;
  status: 'ACTIVE' | 'DEPRECATED' | 'UNDER_REVIEW';
  is_automated: boolean;
  automation_percentage: number;
  neo4j_node_id?: string;
}

export interface SOPStep {
  id: string;
  sop_document_id: string;
  step_number: number;
  step_title: string;
  step_description: string;
  is_manual: boolean;
  is_automated: boolean;
  is_decision_point: boolean;
  estimated_duration_minutes?: number;
  automation_tool?: string;
  automation_confidence?: number;
}

export interface WorkflowDefinition {
  id: string;
  name: string;
  description?: string;
  workflow_type: WorkflowType;
  version: string;
  base_sop_id?: string;
  graph_definition: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by: string;
  is_active: boolean;
  is_tested: boolean;
  test_success_rate?: number;
  average_execution_time?: number;
  success_rate?: number;
  human_intervention_rate?: number;
}

export enum WorkflowType {
  TRADE_VALIDATION = 'TRADE_VALIDATION',
  SETTLEMENT_PROCESSING = 'SETTLEMENT_PROCESSING',
  RECONCILIATION = 'RECONCILIATION',
  EXCEPTION_HANDLING = 'EXCEPTION_HANDLING',
  REGULATORY_REPORTING = 'REGULATORY_REPORTING',
  CLIENT_ONBOARDING = 'CLIENT_ONBOARDING',
  CORPORATE_ACTIONS = 'CORPORATE_ACTIONS',
}

export interface WorkflowExecution {
  id: string;
  workflow_definition_id: string;
  trigger_type: string;
  status: WorkflowStatus;
  current_node?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  requires_human_review: boolean;
  human_review_reason?: string;
  temporal_workflow_id?: string;
}

export enum WorkflowStatus {
  PENDING = 'PENDING',
  RUNNING = 'RUNNING',
  PAUSED = 'PAUSED',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
  REQUIRES_HUMAN_INTERVENTION = 'REQUIRES_HUMAN_INTERVENTION',
}

// Notion-style page types
export interface Page {
  id: string;
  title: string;
  icon?: string;
  cover?: string;
  parent_id?: string;
  type: PageType;
  properties: Record<string, any>;
  content: Block[];
  created_at: string;
  updated_at: string;
  created_by: string;
  last_edited_by: string;
}

export enum PageType {
  SOP_DOCUMENT = 'SOP_DOCUMENT',
  TRADE_DASHBOARD = 'TRADE_DASHBOARD',
  WORKFLOW_BUILDER = 'WORKFLOW_BUILDER',
  ANALYTICS = 'ANALYTICS',
  KNOWLEDGE_BASE = 'KNOWLEDGE_BASE',
  SETTINGS = 'SETTINGS',
}

export interface Block {
  id: string;
  type: BlockType;
  content: string;
  properties?: Record<string, any>;
  children?: Block[];
  parent_id: string;
  created_at: string;
  updated_at: string;
}

export enum BlockType {
  PARAGRAPH = 'PARAGRAPH',
  HEADING_1 = 'HEADING_1',
  HEADING_2 = 'HEADING_2',
  HEADING_3 = 'HEADING_3',
  BULLETED_LIST = 'BULLETED_LIST',
  NUMBERED_LIST = 'NUMBERED_LIST',
  QUOTE = 'QUOTE',
  CODE = 'CODE',
  DIVIDER = 'DIVIDER',
  TABLE = 'TABLE',
  TRADE_TABLE = 'TRADE_TABLE',
  WORKFLOW_DIAGRAM = 'WORKFLOW_DIAGRAM',
  CHART = 'CHART',
  EMBED = 'EMBED',
}

// Search and filtering
export interface SearchResult {
  id: string;
  title: string;
  type: 'sop' | 'trade' | 'workflow' | 'page';
  snippet: string;
  relevance_score: number;
  url: string;
}

export interface FilterOptions {
  categories?: string[];
  business_areas?: string[];
  status?: string[];
  date_range?: {
    start: string;
    end: string;
  };
  priority?: Priority[];
  automation_level?: 'manual' | 'semi_automated' | 'automated';
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Navigation and UI
export interface NavigationItem {
  id: string;
  title: string;
  icon: string;
  path: string;
  type: 'page' | 'database' | 'workspace';
  children?: NavigationItem[];
  parent_id?: string;
}

export interface Workspace {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  pages: NavigationItem[];
  members: User[];
  settings: WorkspaceSettings;
}

export interface WorkspaceSettings {
  theme: 'light' | 'dark';
  sidebar_collapsed: boolean;
  default_view: 'list' | 'board' | 'calendar';
  notifications_enabled: boolean;
}

// Analytics and metrics
export interface DashboardMetrics {
  total_trades: number;
  pending_trades: number;
  automated_trades: number;
  manual_interventions: number;
  processing_time_avg: number;
  success_rate: number;
  cost_savings: number;
  automation_rate: number;
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
    borderColor?: string;
  }[];
}

// Automation and AI
export interface AutomationSuggestion {
  sop_id: string;
  confidence: number;
  potential_savings: number;
  implementation_effort: 'LOW' | 'MEDIUM' | 'HIGH';
  description: string;
  prerequisites: string[];
}