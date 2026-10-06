import { api } from './api';

export interface Rule {
  name: string;
  description: string;
  salience: number;
  trigger_condition: string;
  actions: string[];
  file: string;
  line_range: string;
  category?: string;
  category_name?: string;
}

export interface RuleCategory {
  category: string;
  description: string;
  rules: Rule[];
}

export interface RulesCatalog {
  catalog: Record<string, RuleCategory>;
  summary: {
    total_rules: number;
    total_categories: number;
    categories: string[];
  };
  metadata: {
    requested_by: string;
    timestamp: string;
    version: string;
  };
}

export interface RuleExecutionRequest {
  rule_set: string;
  facts: Array<{
    fact_type: string;
    fact_id: string;
    data: Record<string, any>;
  }>;
  timeout_seconds?: number;
}

export interface RuleExecutionResult {
  rule_name: string;
  status: string;
  facts_processed: number;
  rules_fired: string[];
  actions_triggered: Array<Record<string, any>>;
  execution_time_ms: number;
  error_message?: string;
}

export interface TradeValidationRequest {
  trade_id: number;
}

export interface RiskCheckRequest {
  trade_id: number;
  portfolio_data: Record<string, any>;
}

export interface ComplianceCheckRequest {
  trade_id: number;
  client_data: Record<string, any>;
}

export interface SearchRulesParams {
  query: string;
  category?: string;
}

export interface RulesStatus {
  engine_status: string;
  engine: string;
  timestamp: string;
  user: string;
  rule_versions: Record<string, string>;
}

export const rulesService = {
  // Get rules catalog
  async getRulesCatalog(): Promise<RulesCatalog> {
    return api.get<RulesCatalog>('/rules/catalog');
  },

  // Get rules by category
  async getRulesByCategory(category: string): Promise<{
    category: string;
    rules: RuleCategory;
    count: number;
    requested_by: string;
    timestamp: string;
  }> {
    return api.get(`/rules/catalog/${category}`);
  },

  // Search rules
  async searchRules(params: SearchRulesParams): Promise<{
    query: string;
    category_filter?: string;
    results: Rule[];
    count: number;
    searched_by: string;
    timestamp: string;
  }> {
    const queryParams = new URLSearchParams({
      query: params.query,
    });
    
    if (params.category) {
      queryParams.append('category', params.category);
    }

    return api.get(`/rules/search?${queryParams.toString()}`);
  },

  // Get rules engine status
  async getRulesStatus(): Promise<RulesStatus> {
    return api.get<RulesStatus>('/rules/status');
  },

  // Execute rules
  async executeRules(request: RuleExecutionRequest): Promise<RuleExecutionResult> {
    return api.post<RuleExecutionResult>('/rules/execute', request);
  },

  // Validate trade
  async validateTrade(request: TradeValidationRequest): Promise<RuleExecutionResult> {
    return api.post<RuleExecutionResult>('/rules/validate-trade', request);
  },

  // Check risk limits
  async checkRiskLimits(request: RiskCheckRequest): Promise<RuleExecutionResult> {
    return api.post<RuleExecutionResult>('/rules/check-risk', request);
  },

  // Check compliance
  async checkCompliance(request: ComplianceCheckRequest): Promise<RuleExecutionResult> {
    return api.post<RuleExecutionResult>('/rules/check-compliance', request);
  },

  // Test equity pricing
  async testEquityPricing(symbol: string, marketPrice: number): Promise<RuleExecutionResult> {
    const request: RuleExecutionRequest = {
      rule_set: 'equity-pricing',
      facts: [
        {
          fact_type: 'EquityPricingRequest',
          fact_id: `pricing_${Date.now()}`,
          data: {
            symbol: symbol,
            marketDataPrice: marketPrice,
            currency: 'USD',
            exchange: 'NYSE',
            requestTime: new Date().toISOString(),
            pricingMethod: 'MARKET',
            pricingStatus: 'PENDING',
            validationErrors: []
          }
        },
        {
          fact_type: 'MarketData',
          fact_id: `market_${symbol}`,
          data: {
            symbol: symbol,
            lastPrice: marketPrice,
            bidPrice: marketPrice * 0.999,
            askPrice: marketPrice * 1.001,
            volume: 50000,
            timestamp: new Date().toISOString(),
            exchange: 'NYSE',
            currency: 'USD',
            volatility: 0.25
          }
        }
      ]
    };

    return this.executeRules(request);
  },
};