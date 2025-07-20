import { api } from './api';

export interface GraphEntity {
  id: string;
  name: string;
  description?: string;
  entity_type: string;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
  [key: string]: any;
}

export interface GraphRelationship {
  relationship_type: string;
  from_entity_id: string;
  to_entity_id: string;
  created_at: string;
  properties: Record<string, any>;
}

export interface GraphVisualizationData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: {
    node_count: number;
    edge_count: number;
    center_entity?: string;
  };
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphStatistics {
  total_nodes: number;
  total_relationships: number;
  node_types: Array<{ label: string; count: number }>;
  relationship_types: Array<{ type: string; count: number }>;
}

export interface EntityCreateRequest {
  entity_type: string;
  properties: Record<string, any>;
}

export interface EntityUpdateRequest {
  properties: Record<string, any>;
}

export interface RelationshipCreateRequest {
  from_entity_id: string;
  from_entity_type: string;
  to_entity_id: string;
  to_entity_type: string;
  relationship_type: string;
  properties?: Record<string, any>;
}

export interface CypherQueryRequest {
  cypher_query: string;
  parameters?: Record<string, any>;
}

export interface EntitySearchRequest {
  entity_types?: string[];
  search_term?: string;
  filters?: Record<string, any>;
  limit?: number;
}

export interface CentralityAnalysis {
  centrality_analysis: Array<{
    entity_id: string;
    entity_name: string;
    entity_type: string;
    degree_centrality: number;
  }>;
}

export interface ShortestPathResult {
  from_entity_id: string;
  to_entity_id: string;
  path_length: number;
  path_found: boolean;
}

