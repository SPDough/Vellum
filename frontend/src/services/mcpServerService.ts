import { api } from './api';
import { MCPServer } from '@/types/data';

export interface MCPServerCreateRequest {
  name: string;
  provider_type: string;
  base_url: string;
  auth_type: string;
  auth_config: Record<string, any>;
  capabilities: string[];
  description?: string;
}

export interface MCPServerUpdateRequest {
  name?: string;
  base_url?: string;
  auth_config?: Record<string, any>;
  capabilities?: string[];
  description?: string;
  enabled?: boolean;
}

export interface MCPServerTestResult {
  server_id: string;
  success: boolean;
  response_time_ms: number;
  error_message?: string;
  capabilities_discovered: string[];
  tested_at: string;
}

export interface MCPServerMetrics {
  server_id: string;
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  average_response_time_ms: number;
  last_24h_requests: number;
  uptime_percentage: number;
}

export const mcpServerService = {
  // List all MCP servers
  async listServers(params?: {
    provider_type?: string;
    enabled_only?: boolean;
  }): Promise<MCPServer[]> {
    const queryParams = new URLSearchParams();
    if (params?.provider_type) {
      queryParams.append('provider_type', params.provider_type);
    }
    if (params?.enabled_only) {
      queryParams.append('enabled_only', params.enabled_only.toString());
    }
    
    const url = `/mcp-servers/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<MCPServer[]>(url);
  },

  // Create a new MCP server
  async createServer(serverData: MCPServerCreateRequest): Promise<MCPServer> {
    return api.post<MCPServer>('/mcp-servers/', serverData);
  },

  // Get a specific MCP server
  async getServer(serverId: string): Promise<MCPServer> {
    return api.get<MCPServer>(`/mcp-servers/${serverId}`);
  },

  // Update an MCP server
  async updateServer(serverId: string, updateData: MCPServerUpdateRequest): Promise<MCPServer> {
    return api.put<MCPServer>(`/mcp-servers/${serverId}`, updateData);
  },

  // Delete an MCP server
  async deleteServer(serverId: string): Promise<{ message: string }> {
    return api.delete(`/mcp-servers/${serverId}`);
  },

  // Test MCP server connection
  async testServer(serverId: string): Promise<MCPServerTestResult> {
    return api.post<MCPServerTestResult>(`/mcp-servers/${serverId}/test`);
  },

  // Enable an MCP server
  async enableServer(serverId: string): Promise<{ message: string }> {
    return api.post(`/mcp-servers/${serverId}/enable`);
  },

  // Disable an MCP server
  async disableServer(serverId: string): Promise<{ message: string }> {
    return api.post(`/mcp-servers/${serverId}/disable`);
  },

  // Get server capabilities
  async getServerCapabilities(serverId: string): Promise<{ server_id: string; capabilities: any[] }> {
    return api.get(`/mcp-servers/${serverId}/capabilities`);
  },

  // Get server metrics
  async getServerMetrics(serverId: string): Promise<MCPServerMetrics> {
    return api.get<MCPServerMetrics>(`/mcp-servers/${serverId}/metrics`);
  },

  // Call a tool on an MCP server
  async callTool(serverId: string, toolName: string, parameters: Record<string, any>): Promise<{
    server_id: string;
    tool_name: string;
    result: any;
    timestamp: string;
  }> {
    return api.post(`/mcp-servers/${serverId}/call`, null, {
      params: { tool_name: toolName },
      data: parameters
    });
  },
};