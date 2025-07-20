import { api } from './api';
import { DataStream } from '@/types/data';

export interface DataStreamCreateRequest {
  name: string;
  data_type: string;
  source_mcp_server_id: string;
  description?: string;
  buffer_size?: number;
  batch_size?: number;
  polling_interval_seconds?: number;
}

export interface DataStreamUpdateRequest {
  name?: string;
  description?: string;
  buffer_size?: number;
  batch_size?: number;
  polling_interval_seconds?: number;
  enabled?: boolean;
}

export interface DataStreamMetrics {
  stream_id: string;
  total_records_processed: number;
  records_last_hour: number;
  records_last_24h: number;
  average_latency_ms: number;
  error_rate_percentage: number;
  uptime_percentage: number;
  current_buffer_usage: number;
  peak_throughput_rps: number;
  last_error?: string;
  last_error_time?: string;
}

export interface StreamSubscription {
  subscriber_id: string;
  callback_url?: string;
  webhook_secret?: string;
  filters?: Record<string, any>;
}

export interface StreamDataResponse {
  stream_id: string;
  total_records: number;
  offset: number;
  limit: number;
  records: any[];
}

export const dataStreamService = {
  // List all data streams
  async listStreams(params?: {
    data_type?: string;
    status?: string;
    enabled_only?: boolean;
  }): Promise<DataStream[]> {
    const queryParams = new URLSearchParams();
    if (params?.data_type) {
      queryParams.append('data_type', params.data_type);
    }
    if (params?.status) {
      queryParams.append('status', params.status);
    }
    if (params?.enabled_only) {
      queryParams.append('enabled_only', params.enabled_only.toString());
    }
    
    const url = `/data-streams/${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<DataStream[]>(url);
  },

  // Create a new data stream
  async createStream(streamData: DataStreamCreateRequest): Promise<DataStream> {
    return api.post<DataStream>('/data-streams/', streamData);
  },

  // Get a specific data stream
  async getStream(streamId: string): Promise<DataStream> {
    return api.get<DataStream>(`/data-streams/${streamId}`);
  },

  // Update a data stream
  async updateStream(streamId: string, updateData: DataStreamUpdateRequest): Promise<DataStream> {
    return api.put<DataStream>(`/data-streams/${streamId}`, updateData);
  },

  // Delete a data stream
  async deleteStream(streamId: string): Promise<{ message: string }> {
    return api.delete(`/data-streams/${streamId}`);
  },

  // Start a data stream
  async startStream(streamId: string): Promise<{ message: string }> {
    return api.post(`/data-streams/${streamId}/start`);
  },

  // Pause a data stream
  async pauseStream(streamId: string): Promise<{ message: string }> {
    return api.post(`/data-streams/${streamId}/pause`);
  },

  // Stop a data stream
  async stopStream(streamId: string): Promise<{ message: string }> {
    return api.post(`/data-streams/${streamId}/stop`);
  },

  // Get stream metrics
  async getStreamMetrics(streamId: string): Promise<DataStreamMetrics> {
    return api.get<DataStreamMetrics>(`/data-streams/${streamId}/metrics`);
  },

  // Subscribe to a stream
  async subscribeToStream(streamId: string, subscription: StreamSubscription): Promise<{
    subscription_id: string;
    message: string;
  }> {
    return api.post(`/data-streams/${streamId}/subscribe`, subscription);
  },

  // Unsubscribe from a stream
  async unsubscribeFromStream(streamId: string, subscriptionId: string): Promise<{ message: string }> {
    return api.delete(`/data-streams/${streamId}/subscribe/${subscriptionId}`);
  },

  // List stream subscribers
  async listStreamSubscribers(streamId: string): Promise<{
    stream_id: string;
    subscribers: any[];
  }> {
    return api.get(`/data-streams/${streamId}/subscribers`);
  },

  // Get stream data
  async getStreamData(streamId: string, params?: {
    limit?: number;
    offset?: number;
    start_time?: string;
    end_time?: string;
  }): Promise<StreamDataResponse> {
    const queryParams = new URLSearchParams();
    if (params?.limit) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset) {
      queryParams.append('offset', params.offset.toString());
    }
    if (params?.start_time) {
      queryParams.append('start_time', params.start_time);
    }
    if (params?.end_time) {
      queryParams.append('end_time', params.end_time);
    }
    
    const url = `/data-streams/${streamId}/data${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return api.get<StreamDataResponse>(url);
  },
};