export const knowledgeGraphService = {
  // Health and Statistics
  async getHealth(): Promise<{ status: string; connected: boolean }> {
    return api.get('/knowledge-graph/health');
  },

  async getStatistics(): Promise<GraphStatistics> {
    return api.get('/knowledge-graph/statistics');
  },

  // Entity Management
  async createEntity(request: EntityCreateRequest): Promise<GraphEntity> {
    return api.post('/knowledge-graph/entities/', request);
  },

  async getEntity(entityType: string, entityId: string): Promise<GraphEntity> {
    return api.get(`/knowledge-graph/entities/${entityType}/${entityId}`);
  },

  async updateEntity(
    entityType: string,
    entityId: string,
    request: EntityUpdateRequest
  ): Promise<GraphEntity> {
    return api.put(`/knowledge-graph/entities/${entityType}/${entityId}`, request);
  },

  async deleteEntity(entityType: string, entityId: string): Promise<{ message: string }> {
    return api.delete(`/knowledge-graph/entities/${entityType}/${entityId}`);
  },

  // Relationship Management
  async createRelationship(request: RelationshipCreateRequest): Promise<GraphRelationship> {
    return api.post('/knowledge-graph/relationships/', request);
  },

  async getEntityRelationships(
    entityType: string,
    entityId: string,
    direction: 'incoming' | 'outgoing' | 'both' = 'both'
  ): Promise<{ entity_id: string; relationships: any[] }> {
    return api.get(
      `/knowledge-graph/entities/${entityType}/${entityId}/relationships?direction=${direction}`
    );
  },

  // Search and Query
  async searchEntities(request: EntitySearchRequest): Promise<{
    entities: GraphEntity[];
    count: number;
  }> {
    return api.post('/knowledge-graph/search/entities', request);
  },

  async executeCypherQuery(request: CypherQueryRequest): Promise<{
    results: any[];
    count: number;
  }> {
    return api.post('/knowledge-graph/query/cypher', request);
  },

  // Visualization
  async getGraphVisualization(params?: {
    center_entity_id?: string;
    entity_types?: string[];
    depth?: number;
    limit?: number;
  }): Promise<GraphVisualizationData> {
    const queryParams = new URLSearchParams();
    
    if (params?.center_entity_id) {
      queryParams.append('center_entity_id', params.center_entity_id);
    }
    if (params?.entity_types) {
      params.entity_types.forEach(type => queryParams.append('entity_types', type));
    }
    if (params?.depth) {
      queryParams.append('depth', params.depth.toString());
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }

    const url = `/knowledge-graph/visualization/graph${
      queryParams.toString() ? `?${queryParams.toString()}` : ''
    }`;
    
    return api.get(url);
  },

  // Analytics
  async getCentralityAnalysis(params?: {
    entity_type?: string;
    limit?: number;
  }): Promise<CentralityAnalysis> {
    const queryParams = new URLSearchParams();
    
    if (params?.entity_type) {
      queryParams.append('entity_type', params.entity_type);
    }
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }

    const url = `/knowledge-graph/analytics/centrality${
      queryParams.toString() ? `?${queryParams.toString()}` : ''
    }`;
    
    return api.get(url);
  },

  async getShortestPath(
    fromEntityId: string,
    toEntityId: string,
    maxDepth: number = 6
  ): Promise<ShortestPathResult> {
    const queryParams = new URLSearchParams({
      from_entity_id: fromEntityId,
      to_entity_id: toEntityId,
      max_depth: maxDepth.toString()
    });

    return api.get(`/knowledge-graph/analytics/shortest-path?${queryParams.toString()}`);
  },

  // Utility Methods
  async createSampleAccount(accountData: {
    name: string;
    account_number: string;
    account_type: string;
    base_currency: string;
  }): Promise<GraphEntity> {
    return this.createEntity({
      entity_type: 'Account',
      properties: {
        ...accountData,
        id: `acc_${Date.now()}`,
        status: 'ACTIVE'
      }
    });
  },

  async createSampleSecurity(securityData: {
    name: string;
    symbol: string;
    security_type: string;
    currency: string;
    exchange?: string;
  }): Promise<GraphEntity> {
    return this.createEntity({
      entity_type: 'Security',
      properties: {
        ...securityData,
        id: `sec_${securityData.symbol.toLowerCase()}`,
      }
    });
  },

  async createHolding(
    accountId: string,
    securityId: string,
    holdingData: {
      quantity: number;
      market_value: number;
      book_cost: number;
    }
  ): Promise<GraphRelationship> {
    return this.createRelationship({
      from_entity_id: accountId,
      from_entity_type: 'Account',
      to_entity_id: securityId,
      to_entity_type: 'Security',
      relationship_type: 'HOLDS',
      properties: {
        ...holdingData,
        as_of_date: new Date().toISOString()
      }
    });
  },

  // Common queries for banking use cases
  async getAccountPortfolio(accountId: string): Promise<{
    account: GraphEntity;
    holdings: any[];
  }> {
    const cypherQuery = `
      MATCH (account:Account {id: $accountId})
      OPTIONAL MATCH (account)-[holds:HOLDS]->(security:Security)
      RETURN account, 
             collect({
               security: security,
               relationship: holds
             }) as holdings
    `;

    const result = await this.executeCypherQuery({
      cypher_query: cypherQuery,
      parameters: { accountId }
    });

    if (result.results.length > 0) {
      const record = result.results[0];
      return {
        account: record.account,
        holdings: record.holdings || []
      };
    }

    throw new Error('Account not found');
  },

  async getSecurityHolders(securityId: string): Promise<{
    security: GraphEntity;
    holders: any[];
  }> {
    const cypherQuery = `
      MATCH (security:Security {id: $securityId})
      OPTIONAL MATCH (account:Account)-[holds:HOLDS]->(security)
      RETURN security,
             collect({
               account: account,
               relationship: holds
             }) as holders
    `;

    const result = await this.executeCypherQuery({
      cypher_query: cypherQuery,
      parameters: { securityId }
    });

    if (result.results.length > 0) {
      const record = result.results[0];
      return {
        security: record.security,
        holders: record.holders || []
      };
    }

    throw new Error('Security not found');
  },

  async getDataLineage(mcpServerId: string): Promise<{
    server: GraphEntity;
    workflows: GraphEntity[];
    dataStreams: GraphEntity[];
  }> {
    const cypherQuery = `
      MATCH (server:MCPServer {id: $mcpServerId})
      OPTIONAL MATCH (workflow:Workflow)-[:CONNECTS_TO]->(server)
      OPTIONAL MATCH (server)-[:PROVIDES_DATA]->(stream:DataStream)
      RETURN server,
             collect(DISTINCT workflow) as workflows,
             collect(DISTINCT stream) as dataStreams
    `;

    const result = await this.executeCypherQuery({
      cypher_query: cypherQuery,
      parameters: { mcpServerId }
    });

    if (result.results.length > 0) {
      const record = result.results[0];
      return {
        server: record.server,
        workflows: record.workflows || [],
        dataStreams: record.dataStreams || []
      };
    }

    throw new Error('MCP Server not found');
  }
};